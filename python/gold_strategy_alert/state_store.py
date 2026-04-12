"""SQLite-backed storage for runtime state, events, prices, bars, and notifications."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any

from models import (
    Bar,
    DecisionOutput,
    ExecutionMode,
    EventType,
    ExitReason,
    MarketRegime,
    NotificationRecord,
    ProfileName,
    PriceAlertState,
    PositionState,
    PriceTick,
    StrategyEvent,
    StrategyPhase,
    StrategyMode,
    StrategyRuntimeState,
)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runtime_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    phase TEXT NOT NULL,
    has_position INTEGER NOT NULL,
    execution_mode TEXT NOT NULL DEFAULT 'manual_position_sync',
    profile_name TEXT NOT NULL DEFAULT 'conservative',
    paused_new_entries INTEGER NOT NULL DEFAULT 0,
    force_flatten_requested INTEGER NOT NULL DEFAULT 0,
    price_alert_enabled INTEGER NOT NULL DEFAULT 0,
    price_alert_target_price REAL,
    price_alert_trigger_when_below INTEGER NOT NULL DEFAULT 1,
    price_alert_active_below_triggered INTEGER NOT NULL DEFAULT 0,
    price_alert_last_triggered_at TEXT,
    price_alert_last_triggered_price REAL,
    position_size_grams REAL NOT NULL DEFAULT 0,
    position_state_version INTEGER NOT NULL DEFAULT 0,
    batches_used INTEGER NOT NULL DEFAULT 0,
    entries_today_count INTEGER NOT NULL DEFAULT 0,
    trading_day TEXT,
    consecutive_loss_trades INTEGER NOT NULL DEFAULT 0,
    daily_realized_pnl_yuan REAL NOT NULL DEFAULT 0,
    consecutive_fetch_failures INTEGER NOT NULL DEFAULT 0,
    fetch_alert_active INTEGER NOT NULL DEFAULT 0,
    last_fetch_success_time TEXT,
    entry_price REAL,
    entry_time TEXT,
    entry_bar_time TEXT,
    position_notional_yuan REAL NOT NULL DEFAULT 0,
    initial_stop_price REAL,
    current_stop_loss REAL,
    stop_source TEXT,
    trade_idea_id TEXT,
    strategy_mode TEXT,
    regime_at_entry TEXT,
    last_sync_source TEXT,
    last_sync_at TEXT,
    note TEXT,
    trailing_active INTEGER NOT NULL,
    h_star REAL,
    cooldown_end_time TEXT,
    last_exit_time TEXT,
    last_exit_reason TEXT,
    post_exit_12bar_high REAL,
    last_effective_5m_bar_end TEXT,
    pending_entry_signal_time TEXT,
    pending_entry_deadline TEXT,
    pending_entry_reference_bar_time TEXT,
    pending_entry_atr REAL,
    pending_entry_stop_price REAL,
    pending_entry_reason TEXT,
    last_decision_time TEXT,
    last_email_sent_at TEXT,
    last_email_event_key TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_time TEXT NOT NULL,
    event_type TEXT NOT NULL,
    phase_before TEXT,
    phase_after TEXT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    level TEXT NOT NULL,
    event_key TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS minute_prices (
    observed_at TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    price REAL NOT NULL,
    source TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bars_5m (
    start_at TEXT PRIMARY KEY,
    end_at TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL,
    source TEXT NOT NULL,
    is_complete INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    success INTEGER NOT NULL,
    simulated_send INTEGER NOT NULL DEFAULT 0,
    dedupe_key TEXT,
    decision_action TEXT,
    strategy_mode TEXT,
    error_message TEXT,
    sent_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decided_at TEXT NOT NULL,
    action TEXT NOT NULL,
    strategy_mode TEXT NOT NULL,
    regime TEXT NOT NULL,
    confidence REAL NOT NULL,
    should_send_email INTEGER NOT NULL,
    dedupe_key TEXT,
    payload_json TEXT NOT NULL
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_events_event_time ON events(event_time);
CREATE INDEX IF NOT EXISTS idx_events_event_type_event_time ON events(event_type, event_time);
CREATE INDEX IF NOT EXISTS idx_minute_prices_observed_at ON minute_prices(observed_at);
CREATE INDEX IF NOT EXISTS idx_minute_prices_symbol_observed_at ON minute_prices(symbol, observed_at);
CREATE INDEX IF NOT EXISTS idx_bars_5m_start_is_complete ON bars_5m(start_at, is_complete);
CREATE INDEX IF NOT EXISTS idx_bars_5m_end_at ON bars_5m(end_at);
CREATE INDEX IF NOT EXISTS idx_notifications_sent_at ON notifications(sent_at);
CREATE INDEX IF NOT EXISTS idx_notifications_dedupe_key_sent_at ON notifications(dedupe_key, sent_at);
CREATE INDEX IF NOT EXISTS idx_decisions_decided_at ON decisions(decided_at);
CREATE INDEX IF NOT EXISTS idx_decisions_action_decided_at ON decisions(action, decided_at);
"""


class StateStore(ABC):
    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_runtime_state(self) -> StrategyRuntimeState:
        raise NotImplementedError

    @abstractmethod
    def save_runtime_state(self, state: StrategyRuntimeState) -> None:
        raise NotImplementedError

    @abstractmethod
    def append_event(self, event: StrategyEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def append_minute_price(self, tick: PriceTick) -> None:
        raise NotImplementedError

    @abstractmethod
    def append_bar(self, bar: Bar) -> None:
        raise NotImplementedError

    @abstractmethod
    def append_notification(self, record: NotificationRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def append_decision(self, decision: DecisionOutput) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_latest_minute_price(self) -> PriceTick | None:
        raise NotImplementedError

    @abstractmethod
    def load_recent_completed_bars(self, limit: int = 100) -> list[Bar]:
        raise NotImplementedError

    @abstractmethod
    def load_recent_minute_prices(self, limit: int = 100) -> list[PriceTick]:
        raise NotImplementedError

    @abstractmethod
    def load_bars_after(self, time: datetime) -> list[Bar]:
        raise NotImplementedError

    @abstractmethod
    def load_post_exit_completed_bars(self, exit_time: datetime, limit: int = 12) -> list[Bar]:
        raise NotImplementedError

    @abstractmethod
    def load_recent_events(self, limit: int = 20) -> list[StrategyEvent]:
        raise NotImplementedError

    @abstractmethod
    def load_recent_notifications(self, limit: int = 20) -> list[NotificationRecord]:
        raise NotImplementedError

    @abstractmethod
    def load_recent_decisions(self, limit: int = 20) -> list[DecisionOutput]:
        raise NotImplementedError

    @abstractmethod
    def has_recent_notification_dedupe(self, dedupe_key: str, *, since: datetime) -> bool:
        raise NotImplementedError

    @abstractmethod
    def load_decision_by_id(self, decision_id: int) -> DecisionOutput | None:
        raise NotImplementedError


class SQLiteStateStore(StateStore):
    """SQLite-based persistence with centralized schema and read/write helpers."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
            self._ensure_runtime_state_columns(conn)
            self._ensure_notifications_columns(conn)
            self._ensure_decisions_columns(conn)
            conn.executescript(INDEX_SQL)
            conn.commit()

    def load_runtime_state(self) -> StrategyRuntimeState:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM runtime_state WHERE id = 1").fetchone()
        if row is None:
            return StrategyRuntimeState()
        return self._deserialize_runtime_state(dict(row))

    def save_runtime_state(self, state: StrategyRuntimeState) -> None:
        payload = self._serialize_runtime_state(state)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runtime_state (
                    id, phase, has_position, execution_mode, profile_name, paused_new_entries, force_flatten_requested,
                    price_alert_enabled, price_alert_target_price, price_alert_trigger_when_below,
                    price_alert_active_below_triggered, price_alert_last_triggered_at, price_alert_last_triggered_price,
                    position_size_grams, position_state_version, batches_used, entries_today_count, trading_day, consecutive_loss_trades, daily_realized_pnl_yuan,
                    consecutive_fetch_failures, fetch_alert_active, last_fetch_success_time,
                    entry_price, entry_time, entry_bar_time, position_notional_yuan, initial_stop_price, current_stop_loss,
                    stop_source, trade_idea_id, strategy_mode, regime_at_entry, last_sync_source, last_sync_at, note, trailing_active, h_star, cooldown_end_time, last_exit_time,
                    last_exit_reason, post_exit_12bar_high, last_effective_5m_bar_end,
                    pending_entry_signal_time, pending_entry_deadline, pending_entry_reference_bar_time,
                    pending_entry_atr, pending_entry_stop_price, pending_entry_reason, last_decision_time,
                    last_email_sent_at, last_email_event_key, updated_at
                ) VALUES (
                    1, :phase, :has_position, :execution_mode, :profile_name, :paused_new_entries, :force_flatten_requested,
                    :price_alert_enabled, :price_alert_target_price, :price_alert_trigger_when_below,
                    :price_alert_active_below_triggered, :price_alert_last_triggered_at, :price_alert_last_triggered_price,
                    :position_size_grams, :position_state_version, :batches_used, :entries_today_count, :trading_day, :consecutive_loss_trades, :daily_realized_pnl_yuan,
                    :consecutive_fetch_failures, :fetch_alert_active, :last_fetch_success_time,
                    :entry_price, :entry_time, :entry_bar_time, :position_notional_yuan, :initial_stop_price, :current_stop_loss,
                    :stop_source, :trade_idea_id, :strategy_mode, :regime_at_entry, :last_sync_source, :last_sync_at, :note, :trailing_active, :h_star, :cooldown_end_time, :last_exit_time,
                    :last_exit_reason, :post_exit_12bar_high, :last_effective_5m_bar_end,
                    :pending_entry_signal_time, :pending_entry_deadline, :pending_entry_reference_bar_time,
                    :pending_entry_atr, :pending_entry_stop_price, :pending_entry_reason, :last_decision_time,
                    :last_email_sent_at, :last_email_event_key, :updated_at
                )
                ON CONFLICT(id) DO UPDATE SET
                    phase = excluded.phase,
                    has_position = excluded.has_position,
                    execution_mode = excluded.execution_mode,
                    profile_name = excluded.profile_name,
                    paused_new_entries = excluded.paused_new_entries,
                    force_flatten_requested = excluded.force_flatten_requested,
                    price_alert_enabled = excluded.price_alert_enabled,
                    price_alert_target_price = excluded.price_alert_target_price,
                    price_alert_trigger_when_below = excluded.price_alert_trigger_when_below,
                    price_alert_active_below_triggered = excluded.price_alert_active_below_triggered,
                    price_alert_last_triggered_at = excluded.price_alert_last_triggered_at,
                    price_alert_last_triggered_price = excluded.price_alert_last_triggered_price,
                    position_size_grams = excluded.position_size_grams,
                    position_state_version = excluded.position_state_version,
                    batches_used = excluded.batches_used,
                    entries_today_count = excluded.entries_today_count,
                    trading_day = excluded.trading_day,
                    consecutive_loss_trades = excluded.consecutive_loss_trades,
                    daily_realized_pnl_yuan = excluded.daily_realized_pnl_yuan,
                    consecutive_fetch_failures = excluded.consecutive_fetch_failures,
                    fetch_alert_active = excluded.fetch_alert_active,
                    last_fetch_success_time = excluded.last_fetch_success_time,
                    entry_price = excluded.entry_price,
                    entry_time = excluded.entry_time,
                    entry_bar_time = excluded.entry_bar_time,
                    position_notional_yuan = excluded.position_notional_yuan,
                    initial_stop_price = excluded.initial_stop_price,
                    current_stop_loss = excluded.current_stop_loss,
                    stop_source = excluded.stop_source,
                    trade_idea_id = excluded.trade_idea_id,
                    strategy_mode = excluded.strategy_mode,
                    regime_at_entry = excluded.regime_at_entry,
                    last_sync_source = excluded.last_sync_source,
                    last_sync_at = excluded.last_sync_at,
                    note = excluded.note,
                    trailing_active = excluded.trailing_active,
                    h_star = excluded.h_star,
                    cooldown_end_time = excluded.cooldown_end_time,
                    last_exit_time = excluded.last_exit_time,
                    last_exit_reason = excluded.last_exit_reason,
                    post_exit_12bar_high = excluded.post_exit_12bar_high,
                    last_effective_5m_bar_end = excluded.last_effective_5m_bar_end,
                    pending_entry_signal_time = excluded.pending_entry_signal_time,
                    pending_entry_deadline = excluded.pending_entry_deadline,
                    pending_entry_reference_bar_time = excluded.pending_entry_reference_bar_time,
                    pending_entry_atr = excluded.pending_entry_atr,
                    pending_entry_stop_price = excluded.pending_entry_stop_price,
                    pending_entry_reason = excluded.pending_entry_reason,
                    last_decision_time = excluded.last_decision_time,
                    last_email_sent_at = excluded.last_email_sent_at,
                    last_email_event_key = excluded.last_email_event_key,
                    updated_at = excluded.updated_at
                """,
                payload,
            )
            conn.commit()

    def append_event(self, event: StrategyEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (
                    event_time, event_type, phase_before, phase_after, title, message, level, event_key, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_time.isoformat(),
                    event.event_type.value,
                    event.phase_before.value if event.phase_before else None,
                    event.phase_after.value if event.phase_after else None,
                    event.title,
                    event.message,
                    event.level,
                    event.event_key,
                    json.dumps(event.metadata, ensure_ascii=False),
                ),
            )
            conn.commit()

    def append_minute_price(self, tick: PriceTick) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO minute_prices (observed_at, symbol, price, source, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    tick.observed_at.isoformat(),
                    tick.symbol,
                    tick.price,
                    tick.source,
                    json.dumps(tick.metadata, ensure_ascii=False),
                ),
            )
            conn.commit()

    def append_bar(self, bar: Bar) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO bars_5m
                (start_at, end_at, open, high, low, close, volume, source, is_complete)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bar.start_at.isoformat(),
                    bar.end_at.isoformat(),
                    bar.open,
                    bar.high,
                    bar.low,
                    bar.close,
                    bar.volume,
                    bar.source,
                    int(bar.is_complete),
                ),
            )
            conn.commit()

    def append_notification(self, record: NotificationRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO notifications (
                    title, notification_type, success, simulated_send,
                    dedupe_key, decision_action, strategy_mode, error_message, sent_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.title,
                    record.notification_type,
                    int(record.success),
                    int(record.simulated_send),
                    record.dedupe_key,
                    record.decision_action,
                    record.strategy_mode,
                    record.error_message,
                    record.sent_at.isoformat(),
                ),
            )
            conn.commit()

    def append_decision(self, decision: DecisionOutput) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO decisions (
                    decided_at, action, strategy_mode, regime, confidence, should_send_email, dedupe_key, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.timestamp.isoformat(),
                    decision.action.value,
                    decision.strategy_mode.value,
                    decision.regime.value,
                    decision.confidence,
                    int(decision.whether_send_email),
                    decision.dedupe_key,
                    json.dumps(decision.as_json_dict(), ensure_ascii=False),
                ),
            )
            conn.commit()

    def load_latest_minute_price(self) -> PriceTick | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM minute_prices
                ORDER BY observed_at DESC
                LIMIT 1
                """
            ).fetchone()
        return self._deserialize_tick(dict(row)) if row else None

    def load_recent_completed_bars(self, limit: int = 100) -> list[Bar]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM bars_5m
                WHERE is_complete = 1
                ORDER BY start_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._deserialize_bar(dict(row)) for row in reversed(rows)]

    def load_recent_minute_prices(self, limit: int = 100) -> list[PriceTick]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM minute_prices
                ORDER BY observed_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._deserialize_tick(dict(row)) for row in reversed(rows)]

    def load_bars_after(self, time: datetime) -> list[Bar]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM bars_5m
                WHERE start_at > ?
                ORDER BY start_at ASC
                """,
                (time.isoformat(),),
            ).fetchall()
        return [self._deserialize_bar(dict(row)) for row in rows]

    def load_post_exit_completed_bars(self, exit_time: datetime, limit: int = 12) -> list[Bar]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM bars_5m
                WHERE is_complete = 1 AND start_at > ?
                ORDER BY start_at ASC
                LIMIT ?
                """,
                (exit_time.isoformat(), limit),
            ).fetchall()
        return [self._deserialize_bar(dict(row)) for row in rows]

    def load_recent_events(self, limit: int = 20) -> list[StrategyEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM events
                ORDER BY event_time DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._deserialize_event(dict(row)) for row in rows]

    def load_recent_notifications(self, limit: int = 20) -> list[NotificationRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM notifications
                ORDER BY sent_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._deserialize_notification(dict(row)) for row in rows]

    def load_recent_decisions(self, limit: int = 20) -> list[DecisionOutput]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT payload_json FROM decisions
                ORDER BY decided_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._deserialize_decision(json.loads(row["payload_json"])) for row in rows]

    def has_recent_notification_dedupe(self, dedupe_key: str, *, since: datetime) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT 1 FROM notifications
                WHERE dedupe_key = ? AND sent_at >= ?
                LIMIT 1
                """,
                (dedupe_key, since.isoformat()),
            ).fetchone()
        return row is not None

    def load_decision_by_id(self, decision_id: int) -> DecisionOutput | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT payload_json FROM decisions
                WHERE id = ?
                LIMIT 1
                """,
                (decision_id,),
            ).fetchone()
        if row is None:
            return None
        return self._deserialize_decision(json.loads(row["payload_json"]))

    def _serialize_runtime_state(self, state: StrategyRuntimeState) -> dict[str, Any]:
        return {
            "phase": state.phase.value,
            "has_position": int(state.position.has_position),
            "execution_mode": state.execution_mode.value,
            "profile_name": state.profile_name.value,
            "paused_new_entries": int(state.paused_new_entries),
            "force_flatten_requested": int(state.force_flatten_requested),
            "price_alert_enabled": int(state.price_alert.enabled),
            "price_alert_target_price": state.price_alert.target_price,
            "price_alert_trigger_when_below": int(state.price_alert.trigger_when_below),
            "price_alert_active_below_triggered": int(state.price_alert.active_below_triggered),
            "price_alert_last_triggered_at": self._to_iso(state.price_alert.last_triggered_at),
            "price_alert_last_triggered_price": state.price_alert.last_triggered_price,
            "position_size_grams": state.position.size_grams,
            "position_state_version": state.position_state_version,
            "batches_used": state.batches_used,
            "entries_today_count": state.entries_today_count,
            "trading_day": state.trading_day,
            "consecutive_loss_trades": state.consecutive_loss_trades,
            "daily_realized_pnl_yuan": state.daily_realized_pnl_yuan,
            "consecutive_fetch_failures": state.consecutive_fetch_failures,
            "fetch_alert_active": int(state.fetch_alert_active),
            "last_fetch_success_time": self._to_iso(state.last_fetch_success_time),
            "entry_price": state.position.entry_price,
            "entry_time": self._to_iso(state.position.entry_time),
            "entry_bar_time": self._to_iso(state.position.entry_bar_time),
            "position_notional_yuan": state.position.position_notional_yuan,
            "initial_stop_price": state.position.initial_stop_price,
            "current_stop_loss": state.position.current_stop_loss,
            "stop_source": state.position.stop_source,
            "trade_idea_id": state.position.trade_idea_id,
            "strategy_mode": state.position.strategy_mode.value,
            "regime_at_entry": state.position.regime_at_entry.value,
            "last_sync_source": state.position.last_sync_source,
            "last_sync_at": self._to_iso(state.position.last_sync_at),
            "note": state.position.note,
            "trailing_active": int(state.position.trailing_active),
            "h_star": state.position.h_star,
            "cooldown_end_time": self._to_iso(state.cooldown_end_time),
            "last_exit_time": self._to_iso(state.last_exit_time),
            "last_exit_reason": state.last_exit_reason.value if state.last_exit_reason else None,
            "post_exit_12bar_high": state.post_exit_12bar_high,
            "last_effective_5m_bar_end": self._to_iso(state.last_effective_5m_bar_end),
            "pending_entry_signal_time": self._to_iso(state.pending_entry_signal_time),
            "pending_entry_deadline": self._to_iso(state.pending_entry_deadline),
            "pending_entry_reference_bar_time": self._to_iso(state.pending_entry_reference_bar_time),
            "pending_entry_atr": state.pending_entry_atr,
            "pending_entry_stop_price": state.pending_entry_stop_price,
            "pending_entry_reason": state.pending_entry_reason,
            "last_decision_time": self._to_iso(state.last_decision_time),
            "last_email_sent_at": self._to_iso(state.last_email_sent_at),
            "last_email_event_key": state.last_email_event_key,
            "updated_at": datetime.now().isoformat(),
        }

    def _deserialize_runtime_state(self, raw: dict[str, Any]) -> StrategyRuntimeState:
        phase_value = raw["phase"]
        if phase_value == StrategyPhase.WAITING_FOR_ENTRY_FILL.value:
            phase_value = StrategyPhase.HOLDING.value if raw["has_position"] else StrategyPhase.OBSERVING.value
        return StrategyRuntimeState(
            phase=StrategyPhase(phase_value),
            position=PositionState(
                has_position=bool(raw["has_position"]),
                size_grams=float(raw.get("position_size_grams", 0.0) or 0.0),
                entry_price=raw["entry_price"],
                entry_time=self._parse_dt(raw["entry_time"]),
                entry_bar_time=self._parse_dt(raw.get("entry_bar_time")),
                position_notional_yuan=float(raw.get("position_notional_yuan", 0.0) or 0.0),
                initial_stop_price=raw.get("initial_stop_price"),
                current_stop_loss=raw["current_stop_loss"],
                stop_source=raw.get("stop_source"),
                trade_idea_id=raw.get("trade_idea_id"),
                strategy_mode=StrategyMode(raw.get("strategy_mode") or StrategyMode.NONE.value),
                regime_at_entry=MarketRegime(raw.get("regime_at_entry") or MarketRegime.NOISE.value),
                last_sync_source=raw.get("last_sync_source"),
                last_sync_at=self._parse_dt(raw.get("last_sync_at")),
                note=raw.get("note"),
                trailing_active=bool(raw["trailing_active"]),
                h_star=raw["h_star"],
            ),
            price_alert=PriceAlertState(
                enabled=bool(raw.get("price_alert_enabled", 0)),
                target_price=raw.get("price_alert_target_price"),
                trigger_when_below=bool(raw.get("price_alert_trigger_when_below", 1)),
                active_below_triggered=bool(raw.get("price_alert_active_below_triggered", 0)),
                last_triggered_at=self._parse_dt(raw.get("price_alert_last_triggered_at")),
                last_triggered_price=raw.get("price_alert_last_triggered_price"),
            ),
            execution_mode=ExecutionMode(raw.get("execution_mode") or ExecutionMode.MANUAL_POSITION_SYNC.value),
            profile_name=ProfileName(raw.get("profile_name") or ProfileName.CONSERVATIVE.value),
            paused_new_entries=bool(raw.get("paused_new_entries", 0)),
            force_flatten_requested=bool(raw.get("force_flatten_requested", 0)),
            position_state_version=int(raw.get("position_state_version", 0) or 0),
            batches_used=int(raw.get("batches_used", 0) or 0),
            entries_today_count=int(raw.get("entries_today_count", 0) or 0),
            trading_day=raw.get("trading_day"),
            consecutive_loss_trades=int(raw.get("consecutive_loss_trades", 0) or 0),
            daily_realized_pnl_yuan=float(raw.get("daily_realized_pnl_yuan", 0.0) or 0.0),
            consecutive_fetch_failures=int(raw.get("consecutive_fetch_failures", 0) or 0),
            fetch_alert_active=bool(raw.get("fetch_alert_active", 0)),
            last_fetch_success_time=self._parse_dt(raw.get("last_fetch_success_time")),
            last_exit_time=self._parse_dt(raw["last_exit_time"]),
            last_exit_reason=ExitReason(raw["last_exit_reason"]) if raw["last_exit_reason"] else None,
            cooldown_end_time=self._parse_dt(raw["cooldown_end_time"]),
            post_exit_12bar_high=raw["post_exit_12bar_high"],
            last_effective_5m_bar_end=self._parse_dt(raw["last_effective_5m_bar_end"]),
            pending_entry_signal_time=self._parse_dt(raw["pending_entry_signal_time"]),
            pending_entry_deadline=self._parse_dt(raw["pending_entry_deadline"]),
            pending_entry_reference_bar_time=self._parse_dt(raw["pending_entry_reference_bar_time"]),
            pending_entry_atr=raw["pending_entry_atr"],
            pending_entry_stop_price=raw.get("pending_entry_stop_price"),
            pending_entry_reason=raw["pending_entry_reason"],
            last_decision_time=self._parse_dt(raw["last_decision_time"]),
            last_email_sent_at=self._parse_dt(raw["last_email_sent_at"]),
            last_email_event_key=raw["last_email_event_key"],
        )

    def _deserialize_bar(self, raw: dict[str, Any]) -> Bar:
        return Bar(
            start_at=self._parse_dt(raw["start_at"]) or datetime.min,
            end_at=self._parse_dt(raw["end_at"]) or datetime.min,
            open=raw["open"],
            high=raw["high"],
            low=raw["low"],
            close=raw["close"],
            volume=raw["volume"],
            source=raw["source"],
            is_complete=bool(raw["is_complete"]),
        )

    def _deserialize_tick(self, raw: dict[str, Any]) -> PriceTick:
        return PriceTick(
            symbol=raw["symbol"],
            price=raw["price"],
            observed_at=self._parse_dt(raw["observed_at"]) or datetime.min,
            source=raw["source"],
            metadata=json.loads(raw["metadata_json"]) if raw["metadata_json"] else {},
        )

    def _deserialize_event(self, raw: dict[str, Any]) -> StrategyEvent:
        phase_before = StrategyPhase(raw["phase_before"]) if raw.get("phase_before") else None
        phase_after = StrategyPhase(raw["phase_after"]) if raw.get("phase_after") else None
        try:
            event_type = EventType(raw["event_type"])
        except ValueError:
            event_type = EventType.ERROR
        return StrategyEvent(
            event_type=event_type,
            event_time=self._parse_dt(raw["event_time"]) or datetime.min,
            phase_before=phase_before,
            phase_after=phase_after,
            title=raw["title"],
            message=raw["message"],
            level=raw["level"],
            event_key=raw["event_key"],
            metadata=json.loads(raw["payload_json"]) if raw["payload_json"] else {},
        )

    def _deserialize_notification(self, raw: dict[str, Any]) -> NotificationRecord:
        return NotificationRecord(
            title=raw["title"],
            notification_type=raw["notification_type"],
            success=bool(raw["success"]),
            simulated_send=bool(raw.get("simulated_send", 0)),
            dedupe_key=raw.get("dedupe_key"),
            decision_action=raw.get("decision_action"),
            strategy_mode=raw.get("strategy_mode"),
            error_message=raw["error_message"],
            sent_at=self._parse_dt(raw["sent_at"]) or datetime.min,
        )

    def _deserialize_decision(self, raw: dict[str, Any]) -> DecisionOutput:
        from models import ActionType, FeeBreakdown, MarketRegime, StrategyMode

        fees = raw.get("fees_considered", {})
        return DecisionOutput(
            action=ActionType(raw["action"]),
            strategy_mode=StrategyMode(raw["strategy_mode"]),
            confidence=float(raw["confidence"]),
            regime=MarketRegime(raw["regime"]),
            entry_reason=raw.get("entry_reason", ""),
            invalidation_reason=raw.get("invalidation_reason", ""),
            stop_rule=raw.get("stop_rule", ""),
            take_profit_rule=raw.get("take_profit_rule", ""),
            position_size_yuan=float(raw.get("position_size_yuan", 0.0)),
            fees_considered=FeeBreakdown(
                buy_fee_rate=float(fees.get("buy_fee_rate", 0.0)),
                sell_fee_rate=float(fees.get("sell_fee_rate", 0.0)),
                round_trip_fee_floor_yuan=float(fees.get("round_trip_fee_floor_yuan", 0.0)),
            ),
            whether_send_email=bool(raw.get("whether_send_email", False)),
            short_email_subject=raw.get("short_email_subject", ""),
            short_email_body=raw.get("short_email_body", ""),
            timestamp=self._parse_dt(raw.get("timestamp")) or datetime.min,
            execution_mode=raw.get("execution_mode"),
            profile_name=raw.get("profile_name"),
            has_position=bool(raw.get("has_position", False)),
            position_size_grams=float(raw.get("position_size_grams", 0.0) or 0.0),
            avg_entry_price=raw.get("avg_entry_price"),
            unrealized_pnl_yuan=raw.get("unrealized_pnl_yuan"),
            paused_new_entries=bool(raw.get("paused_new_entries", False)),
            cooldown_status=raw.get("cooldown_status"),
            operator_hint=raw.get("operator_hint"),
            dedupe_key=raw.get("dedupe_key"),
            metadata=raw.get("metadata", {}),
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _ensure_runtime_state_columns(conn: sqlite3.Connection) -> None:
        rows = conn.execute("PRAGMA table_info(runtime_state)").fetchall()
        existing = {row[1] for row in rows}
        migrations = {
            "position_size_grams": "ALTER TABLE runtime_state ADD COLUMN position_size_grams REAL NOT NULL DEFAULT 0",
            "execution_mode": "ALTER TABLE runtime_state ADD COLUMN execution_mode TEXT NOT NULL DEFAULT 'manual_position_sync'",
            "profile_name": "ALTER TABLE runtime_state ADD COLUMN profile_name TEXT NOT NULL DEFAULT 'conservative'",
            "paused_new_entries": "ALTER TABLE runtime_state ADD COLUMN paused_new_entries INTEGER NOT NULL DEFAULT 0",
            "force_flatten_requested": "ALTER TABLE runtime_state ADD COLUMN force_flatten_requested INTEGER NOT NULL DEFAULT 0",
            "price_alert_enabled": "ALTER TABLE runtime_state ADD COLUMN price_alert_enabled INTEGER NOT NULL DEFAULT 0",
            "price_alert_target_price": "ALTER TABLE runtime_state ADD COLUMN price_alert_target_price REAL",
            "price_alert_trigger_when_below": "ALTER TABLE runtime_state ADD COLUMN price_alert_trigger_when_below INTEGER NOT NULL DEFAULT 1",
            "price_alert_active_below_triggered": "ALTER TABLE runtime_state ADD COLUMN price_alert_active_below_triggered INTEGER NOT NULL DEFAULT 0",
            "price_alert_last_triggered_at": "ALTER TABLE runtime_state ADD COLUMN price_alert_last_triggered_at TEXT",
            "price_alert_last_triggered_price": "ALTER TABLE runtime_state ADD COLUMN price_alert_last_triggered_price REAL",
            "position_state_version": "ALTER TABLE runtime_state ADD COLUMN position_state_version INTEGER NOT NULL DEFAULT 0",
            "batches_used": "ALTER TABLE runtime_state ADD COLUMN batches_used INTEGER NOT NULL DEFAULT 0",
            "entries_today_count": "ALTER TABLE runtime_state ADD COLUMN entries_today_count INTEGER NOT NULL DEFAULT 0",
            "trading_day": "ALTER TABLE runtime_state ADD COLUMN trading_day TEXT",
            "consecutive_loss_trades": "ALTER TABLE runtime_state ADD COLUMN consecutive_loss_trades INTEGER NOT NULL DEFAULT 0",
            "daily_realized_pnl_yuan": "ALTER TABLE runtime_state ADD COLUMN daily_realized_pnl_yuan REAL NOT NULL DEFAULT 0",
            "consecutive_fetch_failures": "ALTER TABLE runtime_state ADD COLUMN consecutive_fetch_failures INTEGER NOT NULL DEFAULT 0",
            "fetch_alert_active": "ALTER TABLE runtime_state ADD COLUMN fetch_alert_active INTEGER NOT NULL DEFAULT 0",
            "last_fetch_success_time": "ALTER TABLE runtime_state ADD COLUMN last_fetch_success_time TEXT",
            "entry_bar_time": "ALTER TABLE runtime_state ADD COLUMN entry_bar_time TEXT",
            "position_notional_yuan": "ALTER TABLE runtime_state ADD COLUMN position_notional_yuan REAL NOT NULL DEFAULT 0",
            "initial_stop_price": "ALTER TABLE runtime_state ADD COLUMN initial_stop_price REAL",
            "stop_source": "ALTER TABLE runtime_state ADD COLUMN stop_source TEXT",
            "trade_idea_id": "ALTER TABLE runtime_state ADD COLUMN trade_idea_id TEXT",
            "strategy_mode": "ALTER TABLE runtime_state ADD COLUMN strategy_mode TEXT",
            "regime_at_entry": "ALTER TABLE runtime_state ADD COLUMN regime_at_entry TEXT",
            "last_sync_source": "ALTER TABLE runtime_state ADD COLUMN last_sync_source TEXT",
            "last_sync_at": "ALTER TABLE runtime_state ADD COLUMN last_sync_at TEXT",
            "note": "ALTER TABLE runtime_state ADD COLUMN note TEXT",
            "pending_entry_stop_price": "ALTER TABLE runtime_state ADD COLUMN pending_entry_stop_price REAL",
        }
        for column_name, statement in migrations.items():
            if column_name not in existing:
                conn.execute(statement)

    @staticmethod
    def _ensure_notifications_columns(conn: sqlite3.Connection) -> None:
        rows = conn.execute("PRAGMA table_info(notifications)").fetchall()
        existing = {row[1] for row in rows}
        migrations = {
            "dedupe_key": "ALTER TABLE notifications ADD COLUMN dedupe_key TEXT",
            "decision_action": "ALTER TABLE notifications ADD COLUMN decision_action TEXT",
            "strategy_mode": "ALTER TABLE notifications ADD COLUMN strategy_mode TEXT",
        }
        for column_name, statement in migrations.items():
            if column_name not in existing:
                conn.execute(statement)

    @staticmethod
    def _ensure_decisions_columns(conn: sqlite3.Connection) -> None:
        rows = conn.execute("PRAGMA table_info(decisions)").fetchall()
        existing = {row[1] for row in rows}
        migrations = {
            "dedupe_key": "ALTER TABLE decisions ADD COLUMN dedupe_key TEXT",
        }
        for column_name, statement in migrations.items():
            if column_name not in existing:
                conn.execute(statement)

    @staticmethod
    def _to_iso(value: datetime | None) -> str | None:
        return value.isoformat() if value else None

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value) if value else None
