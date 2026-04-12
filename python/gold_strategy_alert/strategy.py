"""Strategy state machine and decision engine skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from collections.abc import Sequence
from copy import deepcopy

from bar_aggregator import aggregate_minute_ticks_to_bars
from config import AppConfig
from indicators import calculate_bollinger_bands, calculate_donchian_channels, calculate_ema
from models import (
    ActionType,
    Bar,
    DailyMarketSnapshot,
    DecisionOutput,
    ExecutionMode,
    EventType,
    ExitReason,
    FeeBreakdown,
    IndicatorSnapshot,
    MarketRegime,
    PositionState,
    PriceTick,
    StrategyEvent,
    StrategyMode,
    SignalType,
    StrategyDecision,
    StrategyStepResult,
    StrategyPhase,
    StrategyRuntimeState,
)
from regime import classify_regime
from risk_gate import evaluate_long_risk_gate


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class StrategyInput:
    now: datetime
    current_tick: PriceTick | None
    next_minute_tick: PriceTick | None
    indicator_snapshot: IndicatorSnapshot
    daily_snapshot: DailyMarketSnapshot | None
    daily_snapshot_fallback_used: bool
    in_trading_window: bool
    recent_minute_ticks: Sequence[PriceTick] = ()
    force_flatten: bool = False


class StrategyEngine:
    """Centralizes state transitions and strategy decisions."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def evaluate(self, runtime_state: StrategyRuntimeState, data: StrategyInput) -> StrategyDecision | None:
        """Evaluate strategy rules for the current decision point.

        Phase 1 only defines the state-machine entry point and the transitions
        we expect to support in later phases.
        """
        LOGGER.info(
            "Evaluating strategy phase=%s in_window=%s allow_long=%s",
            runtime_state.phase.value,
            data.in_trading_window,
            data.indicator_snapshot.allow_long,
        )

        if runtime_state.phase == StrategyPhase.ERROR:
            return StrategyDecision(
                signal_type=SignalType.ERROR,
                should_send_email=True,
                title="Strategy runtime in error state",
                summary="Manual inspection required before new decisions are trusted.",
                event_key="strategy_error_state",
                allow_long=data.indicator_snapshot.allow_long,
                indicators=data.indicator_snapshot,
            )

        return None

    @staticmethod
    def classify_exit_reason(reason: str) -> ExitReason:
        return ExitReason(reason)


def evaluate_allow_long(snapshot: DailyMarketSnapshot | None) -> tuple[bool, float | None]:
    if snapshot is None:
        return False, None
    r_day = (snapshot.last - snapshot.low) / (snapshot.high - snapshot.low + 1e-9)
    allow_long = (snapshot.last > snapshot.open) and (r_day >= 0.60)
    return allow_long, r_day


def evaluate_entry_signal(
    state: StrategyRuntimeState,
    indicators: IndicatorSnapshot,
    in_trading_window: bool,
) -> bool:
    if state.phase != StrategyPhase.OBSERVING:
        return False
    if not in_trading_window:
        return False
    if not indicators.allow_long:
        return False
    if indicators.close_5m is None or indicators.ema_fast is None or indicators.ema_slow is None:
        return False
    if indicators.donchian_entry_high is None:
        return False
    return (
        indicators.ema_fast > indicators.ema_slow
        and indicators.close_5m > indicators.donchian_entry_high
    )


def resolve_pending_entry_fill(
    state: StrategyRuntimeState,
    candidate_ticks: Sequence[PriceTick],
    now: datetime,
    send_cancel_notification: bool,
    position_size_grams: float = 0.0,
) -> tuple[StrategyRuntimeState, StrategyDecision | None, list[StrategyEvent]]:
    next_state = deepcopy(state)
    if next_state.phase != StrategyPhase.WAITING_FOR_ENTRY_FILL:
        return next_state, None, []

    valid_ticks = sorted(candidate_ticks, key=lambda tick: tick.observed_at)
    valid_fill_tick = valid_ticks[0] if valid_ticks else None
    if valid_fill_tick is not None:
        entry_price = valid_fill_tick.price
        current_stop_loss = next_state.pending_entry_stop_price
        next_state.phase = StrategyPhase.HOLDING
        next_state.position = PositionState(
            has_position=True,
            size_grams=position_size_grams,
            entry_price=entry_price,
            entry_time=valid_fill_tick.observed_at,
            current_stop_loss=current_stop_loss,
            trailing_active=False,
            h_star=entry_price,
        )
        next_state.pending_entry_signal_time = None
        next_state.pending_entry_deadline = None
        next_state.pending_entry_reference_bar_time = None
        next_state.pending_entry_atr = None
        next_state.pending_entry_stop_price = None
        next_state.pending_entry_reason = None
        event = StrategyEvent(
            event_type=EventType.ENTRY_FILLED,
            event_time=valid_fill_tick.observed_at,
            phase_before=state.phase,
            phase_after=next_state.phase,
            title="Entry filled",
            message=f"Entry filled at {entry_price:.2f}",
            event_key="entry_filled",
            metadata={"entry_price": entry_price},
        )
        decision = StrategyDecision(
            signal_type=SignalType.BUY,
            should_send_email=True,
            title="Entry filled",
            summary=f"Simulated entry filled at {entry_price:.2f}",
            event_key="entry_filled",
            price=entry_price,
        )
        return next_state, decision, [event]

    if next_state.pending_entry_deadline is not None and now > next_state.pending_entry_deadline:
        next_state.phase = StrategyPhase.OBSERVING
        next_state.position = PositionState()
        next_state.pending_entry_signal_time = None
        next_state.pending_entry_deadline = None
        next_state.pending_entry_reference_bar_time = None
        next_state.pending_entry_atr = None
        next_state.pending_entry_stop_price = None
        next_state.pending_entry_reason = None
        event = StrategyEvent(
            event_type=EventType.ENTRY_TIMEOUT_CANCELLED,
            event_time=now,
            phase_before=state.phase,
            phase_after=next_state.phase,
            title="Pending entry canceled",
            message="No valid next-minute price arrived before deadline.",
            level="WARNING",
            event_key="pending_entry_canceled",
        )
        decision = StrategyDecision(
            signal_type=SignalType.WARNING,
            should_send_email=send_cancel_notification,
            title="Pending entry canceled",
            summary="No valid next-minute price arrived before deadline.",
            event_key="pending_entry_canceled",
        )
        return next_state, decision, [event]

    return next_state, None, []


def evaluate_exit_conditions(
    state: StrategyRuntimeState,
    current_price: float,
    indicators: IndicatorSnapshot,
    completed_bars: Sequence[Bar],
    now: datetime,
    recent_minute_ticks: Sequence[PriceTick] = (),
    config: AppConfig | None = None,
) -> StrategyDecision | None:
    config = config or AppConfig()
    if state.phase != StrategyPhase.HOLDING or not _has_valid_position_fields(state.position):
        return None
    entry_price = state.position.entry_price
    assert entry_price is not None

    same_confirmation_bar = (
        state.position.entry_bar_time is not None
        and indicators.bar_time is not None
        and indicators.bar_time <= state.position.entry_bar_time
    )

    stop_price = state.position.current_stop_loss
    if stop_price is not None and current_price <= stop_price:
        return StrategyDecision(
            signal_type=SignalType.SELL,
            should_send_email=True,
            title="Structure stop triggered",
            summary="Structure stop was breached.",
            event_key="exit_structure_stop",
            price=current_price,
            exit_reason=ExitReason.INITIAL_STOP,
        )

    if same_confirmation_bar:
        return None

    bars_3m = aggregate_minute_ticks_to_bars(
        recent_minute_ticks,
        bar_minutes=3,
        allow_incomplete_window=False,
    )
    if len(bars_3m) >= 2:
        closes_3m = [bar.close for bar in bars_3m]
        ema20_3m = calculate_ema(closes_3m, config.indicators.ema_fast_period)
        _, donchian10_lower = calculate_donchian_channels(bars_3m, config.indicators.donchian_exit_period)
        last_3m = bars_3m[-1]
        prev_3m = bars_3m[-2]
        ema20_signal = ema20_3m[-1] if ema20_3m else None
        donchian10_signal = donchian10_lower[-1] if donchian10_lower else None

        if donchian10_signal is not None and last_3m.close < donchian10_signal:
            return StrategyDecision(
                signal_type=SignalType.SELL,
                should_send_email=True,
                title="Donchian exit triggered",
                summary="Latest closed 3m bar closed below Donchian10 lower band.",
                event_key="exit_donchian_10",
                price=current_price,
                exit_reason=ExitReason.DONCHIAN_EXIT,
            )

        if ema20_signal is not None and last_3m.close < ema20_signal and last_3m.close < prev_3m.low:
            return StrategyDecision(
                signal_type=SignalType.SELL,
                should_send_email=True,
                title="Structure invalidation exit",
                summary="Latest closed 3m bar lost EMA20 and closed below the previous 3m low.",
                event_key="exit_structure_invalidation",
                price=current_price,
                exit_reason=ExitReason.STRUCTURE_EXIT,
            )

    if state.position.trailing_active and state.position.h_star is not None and current_price < state.position.h_star:
        return StrategyDecision(
            signal_type=SignalType.SELL,
            should_send_email=True,
            title="Trailing structure exit",
            summary="Price failed to extend after activation and structure softened.",
            event_key="exit_trailing_structure",
            price=current_price,
            exit_reason=ExitReason.TRAILING_STOP,
        )

    return None


def evaluate_reentry_eligibility(
    state: StrategyRuntimeState,
    completed_bars: Sequence[Bar],
    indicators: IndicatorSnapshot,
) -> bool:
    if state.phase != StrategyPhase.WAITING_REENTRY_CONFIRMATION:
        return False
    if len(completed_bars) < 12:
        return False
    if indicators.close_5m is None or indicators.atr is None:
        return False
    if indicators.ema_fast is None or indicators.ema_slow is None:
        return False
    post_exit_12bar_high = max(bar.close for bar in completed_bars[-12:])
    return (
        indicators.close_5m > post_exit_12bar_high + 0.2 * indicators.atr
        and indicators.ema_fast > indicators.ema_slow
    )


def _round_price_bucket(price: float | None) -> str:
    if price is None:
        return "na"
    return f"{round(price / 0.5) * 0.5:.1f}"


def _build_fee_breakdown(config: AppConfig) -> FeeBreakdown:
    round_trip_fee_floor = config.risk.default_entry_notional_yuan * (
        1 - (1 - config.fees.buy_fee_rate) * (1 - config.fees.sell_fee_rate)
    )
    return FeeBreakdown(
        buy_fee_rate=config.fees.buy_fee_rate,
        sell_fee_rate=config.fees.sell_fee_rate,
        round_trip_fee_floor_yuan=round_trip_fee_floor,
    )


def _build_decision_output(
    *,
    action: ActionType,
    strategy_mode: StrategyMode,
    regime: MarketRegime,
    confidence: float,
    entry_reason: str,
    invalidation_reason: str,
    stop_rule: str,
    take_profit_rule: str,
    position_size_yuan: float,
    config: AppConfig,
    timestamp: datetime,
    price_for_dedupe: float | None,
    bar_time: datetime | None,
    position_state_version: int,
    should_send_email: bool,
) -> DecisionOutput:
    dedupe_key = (
        f"{action.value}|{strategy_mode.value}|{_round_price_bucket(price_for_dedupe)}|"
        f"{bar_time.isoformat() if bar_time else timestamp.isoformat()}|{position_state_version}"
    )
    subject = f"ICBC Gold {action.value} {strategy_mode.value} {confidence:.2f}"
    body = (
        f"{action.value} {position_size_yuan:.0f} CNY; "
        f"{strategy_mode.value}; stop={stop_rule}; tp={take_profit_rule}"
    )
    return DecisionOutput(
        action=action,
        strategy_mode=strategy_mode,
        confidence=confidence,
        regime=regime,
        entry_reason=entry_reason,
        invalidation_reason=invalidation_reason,
        stop_rule=stop_rule,
        take_profit_rule=take_profit_rule,
        position_size_yuan=position_size_yuan,
        fees_considered=_build_fee_breakdown(config),
        whether_send_email=should_send_email,
        short_email_subject=subject,
        short_email_body=body,
        timestamp=timestamp,
        dedupe_key=dedupe_key,
    )


def _infer_entry_mode(
    indicators: IndicatorSnapshot,
    regime: MarketRegime,
    completed_bars: Sequence[Bar],
    recent_minute_ticks: Sequence[PriceTick],
    config: AppConfig | None = None,
) -> tuple[StrategyMode, float, float | None, str, str, str] | None:
    config = config or AppConfig()
    if indicators.close_5m is None or indicators.atr is None or not completed_bars:
        return None

    bars_3m = aggregate_minute_ticks_to_bars(recent_minute_ticks, bar_minutes=3, allow_incomplete_window=False)
    if len(bars_3m) < 2:
        return None

    last_3m = bars_3m[-1]
    prev_3m = bars_3m[-2]
    close = indicators.close_5m
    closes_3m = [bar.close for bar in bars_3m]
    ema20_3m = calculate_ema(closes_3m, config.indicators.ema_fast_period)
    _, bb_upper_3m, bb_lower_3m, bandwidth_3m = calculate_bollinger_bands(
        closes_3m,
        config.indicators.bollinger_period,
        config.indicators.bollinger_stddev,
    )
    ema20_signal = ema20_3m[-1] if ema20_3m else None
    bb_upper_signal = bb_upper_3m[-1] if bb_upper_3m else None

    if (
        config.strategy_switches.enable_r2
        and
        regime in {MarketRegime.TREND_UP, MarketRegime.PULLBACK_READY}
        and indicators.ema_fast is not None
        and indicators.ema_slow is not None
        and indicators.ema_fast > indicators.ema_slow
        and ema20_signal is not None
        and bb_upper_signal is not None
    ):
        touched_ema20 = last_3m.low <= ema20_signal <= last_3m.high
        reclaimed_ema20 = last_3m.close > ema20_signal
        cleared_prev_high = last_3m.close > prev_3m.high
        not_outside_upper_band = last_3m.close <= bb_upper_signal
        if touched_ema20 and reclaimed_ema20 and cleared_prev_high and not_outside_upper_band:
            stop_price = last_3m.low
            return (
                StrategyMode.R2_PULLBACK,
                0.74,
                stop_price,
                "Trend-up pullback touched 3m EMA20, reclaimed it on close, and closed above the prior 3m high.",
                f"signal_bar_low={stop_price:.2f}",
                "Exit on 3m Donchian10 failure, 3m EMA20 structure failure, or 22:20 flatten.",
            )

    if config.strategy_switches.enable_r1 and regime in {MarketRegime.BREAKOUT_READY, MarketRegime.TREND_UP} and len(bars_3m) >= 21:
        donchian_upper, donchian_lower = calculate_donchian_channels(bars_3m, config.indicators.donchian_entry_period)
        upper_now = donchian_upper[-1]
        box_low = donchian_lower[-1]
        bw_now = bandwidth_3m[-1] if bandwidth_3m else None
        bw_prev = bandwidth_3m[-2] if len(bandwidth_3m) >= 2 else None
        if upper_now is not None and box_low is not None and bw_now is not None and bw_prev is not None:
            if last_3m.close > upper_now and bw_now > bw_prev and last_3m.close > last_3m.open:
                return (
                    StrategyMode.R1_BREAKOUT,
                    0.76,
                    box_low,
                    "3m close broke above Donchian20 with expanding Bollinger bandwidth and a bullish close.",
                    f"box_low={box_low:.2f}",
                    "Exit on 3m Donchian10 breakdown, 3m EMA20 structure failure, or 22:20 flatten.",
                )

    if config.strategy_switches.enable_l1 and regime == MarketRegime.EXHAUSTION_REVERSAL_READY and len(bars_3m) >= 20:
        _, _, lower_band, _ = calculate_bollinger_bands(closes_3m, 20, 2.0)
        if len(bars_3m) >= 2 and lower_band[-1] is not None and lower_band[-2] is not None:
            if bars_3m[-2].close < lower_band[-2] and bars_3m[-1].close >= lower_band[-1]:
                stop_price = min(bar.low for bar in bars_3m[-3:])
                return (
                    StrategyMode.L1_EXHAUSTION,
                    0.58,
                    stop_price,
                    "Price broke below the lower Bollinger band and then closed back inside.",
                    f"extreme_low={stop_price:.2f}",
                    "Mean reversion exit first, otherwise flatten on structure failure or 22:20.",
                )

    return None


def _compute_realized_pnl_yuan(
    *,
    entry_price: float,
    exit_price: float,
    size_grams: float,
    buy_fee_rate: float,
    sell_fee_rate: float,
) -> float:
    gross = (exit_price - entry_price) * size_grams
    fees = (entry_price * size_grams * buy_fee_rate) + (exit_price * size_grams * sell_fee_rate)
    return gross - fees


def _has_valid_position_fields(position: PositionState) -> bool:
    return (
        position.has_position
        and position.entry_price is not None
        and position.entry_time is not None
        and position.size_grams > 0
    )


def _compute_unrealized_pnl_yuan(
    *,
    entry_price: float | None,
    current_price: float | None,
    size_grams: float,
    buy_fee_rate: float,
    sell_fee_rate: float,
) -> float | None:
    if entry_price is None or current_price is None or size_grams <= 0:
        return None
    return _compute_realized_pnl_yuan(
        entry_price=entry_price,
        exit_price=current_price,
        size_grams=size_grams,
        buy_fee_rate=buy_fee_rate,
        sell_fee_rate=sell_fee_rate,
    )


def evaluate_strategy_step(
    state: StrategyRuntimeState,
    data: StrategyInput,
    completed_bars: Sequence[Bar],
    send_entry_cancel_notification: bool = True,
    fee_break_even_multiplier: float = 1.01005,
    position_size_grams: float = 0.0,
    manual_entry_required: bool = False,
    config: AppConfig | None = None,
    buy_fee_rate: float = 0.005,
    sell_fee_rate: float = 0.005,
) -> StrategyStepResult:
    config = config or AppConfig()
    next_state = deepcopy(state)
    if next_state.phase == StrategyPhase.HOLDING and not _has_valid_position_fields(next_state.position):
        next_state.phase = StrategyPhase.OBSERVING
    trading_day = data.now.date().isoformat()
    if next_state.trading_day != trading_day:
        next_state.trading_day = trading_day
        next_state.entries_today_count = 0
        next_state.daily_realized_pnl_yuan = 0.0
        next_state.consecutive_loss_trades = 0
    next_state.last_decision_time = data.now
    regime, regime_confidence = classify_regime(completed_bars, data.indicator_snapshot, data.recent_minute_ticks)

    def result(
        *,
        signal_type: SignalType | None = None,
        exit_reason: ExitReason | None = None,
        should_notify: bool = False,
        decision_message: str = "",
        action: ActionType = ActionType.WAIT_NO_TRADE,
        strategy_mode: StrategyMode = StrategyMode.NONE,
        confidence: float | None = None,
        entry_reason: str = "",
        invalidation_reason: str = "",
        stop_rule: str = "n/a",
        take_profit_rule: str = "n/a",
        price_for_dedupe: float | None = None,
        generated_events: list[StrategyEvent] | None = None,
    ) -> StrategyStepResult:
        effective_confidence = confidence if confidence is not None else regime_confidence
        effective_action = action
        if (
            effective_action == ActionType.BUY_NOW
            and next_state.execution_mode == ExecutionMode.SIGNAL_IMPLIES_POSITION
            and not _has_valid_position_fields(next_state.position)
        ):
            effective_action = ActionType.WAIT_NO_TRADE
        elif effective_action == ActionType.SELL_NOW and not _has_valid_position_fields(state.position):
            effective_action = ActionType.HOLD_POSITION if _has_valid_position_fields(next_state.position) else ActionType.WAIT_NO_TRADE
        elif effective_action == ActionType.HOLD_POSITION and not _has_valid_position_fields(next_state.position):
            effective_action = ActionType.WAIT_NO_TRADE
        elif effective_action == ActionType.WAIT_NO_TRADE and _has_valid_position_fields(next_state.position):
            effective_action = ActionType.HOLD_POSITION

        decision_output = _build_decision_output(
            action=effective_action,
            strategy_mode=strategy_mode,
            regime=regime,
            confidence=effective_confidence,
            entry_reason=entry_reason or decision_message,
            invalidation_reason=invalidation_reason,
            stop_rule=stop_rule,
            take_profit_rule=take_profit_rule,
            position_size_yuan=config.risk.default_entry_notional_yuan,
            config=config,
            timestamp=data.now,
            price_for_dedupe=price_for_dedupe if price_for_dedupe is not None else data.current_tick.price if data.current_tick else data.indicator_snapshot.close_5m,
            bar_time=data.indicator_snapshot.bar_time,
            position_state_version=state.position_state_version,
            should_send_email=should_notify,
        )
        current_price = data.current_tick.price if data.current_tick else data.indicator_snapshot.close_5m
        decision_output.execution_mode = next_state.execution_mode.value
        decision_output.profile_name = next_state.profile_name.value
        decision_output.has_position = _has_valid_position_fields(next_state.position)
        decision_output.position_size_grams = next_state.position.size_grams
        decision_output.avg_entry_price = next_state.position.entry_price
        decision_output.unrealized_pnl_yuan = _compute_unrealized_pnl_yuan(
            entry_price=next_state.position.entry_price,
            current_price=current_price,
            size_grams=next_state.position.size_grams,
            buy_fee_rate=buy_fee_rate,
            sell_fee_rate=sell_fee_rate,
        )
        decision_output.paused_new_entries = next_state.paused_new_entries
        decision_output.cooldown_status = (
            f"until {next_state.cooldown_end_time.isoformat()}"
            if next_state.cooldown_end_time and next_state.cooldown_end_time > data.now
            else "none"
        )
        decision_output.operator_hint = (
            "Manual sync real position after your broker-side buy/sell."
            if next_state.execution_mode == ExecutionMode.MANUAL_POSITION_SYNC
            else "Internal position ledger follows signal outputs automatically."
        )
        return StrategyStepResult(
            next_state=next_state.phase,
            signal_type=signal_type,
            exit_reason=exit_reason,
            should_notify=should_notify,
            decision_message=decision_message,
            action=effective_action,
            strategy_mode=strategy_mode,
            regime=regime,
            confidence=effective_confidence,
            decision_output=decision_output,
            generated_events=generated_events or [],
            updated_runtime_state=next_state,
        )

    if next_state.phase == StrategyPhase.ERROR:
        return result(
            signal_type=SignalType.ERROR,
            should_notify=True,
            decision_message="Strategy runtime is in error state.",
            action=ActionType.WAIT_NO_TRADE,
            generated_events=[
                StrategyEvent(
                    event_type=EventType.ERROR,
                    event_time=data.now,
                    phase_before=state.phase,
                    phase_after=next_state.phase,
                    message="Strategy runtime is in error state.",
                    title="Strategy error state",
                )
            ],
        )

    if next_state.phase == StrategyPhase.WAITING_FOR_ENTRY_FILL:
        next_state.phase = StrategyPhase.OBSERVING

    if next_state.phase == StrategyPhase.COOLDOWN_AFTER_STOP:
        if next_state.cooldown_end_time is not None and data.now >= next_state.cooldown_end_time:
            previous = next_state.phase
            next_state.phase = StrategyPhase.OBSERVING
            return result(
                decision_message="Cooldown ended; back to observing.",
                action=ActionType.WAIT_NO_TRADE,
                generated_events=[
                    StrategyEvent(
                        event_type=EventType.COOLDOWN_STARTED,
                        event_time=data.now,
                        phase_before=previous,
                        phase_after=next_state.phase,
                        message="Cooldown completed; returning to observing.",
                        title="Cooldown completed",
                    )
                ],
            )
        return result(decision_message="In cooldown; no new entry allowed.", action=ActionType.WAIT_NO_TRADE)

    if next_state.phase == StrategyPhase.WAITING_REENTRY_CONFIRMATION:
        if len([bar for bar in completed_bars if bar.is_complete]) < 12:
            return result(decision_message="Waiting for 12 completed bars after exit.", action=ActionType.WAIT_NO_TRADE)
        if evaluate_reentry_eligibility(next_state, completed_bars, data.indicator_snapshot):
            previous = next_state.phase
            next_state.phase = StrategyPhase.OBSERVING
            return result(
                decision_message="Reentry confirmation ready.",
                action=ActionType.WAIT_NO_TRADE,
                generated_events=[
                    StrategyEvent(
                        event_type=EventType.REENTRY_CONFIRMATION_READY,
                        event_time=data.now,
                        phase_before=previous,
                        phase_after=next_state.phase,
                        message="Reentry confirmation condition satisfied.",
                        title="Reentry confirmation ready",
                    )
                ],
            )
        return result(decision_message="Waiting for reentry confirmation.", action=ActionType.WAIT_NO_TRADE)

    if next_state.phase == StrategyPhase.HOLDING:
        if not _has_valid_position_fields(next_state.position):
            return result(
                decision_message="Position fields are incomplete; suppressing hold/sell transition.",
                action=ActionType.WAIT_NO_TRADE,
                strategy_mode=StrategyMode.NONE,
            )
        if data.current_tick is None:
            return result(
                decision_message="Current tick missing while holding.",
                action=ActionType.HOLD_POSITION,
                strategy_mode=StrategyMode.NONE,
            )
        if data.force_flatten:
            current_price = data.current_tick.price
            realized_pnl = _compute_realized_pnl_yuan(
                entry_price=next_state.position.entry_price or current_price,
                exit_price=current_price,
                size_grams=next_state.position.size_grams,
                buy_fee_rate=buy_fee_rate,
                sell_fee_rate=sell_fee_rate,
            )
            next_state.daily_realized_pnl_yuan += realized_pnl
            next_state.consecutive_loss_trades = 0 if realized_pnl >= 0 else next_state.consecutive_loss_trades + 1
            next_state.position_state_version += 1
            next_state.phase = StrategyPhase.OBSERVING
            next_state.last_exit_time = data.now
            next_state.last_exit_reason = ExitReason.FORCE_FLATTEN
            next_state.position = PositionState()
            next_state.force_flatten_requested = False
            next_state.batches_used = 0
            return result(
                signal_type=SignalType.SELL,
                exit_reason=ExitReason.FORCE_FLATTEN,
                should_notify=True,
                decision_message="Forced flatten window reached.",
                action=ActionType.SELL_NOW,
                strategy_mode=StrategyMode.TIME_EXIT,
                confidence=0.99,
                invalidation_reason="Force flatten before end of session.",
                stop_rule="force_flatten",
                take_profit_rule="Immediate flatten.",
                generated_events=[
                    StrategyEvent(
                        event_type=EventType.EXIT_TRIGGERED,
                        event_time=data.now,
                        phase_before=state.phase,
                        phase_after=next_state.phase,
                        message="Forced flatten window reached.",
                        title="Force flatten exit",
                        event_key="force_flatten_exit",
                        metadata={"exit_reason": ExitReason.FORCE_FLATTEN.value},
                    )
                ],
            )
        decision = evaluate_exit_conditions(
            next_state,
            data.current_tick.price,
            data.indicator_snapshot,
            completed_bars,
            data.now,
            data.recent_minute_ticks,
            config,
        )
        if decision is None:
            return result(
                decision_message="Holding position; no exit condition met.",
                action=ActionType.HOLD_POSITION,
                strategy_mode=next_state.position.strategy_mode,
                confidence=0.65,
                stop_rule=f"current_stop={next_state.position.current_stop_loss}",
                take_profit_rule="Hold until stop, time exit, or hard take profit.",
            )
        previous = next_state.phase
        exit_price = data.current_tick.price
        realized_pnl = _compute_realized_pnl_yuan(
            entry_price=next_state.position.entry_price or exit_price,
            exit_price=exit_price,
            size_grams=next_state.position.size_grams,
            buy_fee_rate=buy_fee_rate,
            sell_fee_rate=sell_fee_rate,
        )
        next_state.daily_realized_pnl_yuan += realized_pnl
        next_state.consecutive_loss_trades = 0 if realized_pnl >= 0 else next_state.consecutive_loss_trades + 1
        next_state.position_state_version += 1
        if decision.exit_reason in {ExitReason.INITIAL_STOP, ExitReason.TIME_STOP}:
            next_state.phase = StrategyPhase.COOLDOWN_AFTER_STOP
            next_state.cooldown_end_time = data.now.replace(second=0, microsecond=0)
            from datetime import timedelta
            next_state.cooldown_end_time = next_state.cooldown_end_time + timedelta(minutes=20)
        else:
            next_state.phase = StrategyPhase.WAITING_REENTRY_CONFIRMATION
        next_state.last_exit_time = data.now
        next_state.last_exit_reason = decision.exit_reason
        next_state.position = PositionState()
        next_state.force_flatten_requested = False
        next_state.batches_used = 0
        return result(
            signal_type=decision.signal_type,
            exit_reason=decision.exit_reason,
            should_notify=decision.should_send_email,
            decision_message=decision.summary,
            action=ActionType.SELL_NOW,
            strategy_mode=(
                StrategyMode.TIME_EXIT
                if decision.exit_reason in {ExitReason.TIME_STOP, ExitReason.FORCE_FLATTEN}
                else StrategyMode.RISK_EXIT
            ),
            confidence=0.93,
            invalidation_reason=decision.summary,
            stop_rule=f"exit_reason={decision.exit_reason.value if decision.exit_reason else 'unknown'}",
            take_profit_rule="Flat immediately after sell condition.",
            generated_events=[
                StrategyEvent(
                    event_type=EventType.EXIT_TRIGGERED,
                    event_time=data.now,
                    phase_before=previous,
                    phase_after=next_state.phase,
                    message=decision.summary,
                    title=decision.title,
                    event_key=decision.event_key,
                    metadata={"exit_reason": decision.exit_reason.value if decision.exit_reason else None},
                )
            ],
        )

    if data.daily_snapshot is None:
        return result(
            decision_message="Daily reference missing; cannot make decision.",
            action=ActionType.WAIT_NO_TRADE,
            invalidation_reason="Optional external filter unavailable.",
            generated_events=[
                StrategyEvent(
                    event_type=EventType.DATA_INSUFFICIENT,
                    event_time=data.now,
                    phase_before=state.phase,
                    phase_after=next_state.phase,
                    message="Daily reference snapshot missing.",
                    title="Daily reference missing",
                    level="WARNING",
                )
            ],
        )

    if not data.in_trading_window:
        return result(
            decision_message="Outside new-entry window; no new decision.",
            action=ActionType.WAIT_NO_TRADE,
            invalidation_reason="New entries blocked by session rules.",
        )

    if not data.indicator_snapshot.is_ready:
        return result(
            decision_message="Indicators not ready; warmup incomplete.",
            action=ActionType.WAIT_NO_TRADE,
            invalidation_reason="Warmup incomplete.",
            generated_events=[
                StrategyEvent(
                    event_type=EventType.DATA_INSUFFICIENT,
                    event_time=data.now,
                    phase_before=state.phase,
                    phase_after=next_state.phase,
                    message="Indicator snapshot not ready.",
                    title="Indicators not ready",
                    level="WARNING",
                )
            ],
        )

    if next_state.paused_new_entries:
        return result(
            decision_message="Operator paused new entries.",
            action=ActionType.WAIT_NO_TRADE,
            invalidation_reason="New entries are paused by operator.",
        )

    if next_state.daily_realized_pnl_yuan >= config.risk.daily_profit_lock_yuan:
        return result(
            decision_message="Daily profit lock reached; no new entries today.",
            action=ActionType.WAIT_NO_TRADE,
            invalidation_reason="Daily profit lock prevents new entries.",
        )

    entry_candidate = _infer_entry_mode(
        data.indicator_snapshot,
        regime,
        completed_bars,
        data.recent_minute_ticks,
        config,
    )
    if entry_candidate is not None:
        strategy_mode, confidence, stop_price, entry_reason, stop_rule, take_profit_rule = entry_candidate
        entry_price = data.indicator_snapshot.close_5m
        if entry_price is None:
            return result(
                decision_message="Signal shape exists but confirmation bar close is missing.",
                action=ActionType.WAIT_NO_TRADE,
                strategy_mode=strategy_mode,
                confidence=confidence,
                entry_reason=entry_reason,
                invalidation_reason="Mode A requires signal-bar close as internal fill price.",
                stop_rule=stop_rule,
                take_profit_rule=take_profit_rule,
            )
        risk_gate = evaluate_long_risk_gate(
            entry_price=entry_price,
            stop_price=stop_price,
            atr_value=data.indicator_snapshot.atr,
            config=config,
            state=next_state,
            strategy_mode=strategy_mode,
        )
        if not risk_gate.allowed:
            return result(
                decision_message="Signal shape exists but risk gate blocked entry.",
                action=ActionType.WAIT_NO_TRADE,
                strategy_mode=strategy_mode,
                confidence=confidence,
                entry_reason=entry_reason,
                invalidation_reason=risk_gate.reason,
                stop_rule=stop_rule,
                take_profit_rule=take_profit_rule,
            )
        previous = next_state.phase
        entry_time = data.indicator_snapshot.bar_time or data.now
        trade_idea_id = f"{strategy_mode.value}|{entry_time.isoformat()}"
        size_grams = (
            config.risk.default_entry_notional_yuan * (1 - buy_fee_rate) / entry_price
            if entry_price > 0
            else 0.0
        )
        if next_state.execution_mode == ExecutionMode.SIGNAL_IMPLIES_POSITION:
            next_state.phase = StrategyPhase.HOLDING
            next_state.position = PositionState(
                has_position=True,
                size_grams=size_grams,
                entry_price=entry_price,
                entry_time=entry_time,
                entry_bar_time=data.indicator_snapshot.bar_time or entry_time,
                position_notional_yuan=config.risk.default_entry_notional_yuan,
                initial_stop_price=stop_price,
                current_stop_loss=stop_price,
                stop_source=stop_rule,
                trade_idea_id=trade_idea_id,
                strategy_mode=strategy_mode,
                regime_at_entry=regime,
                trailing_active=False,
                h_star=entry_price,
                last_sync_source="signal_implies_position",
                last_sync_at=data.now,
                note="Internal position opened from BUY_NOW.",
            )
            next_state.position_state_version += 1
        else:
            next_state.phase = StrategyPhase.OBSERVING
        next_state.batches_used = max(state.batches_used, 0) + 1
        next_state.entries_today_count += 1
        next_state.pending_entry_signal_time = None
        next_state.pending_entry_deadline = None
        next_state.pending_entry_reference_bar_time = None
        next_state.pending_entry_atr = None
        next_state.pending_entry_stop_price = None
        next_state.pending_entry_reason = None
        return result(
            signal_type=SignalType.BUY,
            should_notify=True,
            decision_message="BUY_NOW confirmed and internal position opened at signal-bar close.",
            action=ActionType.BUY_NOW,
            strategy_mode=strategy_mode,
            confidence=confidence,
            entry_reason=entry_reason,
            invalidation_reason=(
                "Manual position sync mode: signal fired, but actual position remains unchanged until synced."
                if next_state.execution_mode == ExecutionMode.MANUAL_POSITION_SYNC
                else "Mode A uses signal-bar close as the internal fill price."
            ),
            stop_rule=stop_rule,
            take_profit_rule=take_profit_rule,
            price_for_dedupe=entry_price,
            generated_events=[
                StrategyEvent(
                    event_type=EventType.BUY_SIGNAL,
                    event_time=data.now,
                    phase_before=previous,
                    phase_after=next_state.phase,
                    message="Buy signal confirmed and recorded as an internal position.",
                    title="Buy signal",
                    event_key="buy_signal",
                    metadata={"strategy_mode": strategy_mode.value, "execution_mode": next_state.execution_mode.value},
                ),
                StrategyEvent(
                    event_type=EventType.SIGNAL_EMITTED,
                    event_time=entry_time,
                    phase_before=previous,
                    phase_after=next_state.phase,
                    message=(
                        f"BUY_NOW emitted at {entry_price:.2f}; sync actual fill manually."
                        if next_state.execution_mode == ExecutionMode.MANUAL_POSITION_SYNC
                        else f"Internal position opened at {entry_price:.2f}"
                    ),
                    title="Signal emitted",
                    event_key="signal_emitted",
                    metadata={"entry_price": entry_price, "trade_idea_id": trade_idea_id},
                ),
                *(
                    [
                        StrategyEvent(
                            event_type=EventType.ENTRY_FILLED,
                            event_time=entry_time,
                            phase_before=previous,
                            phase_after=next_state.phase,
                            message=f"Internal position opened at {entry_price:.2f}",
                            title="Entry filled",
                            event_key="entry_filled",
                            metadata={"entry_price": entry_price, "trade_idea_id": trade_idea_id},
                        )
                    ]
                    if next_state.execution_mode == ExecutionMode.SIGNAL_IMPLIES_POSITION
                    else []
                ),
            ],
        )

    return result(
        decision_message="No strategy signal triggered.",
        action=ActionType.WAIT_NO_TRADE,
        strategy_mode=StrategyMode.NONE,
        invalidation_reason="No mode passed confirmation and risk gate.",
    )
