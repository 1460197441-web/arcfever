"""Local web control panel and JSON API."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import socket
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

from config import AppConfig, apply_profile, get_profile_presets
from indicators import compute_indicator_snapshot
from models import (
    EventType,
    ExecutionMode,
    NotificationRecord,
    PositionState,
    ProfileName,
    StrategyEvent,
    StrategyPhase,
    StrategyRuntimeState,
)
from state_store import SQLiteStateStore


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ControlDashboardStatus:
    generated_at: datetime
    runtime_state: StrategyRuntimeState
    latest_tick_price: float | None
    latest_tick_time: datetime | None
    latest_tick_source: str | None
    indicator_summary: dict[str, Any]
    latest_completed_bar_time: datetime | None
    latest_decision: dict[str, Any] | None
    flash_message: str | None = None
    recent_events: list[StrategyEvent] = field(default_factory=list)
    recent_notifications: list[NotificationRecord] = field(default_factory=list)


@dataclass(slots=True)
class ControlCommandResult:
    ok: bool
    message: str
    runtime_state: StrategyRuntimeState


@dataclass(slots=True)
class ControlServerHandle:
    host: str
    port: int
    access_token: str
    thread: Thread
    server: ThreadingHTTPServer

    @property
    def base_url(self) -> str:
        host = self.host if self.host not in {"0.0.0.0", ""} else _detect_lan_ip()
        return f"http://{host}:{self.port}/app?token={self.access_token}"


class ControlCommandService:
    def __init__(self, config: AppConfig, store: SQLiteStateStore) -> None:
        self.config = config
        self.store = store

    def build_status(self) -> ControlDashboardStatus:
        state = self.store.load_runtime_state()
        latest_tick = self.store.load_latest_minute_price()
        completed_bars = self.store.load_recent_completed_bars(limit=120)
        indicator = compute_indicator_snapshot(
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
        recent_decisions = self.store.load_recent_decisions(limit=1)
        latest_bar = completed_bars[-1] if completed_bars else None
        return ControlDashboardStatus(
            generated_at=datetime.now(),
            runtime_state=state,
            latest_tick_price=latest_tick.price if latest_tick else None,
            latest_tick_time=latest_tick.observed_at if latest_tick else None,
            latest_tick_source=latest_tick.source if latest_tick else None,
            indicator_summary={
                "indicator_ready": indicator.is_ready,
                "ema_fast": indicator.ema_fast,
                "ema_slow": indicator.ema_slow,
                "atr": indicator.atr,
                "allow_long": indicator.allow_long,
                "regime_hint": recent_decisions[0].regime.value if recent_decisions else None,
                "bar_time": indicator.bar_time.isoformat() if indicator.bar_time else None,
            },
            latest_completed_bar_time=latest_bar.end_at if latest_bar else None,
            latest_decision=recent_decisions[0].as_json_dict() if recent_decisions else None,
            recent_events=self.store.load_recent_events(limit=self.config.control.recent_events_limit),
            recent_notifications=self.store.load_recent_notifications(limit=10),
        )

    def current_position_payload(self) -> dict[str, Any]:
        state = self.store.load_runtime_state()
        latest_tick = self.store.load_latest_minute_price()
        unrealized = None
        holding_minutes = None
        if (
            state.position.has_position
            and state.position.entry_price is not None
            and latest_tick is not None
            and state.position.size_grams > 0
        ):
            unrealized = (
                (latest_tick.price - state.position.entry_price) * state.position.size_grams
                - (state.position.entry_price * state.position.size_grams * self.config.fees.buy_fee_rate)
                - (latest_tick.price * state.position.size_grams * self.config.fees.sell_fee_rate)
            )
        if state.position.entry_time is not None:
            holding_minutes = max(
                0.0,
                (datetime.now() - state.position.entry_time).total_seconds() / 60.0,
            )
        return {
            "has_position": state.position.has_position,
            "position_size_grams": state.position.size_grams,
            "avg_entry_price": state.position.entry_price,
            "entry_time": state.position.entry_time.isoformat() if state.position.entry_time else None,
            "position_notional_yuan": state.position.position_notional_yuan,
            "effective_stop_price": state.position.current_stop_loss,
            "unrealized_pnl_yuan": unrealized,
            "holding_minutes": holding_minutes,
            "last_sync_at": state.position.last_sync_at.isoformat() if state.position.last_sync_at else None,
            "last_sync_source": state.position.last_sync_source,
            "note": state.position.note,
        }

    def current_price_alert_payload(self) -> dict[str, Any]:
        state = self.store.load_runtime_state()
        return {
            "enabled": state.price_alert.enabled,
            "target_price": state.price_alert.target_price,
            "trigger_when_below": state.price_alert.trigger_when_below,
            "active_below_triggered": state.price_alert.active_below_triggered,
            "last_triggered_at": (
                state.price_alert.last_triggered_at.isoformat() if state.price_alert.last_triggered_at else None
            ),
            "last_triggered_price": state.price_alert.last_triggered_price,
        }

    def sync_position(
        self,
        *,
        has_position: bool,
        position_size_grams: float = 0.0,
        avg_entry_price: float | None = None,
        entry_time: datetime | None = None,
        note: str | None = None,
        sync_source: str = "api_sync",
    ) -> ControlCommandResult:
        state = self.store.load_runtime_state()
        next_state = deepcopy(state)
        now = datetime.now()
        if not has_position:
            next_state.phase = StrategyPhase.OBSERVING
            next_state.position = PositionState()
            next_state.force_flatten_requested = False
            next_state.position_state_version += 1
            self.store.save_runtime_state(next_state)
            self.store.append_event(
                StrategyEvent(
                    event_type=EventType.POSITION_CLEARED,
                    event_time=now,
                    phase_before=state.phase,
                    phase_after=next_state.phase,
                    title="Position cleared",
                    message="Actual position cleared by operator sync.",
                    event_key="position_cleared",
                    metadata={"sync_source": sync_source, "note": note},
                )
            )
            return ControlCommandResult(True, "Actual position cleared.", next_state)

        if avg_entry_price is None or avg_entry_price <= 0 or position_size_grams <= 0:
            return ControlCommandResult(False, "Valid position size and average price are required.", state)

        notional = position_size_grams * avg_entry_price
        next_state.phase = StrategyPhase.HOLDING
        next_state.position = PositionState(
            has_position=True,
            size_grams=position_size_grams,
            entry_price=avg_entry_price,
            entry_time=entry_time or now,
            entry_bar_time=state.position.entry_bar_time,
            position_notional_yuan=notional,
            initial_stop_price=state.position.initial_stop_price,
            current_stop_loss=state.position.current_stop_loss or state.position.initial_stop_price,
            stop_source=state.position.stop_source,
            trade_idea_id=state.position.trade_idea_id,
            strategy_mode=state.position.strategy_mode,
            regime_at_entry=state.position.regime_at_entry,
            trailing_active=state.position.trailing_active,
            h_star=state.position.h_star,
            last_sync_source=sync_source,
            last_sync_at=now,
            note=note,
        )
        next_state.position_state_version += 1
        self.store.save_runtime_state(next_state)
        self.store.append_event(
            StrategyEvent(
                event_type=EventType.POSITION_SYNCED,
                event_time=now,
                phase_before=state.phase,
                phase_after=next_state.phase,
                title="Position synced",
                message=f"Actual position synced to {position_size_grams:.2f}g @ {avg_entry_price:.2f}.",
                event_key="position_synced",
                metadata={
                    "position_size_grams": position_size_grams,
                    "avg_entry_price": avg_entry_price,
                    "sync_source": sync_source,
                    "note": note,
                },
            )
        )
        return ControlCommandResult(True, "Actual position synced.", next_state)

    def adjust_position(self, *, delta_grams: float, fill_price: float, note: str | None = None) -> ControlCommandResult:
        state = self.store.load_runtime_state()
        if fill_price <= 0 or delta_grams == 0:
            return ControlCommandResult(False, "delta_grams and fill_price must be valid.", state)

        current_size = state.position.size_grams if state.position.has_position else 0.0
        new_size = round(current_size + delta_grams, 8)
        if new_size < 0:
            return ControlCommandResult(False, "Position cannot go below zero.", state)

        now = datetime.now()
        if new_size == 0:
            return self.sync_position(
                has_position=False,
                note=note or "Position reduced to zero.",
                sync_source="api_adjust",
            )

        if not state.position.has_position or state.position.entry_price is None or current_size <= 0:
            return self.sync_position(
                has_position=True,
                position_size_grams=new_size,
                avg_entry_price=fill_price,
                entry_time=now,
                note=note or "Position created by adjustment.",
                sync_source="api_adjust",
            )

        if delta_grams > 0:
            avg_entry = ((state.position.entry_price * current_size) + (fill_price * delta_grams)) / new_size
        else:
            avg_entry = state.position.entry_price

        result = self.sync_position(
            has_position=True,
            position_size_grams=new_size,
            avg_entry_price=avg_entry,
            entry_time=state.position.entry_time or now,
            note=note or "Position adjusted.",
            sync_source="api_adjust",
        )
        if result.ok:
            self.store.append_event(
                StrategyEvent(
                    event_type=EventType.POSITION_ADJUSTED,
                    event_time=now,
                    phase_before=state.phase,
                    phase_after=result.runtime_state.phase,
                    title="Position adjusted",
                    message=f"Adjusted position by {delta_grams:.2f}g at {fill_price:.2f}.",
                    event_key="position_adjusted",
                    metadata={"delta_grams": delta_grams, "fill_price": fill_price, "note": note},
                )
            )
        return result

    def set_profile(self, profile_name: str) -> ControlCommandResult:
        if profile_name not in get_profile_presets():
            return ControlCommandResult(False, f"Unknown profile: {profile_name}", self.store.load_runtime_state())
        state = self.store.load_runtime_state()
        apply_profile(self.config, profile_name)
        next_state = deepcopy(state)
        next_state.profile_name = ProfileName(profile_name)
        self.store.save_runtime_state(next_state)
        self.store.append_event(
            StrategyEvent(
                event_type=EventType.PROFILE_CHANGED,
                event_time=datetime.now(),
                phase_before=state.phase,
                phase_after=next_state.phase,
                title="Profile changed",
                message=f"Runtime profile switched to {profile_name}.",
                event_key="profile_changed",
                metadata={"profile_name": profile_name},
            )
        )
        return ControlCommandResult(True, f"Profile switched to {profile_name}.", next_state)

    def set_execution_mode(self, execution_mode: str) -> ControlCommandResult:
        if execution_mode not in {mode.value for mode in ExecutionMode}:
            return ControlCommandResult(False, f"Unknown execution mode: {execution_mode}", self.store.load_runtime_state())
        state = self.store.load_runtime_state()
        next_state = deepcopy(state)
        next_state.execution_mode = ExecutionMode(execution_mode)
        self.config.runtime.execution_mode = execution_mode
        self.store.save_runtime_state(next_state)
        self.store.append_event(
            StrategyEvent(
                event_type=EventType.EXECUTION_MODE_CHANGED,
                event_time=datetime.now(),
                phase_before=state.phase,
                phase_after=next_state.phase,
                title="Execution mode changed",
                message=f"Execution mode set to {execution_mode}.",
                event_key="execution_mode_changed",
                metadata={"execution_mode": execution_mode},
            )
        )
        return ControlCommandResult(True, f"Execution mode set to {execution_mode}.", next_state)

    def set_pause_new_entries(self, paused: bool) -> ControlCommandResult:
        state = self.store.load_runtime_state()
        next_state = deepcopy(state)
        next_state.paused_new_entries = paused
        self.store.save_runtime_state(next_state)
        self.store.append_event(
            StrategyEvent(
                event_type=EventType.OPERATOR_ACTION,
                event_time=datetime.now(),
                phase_before=state.phase,
                phase_after=next_state.phase,
                title="Pause new entries changed",
                message="New entries paused." if paused else "New entries resumed.",
                event_key="pause_new_entries_changed",
                metadata={"paused_new_entries": paused},
            )
        )
        return ControlCommandResult(True, "Paused new entries." if paused else "Resumed new entries.", next_state)

    def request_force_flatten(self) -> ControlCommandResult:
        state = self.store.load_runtime_state()
        next_state = deepcopy(state)
        next_state.force_flatten_requested = True
        self.store.save_runtime_state(next_state)
        self.store.append_event(
            StrategyEvent(
                event_type=EventType.OPERATOR_ACTION,
                event_time=datetime.now(),
                phase_before=state.phase,
                phase_after=next_state.phase,
                title="Force flatten requested",
                message="Operator requested force flatten on the next cycle.",
                event_key="force_flatten_requested",
            )
        )
        return ControlCommandResult(True, "Force flatten request recorded.", next_state)

    def clear_cooldown(self) -> ControlCommandResult:
        state = self.store.load_runtime_state()
        next_state = deepcopy(state)
        next_state.cooldown_end_time = None
        if next_state.phase == StrategyPhase.COOLDOWN_AFTER_STOP:
            next_state.phase = StrategyPhase.OBSERVING
        self.store.save_runtime_state(next_state)
        self.store.append_event(
            StrategyEvent(
                event_type=EventType.OPERATOR_ACTION,
                event_time=datetime.now(),
                phase_before=state.phase,
                phase_after=next_state.phase,
                title="Cooldown cleared",
                message="Cooldown cleared by operator.",
                event_key="cooldown_cleared",
            )
        )
        return ControlCommandResult(True, "Cooldown cleared.", next_state)

    def set_price_below_alert(self, target_price: float) -> ControlCommandResult:
        state = self.store.load_runtime_state()
        if target_price <= 0:
            return ControlCommandResult(False, "Target price must be greater than zero.", state)

        next_state = deepcopy(state)
        next_state.price_alert.enabled = True
        next_state.price_alert.target_price = target_price
        next_state.price_alert.trigger_when_below = True
        next_state.price_alert.active_below_triggered = False
        self.store.save_runtime_state(next_state)
        self.store.append_event(
            StrategyEvent(
                event_type=EventType.PRICE_ALERT_UPDATED,
                event_time=datetime.now(),
                phase_before=state.phase,
                phase_after=next_state.phase,
                title="Price alert updated",
                message=f"Price-below alert set at {target_price:.2f}.",
                event_key="price_alert_updated",
                metadata={"target_price": target_price},
            )
        )
        return ControlCommandResult(True, f"Price alert set: notify when <= {target_price:.2f}.", next_state)

    def clear_price_alert(self) -> ControlCommandResult:
        state = self.store.load_runtime_state()
        next_state = deepcopy(state)
        next_state.price_alert.enabled = False
        next_state.price_alert.target_price = None
        next_state.price_alert.active_below_triggered = False
        self.store.save_runtime_state(next_state)
        self.store.append_event(
            StrategyEvent(
                event_type=EventType.PRICE_ALERT_CLEARED,
                event_time=datetime.now(),
                phase_before=state.phase,
                phase_after=next_state.phase,
                title="Price alert cleared",
                message="Price-below alert cleared by operator.",
                event_key="price_alert_cleared",
            )
        )
        return ControlCommandResult(True, "Price alert cleared.", next_state)


def start_control_server(config: AppConfig, store: SQLiteStateStore) -> ControlServerHandle | None:
    if not config.control.enabled:
        return None
    service = ControlCommandService(config, store)
    handler = _build_handler(config, service)
    server = ThreadingHTTPServer((config.control.host, config.control.port), handler)
    thread = Thread(target=server.serve_forever, name="gold-control-server", daemon=True)
    thread.start()
    handle = ControlServerHandle(
        config.control.host,
        config.control.port,
        config.control.access_token,
        thread,
        server,
    )
    LOGGER.info("Control panel started at %s", handle.base_url)
    return handle


def _build_handler(config: AppConfig, service: ControlCommandService) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if not _is_authorized(config, parsed.query, {}, self.headers):
                self._write_json(403, {"ok": False, "message": "Missing or invalid token."})
                return

            status = service.build_status()
            flash = parse_qs(parsed.query).get("msg", [None])[0]
            status.flash_message = flash
            path = parsed.path
            if path in {"/", "/app", "/dashboard"}:
                self._write_html(200, _render_dashboard_v2(config, status))
                return
            if path == "/api/health":
                self._write_json(200, {"ok": True, "time": status.generated_at.isoformat()})
                return
            if path == "/api/config/public":
                self._write_json(
                    200,
                    {
                        "execution_mode": status.runtime_state.execution_mode.value,
                        "profile_name": status.runtime_state.profile_name.value,
                        "profiles": list(get_profile_presets().keys()),
                        "execution_modes": [mode.value for mode in ExecutionMode],
                        "control_enabled": config.control.enabled,
                    },
                )
                return
            if path == "/api/state/current":
                self._write_json(200, _build_state_payload(status))
                return
            if path == "/api/position/current":
                self._write_json(200, service.current_position_payload())
                return
            if path == "/api/alerts/current":
                self._write_json(200, service.current_price_alert_payload())
                return
            if path == "/api/signals/recent":
                self._write_json(
                    200,
                    [decision.as_json_dict() for decision in service.store.load_recent_decisions(limit=20)],
                )
                return
            if path == "/api/events/recent":
                self._write_json(200, [_event_to_dict(event) for event in status.recent_events])
                return
            if path == "/api/profile/current":
                self._write_json(
                    200,
                    {
                        "profile_name": status.runtime_state.profile_name.value,
                        "execution_mode": status.runtime_state.execution_mode.value,
                        "paused_new_entries": status.runtime_state.paused_new_entries,
                    },
                )
                return
            if path == "/api/email-events/recent":
                self._write_json(200, [_notification_to_dict(item) for item in status.recent_notifications])
                return
            if path == "/api/openapi.json":
                self._write_json(200, _build_openapi_spec(config))
                return
            self._write_json(404, {"ok": False, "message": "Not found"})

        def do_PUT(self) -> None:  # noqa: N802
            self._handle_mutation()

        def do_POST(self) -> None:  # noqa: N802
            self._handle_mutation()

        def _handle_mutation(self) -> None:
            parsed = urlparse(self.path)
            payload = self._read_payload()
            if not _is_authorized(config, parsed.query, payload, self.headers):
                self._write_json(403, {"ok": False, "message": "Missing or invalid token."})
                return

            path = parsed.path
            if path == "/api/position/sync":
                result = service.sync_position(
                    has_position=str(payload.get("has_position")).lower() in {"true", "1", "yes"},
                    position_size_grams=float(payload.get("position_size_grams") or 0.0),
                    avg_entry_price=_to_float(payload.get("avg_entry_price")),
                    entry_time=_parse_datetime(payload.get("entry_time")),
                    note=payload.get("note"),
                )
            elif path == "/api/position/clear":
                result = service.sync_position(has_position=False, note=payload.get("note"))
            elif path == "/api/position/adjust":
                result = service.adjust_position(
                    delta_grams=float(payload.get("delta_grams") or 0.0),
                    fill_price=float(payload.get("fill_price") or 0.0),
                    note=payload.get("note"),
                )
            elif path == "/api/operator/set-profile":
                result = service.set_profile(str(payload.get("profile_name")))
            elif path == "/api/operator/set-execution-mode":
                result = service.set_execution_mode(str(payload.get("execution_mode")))
            elif path == "/api/operator/pause-new-entries":
                result = service.set_pause_new_entries(True)
            elif path == "/api/operator/resume-new-entries":
                result = service.set_pause_new_entries(False)
            elif path == "/api/operator/force-flatten-request":
                result = service.request_force_flatten()
            elif path == "/api/operator/clear-cooldown":
                result = service.clear_cooldown()
            elif path == "/api/alerts/price-below":
                result = service.set_price_below_alert(float(payload.get("target_price") or 0.0))
            elif path == "/api/alerts/clear":
                result = service.clear_price_alert()
            else:
                self._write_json(404, {"ok": False, "message": "Not found"})
                return

            if self._prefers_html_form():
                self._redirect_with_message(result.message)
                return

            self._write_json(
                200 if result.ok else 400,
                {
                    "ok": result.ok,
                    "message": result.message,
                    "runtime_state": _runtime_state_summary(result.runtime_state),
                },
            )

        def _read_payload(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            raw_body = self.rfile.read(length).decode("utf-8")
            if "application/json" in self.headers.get("Content-Type", ""):
                return json.loads(raw_body or "{}")
            return {key: values[0] for key, values in parse_qs(raw_body).items()}

        def _prefers_html_form(self) -> bool:
            content_type = self.headers.get("Content-Type", "")
            accept = self.headers.get("Accept", "")
            return (
                "application/x-www-form-urlencoded" in content_type
                or "text/html" in accept
            )

        def _redirect_with_message(self, message: str) -> None:
            location = f"/app?token={quote(config.control.access_token)}&msg={quote(message)}"
            self.send_response(303)
            self.send_header("Location", location)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _write_json(self, status_code: int, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False, default=_json_default).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _write_html(self, status_code: int, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            LOGGER.info('control "%s"', format % args)

    return Handler


def _build_state_payload(status: ControlDashboardStatus) -> dict[str, Any]:
    return {
        "generated_at": status.generated_at.isoformat(),
        "runtime_state": _runtime_state_summary(status.runtime_state),
        "latest_tick_price": status.latest_tick_price,
        "latest_tick_time": status.latest_tick_time.isoformat() if status.latest_tick_time else None,
        "latest_tick_source": status.latest_tick_source,
        "indicator_summary": status.indicator_summary,
        "latest_completed_bar_time": status.latest_completed_bar_time.isoformat() if status.latest_completed_bar_time else None,
        "latest_signal": status.latest_decision,
    }


def _runtime_state_summary(state: StrategyRuntimeState) -> dict[str, Any]:
    return {
        "phase": state.phase.value,
        "execution_mode": state.execution_mode.value,
        "profile_name": state.profile_name.value,
        "paused_new_entries": state.paused_new_entries,
        "force_flatten_requested": state.force_flatten_requested,
        "position": {
            "has_position": state.position.has_position,
            "position_size_grams": state.position.size_grams,
            "avg_entry_price": state.position.entry_price,
            "entry_time": state.position.entry_time.isoformat() if state.position.entry_time else None,
            "position_notional_yuan": state.position.position_notional_yuan,
            "effective_stop_price": state.position.current_stop_loss,
            "initial_stop_price": state.position.initial_stop_price,
            "strategy_mode": state.position.strategy_mode.value,
            "last_sync_source": state.position.last_sync_source,
            "last_sync_at": state.position.last_sync_at.isoformat() if state.position.last_sync_at else None,
            "note": state.position.note,
        },
        "price_alert": {
            "enabled": state.price_alert.enabled,
            "target_price": state.price_alert.target_price,
            "trigger_when_below": state.price_alert.trigger_when_below,
            "active_below_triggered": state.price_alert.active_below_triggered,
            "last_triggered_at": state.price_alert.last_triggered_at.isoformat() if state.price_alert.last_triggered_at else None,
            "last_triggered_price": state.price_alert.last_triggered_price,
        },
        "cooldown_end_time": state.cooldown_end_time.isoformat() if state.cooldown_end_time else None,
    }


def _notification_to_dict(record: NotificationRecord) -> dict[str, Any]:
    return {
        "title": record.title,
        "notification_type": record.notification_type,
        "success": record.success,
        "simulated_send": record.simulated_send,
        "sent_at": record.sent_at.isoformat(),
        "dedupe_key": record.dedupe_key,
        "decision_action": record.decision_action,
        "strategy_mode": record.strategy_mode,
        "error_message": record.error_message,
    }


def _event_to_dict(event: StrategyEvent) -> dict[str, Any]:
    return {
        "event_type": event.event_type.value,
        "event_time": event.event_time.isoformat(),
        "title": event.title,
        "message": event.message,
        "level": event.level,
        "event_key": event.event_key,
        "metadata": event.metadata,
    }


def _build_openapi_spec(config: AppConfig) -> dict[str, Any]:
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "ICBC Gold Local Control API",
            "version": "1.0.0",
            "description": "Local operator dashboard and JSON API for the ICBC gold assist system.",
        },
        "servers": [{"url": f"http://{config.control.host}:{config.control.port}"}],
        "paths": {
            "/api/state/current": {"get": {"summary": "Current runtime state"}},
            "/api/position/current": {"get": {"summary": "Current actual position"}},
            "/api/alerts/current": {"get": {"summary": "Current price alert state"}},
            "/api/alerts/price-below": {"post": {"summary": "Set alert when price is below target"}},
            "/api/alerts/clear": {"post": {"summary": "Clear current price alert"}},
            "/api/position/sync": {"put": {"summary": "Sync actual position ledger"}},
            "/api/position/clear": {"post": {"summary": "Clear actual position"}},
            "/api/position/adjust": {"post": {"summary": "Adjust actual position"}},
            "/api/operator/set-profile": {"post": {"summary": "Set profile"}},
            "/api/operator/set-execution-mode": {"post": {"summary": "Set execution mode"}},
            "/api/operator/pause-new-entries": {"post": {"summary": "Pause entries"}},
            "/api/operator/resume-new-entries": {"post": {"summary": "Resume entries"}},
            "/api/operator/force-flatten-request": {"post": {"summary": "Request force flatten"}},
            "/api/operator/clear-cooldown": {"post": {"summary": "Clear cooldown"}},
            "/api/signals/recent": {"get": {"summary": "Recent strategy outputs"}},
            "/api/events/recent": {"get": {"summary": "Recent events"}},
            "/api/email-events/recent": {"get": {"summary": "Recent emails"}},
            "/api/profile/current": {"get": {"summary": "Current operator profile"}},
            "/api/config/public": {"get": {"summary": "Public runtime config"}},
            "/api/health": {"get": {"summary": "Health check"}},
        },
    }


def _render_dashboard(config: AppConfig, status: ControlDashboardStatus) -> str:
    token = escape(config.control.access_token)
    latest_signal = status.latest_decision or {}
    position = _runtime_state_summary(status.runtime_state)["position"]
    recent_events = "".join(
        f"<li><b>{escape(event.event_type.value)}</b> {escape(event.event_time.isoformat())} - {escape(event.message)}</li>"
        for event in status.recent_events
    ) or "<li>No recent events.</li>"
    recent_emails = "".join(
        f"<li><b>{escape(item.title)}</b> {escape(item.sent_at.isoformat())} simulated={item.simulated_send}</li>"
        for item in status.recent_notifications
    ) or "<li>No recent email events.</li>"
    flash_html = (
        f'<div style="background:#e9f7ef;border:1px solid #b7e1c1;padding:10px;border-radius:8px;margin-bottom:16px;">{escape(status.flash_message)}</div>'
        if status.flash_message
        else ""
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>ICBC Gold Dashboard</title>
  <style>
    body {{ font-family: "Microsoft YaHei", sans-serif; margin: 24px; background: #f7f8fb; color: #1c2333; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(320px,1fr)); gap: 16px; }}
    .card {{ background: white; border-radius: 12px; padding: 16px; box-shadow: 0 6px 18px rgba(0,0,0,0.08); }}
    h1, h2 {{ margin-top: 0; }}
    dl {{ display: grid; grid-template-columns: 150px 1fr; gap: 6px 12px; margin: 0; }}
    dt {{ font-weight: 700; }}
    form {{ margin: 0 0 10px 0; }}
    input, select, button {{ width: 100%; padding: 8px; margin-top: 6px; box-sizing: border-box; }}
    button {{ cursor: pointer; }}
    ul {{ margin: 0; padding-left: 18px; }}
    .small {{ color: #5c667a; font-size: 13px; }}
  </style>
</head>
<body>
  <h1>ICBC Gold Local Dashboard</h1>
  <p class="small">Token protected local dashboard. Query token: <code>{token}</code></p>
  {flash_html}
  <div class="grid">
    <section class="card">
      <h2>当前状态</h2>
      <dl>
        <dt>execution_mode</dt><dd>{escape(status.runtime_state.execution_mode.value)}</dd>
        <dt>profile_name</dt><dd>{escape(status.runtime_state.profile_name.value)}</dd>
        <dt>phase</dt><dd>{escape(status.runtime_state.phase.value)}</dd>
        <dt>current_price</dt><dd>{_fmt(status.latest_tick_price)}</dd>
        <dt>price_time</dt><dd>{escape(status.latest_tick_time.isoformat()) if status.latest_tick_time else "-"}</dd>
        <dt>regime</dt><dd>{escape(str(status.indicator_summary.get("regime_hint") or "-"))}</dd>
        <dt>ema_fast</dt><dd>{_fmt(status.indicator_summary.get("ema_fast"))}</dd>
        <dt>ema_slow</dt><dd>{_fmt(status.indicator_summary.get("ema_slow"))}</dd>
        <dt>atr</dt><dd>{_fmt(status.indicator_summary.get("atr"))}</dd>
        <dt>indicator_ready</dt><dd>{escape(str(status.indicator_summary.get("indicator_ready")))}</dd>
        <dt>paused_new_entries</dt><dd>{escape(str(status.runtime_state.paused_new_entries))}</dd>
        <dt>cooldown_status</dt><dd>{escape(status.runtime_state.cooldown_end_time.isoformat()) if status.runtime_state.cooldown_end_time else "none"}</dd>
      </dl>
    </section>
    <section class="card">
      <h2>当前信号</h2>
      <dl>
        <dt>action</dt><dd>{escape(str(latest_signal.get("action", "-")))}</dd>
        <dt>strategy_mode</dt><dd>{escape(str(latest_signal.get("strategy_mode", "-")))}</dd>
        <dt>confidence</dt><dd>{_fmt(latest_signal.get("confidence"))}</dd>
        <dt>entry_reason</dt><dd>{escape(str(latest_signal.get("entry_reason", "-")))}</dd>
        <dt>invalidation_reason</dt><dd>{escape(str(latest_signal.get("invalidation_reason", "-")))}</dd>
        <dt>stop_rule</dt><dd>{escape(str(latest_signal.get("stop_rule", "-")))}</dd>
        <dt>take_profit_rule</dt><dd>{escape(str(latest_signal.get("take_profit_rule", "-")))}</dd>
        <dt>whether_send_email</dt><dd>{escape(str(latest_signal.get("whether_send_email", False)))}</dd>
        <dt>triggered_at</dt><dd>{escape(str(latest_signal.get("timestamp", "-")))}</dd>
        <dt>dedupe_key</dt><dd>{escape(str(latest_signal.get("dedupe_key", "-")))}</dd>
      </dl>
    </section>
    <section class="card">
      <h2>真实仓位</h2>
      <dl>
        <dt>has_position</dt><dd>{escape(str(position["has_position"]))}</dd>
        <dt>position_size_grams</dt><dd>{_fmt(position["position_size_grams"])}</dd>
        <dt>avg_entry_price</dt><dd>{_fmt(position["avg_entry_price"])}</dd>
        <dt>entry_time</dt><dd>{escape(str(position["entry_time"] or "-"))}</dd>
        <dt>position_notional_yuan</dt><dd>{_fmt(position["position_notional_yuan"])}</dd>
        <dt>effective_stop_price</dt><dd>{_fmt(position["effective_stop_price"])}</dd>
        <dt>last_sync_at</dt><dd>{escape(str(position["last_sync_at"] or "-"))}</dd>
        <dt>last_sync_source</dt><dd>{escape(str(position["last_sync_source"] or "-"))}</dd>
        <dt>note</dt><dd>{escape(str(position["note"] or "-"))}</dd>
      </dl>
    </section>
    <section class="card">
      <h2>操作区</h2>
      <form method="post" action="/api/position/sync?token={token}">
        <strong>写入当前仓位</strong>
        <input name="has_position" value="true" />
        <input name="position_size_grams" placeholder="grams" />
        <input name="avg_entry_price" placeholder="avg entry price" />
        <input name="entry_time" placeholder="2026-03-25T21:00:00" />
        <input name="note" placeholder="note" />
        <button type="submit">写入仓位</button>
      </form>
      <form method="post" action="/api/position/clear?token={token}"><button type="submit">清空仓位</button></form>
      <form method="post" action="/api/position/adjust?token={token}">
        <strong>手动加仓/减仓</strong>
        <input name="delta_grams" placeholder="+1 or -1" />
        <input name="fill_price" placeholder="fill price" />
        <input name="note" placeholder="note" />
        <button type="submit">调整仓位</button>
      </form>
      <form method="post" action="/api/operator/set-profile?token={token}">
        <select name="profile_name">
          <option value="conservative">conservative</option>
          <option value="slightly_aggressive_today">slightly_aggressive_today</option>
        </select>
        <button type="submit">切换策略档位</button>
      </form>
      <form method="post" action="/api/operator/set-execution-mode?token={token}">
        <select name="execution_mode">
          <option value="manual_position_sync">manual_position_sync</option>
          <option value="signal_implies_position">signal_implies_position</option>
        </select>
        <button type="submit">切换执行模式</button>
      </form>
      <form method="post" action="/api/operator/pause-new-entries?token={token}"><button type="submit">暂停新开仓</button></form>
      <form method="post" action="/api/operator/resume-new-entries?token={token}"><button type="submit">恢复新开仓</button></form>
      <form method="post" action="/api/operator/force-flatten-request?token={token}"><button type="submit">请求强制平仓</button></form>
      <form method="post" action="/api/operator/clear-cooldown?token={token}"><button type="submit">清除冷静期</button></form>
    </section>
    <section class="card"><h2>最近事件</h2><ul>{recent_events}</ul></section>
    <section class="card"><h2>最近邮件</h2><ul>{recent_emails}</ul></section>
  </div>
</body>
</html>"""


def _render_dashboard_v2(config: AppConfig, status: ControlDashboardStatus) -> str:
    token = escape(config.control.access_token)
    latest_signal = status.latest_decision or {}
    runtime_summary = _runtime_state_summary(status.runtime_state)
    position = runtime_summary["position"]
    price_alert = runtime_summary["price_alert"]
    recent_events = "".join(
        f"<li><b>{escape(event.event_type.value)}</b> {escape(event.event_time.isoformat())} - {escape(event.message)}</li>"
        for event in status.recent_events
    ) or "<li>No recent events.</li>"
    recent_emails = "".join(
        f"<li><b>{escape(item.title)}</b> {escape(item.sent_at.isoformat())} simulated={item.simulated_send}</li>"
        for item in status.recent_notifications
    ) or "<li>No recent email events.</li>"
    flash_html = (
        f'<div style="background:#e9f7ef;border:1px solid #b7e1c1;padding:10px;border-radius:8px;margin-bottom:16px;">{escape(status.flash_message)}</div>'
        if status.flash_message
        else ""
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>ICBC Gold Dashboard</title>
  <style>
    body {{ font-family: "Microsoft YaHei", sans-serif; margin: 24px; background: #f7f8fb; color: #1c2333; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(320px,1fr)); gap: 16px; }}
    .card {{ background: white; border-radius: 12px; padding: 16px; box-shadow: 0 6px 18px rgba(0,0,0,0.08); }}
    h1, h2 {{ margin-top: 0; }}
    dl {{ display: grid; grid-template-columns: 150px 1fr; gap: 6px 12px; margin: 0; }}
    dt {{ font-weight: 700; }}
    form {{ margin: 0 0 10px 0; }}
    input, select, button {{ width: 100%; padding: 8px; margin-top: 6px; box-sizing: border-box; }}
    button {{ cursor: pointer; }}
    ul {{ margin: 0; padding-left: 18px; }}
    .small {{ color: #5c667a; font-size: 13px; }}
  </style>
</head>
<body>
  <h1>ICBC Gold Local Dashboard</h1>
  <p class="small">Token protected local dashboard. Query token: <code>{token}</code></p>
  {flash_html}
  <div class="grid">
    <section class="card">
      <h2>当前状态</h2>
      <dl>
        <dt>execution_mode</dt><dd>{escape(status.runtime_state.execution_mode.value)}</dd>
        <dt>profile_name</dt><dd>{escape(status.runtime_state.profile_name.value)}</dd>
        <dt>phase</dt><dd>{escape(status.runtime_state.phase.value)}</dd>
        <dt>current_price</dt><dd>{_fmt(status.latest_tick_price)}</dd>
        <dt>price_time</dt><dd>{escape(status.latest_tick_time.isoformat()) if status.latest_tick_time else "-"}</dd>
        <dt>regime</dt><dd>{escape(str(status.indicator_summary.get("regime_hint") or "-"))}</dd>
        <dt>ema_fast</dt><dd>{_fmt(status.indicator_summary.get("ema_fast"))}</dd>
        <dt>ema_slow</dt><dd>{_fmt(status.indicator_summary.get("ema_slow"))}</dd>
        <dt>atr</dt><dd>{_fmt(status.indicator_summary.get("atr"))}</dd>
        <dt>indicator_ready</dt><dd>{escape(str(status.indicator_summary.get("indicator_ready")))}</dd>
        <dt>paused_new_entries</dt><dd>{escape(str(status.runtime_state.paused_new_entries))}</dd>
        <dt>cooldown_status</dt><dd>{escape(status.runtime_state.cooldown_end_time.isoformat()) if status.runtime_state.cooldown_end_time else "none"}</dd>
      </dl>
    </section>
    <section class="card">
      <h2>当前信号</h2>
      <dl>
        <dt>action</dt><dd>{escape(str(latest_signal.get("action", "-")))}</dd>
        <dt>strategy_mode</dt><dd>{escape(str(latest_signal.get("strategy_mode", "-")))}</dd>
        <dt>confidence</dt><dd>{_fmt(latest_signal.get("confidence"))}</dd>
        <dt>entry_reason</dt><dd>{escape(str(latest_signal.get("entry_reason", "-")))}</dd>
        <dt>invalidation_reason</dt><dd>{escape(str(latest_signal.get("invalidation_reason", "-")))}</dd>
        <dt>stop_rule</dt><dd>{escape(str(latest_signal.get("stop_rule", "-")))}</dd>
        <dt>take_profit_rule</dt><dd>{escape(str(latest_signal.get("take_profit_rule", "-")))}</dd>
        <dt>whether_send_email</dt><dd>{escape(str(latest_signal.get("whether_send_email", False)))}</dd>
        <dt>triggered_at</dt><dd>{escape(str(latest_signal.get("timestamp", "-")))}</dd>
        <dt>dedupe_key</dt><dd>{escape(str(latest_signal.get("dedupe_key", "-")))}</dd>
      </dl>
    </section>
    <section class="card">
      <h2>价格提醒</h2>
      <dl>
        <dt>enabled</dt><dd>{escape(str(price_alert["enabled"]))}</dd>
        <dt>target_price</dt><dd>{_fmt(price_alert["target_price"])}</dd>
        <dt>armed</dt><dd>{escape(str(not price_alert["active_below_triggered"]))}</dd>
        <dt>last_triggered_at</dt><dd>{escape(str(price_alert["last_triggered_at"] or "-"))}</dd>
        <dt>last_triggered_price</dt><dd>{_fmt(price_alert["last_triggered_price"])}</dd>
      </dl>
    </section>
    <section class="card">
      <h2>真实仓位</h2>
      <dl>
        <dt>has_position</dt><dd>{escape(str(position["has_position"]))}</dd>
        <dt>position_size_grams</dt><dd>{_fmt(position["position_size_grams"])}</dd>
        <dt>avg_entry_price</dt><dd>{_fmt(position["avg_entry_price"])}</dd>
        <dt>entry_time</dt><dd>{escape(str(position["entry_time"] or "-"))}</dd>
        <dt>position_notional_yuan</dt><dd>{_fmt(position["position_notional_yuan"])}</dd>
        <dt>effective_stop_price</dt><dd>{_fmt(position["effective_stop_price"])}</dd>
        <dt>last_sync_at</dt><dd>{escape(str(position["last_sync_at"] or "-"))}</dd>
        <dt>last_sync_source</dt><dd>{escape(str(position["last_sync_source"] or "-"))}</dd>
        <dt>note</dt><dd>{escape(str(position["note"] or "-"))}</dd>
      </dl>
    </section>
    <section class="card">
      <h2>操作区</h2>
      <form method="post" action="/api/alerts/price-below?token={token}">
        <strong>设置金价提醒</strong>
        <input name="target_price" type="number" step="0.01" min="0" placeholder="低于这个价格就提醒" />
        <button type="submit">设置低价提醒</button>
      </form>
      <form method="post" action="/api/alerts/clear?token={token}">
        <button type="submit">清除金价提醒</button>
      </form>
      <form method="post" action="/api/position/sync?token={token}">
        <strong>写入当前仓位</strong>
        <input name="has_position" value="true" />
        <input name="position_size_grams" placeholder="grams" />
        <input name="avg_entry_price" placeholder="avg entry price" />
        <input name="entry_time" placeholder="2026-03-25T21:00:00" />
        <input name="note" placeholder="note" />
        <button type="submit">写入仓位</button>
      </form>
      <form method="post" action="/api/position/clear?token={token}"><button type="submit">清空仓位</button></form>
      <form method="post" action="/api/position/adjust?token={token}">
        <strong>手动加仓/减仓</strong>
        <input name="delta_grams" placeholder="+1 or -1" />
        <input name="fill_price" placeholder="fill price" />
        <input name="note" placeholder="note" />
        <button type="submit">调整仓位</button>
      </form>
      <form method="post" action="/api/operator/set-profile?token={token}">
        <select name="profile_name">
          <option value="conservative">conservative</option>
          <option value="slightly_aggressive_today">slightly_aggressive_today</option>
        </select>
        <button type="submit">切换策略档位</button>
      </form>
      <form method="post" action="/api/operator/set-execution-mode?token={token}">
        <select name="execution_mode">
          <option value="manual_position_sync">manual_position_sync</option>
          <option value="signal_implies_position">signal_implies_position</option>
        </select>
        <button type="submit">切换执行模式</button>
      </form>
      <form method="post" action="/api/operator/pause-new-entries?token={token}"><button type="submit">暂停新开仓</button></form>
      <form method="post" action="/api/operator/resume-new-entries?token={token}"><button type="submit">恢复新开仓</button></form>
      <form method="post" action="/api/operator/force-flatten-request?token={token}"><button type="submit">请求强制平仓</button></form>
      <form method="post" action="/api/operator/clear-cooldown?token={token}"><button type="submit">清除冷静期</button></form>
    </section>
    <section class="card"><h2>最近事件</h2><ul>{recent_events}</ul></section>
    <section class="card"><h2>最近邮件</h2><ul>{recent_emails}</ul></section>
  </div>
</body>
</html>"""


def _is_authorized(config: AppConfig, query: str, payload: dict[str, Any], headers: Any) -> bool:
    parsed_query = parse_qs(query or "")
    token = (
        parsed_query.get("token", [None])[0]
        or payload.get("token")
        or headers.get("X-Control-Token")
        or headers.get("Authorization", "").removeprefix("Bearer ").strip()
    )
    return token == config.control.access_token


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _to_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(str(value))


def _detect_lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
