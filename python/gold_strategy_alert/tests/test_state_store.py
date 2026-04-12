from __future__ import annotations

from datetime import datetime, timedelta
import json
import sqlite3

from models import (
    Bar,
    EventType,
    ExitReason,
    MarketRegime,
    NotificationRecord,
    PositionState,
    PriceTick,
    StrategyEvent,
    StrategyPhase,
    StrategyMode,
    StrategyRuntimeState,
)
from state_store import SQLiteStateStore


def _bar(index: int, close: float, is_complete: bool = True) -> Bar:
    start = datetime(2026, 3, 23, 9, 15) + timedelta(minutes=5 * index)
    return Bar(
        start_at=start,
        end_at=start + timedelta(minutes=5),
        open=close - 1,
        high=close + 1,
        low=close - 2,
        close=close,
        source="test",
        is_complete=is_complete,
    )


def test_runtime_state_single_row_overwrite_save(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    store.save_runtime_state(StrategyRuntimeState(phase=StrategyPhase.OBSERVING))
    store.save_runtime_state(StrategyRuntimeState(phase=StrategyPhase.ERROR))
    with sqlite3.connect(tmp_path / "state.db") as conn:
        count = conn.execute("SELECT COUNT(*) FROM runtime_state").fetchone()[0]
    assert count == 1


def test_runtime_state_round_trip_persists_mode_a_position_fields(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    state = StrategyRuntimeState(
        phase=StrategyPhase.HOLDING,
        consecutive_fetch_failures=2,
        fetch_alert_active=True,
        last_fetch_success_time=datetime(2026, 3, 23, 10, 4, 0),
        position=PositionState(
            has_position=True,
            size_grams=1.9,
            entry_price=810.0,
            entry_time=datetime(2026, 3, 23, 10, 5, 0),
            entry_bar_time=datetime(2026, 3, 23, 10, 5, 0),
            position_notional_yuan=1000.0,
            initial_stop_price=804.0,
            current_stop_loss=804.0,
            stop_source="structure_low=804.00",
            trade_idea_id="R2_PULLBACK|2026-03-23T10:05:00",
            strategy_mode=StrategyMode.R2_PULLBACK,
            regime_at_entry=MarketRegime.TREND_UP,
        ),
        last_decision_time=datetime(2026, 3, 23, 10, 5, 0),
    )
    store.save_runtime_state(state)
    recovered = store.load_runtime_state()
    assert recovered.phase == StrategyPhase.HOLDING
    assert recovered.consecutive_fetch_failures == 2
    assert recovered.fetch_alert_active is True
    assert recovered.last_fetch_success_time == datetime(2026, 3, 23, 10, 4, 0)
    assert recovered.position.entry_price == 810.0
    assert recovered.position.entry_bar_time == datetime(2026, 3, 23, 10, 5, 0)
    assert recovered.position.position_notional_yuan == 1000.0
    assert recovered.position.initial_stop_price == 804.0
    assert recovered.position.stop_source == "structure_low=804.00"
    assert recovered.position.trade_idea_id == "R2_PULLBACK|2026-03-23T10:05:00"


def test_holding_state_round_trip_persists_position_and_trailing_context(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    state = StrategyRuntimeState(
        phase=StrategyPhase.HOLDING,
        position=PositionState(
            has_position=True,
            size_grams=2.0,
            entry_price=800.0,
            entry_time=datetime(2026, 3, 23, 10, 6, 0),
            current_stop_loss=796.0,
            trailing_active=True,
            h_star=822.0,
        ),
        last_decision_time=datetime(2026, 3, 23, 10, 20, 0),
    )
    store.save_runtime_state(state)
    recovered = store.load_runtime_state()
    assert recovered.phase == StrategyPhase.HOLDING
    assert recovered.position.has_position is True
    assert recovered.position.size_grams == 2.0
    assert recovered.position.entry_price == 800.0
    assert recovered.position.trailing_active is True
    assert recovered.position.h_star == 822.0


def test_cooldown_state_round_trip_persists_cooldown_context(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    state = StrategyRuntimeState(
        phase=StrategyPhase.COOLDOWN_AFTER_STOP,
        cooldown_end_time=datetime(2026, 3, 23, 10, 40, 0),
        last_exit_time=datetime(2026, 3, 23, 10, 20, 0),
        last_exit_reason=ExitReason.TIME_STOP,
    )
    store.save_runtime_state(state)
    recovered = store.load_runtime_state()
    assert recovered.phase == StrategyPhase.COOLDOWN_AFTER_STOP
    assert recovered.cooldown_end_time == datetime(2026, 3, 23, 10, 40, 0)
    assert recovered.last_exit_reason == ExitReason.TIME_STOP


def test_reentry_state_round_trip_persists_reentry_context(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    state = StrategyRuntimeState(
        phase=StrategyPhase.WAITING_REENTRY_CONFIRMATION,
        last_exit_time=datetime(2026, 3, 23, 10, 20, 0),
        last_exit_reason=ExitReason.HARD_TAKE_PROFIT,
        post_exit_12bar_high=812.5,
        last_effective_5m_bar_end=datetime(2026, 3, 23, 10, 25, 0),
    )
    store.save_runtime_state(state)
    recovered = store.load_runtime_state()
    assert recovered.phase == StrategyPhase.WAITING_REENTRY_CONFIRMATION
    assert recovered.post_exit_12bar_high == 812.5
    assert recovered.last_effective_5m_bar_end == datetime(2026, 3, 23, 10, 25, 0)


def test_events_write_structured_payload_and_phase_transition(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    store.append_event(
        StrategyEvent(
            event_type=EventType.ENTRY_TIMEOUT_CANCELLED,
            event_time=datetime(2026, 3, 23, 10, 8, 0),
            phase_before=StrategyPhase.WAITING_FOR_ENTRY_FILL,
            phase_after=StrategyPhase.OBSERVING,
            title="Pending entry canceled",
            message="No valid next-minute price arrived before deadline.",
            metadata={"reason": "timeout"},
        )
    )
    with sqlite3.connect(tmp_path / "state.db") as conn:
        row = conn.execute(
            "SELECT event_type, phase_before, phase_after, payload_json FROM events"
        ).fetchone()
    assert row[0] == EventType.ENTRY_TIMEOUT_CANCELLED.value
    assert row[1] == StrategyPhase.WAITING_FOR_ENTRY_FILL.value
    assert row[2] == StrategyPhase.OBSERVING.value
    assert json.loads(row[3])["reason"] == "timeout"


def test_minute_prices_and_bars_can_be_written_and_read_back(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    for minute in range(3):
        store.append_minute_price(
            PriceTick(
                symbol="ICBC_ACC_GOLD",
                price=800.0 + minute,
                observed_at=datetime(2026, 3, 23, 10, minute, 0),
                source="test",
            )
        )
    for index in range(3):
        store.append_bar(_bar(index, 800.0 + index, is_complete=True))

    recent_ticks = store.load_recent_minute_prices(limit=2)
    latest_tick = store.load_latest_minute_price()
    recent_bars = store.load_recent_completed_bars(limit=2)
    assert len(recent_ticks) == 2
    assert recent_ticks[-1].price == 802.0
    assert latest_tick is not None
    assert latest_tick.price == 802.0
    assert len(recent_bars) == 2
    assert recent_bars[-1].close == 802.0


def test_load_bars_after_and_post_exit_queries_are_correct(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    for index in range(5):
        store.append_bar(_bar(index, 800.0 + index, is_complete=True))
    bars_after = store.load_bars_after(datetime(2026, 3, 23, 9, 20, 0))
    post_exit_bars = store.load_post_exit_completed_bars(datetime(2026, 3, 23, 9, 25, 0), limit=2)
    assert [bar.close for bar in bars_after] == [802.0, 803.0, 804.0]
    assert [bar.close for bar in post_exit_bars] == [803.0, 804.0]


def test_restart_recovery_state_is_usable_for_continued_strategy_flow(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    initial = StrategyRuntimeState(
        phase=StrategyPhase.HOLDING,
        position=PositionState(
            has_position=True,
            size_grams=1.2,
            entry_price=810.0,
            entry_time=datetime(2026, 3, 23, 10, 5, 0),
            entry_bar_time=datetime(2026, 3, 23, 10, 5, 0),
            position_notional_yuan=1000.0,
            initial_stop_price=804.0,
            current_stop_loss=804.0,
        ),
    )
    store.save_runtime_state(initial)
    restarted_store = SQLiteStateStore(tmp_path / "state.db")
    restarted_store.initialize()
    recovered = restarted_store.load_runtime_state()
    assert recovered.phase == StrategyPhase.HOLDING
    assert recovered.position.entry_price == 810.0


def test_sqlite_schema_creates_required_indexes(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    with sqlite3.connect(tmp_path / "state.db") as conn:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}
    assert "idx_events_event_time" in names
    assert "idx_events_event_type_event_time" in names
    assert "idx_minute_prices_observed_at" in names
    assert "idx_bars_5m_start_is_complete" in names
    assert "idx_notifications_sent_at" in names


def test_append_notification_writes_notification_row(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    store.append_notification(
        NotificationRecord(
            title="notice",
            notification_type="buy",
            success=True,
            simulated_send=True,
            sent_at=datetime(2026, 3, 23, 10, 5, 5),
        )
    )
    with sqlite3.connect(tmp_path / "state.db") as conn:
        row = conn.execute("SELECT COUNT(*), simulated_send FROM notifications").fetchone()
    assert row[0] == 1
    assert row[1] == 1


def test_load_recent_events_and_notifications_round_trip(tmp_path) -> None:
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    store.append_event(
        StrategyEvent(
            event_type=EventType.MANUAL_POSITION_SET,
            event_time=datetime(2026, 3, 23, 10, 10, 0),
            title="manual",
            message="manual set",
        )
    )
    store.append_notification(
        NotificationRecord(
            title="manual notice",
            notification_type="info",
            success=True,
            simulated_send=True,
            sent_at=datetime(2026, 3, 23, 10, 10, 5),
        )
    )
    events = store.load_recent_events(limit=5)
    notifications = store.load_recent_notifications(limit=5)
    assert events[0].event_type == EventType.MANUAL_POSITION_SET
    assert notifications[0].title == "manual notice"
