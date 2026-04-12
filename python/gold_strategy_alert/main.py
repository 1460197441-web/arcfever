"""Application runtime integration for live, replay, and mock execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from pathlib import Path
import time
from copy import deepcopy

from bar_aggregator import MinuteBarAggregator
from config import AppConfig, apply_profile, default_config
from control_server import start_control_server
from data_provider import OrchestratedMarketDataProvider, build_default_market_data_provider
from indicators import compute_indicator_snapshot
from logger import configure_logging
from models import (
    ActionType,
    DailyMarketSnapshot,
    EventType,
    IndicatorSnapshot,
    MarketRegime,
    NotificationRecord,
    PriceTick,
    ReadinessLevel,
    SignalType,
    StrategyDecision,
    StrategyEvent,
    StrategyPhase,
    StrategyRuntimeState,
    StrategyMode,
    StrategyStepResult,
)
from notifier import EmailNotifier, NotificationContext
from scheduler import (
    ReplayController,
    RuntimeClock,
    is_strategy_decision_allowed,
    seconds_until_next_sample,
)
from state_store import SQLiteStateStore
from strategy import StrategyInput, evaluate_allow_long, evaluate_strategy_step


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineCycleResult:
    run_mode: str
    session_mode: str
    now: datetime
    tick_written: bool = False
    new_bars_count: int = 0
    indicator_ready: bool = False
    decision_allowed: bool = False
    readiness_level: str | None = None
    direction_ready: bool = False
    execution_ready: bool = False
    risk_ready: bool = False
    strategy_result: StrategyStepResult | None = None
    events_count: int = 0
    notification_record: NotificationRecord | None = None
    fallback_used: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PipelineInputs:
    now: datetime
    current_tick: PriceTick | None = None
    daily_snapshot: DailyMarketSnapshot | None = None
    fallback_used: bool = False
    generated_events: list[StrategyEvent] = field(default_factory=list)


class PipelineRunner:
    def __init__(
        self,
        config: AppConfig,
        store: SQLiteStateStore,
        notifier: EmailNotifier,
        live_provider: OrchestratedMarketDataProvider | None = None,
        replay_controller: ReplayController | None = None,
        clock: RuntimeClock | None = None,
    ) -> None:
        self.config = config
        self.store = store
        self.notifier = notifier
        self.live_provider = live_provider
        self.replay_controller = replay_controller
        self.clock = clock or RuntimeClock(config.trading_window.timezone_name)
        self.bar_aggregator = MinuteBarAggregator(bar_minutes=config.sampling.decision_interval_minutes)
        self.preloaded_ticks_count = 0
        self.preloaded_bars_count = 0
        preload_limit = max(int(config.runtime.history_preload_minutes), 1)
        preloaded_ticks = self.store.load_recent_minute_prices(limit=preload_limit)
        for tick in preloaded_ticks:
            self.bar_aggregator.add_tick(tick)
        self.preloaded_ticks_count = len(preloaded_ticks)
        self._bootstrap_history(preloaded_ticks)

    def run_once(self, now: datetime | None = None) -> PipelineCycleResult:
        now = now or self.clock.now()
        cycle_result = PipelineCycleResult(
            run_mode=self.config.runtime.run_mode,
            session_mode=self.config.runtime.session_mode,
            now=now,
        )
        runtime_state = self.store.load_runtime_state()

        try:
            try:
                inputs = self._load_inputs(now)
            except Exception as exc:  # noqa: BLE001
                return self._handle_fetch_failure(runtime_state, cycle_result, now, exc)

            runtime_state, pre_events, pre_notification_record = self._handle_fetch_success(runtime_state, now)
            cycle_result.fallback_used = inputs.fallback_used

            if inputs.current_tick is not None:
                self.store.append_minute_price(inputs.current_tick)
                self.bar_aggregator.add_tick(inputs.current_tick)
                cycle_result.tick_written = True

            new_bars = list(self.bar_aggregator.build_completed_bars(now))
            for bar in new_bars:
                self.store.append_bar(bar)
            cycle_result.new_bars_count = len(new_bars)

            completed_bars = self.store.load_recent_completed_bars(limit=100)
            recent_minute_ticks = self.store.load_recent_minute_prices(limit=60)
            indicator_snapshot = compute_indicator_snapshot(
                completed_bars,
                min_ready_bars=self.config.indicators.min_ready_bars,
                ema_fast_period=self.config.indicators.ema_fast_period,
                ema_slow_period=self.config.indicators.ema_slow_period,
                atr_period=self.config.indicators.atr_period,
                breakout_lookback_bars=self.config.indicators.breakout_lookback_bars,
                bollinger_period=self.config.indicators.bollinger_period,
                bollinger_stddev=self.config.indicators.bollinger_stddev,
                donchian_exit_period=self.config.indicators.donchian_exit_period,
            )
            cycle_result.indicator_ready = indicator_snapshot.is_ready

            allow_long, r_day = evaluate_allow_long(inputs.daily_snapshot)
            indicator_snapshot.allow_long = allow_long
            indicator_snapshot.day_snapshot_source = inputs.daily_snapshot.source if inputs.daily_snapshot else None
            indicator_snapshot.day_r_value = r_day

            readiness_level, direction_ready, execution_ready, risk_ready = self._compute_readiness(
                now=now,
                current_tick=inputs.current_tick,
                completed_bars=completed_bars,
                indicator_snapshot=indicator_snapshot,
            )
            cycle_result.readiness_level = readiness_level.value
            cycle_result.direction_ready = direction_ready
            cycle_result.execution_ready = execution_ready
            cycle_result.risk_ready = risk_ready

            decision_allowed = is_strategy_decision_allowed(self.config, now)
            cycle_result.decision_allowed = decision_allowed

            entry_allowed = (
                decision_allowed
                and readiness_level == ReadinessLevel.FULL_READY
                and not self._is_in_market_open_entry_freeze(now)
                and not self._is_after_no_new_cutoff(now)
            )

            strategy_input = StrategyInput(
                now=now,
                current_tick=inputs.current_tick,
                next_minute_tick=None,
                indicator_snapshot=indicator_snapshot,
                daily_snapshot=inputs.daily_snapshot,
                daily_snapshot_fallback_used=inputs.fallback_used,
                in_trading_window=entry_allowed,
                recent_minute_ticks=recent_minute_ticks,
                force_flatten=self._is_force_flatten_required(now) or runtime_state.force_flatten_requested,
            )
            strategy_result = evaluate_strategy_step(
                state=runtime_state,
                data=strategy_input,
                completed_bars=completed_bars,
                send_entry_cancel_notification=self.config.email.entry_cancel_notify,
                fee_break_even_multiplier=self.config.fees.fee_break_even_multiplier,
                position_size_grams=self.config.sampling.position_size_grams,
                manual_entry_required=self.config.control.manual_entry_confirmation,
                config=self.config,
                buy_fee_rate=self.config.fees.buy_fee_rate,
                sell_fee_rate=self.config.fees.sell_fee_rate,
            )
            cycle_result.strategy_result = strategy_result
            final_runtime_state = strategy_result.updated_runtime_state
            price_alert_events: list[StrategyEvent] = []
            price_alert_notification: NotificationRecord | None = None
            if inputs.current_tick is not None:
                (
                    final_runtime_state,
                    price_alert_events,
                    price_alert_notification,
                ) = self._evaluate_price_below_alert(
                    state=final_runtime_state,
                    current_tick=inputs.current_tick,
                    now=now,
                )
                strategy_result.updated_runtime_state = final_runtime_state

            self.store.save_runtime_state(final_runtime_state)
            if strategy_result.decision_output is not None:
                self.store.append_decision(strategy_result.decision_output)

            all_events = [*pre_events, *inputs.generated_events, *strategy_result.generated_events, *price_alert_events]
            for event in all_events:
                self.store.append_event(event)
            cycle_result.events_count = len(all_events)

            if pre_notification_record is not None:
                self.store.append_notification(pre_notification_record)
                cycle_result.notification_record = pre_notification_record

            if price_alert_notification is not None:
                self.store.append_notification(price_alert_notification)
                cycle_result.notification_record = price_alert_notification

            if strategy_result.should_notify:
                self.notifier.configure_test_mode(
                    enable_test_mode=self.config.runtime.enable_test_mode,
                    send_real_email_in_test_mode=self.config.runtime.send_real_email_in_test_mode,
                )
                notification_context = NotificationContext(
                    triggered_at=now,
                    current_price=inputs.current_tick.price if inputs.current_tick else None,
                    indicator_snapshot=indicator_snapshot,
                    daily_snapshot=inputs.daily_snapshot,
                    allow_long=indicator_snapshot.allow_long,
                    source_name=inputs.daily_snapshot.source if inputs.daily_snapshot else None,
                    fallback_used=inputs.fallback_used,
                    fetch_success=(inputs.current_tick is not None or self.config.runtime.run_mode == "mock"),
                    extra={"position_size_grams": self.config.sampling.position_size_grams},
                )
                if self.notifier.should_send_step_result(strategy_result):
                    dedupe_key = (
                        strategy_result.decision_output.dedupe_key
                        if strategy_result.decision_output is not None
                        else None
                    )
                    should_skip = False
                    if dedupe_key:
                        should_skip = self.store.has_recent_notification_dedupe(
                            dedupe_key,
                            since=now - timedelta(minutes=self.config.risk.email_dedupe_minutes),
                        )
                    if not should_skip:
                        notification_record = self.notifier.send_step_result(
                            strategy_result,
                            strategy_result.updated_runtime_state,
                            notification_context,
                        )
                        self.store.append_notification(notification_record)
                        cycle_result.notification_record = notification_record

            return cycle_result
        except Exception as exc:  # noqa: BLE001
            cycle_result.errors.append(str(exc))
            error_event = StrategyEvent(
                event_type=EventType.ERROR,
                event_time=now,
                phase_before=runtime_state.phase,
                phase_after=runtime_state.phase,
                title="Pipeline cycle error",
                message=str(exc),
                level="ERROR",
                metadata={"run_mode": self.config.runtime.run_mode},
            )
            self.store.append_event(error_event)
            cycle_result.events_count += 1
            try:
                self.notifier.configure_test_mode(
                    enable_test_mode=self.config.runtime.enable_test_mode,
                    send_real_email_in_test_mode=self.config.runtime.send_real_email_in_test_mode,
                )
                error_result = StrategyStepResult(
                    next_state=runtime_state.phase,
                    signal_type=None,
                    exit_reason=None,
                    should_notify=True,
                    decision_message=str(exc),
                    generated_events=[error_event],
                    updated_runtime_state=runtime_state,
                )
                if self.notifier.should_send_step_result(error_result):
                    notification_record = self.notifier.send_step_result(
                        error_result,
                        runtime_state,
                        NotificationContext(
                            triggered_at=now,
                            fetch_success=False,
                            exception_message=str(exc),
                            extra={"position_size_grams": self.config.sampling.position_size_grams},
                        ),
                    )
                    self.store.append_notification(notification_record)
                    cycle_result.notification_record = notification_record
            except Exception as notification_exc:  # noqa: BLE001
                cycle_result.errors.append(str(notification_exc))
            return cycle_result

    def _handle_fetch_failure(
        self,
        runtime_state: StrategyRuntimeState,
        cycle_result: PipelineCycleResult,
        now: datetime,
        exc: Exception,
    ) -> PipelineCycleResult:
        cycle_result.errors.append(str(exc))
        next_state = deepcopy(runtime_state)
        next_state.consecutive_fetch_failures += 1
        threshold = max(int(self.config.runtime.fetch_failure_alert_threshold), 1)
        should_alert = next_state.consecutive_fetch_failures >= threshold and not next_state.fetch_alert_active
        if should_alert:
            next_state.fetch_alert_active = True

        self.store.save_runtime_state(next_state)

        event = StrategyEvent(
            event_type=EventType.SAMPLE_FAILURE,
            event_time=now,
            phase_before=runtime_state.phase,
            phase_after=next_state.phase,
            title="Price collection failed",
            message=str(exc),
            level="ERROR" if should_alert else "WARNING",
            event_key="fetch_failure_alert" if should_alert else "fetch_failure",
            metadata={
                "consecutive_fetch_failures": next_state.consecutive_fetch_failures,
                "threshold": threshold,
                "run_mode": self.config.runtime.run_mode,
            },
        )
        self.store.append_event(event)
        cycle_result.events_count += 1

        step_result = StrategyStepResult(
            next_state=next_state.phase,
            signal_type=SignalType.RISK if should_alert else None,
            exit_reason=None,
            should_notify=should_alert,
            decision_message=(
                f"Price collection failed {next_state.consecutive_fetch_failures} consecutive times."
                if should_alert
                else str(exc)
            ),
            generated_events=[event],
            updated_runtime_state=next_state,
        )
        cycle_result.strategy_result = step_result

        if should_alert:
            self.notifier.configure_test_mode(
                enable_test_mode=self.config.runtime.enable_test_mode,
                send_real_email_in_test_mode=self.config.runtime.send_real_email_in_test_mode,
            )
            notification_record = self.notifier.send_step_result(
                step_result,
                next_state,
                NotificationContext(
                    triggered_at=now,
                    fetch_success=False,
                    exception_message=str(exc),
                    extra={
                        "position_size_grams": self.config.sampling.position_size_grams,
                        "consecutive_fetch_failures": next_state.consecutive_fetch_failures,
                    },
                ),
            )
            self.store.append_notification(notification_record)
            cycle_result.notification_record = notification_record

        return cycle_result

    def _handle_fetch_success(
        self,
        runtime_state: StrategyRuntimeState,
        now: datetime,
    ) -> tuple[StrategyRuntimeState, list[StrategyEvent], NotificationRecord | None]:
        next_state = deepcopy(runtime_state)
        pre_events: list[StrategyEvent] = []
        notification_record: NotificationRecord | None = None

        had_failures = next_state.consecutive_fetch_failures > 0
        should_send_recovery = next_state.fetch_alert_active and self.config.runtime.send_fetch_recovery_notification
        previous_failures = next_state.consecutive_fetch_failures
        next_state.consecutive_fetch_failures = 0
        next_state.last_fetch_success_time = now

        if had_failures and next_state.fetch_alert_active:
            next_state.fetch_alert_active = False
            event = StrategyEvent(
                event_type=EventType.FETCH_RECOVERED,
                event_time=now,
                phase_before=runtime_state.phase,
                phase_after=next_state.phase,
                title="Price collection recovered",
                message=f"Price collection recovered after {previous_failures} consecutive failures.",
                level="INFO",
                event_key="fetch_recovered",
                metadata={"previous_failures": previous_failures},
            )
            pre_events.append(event)
            if should_send_recovery:
                self.notifier.configure_test_mode(
                    enable_test_mode=self.config.runtime.enable_test_mode,
                    send_real_email_in_test_mode=self.config.runtime.send_real_email_in_test_mode,
                )
                step_result = StrategyStepResult(
                    next_state=next_state.phase,
                    signal_type=SignalType.INFO,
                    exit_reason=None,
                    should_notify=True,
                    decision_message=f"Price collection recovered after {previous_failures} consecutive failures.",
                    generated_events=[event],
                    updated_runtime_state=next_state,
                )
                notification_record = self.notifier.send_step_result(
                    step_result,
                    next_state,
                    NotificationContext(
                        triggered_at=now,
                        fetch_success=True,
                        extra={
                            "position_size_grams": self.config.sampling.position_size_grams,
                            "previous_failures": previous_failures,
                        },
                    ),
                )

        return next_state, pre_events, notification_record

    def run_forever(self) -> None:
        while True:
            cycle_result = self.run_once()
            LOGGER.info(
                "cycle run_mode=%s now=%s tick_written=%s new_bars=%s events=%s errors=%s",
                cycle_result.run_mode,
                cycle_result.now.isoformat(),
                cycle_result.tick_written,
                cycle_result.new_bars_count,
                cycle_result.events_count,
                cycle_result.errors,
            )

            if self.config.runtime.run_mode == "replay":
                if self.replay_controller is None:
                    break
                if self.replay_controller.mode == "step":
                    break
                if self.replay_controller.cursor >= len(self.replay_controller.ticks):
                    break
                if self.replay_controller.mode == "fast_forward":
                    continue

            time.sleep(seconds_until_next_sample(self.config, self.clock.now()))

    def _load_inputs(self, now: datetime) -> PipelineInputs:
        if self.config.runtime.run_mode == "live":
            provider = self.live_provider or build_default_market_data_provider(self.config)
            fetched = provider.fetch(now)
            return PipelineInputs(
                now=now,
                current_tick=fetched.tick,
                daily_snapshot=fetched.daily_reference,
                fallback_used=fetched.fallback_used,
                generated_events=fetched.events,
            )

        if self.config.runtime.run_mode == "replay":
            current_tick = self._next_replay_tick()
            return PipelineInputs(
                now=(current_tick.observed_at if current_tick else now),
                current_tick=current_tick,
                daily_snapshot=self._build_mock_daily_snapshot(current_tick.observed_at if current_tick else now),
                fallback_used=False,
            )

        if self.config.runtime.run_mode == "mock":
            tick = self._build_mock_tick(now)
            return PipelineInputs(
                now=now,
                current_tick=tick,
                daily_snapshot=self._build_mock_daily_snapshot(now),
                fallback_used=False,
            )

        raise ValueError(f"Unsupported run_mode: {self.config.runtime.run_mode}")

    def _build_mock_tick(self, now: datetime) -> PriceTick | None:
        if self.config.runtime.mock_current_price is None:
            return None
        return PriceTick(
            symbol="ICBC_ACC_GOLD",
            price=float(self.config.runtime.mock_current_price),
            observed_at=now,
            source="mock",
        )

    def _build_mock_daily_snapshot(self, now: datetime) -> DailyMarketSnapshot | None:
        if None in (
            self.config.runtime.mock_daily_open,
            self.config.runtime.mock_daily_high,
            self.config.runtime.mock_daily_low,
            self.config.runtime.mock_daily_last,
        ):
            return None
        return DailyMarketSnapshot(
            symbol="MOCK",
            open=float(self.config.runtime.mock_daily_open),
            high=float(self.config.runtime.mock_daily_high),
            low=float(self.config.runtime.mock_daily_low),
            last=float(self.config.runtime.mock_daily_last),
            observed_at=now,
            source="mock_daily",
        )

    def _next_replay_tick(self) -> PriceTick | None:
        if self.replay_controller is None:
            return None
        if self.replay_controller.mode == "fast_forward":
            ticks = self.replay_controller.fast_forward(steps=1)
            return ticks[0] if ticks else None
        return self.replay_controller.step()

    def _bootstrap_history(self, preloaded_ticks: list[PriceTick]) -> None:
        if not preloaded_ticks:
            return
        bootstrap_now = preloaded_ticks[-1].observed_at.replace(second=0, microsecond=0) + timedelta(
            minutes=1
        )
        completed_bars = list(self.bar_aggregator.build_completed_bars(bootstrap_now))
        for bar in completed_bars:
            self.store.append_bar(bar)
        self.preloaded_bars_count = len(completed_bars)
        LOGGER.info(
            "history preload ticks=%s rebuilt_bars=%s preload_minutes=%s",
            self.preloaded_ticks_count,
            self.preloaded_bars_count,
            self.config.runtime.history_preload_minutes,
        )

    def _compute_readiness(
        self,
        *,
        now: datetime,
        current_tick: PriceTick | None,
        completed_bars: list,
        indicator_snapshot: IndicatorSnapshot,
    ) -> tuple[ReadinessLevel, bool, bool, bool]:
        recent_ticks = self.store.load_recent_minute_prices(limit=10)
        recent_cutoff = now.timestamp() - 10 * 60
        recent_tick_count = sum(1 for tick in recent_ticks if tick.observed_at.timestamp() >= recent_cutoff)

        latest_tick = current_tick or (recent_ticks[-1] if recent_ticks else None)
        fresh_seconds = None
        if latest_tick is not None:
            fresh_seconds = (now - latest_tick.observed_at).total_seconds()

        if self.config.runtime.run_mode == "live":
            risk_ready = latest_tick is not None and fresh_seconds is not None and fresh_seconds <= 180 and recent_tick_count >= 7
        else:
            risk_ready = latest_tick is not None
        execution_ready = len(completed_bars) >= max(self.config.indicators.breakout_lookback_bars, 14)
        direction_ready = len(completed_bars) >= self.config.indicators.ema_slow_period

        if not risk_ready:
            return ReadinessLevel.DATA_BAD_MODE, direction_ready, execution_ready, risk_ready
        if direction_ready and execution_ready and indicator_snapshot.atr is not None:
            return ReadinessLevel.FULL_READY, direction_ready, execution_ready, risk_ready
        return ReadinessLevel.EXIT_ONLY_READY, direction_ready, execution_ready, risk_ready

    def _is_in_market_open_entry_freeze(self, now: datetime) -> bool:
        market_open = now.replace(
            hour=self.config.trading_window.start.hour,
            minute=self.config.trading_window.start.minute,
            second=0,
            microsecond=0,
        )
        freeze_seconds = max(self.config.strategy.market_open_entry_freeze_minutes, 0) * 60
        market_open_end = datetime.fromtimestamp(market_open.timestamp() + freeze_seconds, tz=market_open.tzinfo)
        return market_open <= now < market_open_end

    def _is_after_no_new_cutoff(self, now: datetime) -> bool:
        cutoff = now.replace(
            hour=self.config.strategy.no_new_after.hour,
            minute=self.config.strategy.no_new_after.minute,
            second=0,
            microsecond=0,
        )
        return now >= cutoff

    def _is_force_flatten_required(self, now: datetime) -> bool:
        flatten_at = now.replace(
            hour=self.config.strategy.force_flatten_at.hour,
            minute=self.config.strategy.force_flatten_at.minute,
            second=0,
            microsecond=0,
        )
        return now >= flatten_at

    def _evaluate_price_below_alert(
        self,
        *,
        state: StrategyRuntimeState,
        current_tick: PriceTick,
        now: datetime,
    ) -> tuple[StrategyRuntimeState, list[StrategyEvent], NotificationRecord | None]:
        next_state = deepcopy(state)
        alert = next_state.price_alert
        if not alert.enabled or alert.target_price is None:
            return next_state, [], None

        if current_tick.price > alert.target_price:
            if alert.active_below_triggered:
                alert.active_below_triggered = False
                rearmed_event = StrategyEvent(
                    event_type=EventType.PRICE_ALERT_REARMED,
                    event_time=now,
                    phase_before=state.phase,
                    phase_after=next_state.phase,
                    title="Price alert rearmed",
                    message=f"Price moved back above {alert.target_price:.2f}; alert rearmed.",
                    event_key="price_alert_rearmed",
                    metadata={"target_price": alert.target_price, "current_price": current_tick.price},
                )
                return next_state, [rearmed_event], None
            return next_state, [], None

        if alert.active_below_triggered:
            return next_state, [], None

        alert.active_below_triggered = True
        alert.last_triggered_at = now
        alert.last_triggered_price = current_tick.price
        trigger_event = StrategyEvent(
            event_type=EventType.PRICE_ALERT_TRIGGERED,
            event_time=now,
            phase_before=state.phase,
            phase_after=next_state.phase,
            title="Price alert triggered",
            message=f"Current price {current_tick.price:.2f} is below target {alert.target_price:.2f}.",
            event_key=f"price_below:{alert.target_price:.2f}:{now.strftime('%Y%m%d%H%M')}",
            metadata={
                "target_price": alert.target_price,
                "current_price": current_tick.price,
                "source": current_tick.source,
            },
        )
        self.notifier.configure_test_mode(
            enable_test_mode=self.config.runtime.enable_test_mode,
            send_real_email_in_test_mode=self.config.runtime.send_real_email_in_test_mode,
        )
        notification_record = self.notifier.send(
            StrategyDecision(
                signal_type=SignalType.WARNING,
                should_send_email=True,
                title="ICBC Gold price-below alert",
                summary=f"Current price {current_tick.price:.2f} is below target {alert.target_price:.2f}.",
                event_key=trigger_event.event_key or "price_below_alert",
                price=current_tick.price,
                metadata={
                    "target_price": alert.target_price,
                    "dashboard_link": self.config.email.dashboard_link,
                },
            ),
            next_state,
            NotificationContext(
                triggered_at=now,
                current_price=current_tick.price,
                fetch_success=True,
                extra={
                    "target_price": alert.target_price,
                    "position_size_grams": self.config.sampling.position_size_grams,
                },
            ),
        )
        return next_state, [trigger_event], notification_record


def run_live_cycle(
    config: AppConfig,
    store: SQLiteStateStore,
    notifier: EmailNotifier,
    live_provider: OrchestratedMarketDataProvider | None = None,
    now: datetime | None = None,
) -> PipelineCycleResult:
    runner = PipelineRunner(config=config, store=store, notifier=notifier, live_provider=live_provider)
    return runner.run_once(now=now)


def run_replay_cycle(
    config: AppConfig,
    store: SQLiteStateStore,
    notifier: EmailNotifier,
    replay_controller: ReplayController,
    now: datetime | None = None,
) -> PipelineCycleResult:
    runner = PipelineRunner(config=config, store=store, notifier=notifier, replay_controller=replay_controller)
    return runner.run_once(now=now)


def run_mock_cycle(
    config: AppConfig,
    store: SQLiteStateStore,
    notifier: EmailNotifier,
    now: datetime | None = None,
) -> PipelineCycleResult:
    runner = PipelineRunner(config=config, store=store, notifier=notifier)
    return runner.run_once(now=now)


def run_once(
    config: AppConfig,
    store: SQLiteStateStore,
    notifier: EmailNotifier,
    live_provider: OrchestratedMarketDataProvider | None = None,
    replay_controller: ReplayController | None = None,
    now: datetime | None = None,
) -> PipelineCycleResult:
    runner = PipelineRunner(
        config=config,
        store=store,
        notifier=notifier,
        live_provider=live_provider,
        replay_controller=replay_controller,
    )
    return runner.run_once(now=now)


def run_forever(
    config: AppConfig,
    store: SQLiteStateStore,
    notifier: EmailNotifier,
    live_provider: OrchestratedMarketDataProvider | None = None,
    replay_controller: ReplayController | None = None,
) -> None:
    runner = PipelineRunner(
        config=config,
        store=store,
        notifier=notifier,
        live_provider=live_provider,
        replay_controller=replay_controller,
    )
    runner.run_forever()


def main() -> int:
    config = default_config()
    configure_logging(config.storage.log_path)
    store = SQLiteStateStore(config.storage.sqlite_path)
    store.initialize()
    restored_state = store.load_runtime_state()
    apply_profile(config, restored_state.profile_name.value)
    config.runtime.execution_mode = restored_state.execution_mode.value
    notifier = EmailNotifier(config.email)
    control_handle = start_control_server(config, store)

    LOGGER.info("Service started at %s", RuntimeClock(config.trading_window.timezone_name).now().isoformat())
    if control_handle is not None:
        LOGGER.info("Control panel available at %s", control_handle.base_url)
    if config.runtime.run_mode == "replay" and config.runtime.replay_data_path:
        replay_controller = ReplayController.from_csv(
            Path(config.runtime.replay_data_path),  # type: ignore[name-defined]
            mode=config.runtime.replay_speed,
        )
        run_forever(config, store, notifier, replay_controller=replay_controller)
    elif config.runtime.run_mode == "mock":
        run_forever(config, store, notifier)
    else:
        run_forever(config, store, notifier, live_provider=build_default_market_data_provider(config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
