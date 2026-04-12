from __future__ import annotations

from datetime import datetime, timedelta

from config import ProfileName, default_config
from control_server import ControlCommandService
from models import EventType, ExecutionMode, PositionState, StrategyPhase, StrategyRuntimeState
from state_store import SQLiteStateStore


def test_position_sync_api_updates_state(tmp_path) -> None:
    config = default_config()
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    service = ControlCommandService(config, store)

    result = service.sync_position(
        has_position=True,
        position_size_grams=2.0,
        avg_entry_price=960.0,
        entry_time=datetime(2026, 3, 25, 10, 0, 0),
        note="manual broker fill",
    )

    state = store.load_runtime_state()
    assert result.ok is True
    assert state.phase == StrategyPhase.HOLDING
    assert state.position.has_position is True
    assert state.position.size_grams == 2.0
    assert state.position.entry_price == 960.0
    assert state.position.note == "manual broker fill"
    assert state.position.last_sync_source == "api_sync"


def test_position_adjust_recalculates_avg_price(tmp_path) -> None:
    config = default_config()
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    service = ControlCommandService(config, store)

    service.sync_position(
        has_position=True,
        position_size_grams=1.0,
        avg_entry_price=960.0,
        entry_time=datetime(2026, 3, 25, 10, 0, 0),
    )
    result = service.adjust_position(delta_grams=1.0, fill_price=980.0, note="add")

    state = store.load_runtime_state()
    assert result.ok is True
    assert state.position.size_grams == 2.0
    assert state.position.entry_price == 970.0


def test_profile_switch_to_aggressive_updates_runtime_config(tmp_path) -> None:
    config = default_config()
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    service = ControlCommandService(config, store)

    result = service.set_profile(ProfileName.SLIGHTLY_AGGRESSIVE_TODAY.value)

    state = store.load_runtime_state()
    assert result.ok is True
    assert state.profile_name == ProfileName.SLIGHTLY_AGGRESSIVE_TODAY
    assert config.runtime.profile_name == ProfileName.SLIGHTLY_AGGRESSIVE_TODAY.value
    assert config.strategy_switches.enable_r1 is True
    assert config.strategy_switches.enable_l1 is False
    assert config.risk.first_entry_yuan == 2000.0


def test_aggressive_mode_enables_r1_but_not_l1(tmp_path) -> None:
    config = default_config()
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    service = ControlCommandService(config, store)

    service.set_profile(ProfileName.SLIGHTLY_AGGRESSIVE_TODAY.value)

    assert config.strategy_switches.enable_r2 is True
    assert config.strategy_switches.enable_r1 is True
    assert config.strategy_switches.enable_l1 is False


def test_execution_mode_switch_persists(tmp_path) -> None:
    config = default_config()
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    service = ControlCommandService(config, store)

    result = service.set_execution_mode(ExecutionMode.SIGNAL_IMPLIES_POSITION.value)

    state = store.load_runtime_state()
    assert result.ok is True
    assert state.execution_mode == ExecutionMode.SIGNAL_IMPLIES_POSITION
    assert config.runtime.execution_mode == ExecutionMode.SIGNAL_IMPLIES_POSITION.value


def test_operator_actions_are_persisted(tmp_path) -> None:
    config = default_config()
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    service = ControlCommandService(config, store)

    service.set_pause_new_entries(True)
    service.request_force_flatten()
    service.clear_cooldown()

    recent_events = store.load_recent_events(limit=10)
    event_types = [event.event_type for event in recent_events]
    assert EventType.OPERATOR_ACTION in event_types


def test_clear_position_returns_to_observing(tmp_path) -> None:
    config = default_config()
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    store.save_runtime_state(
        StrategyRuntimeState(
            phase=StrategyPhase.HOLDING,
            position=PositionState(
                has_position=True,
                size_grams=2.0,
                entry_price=960.0,
                entry_time=datetime(2026, 3, 25, 10, 0, 0),
                current_stop_loss=955.0,
            ),
        )
    )
    service = ControlCommandService(config, store)

    result = service.sync_position(has_position=False, note="manual close")

    state = store.load_runtime_state()
    assert result.ok is True
    assert state.phase == StrategyPhase.OBSERVING
    assert state.position.has_position is False


def test_build_status_exposes_runtime_and_position_snapshot(tmp_path) -> None:
    config = default_config()
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    service = ControlCommandService(config, store)

    service.sync_position(
        has_position=True,
        position_size_grams=1.2,
        avg_entry_price=965.0,
        entry_time=datetime.now() - timedelta(minutes=15),
        note="test position",
    )
    status = service.build_status()

    assert status.runtime_state.position.has_position is True
    assert status.runtime_state.position.entry_price == 965.0


def test_price_alert_can_be_set_and_cleared(tmp_path) -> None:
    config = default_config()
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    service = ControlCommandService(config, store)

    result = service.set_price_below_alert(1000.0)
    state = store.load_runtime_state()
    assert result.ok is True
    assert state.price_alert.enabled is True
    assert state.price_alert.target_price == 1000.0

    clear_result = service.clear_price_alert()
    cleared_state = store.load_runtime_state()
    assert clear_result.ok is True
    assert cleared_state.price_alert.enabled is False
    assert cleared_state.price_alert.target_price is None


def test_price_alert_payload_exposes_current_alert_state(tmp_path) -> None:
    config = default_config()
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    service = ControlCommandService(config, store)

    service.set_price_below_alert(999.99)
    payload = service.current_price_alert_payload()

    assert payload["enabled"] is True
    assert payload["target_price"] == 999.99
    assert payload["trigger_when_below"] is True
