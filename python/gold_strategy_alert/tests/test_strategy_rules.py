from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from config import default_config
from models import (
    ActionType,
    Bar,
    DailyMarketSnapshot,
    ExecutionMode,
    EventType,
    ExitReason,
    IndicatorSnapshot,
    MarketRegime,
    PositionState,
    PriceTick,
    RiskGateResult,
    StrategyMode,
    StrategyPhase,
    StrategyRuntimeState,
)
from strategy import (
    StrategyInput,
    _infer_entry_mode,
    evaluate_allow_long,
    evaluate_entry_signal,
    evaluate_exit_conditions,
    evaluate_strategy_step,
    evaluate_reentry_eligibility,
)


def _tick(price: float, minute: int) -> PriceTick:
    return PriceTick(
        symbol="ICBC_ACC_GOLD",
        price=price,
        observed_at=datetime(2026, 3, 23, 10, minute, 0),
        source="test",
    )


def _bar(index: int, close: float, *, high: float | None = None, low: float | None = None, open_: float | None = None) -> Bar:
    start = datetime(2026, 3, 23, 9, 15) + timedelta(minutes=5 * index)
    close_value = close
    open_value = close_value if open_ is None else open_
    high_value = close_value if high is None else high
    low_value = close_value if low is None else low
    return Bar(
        start_at=start,
        end_at=start + timedelta(minutes=5),
        open=open_value,
        high=high_value,
        low=low_value,
        close=close_value,
        source="test",
    )


def _daily_snapshot() -> DailyMarketSnapshot:
    return DailyMarketSnapshot(
        symbol="Au99.99",
        open=700.0,
        high=720.0,
        low=690.0,
        last=709.0,
        observed_at=datetime(2026, 3, 23, 10, 0, 0),
        source="sge",
    )


def _ready_indicator(**overrides) -> IndicatorSnapshot:
    payload = {
        "bar_time": datetime(2026, 3, 23, 10, 0, 0),
        "close_5m": 810.0,
        "last_close": 810.0,
        "ema_fast": 809.0,
        "ema_slow": 805.0,
        "atr": 4.0,
        "hh": 808.0,
        "ll": 790.0,
        "bollinger_mid": 806.0,
        "bollinger_upper": 812.0,
        "bollinger_lower": 800.0,
        "bollinger_bandwidth": 0.01,
        "donchian_entry_high": 808.0,
        "donchian_entry_low": 790.0,
        "donchian_exit_high": 809.0,
        "donchian_exit_low": 795.0,
        "allow_long": True,
        "is_ready": True,
        "warmup_complete": True,
    }
    payload.update(overrides)
    return IndicatorSnapshot(**payload)


def test_allow_long_is_true_when_last_above_open_and_r_day_at_least_060() -> None:
    allow_long, r_day = evaluate_allow_long(_daily_snapshot())
    assert allow_long is True
    assert r_day == pytest.approx((709.0 - 690.0) / (720.0 - 690.0 + 1e-9))


def test_allow_long_is_false_when_last_not_above_open() -> None:
    snapshot = DailyMarketSnapshot(
        symbol="Au99.99",
        open=700.0,
        high=720.0,
        low=690.0,
        last=699.0,
        observed_at=datetime(2026, 3, 23, 10, 0, 0),
        source="sge",
    )
    allow_long, _ = evaluate_allow_long(snapshot)
    assert allow_long is False


def test_entry_signal_requires_all_conditions_and_observing_phase() -> None:
    state = StrategyRuntimeState(phase=StrategyPhase.OBSERVING)
    indicators = _ready_indicator()
    assert evaluate_entry_signal(state, indicators, in_trading_window=True) is True


def test_r2_priority_over_r1_and_l1(monkeypatch) -> None:
    ema20 = 100.0
    bars_3m = [
        Bar(
                start_at=datetime(2026, 3, 23, 9, 0, 0) + timedelta(minutes=3 * idx),
                end_at=datetime(2026, 3, 23, 9, 3, 0) + timedelta(minutes=3 * idx),
                open=99.5,
                high=100.4 if idx == 19 else (100.8 if idx >= 18 else 100.2),
                low=99.2 if idx >= 18 else 99.8,
                close=100.6 if idx == 20 else 100.0,
            source="test",
        )
        for idx in range(21)
    ]
    indicators = _ready_indicator(close_5m=101.0, ema_fast=ema20, ema_slow=98.0, atr=2.0)

    monkeypatch.setattr("strategy.aggregate_minute_ticks_to_bars", lambda *_args, **_kwargs: bars_3m)
    monkeypatch.setattr(
        "strategy.calculate_donchian_channels",
        lambda _bars, _period: ([None] * 20 + [99.0], [None] * 20 + [95.0]),
    )
    monkeypatch.setattr(
        "strategy.calculate_bollinger_bands",
        lambda _values, _period, _std: ([None] * 21, [None] * 20 + [101.0], [None] * 21, [None] * 19 + [0.8, 1.0]),
    )

    result = _infer_entry_mode(
        indicators=indicators,
        regime=MarketRegime.TREND_UP,
        completed_bars=[_bar(i, 90 + i) for i in range(25)],
        recent_minute_ticks=[_tick(100.0, i % 60) for i in range(25)],
    )
    assert result is not None
    assert result[0] == StrategyMode.R2_PULLBACK


def test_confidence_not_primary_trigger(monkeypatch) -> None:
    state = StrategyRuntimeState(phase=StrategyPhase.OBSERVING)
    monkeypatch.setattr("strategy.classify_regime", lambda *_args, **_kwargs: (MarketRegime.TREND_UP, 0.99))
    monkeypatch.setattr(
        "strategy._infer_entry_mode",
        lambda *_args, **_kwargs: (
            StrategyMode.R2_PULLBACK,
            0.99,
            790.0,
            "pattern matched",
            "structure_low=790.00",
            "Exit on Donchian10 or structure failure.",
        ),
    )
    monkeypatch.setattr(
        "strategy.evaluate_long_risk_gate",
        lambda **_kwargs: RiskGateResult(
            allowed=False,
            entry_price=810.0,
            stop_price=790.0,
            stop_distance_per_gram=20.0,
            estimated_grams=1.0,
            fee_floor_yuan=10.0,
            max_price_risk_budget_yuan=10.0,
            max_stop_distance_per_gram=10.0,
            risk_amount_yuan=30.0,
            notional_yuan=1000.0,
            reason="Risk gate blocked it.",
            atr_cap_per_gram=4.0,
        ),
    )

    result = evaluate_strategy_step(
        state=state,
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(810.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
            recent_minute_ticks=[_tick(809.5, 0), _tick(810.0, 1), _tick(810.2, 2)],
        ),
        completed_bars=[_bar(i, 780.0 + i) for i in range(25)],
    )
    assert result.action == ActionType.WAIT_NO_TRADE
    assert result.confidence == pytest.approx(0.99)
    assert result.next_state == StrategyPhase.OBSERVING


def test_riskgate_blocks_trade_even_if_pattern_matches() -> None:
    config = default_config()
    result = evaluate_strategy_step(
        state=StrategyRuntimeState(phase=StrategyPhase.OBSERVING),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(1000.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(close_5m=1000.0, ema_fast=999.0, ema_slow=990.0, atr=2.0),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
            recent_minute_ticks=[_tick(999.5, 0), _tick(1000.0, 1), _tick(1000.2, 2)],
        ),
        completed_bars=[_bar(i, 950.0 + i, high=951.0 + i, low=949.0 + i) for i in range(25)],
        config=config,
    )
    assert result.action == ActionType.WAIT_NO_TRADE


def test_initial_stop_exit_is_triggered_when_price_breaches_structure_stop() -> None:
    state = StrategyRuntimeState(
        phase=StrategyPhase.HOLDING,
        position=PositionState(
            has_position=True,
            size_grams=1.0,
            entry_price=800.0,
            entry_time=datetime(2026, 3, 23, 9, 30, 0),
            entry_bar_time=datetime(2026, 3, 23, 9, 25, 0),
            current_stop_loss=796.0,
        ),
    )
    decision = evaluate_exit_conditions(
        state=state,
        current_price=795.8,
        indicators=_ready_indicator(),
        completed_bars=[_bar(i, 800.0 + i) for i in range(12)],
        now=datetime(2026, 3, 23, 9, 45, 0),
    )
    assert decision is not None
    assert decision.exit_reason == ExitReason.INITIAL_STOP


def test_sell_now_checked_before_new_buy(monkeypatch) -> None:
    state = StrategyRuntimeState(
        phase=StrategyPhase.HOLDING,
        position=PositionState(
            has_position=True,
            size_grams=1.0,
            entry_price=800.0,
            entry_time=datetime(2026, 3, 23, 9, 30, 0),
            current_stop_loss=796.0,
        ),
    )
    monkeypatch.setattr(
        "strategy._infer_entry_mode",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("buy logic should not run while selling")),
    )
    result = evaluate_strategy_step(
        state=state,
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(795.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
        ),
        completed_bars=[_bar(i, 800.0 + i) for i in range(12)],
    )
    assert result.action == ActionType.SELL_NOW
    assert result.exit_reason == ExitReason.INITIAL_STOP


def test_time_exit_at_2220() -> None:
    state = StrategyRuntimeState(
        phase=StrategyPhase.HOLDING,
        position=PositionState(
            has_position=True,
            size_grams=1.0,
            entry_price=800.0,
            entry_time=datetime(2026, 3, 23, 9, 30, 0),
            current_stop_loss=790.0,
        ),
    )
    result = evaluate_strategy_step(
        state=state,
        data=StrategyInput(
            now=datetime(2026, 3, 23, 22, 20, 0),
            current_tick=PriceTick(symbol="ICBC_ACC_GOLD", price=820.0, observed_at=datetime(2026, 3, 23, 22, 20, 0), source="test"),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=False,
            force_flatten=True,
        ),
        completed_bars=[_bar(i, 800.0 + i) for i in range(12)],
    )
    assert result.action == ActionType.SELL_NOW
    assert result.exit_reason == ExitReason.FORCE_FLATTEN
    assert any(event.event_type == EventType.EXIT_TRIGGERED for event in result.generated_events)


def test_reentry_requires_at_least_12_completed_bars_after_exit() -> None:
    state = StrategyRuntimeState(
        phase=StrategyPhase.WAITING_REENTRY_CONFIRMATION,
        last_exit_time=datetime(2026, 3, 23, 10, 0, 0),
    )
    bars = [_bar(i, 800.0 + i) for i in range(11)]
    indicators = _ready_indicator(close_5m=820.0, ema_fast=819.0, ema_slow=818.0, atr=2.0)
    assert evaluate_reentry_eligibility(state, bars, indicators) is False


def test_buy_now_creates_position_atomically(monkeypatch) -> None:
    state = StrategyRuntimeState(
        phase=StrategyPhase.OBSERVING,
        execution_mode=ExecutionMode.SIGNAL_IMPLIES_POSITION,
    )
    monkeypatch.setattr("strategy.classify_regime", lambda *_args, **_kwargs: (MarketRegime.TREND_UP, 0.88))
    monkeypatch.setattr(
        "strategy._infer_entry_mode",
        lambda *_args, **_kwargs: (
            StrategyMode.R2_PULLBACK,
            0.88,
            804.0,
            "EMA20 pullback reclaimed.",
            "structure_low=804.00",
            "Exit on Donchian10 or structure failure.",
        ),
    )
    monkeypatch.setattr(
        "strategy.evaluate_long_risk_gate",
        lambda **_kwargs: RiskGateResult(
            allowed=True,
            entry_price=810.0,
            stop_price=804.0,
            stop_distance_per_gram=6.0,
            estimated_grams=1.0,
            fee_floor_yuan=10.0,
            max_price_risk_budget_yuan=10.0,
            max_stop_distance_per_gram=10.0,
            risk_amount_yuan=16.0,
            notional_yuan=1000.0,
            reason="Risk gate passed.",
            atr_cap_per_gram=4.0,
        ),
    )

    result = evaluate_strategy_step(
        state=state,
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(810.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
            recent_minute_ticks=[_tick(809.5, 0), _tick(810.0, 1), _tick(810.2, 2)],
        ),
        completed_bars=[_bar(i, 780.0 + i) for i in range(25)],
    )
    assert result.next_state == StrategyPhase.HOLDING
    assert result.signal_type is not None
    assert result.action == ActionType.BUY_NOW
    assert result.updated_runtime_state.position.has_position is True
    assert result.updated_runtime_state.position.entry_price == pytest.approx(810.0)
    assert result.updated_runtime_state.position.entry_time == datetime(2026, 3, 23, 10, 0, 0)
    assert result.updated_runtime_state.position.initial_stop_price == pytest.approx(804.0)
    assert result.updated_runtime_state.position.current_stop_loss == pytest.approx(804.0)
    assert result.updated_runtime_state.position.strategy_mode == StrategyMode.R2_PULLBACK


def test_no_none_entry_price_after_buy(monkeypatch) -> None:
    monkeypatch.setattr("strategy.classify_regime", lambda *_args, **_kwargs: (MarketRegime.TREND_UP, 0.88))
    monkeypatch.setattr(
        "strategy._infer_entry_mode",
        lambda *_args, **_kwargs: (
            StrategyMode.R2_PULLBACK,
            0.88,
            804.0,
            "EMA20 pullback reclaimed.",
            "structure_low=804.00",
            "Exit on Donchian10 or structure failure.",
        ),
    )
    monkeypatch.setattr(
        "strategy.evaluate_long_risk_gate",
        lambda **_kwargs: RiskGateResult(
            allowed=True,
            entry_price=810.0,
            stop_price=804.0,
            stop_distance_per_gram=6.0,
            estimated_grams=1.0,
            fee_floor_yuan=10.0,
            max_price_risk_budget_yuan=10.0,
            max_stop_distance_per_gram=10.0,
            risk_amount_yuan=16.0,
            notional_yuan=1000.0,
            reason="Risk gate passed.",
            atr_cap_per_gram=4.0,
        ),
    )
    result = evaluate_strategy_step(
        state=StrategyRuntimeState(
            phase=StrategyPhase.OBSERVING,
            execution_mode=ExecutionMode.SIGNAL_IMPLIES_POSITION,
        ),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(810.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(close_5m=810.0),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
            recent_minute_ticks=[_tick(809.5, 0), _tick(810.0, 1), _tick(810.2, 2)],
        ),
        completed_bars=[_bar(i, 780.0 + i) for i in range(25)],
    )
    assert result.action == ActionType.BUY_NOW
    assert result.updated_runtime_state.position.entry_price is not None


def test_no_sell_now_without_position() -> None:
    result = evaluate_strategy_step(
        state=StrategyRuntimeState(phase=StrategyPhase.OBSERVING),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(795.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
        ),
        completed_bars=[_bar(i, 800.0 + i) for i in range(12)],
    )
    assert result.action == ActionType.WAIT_NO_TRADE


def test_hold_position_requires_existing_position() -> None:
    result = evaluate_strategy_step(
        state=StrategyRuntimeState(
            phase=StrategyPhase.HOLDING,
            position=PositionState(has_position=False),
        ),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(810.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
        ),
        completed_bars=[_bar(i, 800.0 + i) for i in range(12)],
    )
    assert result.action == ActionType.WAIT_NO_TRADE


def test_wait_no_trade_requires_flat_position(monkeypatch) -> None:
    monkeypatch.setattr("strategy.classify_regime", lambda *_args, **_kwargs: (MarketRegime.NOISE, 0.3))
    result = evaluate_strategy_step(
        state=StrategyRuntimeState(
            phase=StrategyPhase.HOLDING,
            position=PositionState(
                has_position=True,
                size_grams=1.0,
                entry_price=800.0,
                entry_time=datetime(2026, 3, 23, 9, 30, 0),
                entry_bar_time=datetime(2026, 3, 23, 9, 30, 0),
                current_stop_loss=790.0,
                strategy_mode=StrategyMode.R2_PULLBACK,
            ),
        ),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(810.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
        ),
        completed_bars=[_bar(i, 800.0 + i) for i in range(12)],
    )
    assert result.action == ActionType.HOLD_POSITION


def test_same_bar_no_regular_exit_after_entry() -> None:
    state = StrategyRuntimeState(
        phase=StrategyPhase.HOLDING,
        position=PositionState(
            has_position=True,
            size_grams=1.0,
            entry_price=810.0,
            entry_time=datetime(2026, 3, 23, 10, 0, 0),
            entry_bar_time=datetime(2026, 3, 23, 10, 0, 0),
            current_stop_loss=790.0,
            strategy_mode=StrategyMode.R2_PULLBACK,
        ),
    )
    decision = evaluate_exit_conditions(
        state=state,
        current_price=808.0,
        indicators=_ready_indicator(
            bar_time=datetime(2026, 3, 23, 10, 0, 0),
            close_5m=794.0,
            donchian_exit_low=795.0,
            ema_fast=806.0,
            bollinger_mid=805.0,
        ),
        completed_bars=[_bar(i, 800.0 + i) for i in range(12)],
        now=datetime(2026, 3, 23, 10, 0, 0),
    )
    assert decision is None


def test_initial_stop_frozen_on_entry(monkeypatch) -> None:
    monkeypatch.setattr("strategy.classify_regime", lambda *_args, **_kwargs: (MarketRegime.TREND_UP, 0.88))
    monkeypatch.setattr(
        "strategy._infer_entry_mode",
        lambda *_args, **_kwargs: (
            StrategyMode.R2_PULLBACK,
            0.88,
            804.0,
            "EMA20 pullback reclaimed.",
            "structure_low=804.00",
            "Exit on Donchian10 or structure failure.",
        ),
    )
    monkeypatch.setattr(
        "strategy.evaluate_long_risk_gate",
        lambda **_kwargs: RiskGateResult(
            allowed=True,
            entry_price=810.0,
            stop_price=804.0,
            stop_distance_per_gram=6.0,
            estimated_grams=1.0,
            fee_floor_yuan=10.0,
            max_price_risk_budget_yuan=10.0,
            max_stop_distance_per_gram=10.0,
            risk_amount_yuan=16.0,
            notional_yuan=1000.0,
            reason="Risk gate passed.",
            atr_cap_per_gram=4.0,
        ),
    )
    result = evaluate_strategy_step(
        state=StrategyRuntimeState(
            phase=StrategyPhase.OBSERVING,
            execution_mode=ExecutionMode.SIGNAL_IMPLIES_POSITION,
        ),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(810.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(close_5m=810.0),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
            recent_minute_ticks=[_tick(809.5, 0), _tick(810.0, 1), _tick(810.2, 2)],
        ),
        completed_bars=[_bar(i, 780.0 + i) for i in range(25)],
    )
    assert result.updated_runtime_state.position.initial_stop_price == pytest.approx(804.0)
    assert result.updated_runtime_state.position.current_stop_loss == pytest.approx(804.0)


def test_confidence_drop_does_not_trigger_exit() -> None:
    state = StrategyRuntimeState(
        phase=StrategyPhase.HOLDING,
        position=PositionState(
            has_position=True,
            size_grams=1.0,
            entry_price=800.0,
            entry_time=datetime(2026, 3, 23, 9, 30, 0),
            entry_bar_time=datetime(2026, 3, 23, 9, 30, 0),
            current_stop_loss=790.0,
            strategy_mode=StrategyMode.R2_PULLBACK,
        ),
    )
    result = evaluate_strategy_step(
        state=state,
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(801.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(
                bar_time=datetime(2026, 3, 23, 10, 5, 0),
                close_5m=801.0,
                donchian_exit_low=795.0,
                ema_fast=800.0,
                bollinger_mid=799.0,
            ),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
        ),
        completed_bars=[_bar(i, 800.0 + i) for i in range(12)],
    )
    assert result.action == ActionType.HOLD_POSITION


def test_sell_now_requires_valid_position_fields() -> None:
    decision = evaluate_exit_conditions(
        state=StrategyRuntimeState(
            phase=StrategyPhase.HOLDING,
            position=PositionState(
                has_position=True,
                size_grams=0.0,
                entry_price=800.0,
                entry_time=None,
                current_stop_loss=790.0,
            ),
        ),
        current_price=780.0,
        indicators=_ready_indicator(),
        completed_bars=[_bar(i, 800.0 + i) for i in range(12)],
        now=datetime(2026, 3, 23, 10, 5, 0),
    )
    assert decision is None


def test_manual_position_sync_overrides_signal_state(monkeypatch) -> None:
    state = StrategyRuntimeState(
        phase=StrategyPhase.HOLDING,
        execution_mode=ExecutionMode.MANUAL_POSITION_SYNC,
        position=PositionState(
            has_position=True,
            size_grams=2.0,
            entry_price=960.0,
            entry_time=datetime(2026, 3, 23, 9, 30, 0),
            entry_bar_time=datetime(2026, 3, 23, 9, 30, 0),
            current_stop_loss=950.0,
            strategy_mode=StrategyMode.R2_PULLBACK,
        ),
    )
    monkeypatch.setattr(
        "strategy._infer_entry_mode",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("new buy logic should not run with actual position")),
    )

    result = evaluate_strategy_step(
        state=state,
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(965.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
        ),
        completed_bars=[_bar(i, 800.0 + i) for i in range(12)],
    )
    assert result.action == ActionType.HOLD_POSITION


def test_manual_position_sync_buy_signal_does_not_create_internal_position(monkeypatch) -> None:
    monkeypatch.setattr("strategy.classify_regime", lambda *_args, **_kwargs: (MarketRegime.TREND_UP, 0.88))
    monkeypatch.setattr(
        "strategy._infer_entry_mode",
        lambda *_args, **_kwargs: (
            StrategyMode.R2_PULLBACK,
            0.88,
            804.0,
            "EMA20 pullback reclaimed.",
            "structure_low=804.00",
            "Exit on Donchian10 or structure failure.",
        ),
    )
    monkeypatch.setattr(
        "strategy.evaluate_long_risk_gate",
        lambda **_kwargs: RiskGateResult(
            allowed=True,
            entry_price=810.0,
            stop_price=804.0,
            stop_distance_per_gram=6.0,
            estimated_grams=1.0,
            fee_floor_yuan=10.0,
            max_price_risk_budget_yuan=10.0,
            max_stop_distance_per_gram=10.0,
            risk_amount_yuan=16.0,
            notional_yuan=1000.0,
            reason="Risk gate passed.",
            atr_cap_per_gram=4.0,
        ),
    )

    result = evaluate_strategy_step(
        state=StrategyRuntimeState(
            phase=StrategyPhase.OBSERVING,
            execution_mode=ExecutionMode.MANUAL_POSITION_SYNC,
        ),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 5, 0),
            current_tick=_tick(810.0, 5),
            next_minute_tick=None,
            indicator_snapshot=_ready_indicator(close_5m=810.0),
            daily_snapshot=_daily_snapshot(),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
            recent_minute_ticks=[_tick(809.5, 0), _tick(810.0, 1), _tick(810.2, 2)],
        ),
        completed_bars=[_bar(i, 780.0 + i) for i in range(25)],
    )
    assert result.action == ActionType.BUY_NOW
    assert result.updated_runtime_state.phase == StrategyPhase.OBSERVING
    assert result.updated_runtime_state.position.has_position is False
