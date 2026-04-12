"""Notification contracts and SMTP notifier implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from email.header import Header
from email.message import EmailMessage
import smtplib
import ssl
from typing import Any

from config import EmailConfig
from models import (
    DailyMarketSnapshot,
    EventType,
    IndicatorSnapshot,
    NotificationRecord,
    SignalType,
    StrategyDecision,
    StrategyRuntimeState,
    StrategyStepResult,
)


@dataclass(slots=True)
class NotificationContext:
    triggered_at: datetime
    current_price: float | None = None
    indicator_snapshot: IndicatorSnapshot | None = None
    daily_snapshot: DailyMarketSnapshot | None = None
    allow_long: bool | None = None
    source_name: str | None = None
    fallback_used: bool = False
    fetch_success: bool = True
    exception_message: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class Notifier(ABC):
    @abstractmethod
    def send_step_result(
        self,
        result: StrategyStepResult,
        runtime_state: StrategyRuntimeState,
        context: NotificationContext,
    ) -> NotificationRecord:
        raise NotImplementedError


class EmailNotifier(Notifier):
    def __init__(self, config: EmailConfig) -> None:
        self.config = config
        self.enable_test_mode = False
        self.send_real_email_in_test_mode = False

    def configure_test_mode(self, enable_test_mode: bool, send_real_email_in_test_mode: bool) -> None:
        self.enable_test_mode = enable_test_mode
        self.send_real_email_in_test_mode = send_real_email_in_test_mode

    def should_send_step_result(self, result: StrategyStepResult) -> bool:
        if not result.should_notify:
            return False
        generated_event_types = {event.event_type for event in result.generated_events}
        if generated_event_types & {EventType.SAMPLE_FAILURE, EventType.FETCH_RECOVERED}:
            return self.config.send_operational_email
        if not self.config.notify_only_actionable:
            return True
        return result.action.value in {"BUY_NOW", "SELL_NOW"} or result.signal_type in {SignalType.BUY, SignalType.SELL}

    def send_step_result(
        self,
        result: StrategyStepResult,
        runtime_state: StrategyRuntimeState,
        context: NotificationContext,
    ) -> NotificationRecord:
        message = self.build_step_result_message(result, runtime_state, context)
        if self.enable_test_mode and not self.send_real_email_in_test_mode:
            return NotificationRecord(
                title=message["Subject"],
                notification_type=(result.signal_type.value if result.signal_type else "info"),
                success=True,
                sent_at=context.triggered_at,
                simulated_send=True,
                dedupe_key=(result.decision_output.dedupe_key if result.decision_output else None),
                decision_action=result.action.value,
                strategy_mode=result.strategy_mode.value,
            )
        try:
            self._send_message(message)
            return NotificationRecord(
                title=message["Subject"],
                notification_type=(result.signal_type.value if result.signal_type else "info"),
                success=True,
                sent_at=context.triggered_at,
                simulated_send=False,
                dedupe_key=(result.decision_output.dedupe_key if result.decision_output else None),
                decision_action=result.action.value,
                strategy_mode=result.strategy_mode.value,
            )
        except Exception as exc:  # noqa: BLE001
            return NotificationRecord(
                title=message["Subject"],
                notification_type=(result.signal_type.value if result.signal_type else "info"),
                success=False,
                sent_at=context.triggered_at,
                simulated_send=False,
                error_message=str(exc),
                dedupe_key=(result.decision_output.dedupe_key if result.decision_output else None),
                decision_action=result.action.value,
                strategy_mode=result.strategy_mode.value,
            )

    def send(
        self,
        decision: StrategyDecision,
        state: StrategyRuntimeState,
        context: NotificationContext | None = None,
    ) -> NotificationRecord:
        context = context or NotificationContext(
            triggered_at=datetime.now(),
            current_price=decision.price,
            indicator_snapshot=decision.indicators,
            allow_long=decision.allow_long,
            extra=decision.metadata,
        )
        message = self._build_decision_message(decision, state, context)
        if self.enable_test_mode and not self.send_real_email_in_test_mode:
            return NotificationRecord(
                title=message["Subject"],
                notification_type=decision.signal_type.value,
                success=True,
                sent_at=context.triggered_at,
                simulated_send=True,
            )
        try:
            self._send_message(message)
            return NotificationRecord(
                title=message["Subject"],
                notification_type=decision.signal_type.value,
                success=True,
                sent_at=context.triggered_at,
                simulated_send=False,
            )
        except Exception as exc:  # noqa: BLE001
            return NotificationRecord(
                title=message["Subject"],
                notification_type=decision.signal_type.value,
                success=False,
                sent_at=context.triggered_at,
                simulated_send=False,
                error_message=str(exc),
            )

    def build_step_result_message(
        self,
        result: StrategyStepResult,
        runtime_state: StrategyRuntimeState,
        context: NotificationContext,
    ) -> EmailMessage:
        title = self._build_subject_title(result)
        message = EmailMessage()
        message["From"] = self.config.username
        message["To"] = ", ".join(self.config.recipients)
        message["Subject"] = Header(f"[{self.config.subject_prefix}] {title}", "utf-8").encode()
        message.set_content(self._build_step_result_body(result, runtime_state, context), charset="utf-8")
        return message

    def _build_decision_message(
        self,
        decision: StrategyDecision,
        state: StrategyRuntimeState,
        context: NotificationContext,
    ) -> EmailMessage:
        message = EmailMessage()
        message["From"] = self.config.username
        message["To"] = ", ".join(self.config.recipients)
        message["Subject"] = Header(f"[{self.config.subject_prefix}] {decision.title}", "utf-8").encode()
        message.set_content(self._build_decision_body(decision, state, context), charset="utf-8")
        return message

    def _build_step_result_body(
        self,
        result: StrategyStepResult,
        runtime_state: StrategyRuntimeState,
        context: NotificationContext,
    ) -> str:
        generated_event_types = {event.event_type for event in result.generated_events}
        if generated_event_types & {EventType.SAMPLE_FAILURE, EventType.FETCH_RECOVERED}:
            return self._build_operational_alert_body(result, context)

        indicators = context.indicator_snapshot
        daily = context.daily_snapshot
        entry_time = runtime_state.position.entry_time
        holding_minutes = (
            f"{((context.triggered_at - entry_time).total_seconds() / 60.0):.1f}"
            if entry_time is not None
            else "None"
        )
        day_summary = (
            f"open={daily.open}, high={daily.high}, low={daily.low}, last={daily.last}"
            if daily is not None
            else "None"
        )
        filter_source = context.source_name or (daily.source if daily is not None else "unknown")
        lines = [
            f"action: {result.action.value}",
            f"strategy_mode: {result.strategy_mode.value}",
            f"regime: {result.regime.value}",
            f"confidence: {result.confidence}",
            f"signal_type: {result.signal_type.value if result.signal_type else 'none'}",
            f"triggered_at: {context.triggered_at.isoformat()}",
            f"current_price: {context.current_price}",
            f"max_position_grams: {context.extra.get('position_size_grams')}",
            f"entry_price: {runtime_state.position.entry_price}",
            f"holding_minutes: {holding_minutes}",
            f"ema_fast: {indicators.ema_fast if indicators else None}",
            f"ema_slow: {indicators.ema_slow if indicators else None}",
            f"atr: {indicators.atr if indicators else None}",
            f"hh: {indicators.hh if indicators else None}",
            f"ll: {indicators.ll if indicators else None}",
            f"allow_long: {context.allow_long}",
            f"exit_reason: {result.exit_reason.value if result.exit_reason else None}",
            f"day_summary: {day_summary}",
            f"filter_source: {filter_source}",
            f"fallback_used: {context.fallback_used}",
            f"fetch_success: {context.fetch_success}",
            f"exception_message: {context.exception_message}",
            f"decision_message: {result.decision_message}",
            f"next_state: {result.next_state.value}",
            f"generated_events: {[event.event_type.value for event in result.generated_events]}",
            f"dedupe_key: {result.decision_output.dedupe_key if result.decision_output else None}",
            f"extra: {context.extra}",
        ]
        if self.config.dashboard_link:
            lines.append(f"dashboard_link: {self.config.dashboard_link}")
        return "\n".join(lines)

    def _build_operational_alert_body(
        self,
        result: StrategyStepResult,
        context: NotificationContext,
    ) -> str:
        lines = [
            f"triggered_at: {context.triggered_at.isoformat()}",
            f"message: {result.decision_message}",
            f"fetch_success: {context.fetch_success}",
            f"current_price: {context.current_price}",
            f"consecutive_fetch_failures: {context.extra.get('consecutive_fetch_failures')}",
            f"previous_failures: {context.extra.get('previous_failures')}",
            f"max_position_grams: {context.extra.get('position_size_grams')}",
            f"exception_message: {context.exception_message}",
        ]
        if self.config.dashboard_link:
            lines.append(f"dashboard_link: {self.config.dashboard_link}")
        return "\n".join(lines)

    def _build_decision_body(
        self,
        decision: StrategyDecision,
        state: StrategyRuntimeState,
        context: NotificationContext,
    ) -> str:
        indicators = decision.indicators or context.indicator_snapshot
        daily = context.daily_snapshot
        lines = [
            f"title: {decision.title}",
            f"signal_type: {decision.signal_type.value}",
            f"summary: {decision.summary}",
            f"event_key: {decision.event_key}",
            f"current_price: {decision.price}",
            f"max_position_grams: {context.extra.get('position_size_grams')}",
            f"allow_long: {decision.allow_long}",
            f"entry_price: {state.position.entry_price}",
            f"entry_time: {state.position.entry_time}",
            f"ema_fast: {indicators.ema_fast if indicators else None}",
            f"ema_slow: {indicators.ema_slow if indicators else None}",
            f"atr: {indicators.atr if indicators else None}",
            f"hh: {indicators.hh if indicators else None}",
            f"ll: {indicators.ll if indicators else None}",
            f"day_snapshot_source: {indicators.day_snapshot_source if indicators else None}",
            f"day_summary: {f'open={daily.open}, high={daily.high}, low={daily.low}, last={daily.last}' if daily else None}",
            f"fallback_used: {context.fallback_used}",
            f"fetch_success: {context.fetch_success}",
            f"exception_message: {context.exception_message}",
            f"metadata: {decision.metadata}",
        ]
        if self.config.dashboard_link:
            lines.append(f"dashboard_link: {self.config.dashboard_link}")
        return "\n".join(lines)

    def _build_subject_title(self, result: StrategyStepResult) -> str:
        event_types = {event.event_type for event in result.generated_events}
        if EventType.SAMPLE_FAILURE in event_types:
            return "ICBC Accumulated Gold fetch alert"
        if EventType.FETCH_RECOVERED in event_types:
            return "ICBC Accumulated Gold fetch recovered"
        if result.exit_reason is not None:
            return f"ICBC Accumulated Gold {result.exit_reason.value}"
        if result.action.value in {"BUY_NOW", "SELL_NOW"} and result.decision_output is not None:
            return result.decision_output.short_email_subject
        if result.signal_type is not None:
            return f"ICBC Accumulated Gold {result.signal_type.value}"
        return "ICBC Accumulated Gold info"

    def _send_message(self, message: EmailMessage) -> None:
        if self.config.use_ssl:
            with smtplib.SMTP_SSL(
                self.config.smtp_host,
                self.config.smtp_port,
                context=ssl.create_default_context(),
            ) as server:
                server.login(self.config.username, self.config.password)
                server.send_message(message)
            return

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(self.config.username, self.config.password)
            server.send_message(message)
