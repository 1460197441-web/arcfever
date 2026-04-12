from __future__ import annotations

from datetime import datetime, timedelta

from config import default_config
from models import (
    ActionType,
    DecisionOutput,
    FeeBreakdown,
    MarketRegime,
    NotificationRecord,
    StrategyMode,
    StrategyRuntimeState,
)
from risk_gate import evaluate_long_risk_gate
from state_store import SQLiteStateStore


def test_fee_aware_risk_gate_blocks_when_stop_distance_exceeds_budget() -> None:
    config = default_config()
    result = evaluate_long_risk_gate(
        entry_price=1000.0,
        stop_price=980.0,
        atr_value=30.0,
        config=config,
        state=StrategyRuntimeState(),
        strategy_mode=StrategyMode.R1_BREAKOUT,
    )
    assert result.allowed is False
    assert "budget" in result.reason.lower()


def test_fee_aware_risk_gate_blocks_averaging_down() -> None:
    config = default_config()
    state = StrategyRuntimeState()
    state.position.has_position = True
    state.position.entry_price = 1005.0
    state.batches_used = 0
    result = evaluate_long_risk_gate(
        entry_price=1000.0,
        stop_price=996.0,
        atr_value=10.0,
        config=config,
        state=state,
        strategy_mode=StrategyMode.R2_PULLBACK,
    )
    assert result.allowed is False
    assert "averaging down" in result.reason.lower()


def test_structural_stop_required() -> None:
    config = default_config()
    result = evaluate_long_risk_gate(
        entry_price=1000.0,
        stop_price=None,
        atr_value=10.0,
        config=config,
        state=StrategyRuntimeState(),
        strategy_mode=StrategyMode.R2_PULLBACK,
    )
    assert result.allowed is False
    assert "stop price is required" in result.reason.lower()


def test_l1_single_probe_only() -> None:
    config = default_config()
    state = StrategyRuntimeState()
    state.batches_used = 1
    result = evaluate_long_risk_gate(
        entry_price=1000.0,
        stop_price=995.0,
        atr_value=10.0,
        config=config,
        state=state,
        strategy_mode=StrategyMode.L1_EXHAUSTION,
    )
    assert result.allowed is False
    assert "one probe" in result.reason.lower()


def test_no_average_down() -> None:
    config = default_config()
    state = StrategyRuntimeState()
    state.position.has_position = True
    state.position.entry_price = 1000.0
    result = evaluate_long_risk_gate(
        entry_price=999.0,
        stop_price=995.0,
        atr_value=10.0,
        config=config,
        state=state,
        strategy_mode=StrategyMode.R2_PULLBACK,
    )
    assert result.allowed is False
    assert "averaging down" in result.reason.lower()


def test_decision_round_trip_and_notification_dedupe(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    now = datetime(2026, 3, 25, 10, 31, 0)
    decision = DecisionOutput(
        action=ActionType.BUY_NOW,
        strategy_mode=StrategyMode.R1_BREAKOUT,
        confidence=0.84,
        regime=MarketRegime.BREAKOUT_READY,
        entry_reason="compression breakout",
        invalidation_reason="",
        stop_rule="breakout_low_buffer -> 1000.20",
        take_profit_rule="trail after 1.8R",
        position_size_yuan=1000.0,
        fees_considered=FeeBreakdown(0.005, 0.005, 9.975),
        whether_send_email=True,
        short_email_subject="ICBC Gold BUY_NOW R1_BREAKOUT 0.84",
        short_email_body="BUY_NOW 1000 CNY",
        timestamp=now,
        dedupe_key="BUY_NOW|R1_BREAKOUT|1000.0|2026-03-25T10:30:00|0",
    )
    store.append_decision(decision)

    stored = store.load_recent_decisions(limit=5)
    assert stored[0].action == ActionType.BUY_NOW
    assert stored[0].strategy_mode == StrategyMode.R1_BREAKOUT
    assert stored[0].dedupe_key == decision.dedupe_key

    store.append_notification(
        NotificationRecord(
            title=decision.short_email_subject,
            notification_type="buy",
            success=True,
            sent_at=now,
            dedupe_key=decision.dedupe_key,
            decision_action=decision.action.value,
            strategy_mode=decision.strategy_mode.value,
        )
    )
    assert store.has_recent_notification_dedupe(decision.dedupe_key or "", since=now - timedelta(minutes=15)) is True
