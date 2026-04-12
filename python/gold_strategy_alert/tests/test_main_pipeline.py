from __future__ import annotations

from datetime import datetime, timedelta
import sqlite3

from config import default_config
from data_provider import DataFetchResult
from main import PipelineRunner
from models import (
    DailyMarketSnapshot,
    EventType,
    MarketPriceQuote,
    PositionState,
    PriceTick,
    StrategyEvent,
    StrategyPhase,
    StrategyRuntimeState,
)
from notifier import EmailNotifier
from scheduler import ReplayController
from state_store import SQLiteStateStore


class FakeLiveProvider:
    def __init__(self, tick: PriceTick, daily_snapshot: DailyMarketSnapshot, fallback_used: bool = False) -> None:
        self.tick = tick
        self.daily_snapshot = daily_snapshot
        self.fallback_used = fallback_used

    def fetch(self, now: datetime) -> DataFetchResult:
        return DataFetchResult(
            tick=self.tick,
            primary_quote=MarketPriceQuote(
                current_price=self.tick.price,
                instrument_name="工银积存金",
                quote_time=self.tick.observed_at,
                quote_time_source="fetch_time",
                currency="CNY",
                source_name="fake_live",
                open_price=self.daily_snapshot.open,
                high_price=self.daily_snapshot.high,
                low_price=self.daily_snapshot.low,
            ),
            daily_reference=self.daily_snapshot,
            fallback_used=self.fallback_used,
            events=[
                StrategyEvent(
                    event_type=EventType.SAMPLE_SUCCESS,
                    event_time=now,
                    title="sample",
                    message="sample success",
                )
            ],
        )


class FailingLiveProvider:
    def __init__(self, message: str = "fetch failed") -> None:
        self.message = message

    def fetch(self, now: datetime) -> DataFetchResult:
        raise RuntimeError(self.message)


def _bar_close(index: int) -> float:
    return 800.0 + index


def _seed_ready_bars(store: SQLiteStateStore, count: int = 50) -> None:
    start = datetime(2026, 3, 23, 7, 0, 0)
    for index in range(count):
        bar_start = start + timedelta(minutes=5 * index)
        close = _bar_close(index)
        if index == count - 1:
            close += 10.0
        from models import Bar

        store.append_bar(
            Bar(
                start_at=bar_start,
                end_at=bar_start + timedelta(minutes=5),
                open=close - 1,
                high=close + 2,
                low=close - 2,
                close=close,
                source="seed",
                is_complete=True,
            )
        )


def _daily_snapshot(now: datetime) -> DailyMarketSnapshot:
    return DailyMarketSnapshot(
        symbol="Au99.99",
        open=700.0,
        high=720.0,
        low=690.0,
        last=709.0,
        observed_at=now,
        source="sge",
    )


def _notifier(config):
    notifier = EmailNotifier(config.email)
    notifier.configure_test_mode(
        enable_test_mode=config.runtime.enable_test_mode,
        send_real_email_in_test_mode=config.runtime.send_real_email_in_test_mode,
    )
    return notifier


def test_live_like_single_cycle_runs_collect_aggregate_indicator_strategy_and_persistence(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "live"
    config.runtime.session_mode = "force_open"
    config.runtime.enable_test_mode = True
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    _seed_ready_bars(store)
    tick = PriceTick(
        symbol="ICBC_ACC_GOLD",
        price=850.0,
        observed_at=datetime(2026, 3, 23, 10, 35, 0),
        source="fake_live",
    )
    provider = FakeLiveProvider(tick=tick, daily_snapshot=_daily_snapshot(tick.observed_at))
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config), live_provider=provider)
    result = runner.run_once(now=tick.observed_at)
    assert result.tick_written is True
    assert result.strategy_result is not None
    assert result.events_count >= 1
    assert store.load_runtime_state().phase == result.strategy_result.updated_runtime_state.phase


def test_replay_step_advances_state_machine_one_tick_at_a_time(tmp_path) -> None:
    csv_path = tmp_path / "ticks.csv"
    csv_path.write_text(
        "observed_at,price,symbol,source\n"
        "2026-03-23T10:06:00,811.2,ICBC_ACC_GOLD,replay\n"
        "2026-03-23T10:07:00,812.0,ICBC_ACC_GOLD,replay\n",
        encoding="utf-8",
    )
    config = default_config()
    config.runtime.run_mode = "replay"
    config.runtime.session_mode = "force_open"
    config.runtime.enable_test_mode = True
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    _seed_ready_bars(store)
    controller = ReplayController.from_csv(csv_path, mode="step")
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config), replay_controller=controller)
    result = runner.run_once(now=datetime(2026, 3, 23, 10, 6, 0))
    assert result.strategy_result is not None
    assert result.tick_written is True
    assert store.load_latest_minute_price() is not None


def test_mock_mode_runs_notification_and_notification_record_is_persisted(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "mock"
    config.runtime.session_mode = "force_open"
    config.runtime.enable_test_mode = True
    config.runtime.mock_current_price = 850.0
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    _seed_ready_bars(store)
    store.save_runtime_state(
        StrategyRuntimeState(
            phase=StrategyPhase.HOLDING,
            position=PositionState(
                has_position=True,
                size_grams=1.0,
                entry_price=800.0,
                entry_time=datetime(2026, 3, 23, 10, 0, 0),
                entry_bar_time=datetime(2026, 3, 23, 10, 0, 0),
                current_stop_loss=790.0,
            ),
        )
    )
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config))
    result = runner.run_once(now=datetime(2026, 3, 23, 22, 20, 0))
    assert result.notification_record is not None
    with sqlite3.connect(tmp_path / "state.db") as conn:
        row = conn.execute("SELECT COUNT(*), simulated_send FROM notifications").fetchone()
    assert row[0] == 1
    assert row[1] == 1


def test_market_hours_outside_session_only_writes_data_without_new_decision(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "mock"
    config.runtime.session_mode = "market_hours"
    config.runtime.mock_current_price = 850.0
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    _seed_ready_bars(store)
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config))
    result = runner.run_once(now=datetime(2026, 3, 23, 8, 0, 0))
    assert result.tick_written is True
    assert result.decision_allowed is False
    assert result.strategy_result is not None
    assert result.strategy_result.updated_runtime_state.phase == StrategyPhase.OBSERVING


def test_force_open_outside_session_allows_full_decision(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "mock"
    config.runtime.session_mode = "force_open"
    config.runtime.mock_current_price = 850.0
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    _seed_ready_bars(store)
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config))
    result = runner.run_once(now=datetime(2026, 3, 23, 8, 0, 0))
    assert result.decision_allowed is True
    assert result.strategy_result is not None
    assert result.readiness_level == "full_ready"


def test_market_open_entry_freeze_blocks_new_entry_even_when_indicators_ready(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "mock"
    config.runtime.session_mode = "market_hours"
    config.runtime.mock_current_price = 850.0
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    _seed_ready_bars(store)
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config))
    result = runner.run_once(now=datetime(2026, 3, 23, 9, 20, 0))
    assert result.readiness_level == "full_ready"
    assert result.strategy_result is not None
    assert result.strategy_result.updated_runtime_state.phase == StrategyPhase.OBSERVING


def test_exit_only_ready_still_allows_existing_position_to_exit(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "mock"
    config.runtime.session_mode = "force_open"
    config.runtime.mock_current_price = 770.0
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    for index in range(20):
        close = 800.0 + index
        start = datetime(2026, 3, 23, 9, 0, 0) + timedelta(minutes=5 * index)
        from models import Bar
        store.append_bar(
            Bar(
                start_at=start,
                end_at=start + timedelta(minutes=5),
                open=close - 1,
                high=close + 2,
                low=close - 2,
                close=close,
                source="seed",
                is_complete=True,
            )
        )
    store.save_runtime_state(
        StrategyRuntimeState(
            phase=StrategyPhase.HOLDING,
            position=PositionState(
                has_position=True,
                size_grams=1.0,
                entry_price=800.0,
                entry_time=datetime(2026, 3, 23, 9, 30, 0),
                entry_bar_time=datetime(2026, 3, 23, 9, 30, 0),
                current_stop_loss=790.0,
            ),
        )
    )
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config))
    result = runner.run_once(now=datetime(2026, 3, 23, 10, 40, 0))
    assert result.readiness_level == "exit_only_ready"
    assert result.strategy_result is not None
    assert result.strategy_result.exit_reason is not None


def test_notify_only_mode_does_not_advance_to_real_holding_state(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "mock"
    config.runtime.session_mode = "notify_only"
    config.runtime.mock_current_price = 850.0
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    _seed_ready_bars(store)
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config))
    result = runner.run_once(now=datetime(2026, 3, 23, 8, 0, 0))
    assert result.strategy_result is not None
    assert result.strategy_result.updated_runtime_state.phase == StrategyPhase.OBSERVING


def test_price_below_alert_triggers_notification_and_event_once(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "mock"
    config.runtime.session_mode = "force_open"
    config.runtime.enable_test_mode = True
    config.runtime.mock_current_price = 995.0
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    _seed_ready_bars(store)
    state = store.load_runtime_state()
    state.price_alert.enabled = True
    state.price_alert.target_price = 1000.0
    store.save_runtime_state(state)

    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config))
    result = runner.run_once(now=datetime(2026, 3, 23, 10, 0, 0))

    assert result.notification_record is not None
    assert result.notification_record.simulated_send is True
    assert any(event.event_type == EventType.PRICE_ALERT_TRIGGERED for event in store.load_recent_events(limit=10))
    assert store.load_runtime_state().price_alert.active_below_triggered is True

    second_result = runner.run_once(now=datetime(2026, 3, 23, 10, 1, 0))
    notifications = store.load_recent_notifications(limit=10)
    assert second_result.notification_record is None or second_result.notification_record == result.notification_record
    assert len([item for item in notifications if item.title == result.notification_record.title]) == 1


def test_price_below_alert_rearms_after_price_recovers(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "mock"
    config.runtime.session_mode = "force_open"
    config.runtime.enable_test_mode = True
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    _seed_ready_bars(store)
    state = store.load_runtime_state()
    state.price_alert.enabled = True
    state.price_alert.target_price = 1000.0
    store.save_runtime_state(state)

    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config))
    config.runtime.mock_current_price = 995.0
    runner.run_once(now=datetime(2026, 3, 23, 10, 0, 0))
    assert store.load_runtime_state().price_alert.active_below_triggered is True

    config.runtime.mock_current_price = 1005.0
    runner.run_once(now=datetime(2026, 3, 23, 10, 1, 0))
    assert store.load_runtime_state().price_alert.active_below_triggered is False


def test_email_failure_does_not_break_state_or_event_persistence(tmp_path, monkeypatch) -> None:
    config = default_config()
    config.runtime.run_mode = "mock"
    config.runtime.session_mode = "force_open"
    config.runtime.enable_test_mode = False
    config.runtime.mock_current_price = 850.0
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    _seed_ready_bars(store)
    store.save_runtime_state(
        StrategyRuntimeState(
            phase=StrategyPhase.HOLDING,
            position=PositionState(
                has_position=True,
                size_grams=1.0,
                entry_price=800.0,
                entry_time=datetime(2026, 3, 23, 10, 0, 0),
                entry_bar_time=datetime(2026, 3, 23, 10, 0, 0),
                current_stop_loss=790.0,
            ),
        )
    )
    notifier = _notifier(config)

    def fail_send(message):
        raise RuntimeError("smtp failed")

    monkeypatch.setattr(notifier, "_send_message", fail_send)
    runner = PipelineRunner(config=config, store=store, notifier=notifier)
    result = runner.run_once(now=datetime(2026, 3, 23, 22, 20, 0))
    assert result.notification_record is not None
    assert result.notification_record.success is False
    assert store.load_runtime_state().phase == StrategyPhase.OBSERVING
    with sqlite3.connect(tmp_path / "state.db") as conn:
        event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        notification_count = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
    assert event_count >= 1
    assert notification_count == 1


def test_runtime_state_recovery_allows_continued_pipeline_execution(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "replay"
    config.runtime.session_mode = "force_open"
    config.runtime.enable_test_mode = True
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    store.save_runtime_state(
        StrategyRuntimeState(
            phase=StrategyPhase.HOLDING,
            position=PositionState(
                has_position=True,
                size_grams=1.0,
                entry_price=811.2,
                entry_time=datetime(2026, 3, 23, 10, 5, 0),
                entry_bar_time=datetime(2026, 3, 23, 10, 5, 0),
                current_stop_loss=790.0,
                initial_stop_price=790.0,
            ),
        )
    )
    csv_path = tmp_path / "ticks.csv"
    csv_path.write_text(
        "observed_at,price,symbol,source\n"
        "2026-03-23T10:06:00,811.2,ICBC_ACC_GOLD,replay\n",
        encoding="utf-8",
    )
    controller = ReplayController.from_csv(csv_path, mode="step")
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config), replay_controller=controller)
    result = runner.run_once(now=datetime(2026, 3, 23, 10, 6, 0))
    assert result.strategy_result is not None
    assert result.strategy_result.updated_runtime_state.phase == StrategyPhase.HOLDING


def test_generated_events_are_written_and_notifications_are_persisted(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "mock"
    config.runtime.session_mode = "force_open"
    config.runtime.enable_test_mode = True
    config.runtime.mock_current_price = 850.0
    config.runtime.mock_daily_open = 700.0
    config.runtime.mock_daily_high = 720.0
    config.runtime.mock_daily_low = 690.0
    config.runtime.mock_daily_last = 709.0
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    _seed_ready_bars(store)
    store.save_runtime_state(
        StrategyRuntimeState(
            phase=StrategyPhase.HOLDING,
            position=PositionState(
                has_position=True,
                size_grams=1.0,
                entry_price=800.0,
                entry_time=datetime(2026, 3, 23, 10, 0, 0),
                entry_bar_time=datetime(2026, 3, 23, 10, 0, 0),
                current_stop_loss=790.0,
            ),
        )
    )
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config))
    result = runner.run_once(now=datetime(2026, 3, 23, 22, 20, 0))
    with sqlite3.connect(tmp_path / "state.db") as conn:
        event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        notification_count = conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
    assert result.events_count == event_count
    assert notification_count == 1


def test_live_fetch_failure_alert_only_triggers_after_threshold(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "live"
    config.runtime.session_mode = "force_open"
    config.runtime.enable_test_mode = True
    config.runtime.fetch_failure_alert_threshold = 2
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    runner = PipelineRunner(
        config=config,
        store=store,
        notifier=_notifier(config),
        live_provider=FailingLiveProvider("icbc down"),
    )

    first = runner.run_once(now=datetime(2026, 3, 23, 10, 0, 0))
    assert first.notification_record is None
    assert store.load_runtime_state().consecutive_fetch_failures == 1

    second = runner.run_once(now=datetime(2026, 3, 23, 10, 1, 0))
    recovered_state = store.load_runtime_state()
    assert second.notification_record is not None
    assert second.notification_record.simulated_send is True
    assert recovered_state.consecutive_fetch_failures == 2
    assert recovered_state.fetch_alert_active is True


def test_live_fetch_recovery_sends_recovery_notification_and_resets_counter(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "live"
    config.runtime.session_mode = "force_open"
    config.runtime.enable_test_mode = True
    config.runtime.fetch_failure_alert_threshold = 2
    config.runtime.send_fetch_recovery_notification = True
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    store.save_runtime_state(
        StrategyRuntimeState(
            phase=StrategyPhase.OBSERVING,
            consecutive_fetch_failures=2,
            fetch_alert_active=True,
        )
    )
    provider = FakeLiveProvider(
        tick=PriceTick(
            symbol="ICBC_ACC_GOLD",
            price=850.0,
            observed_at=datetime(2026, 3, 23, 10, 35, 0),
            source="fake_live",
        ),
        daily_snapshot=_daily_snapshot(datetime(2026, 3, 23, 10, 35, 0)),
    )
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config), live_provider=provider)
    result = runner.run_once(now=datetime(2026, 3, 23, 10, 35, 0))

    state = store.load_runtime_state()
    assert result.notification_record is not None
    assert result.notification_record.simulated_send is True
    assert state.consecutive_fetch_failures == 0
    assert state.fetch_alert_active is False
    assert state.last_fetch_success_time == datetime(2026, 3, 23, 10, 35, 0)


def test_history_preload_rebuilds_completed_bars_from_existing_minute_prices(tmp_path) -> None:
    config = default_config()
    config.runtime.run_mode = "mock"
    config.runtime.session_mode = "force_open"
    store = SQLiteStateStore(tmp_path / "state.db")
    store.initialize()
    for minute in range(10):
        store.append_minute_price(
            PriceTick(
                symbol="ICBC_ACC_GOLD",
                price=800.0 + minute,
                observed_at=datetime(2026, 3, 23, 9, minute, 0),
                source="seed",
            )
        )
    runner = PipelineRunner(config=config, store=store, notifier=_notifier(config))
    rebuilt_bars = store.load_recent_completed_bars(limit=10)
    assert runner.preloaded_ticks_count == 10
    assert runner.preloaded_bars_count >= 2
    assert len(rebuilt_bars) >= 2


def test_holding_exit_still_runs_when_daily_snapshot_is_missing(tmp_path) -> None:
    config = default_config()
    state = StrategyRuntimeState(
        phase=StrategyPhase.HOLDING,
        position=PositionState(
            has_position=True,
            size_grams=1.0,
            entry_price=800.0,
            entry_time=datetime(2026, 3, 23, 9, 0, 0),
            entry_bar_time=datetime(2026, 3, 23, 9, 0, 0),
            current_stop_loss=790.0,
        ),
    )
    from strategy import StrategyInput, evaluate_strategy_step
    from models import IndicatorSnapshot
    result = evaluate_strategy_step(
        state=state,
        data=StrategyInput(
            now=datetime(2026, 3, 23, 10, 0, 0),
            current_tick=PriceTick(
                symbol="ICBC_ACC_GOLD",
                price=789.0,
                observed_at=datetime(2026, 3, 23, 10, 0, 0),
                source="test",
            ),
            next_minute_tick=None,
            indicator_snapshot=IndicatorSnapshot(is_ready=False),
            daily_snapshot=None,
            daily_snapshot_fallback_used=False,
            in_trading_window=False,
        ),
        completed_bars=[],
        fee_break_even_multiplier=config.fees.fee_break_even_multiplier,
    )
    assert result.exit_reason is not None
    assert result.updated_runtime_state.phase == StrategyPhase.COOLDOWN_AFTER_STOP
