from __future__ import annotations

from datetime import datetime

from models import DailyMarketSnapshot, IndicatorSnapshot, StrategyPhase, StrategyRuntimeState
from strategy import StrategyInput, evaluate_strategy_step
from models import PriceTick


def _tick(minute: int, price: float) -> PriceTick:
    return PriceTick(
        symbol="ICBC_ACC_GOLD",
        price=price,
        observed_at=datetime(2026, 3, 23, 10, minute, 0),
        source="test",
    )


def _pending_state() -> StrategyRuntimeState:
    return StrategyRuntimeState(
        phase=StrategyPhase.WAITING_FOR_ENTRY_FILL,
        pending_entry_signal_time=datetime(2026, 3, 23, 10, 5, 0),
        pending_entry_deadline=datetime(2026, 3, 23, 10, 7, 0),
        pending_entry_reference_bar_time=datetime(2026, 3, 23, 10, 5, 0),
        pending_entry_atr=4.2,
        pending_entry_reason="breakout_buy",
    )


def test_legacy_waiting_state_is_downgraded_to_observing_under_mode_a() -> None:
    result = evaluate_strategy_step(
        state=_pending_state(),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 6, 0),
            current_tick=None,
            next_minute_tick=None,
            indicator_snapshot=IndicatorSnapshot(is_ready=True),
            daily_snapshot=DailyMarketSnapshot(
                symbol="Au99.99",
                open=700.0,
                high=720.0,
                low=690.0,
                last=709.0,
                observed_at=datetime(2026, 3, 23, 10, 0, 0),
                source="sge",
            ),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
        ),
        completed_bars=[],
    )
    assert result.next_state == StrategyPhase.OBSERVING
    assert result.action.value == "WAIT_NO_TRADE"


def test_legacy_waiting_state_does_not_create_position_on_next_tick_under_mode_a() -> None:
    result = evaluate_strategy_step(
        state=_pending_state(),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 7, 0),
            current_tick=_tick(7, 812.5),
            next_minute_tick=None,
            indicator_snapshot=IndicatorSnapshot(is_ready=True),
            daily_snapshot=DailyMarketSnapshot(
                symbol="Au99.99",
                open=700.0,
                high=720.0,
                low=690.0,
                last=709.0,
                observed_at=datetime(2026, 3, 23, 10, 0, 0),
                source="sge",
            ),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
        ),
        completed_bars=[],
    )
    assert result.next_state == StrategyPhase.OBSERVING
    assert result.updated_runtime_state.position.has_position is False


def test_legacy_pending_fields_are_not_used_as_default_entry_flow() -> None:
    result = evaluate_strategy_step(
        state=_pending_state(),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 8, 0),
            current_tick=None,
            next_minute_tick=None,
            indicator_snapshot=IndicatorSnapshot(is_ready=True),
            daily_snapshot=DailyMarketSnapshot(
                symbol="Au99.99",
                open=700.0,
                high=720.0,
                low=690.0,
                last=709.0,
                observed_at=datetime(2026, 3, 23, 10, 0, 0),
                source="sge",
            ),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
        ),
        completed_bars=[],
    )
    assert result.updated_runtime_state.pending_entry_signal_time is not None


def test_strategy_step_keeps_no_pending_fill_state_under_mode_a() -> None:
    result = evaluate_strategy_step(
        state=_pending_state(),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 6, 0),
            current_tick=None,
            next_minute_tick=None,
            indicator_snapshot=IndicatorSnapshot(is_ready=True),
            daily_snapshot=DailyMarketSnapshot(
                symbol="Au99.99",
                open=700.0,
                high=720.0,
                low=690.0,
                last=709.0,
                observed_at=datetime(2026, 3, 23, 10, 0, 0),
                source="sge",
            ),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
        ),
        completed_bars=[],
    )
    assert result.next_state == StrategyPhase.OBSERVING
    assert result.signal_type is None


def test_manual_entry_mode_flag_no_longer_changes_default_mode_a_behavior() -> None:
    result = evaluate_strategy_step(
        state=_pending_state(),
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 6, 0),
            current_tick=_tick(6, 811.2),
            next_minute_tick=None,
            indicator_snapshot=IndicatorSnapshot(is_ready=True),
            daily_snapshot=DailyMarketSnapshot(
                symbol="Au99.99",
                open=700.0,
                high=720.0,
                low=690.0,
                last=709.0,
                observed_at=datetime(2026, 3, 23, 10, 0, 0),
                source="sge",
            ),
            daily_snapshot_fallback_used=False,
            in_trading_window=True,
        ),
        completed_bars=[],
        manual_entry_required=True,
    )
    assert result.next_state == StrategyPhase.OBSERVING
    assert result.updated_runtime_state.position.has_position is False
    assert result.signal_type is None
    assert "manual execution confirmation" not in result.decision_message
