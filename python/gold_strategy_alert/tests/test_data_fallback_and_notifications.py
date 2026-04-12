from __future__ import annotations

from datetime import datetime
from email.message import EmailMessage

from config import EmailConfig
from models import (
    DailyMarketSnapshot,
    EventType,
    ExitReason,
    IndicatorSnapshot,
    NotificationRecord,
    PositionState,
    SignalType,
    StrategyEvent,
    StrategyPhase,
    StrategyRuntimeState,
    StrategyStepResult,
)
from notifier import EmailNotifier, NotificationContext


def _runtime_state() -> StrategyRuntimeState:
    return StrategyRuntimeState(
        phase=StrategyPhase.HOLDING,
        position=PositionState(
            has_position=True,
            entry_price=800.0,
            entry_time=datetime(2026, 3, 23, 10, 0, 0),
            current_stop_loss=796.0,
            trailing_active=True,
            h_star=820.0,
        ),
    )


def _context() -> NotificationContext:
    return NotificationContext(
        triggered_at=datetime(2026, 3, 23, 10, 30, 0),
        current_price=824.0,
        indicator_snapshot=IndicatorSnapshot(
            close_5m=824.0,
            ema_fast=819.5,
            ema_slow=813.1,
            atr=3.2,
            hh=818.0,
            ll=790.0,
            allow_long=True,
            day_snapshot_source="sge",
        ),
        daily_snapshot=DailyMarketSnapshot(
            symbol="Au99.99",
            open=800.0,
            high=825.0,
            low=798.0,
            last=824.0,
            observed_at=datetime(2026, 3, 23, 10, 30, 0),
            source="sge",
        ),
        allow_long=True,
        source_name="sge",
        fallback_used=False,
        fetch_success=True,
        exception_message=None,
        extra={"note": "test"},
    )


def test_step_result_notification_message_contains_required_fields() -> None:
    notifier = EmailNotifier(
        EmailConfig(
            username="sender@example.com",
            recipients=["receiver@example.com"],
            password="secret",
        )
    )
    result = StrategyStepResult(
        next_state=StrategyPhase.WAITING_REENTRY_CONFIRMATION,
        signal_type=SignalType.SELL,
        exit_reason=ExitReason.HARD_TAKE_PROFIT,
        should_notify=True,
        decision_message="Hard take profit triggered.",
        generated_events=[
            StrategyEvent(
                event_type=EventType.EXIT_TRIGGERED,
                event_time=datetime(2026, 3, 23, 10, 30, 0),
                title="ignored",
                message="ignored",
            )
        ],
        updated_runtime_state=_runtime_state(),
    )
    message = notifier.build_step_result_message(result, _runtime_state(), _context())
    body = message.get_content()
    assert isinstance(message, EmailMessage)
    assert "signal_type: sell" in body
    assert "current_price: 824.0" in body
    assert "entry_price: 800.0" in body
    assert "holding_minutes: 30.0" in body
    assert "ema_fast: 819.5" in body
    assert "hh: 818.0" in body
    assert "allow_long: True" in body
    assert "exit_reason: hard_take_profit" in body
    assert "day_summary: open=800.0, high=825.0, low=798.0, last=824.0" in body
    assert "filter_source: sge" in body
    assert "fetch_success: True" in body


def test_send_step_result_returns_success_notification_record_when_send_succeeds(monkeypatch) -> None:
    notifier = EmailNotifier(
        EmailConfig(
            username="sender@example.com",
            recipients=["receiver@example.com"],
            password="secret",
        )
    )

    def fake_send(message: EmailMessage) -> None:
        return None

    monkeypatch.setattr(notifier, "_send_message", fake_send)
    result = StrategyStepResult(
        next_state=StrategyPhase.OBSERVING,
        signal_type=SignalType.BUY,
        exit_reason=None,
        should_notify=True,
        decision_message="Buy signal triggered.",
        updated_runtime_state=StrategyRuntimeState(),
    )
    record = notifier.send_step_result(result, StrategyRuntimeState(), _context())
    assert record.success is True
    assert record.notification_type == "buy"
    assert record.simulated_send is False


def test_send_step_result_returns_failed_notification_record_when_send_raises(monkeypatch) -> None:
    notifier = EmailNotifier(
        EmailConfig(
            username="sender@example.com",
            recipients=["receiver@example.com"],
            password="secret",
        )
    )

    def fake_send(message: EmailMessage) -> None:
        raise RuntimeError("smtp down")

    monkeypatch.setattr(notifier, "_send_message", fake_send)
    result = StrategyStepResult(
        next_state=StrategyPhase.ERROR,
        signal_type=SignalType.ERROR,
        exit_reason=None,
        should_notify=True,
        decision_message="error",
        updated_runtime_state=StrategyRuntimeState(phase=StrategyPhase.ERROR),
    )
    record = notifier.send_step_result(result, StrategyRuntimeState(), _context())
    assert record.success is False
    assert record.error_message == "smtp down"


def test_test_mode_simulates_send_without_calling_smtp(monkeypatch) -> None:
    notifier = EmailNotifier(
        EmailConfig(
            username="sender@example.com",
            recipients=["receiver@example.com"],
            password="secret",
        )
    )
    notifier.configure_test_mode(enable_test_mode=True, send_real_email_in_test_mode=False)

    def fail_if_called(message: EmailMessage) -> None:
        raise AssertionError("SMTP should not be called in simulated test mode")

    monkeypatch.setattr(notifier, "_send_message", fail_if_called)
    result = StrategyStepResult(
        next_state=StrategyPhase.OBSERVING,
        signal_type=SignalType.BUY,
        exit_reason=None,
        should_notify=True,
        decision_message="Buy signal triggered.",
        updated_runtime_state=StrategyRuntimeState(),
    )
    record = notifier.send_step_result(result, StrategyRuntimeState(), _context())
    assert record.success is True
    assert record.simulated_send is True
    assert record.error_message is None


def test_should_send_step_result_filters_non_actionable_notifications_by_default() -> None:
    notifier = EmailNotifier(
        EmailConfig(
            username="sender@example.com",
            recipients=["receiver@example.com"],
            password="secret",
        )
    )
    result = StrategyStepResult(
        next_state=StrategyPhase.OBSERVING,
        signal_type=None,
        exit_reason=None,
        should_notify=True,
        decision_message="Indicators not ready.",
        updated_runtime_state=StrategyRuntimeState(),
    )
    assert notifier.should_send_step_result(result) is False


def test_should_send_step_result_allows_buy_sell_notifications() -> None:
    notifier = EmailNotifier(
        EmailConfig(
            username="sender@example.com",
            recipients=["receiver@example.com"],
            password="secret",
        )
    )
    result = StrategyStepResult(
        next_state=StrategyPhase.WAITING_FOR_ENTRY_FILL,
        signal_type=SignalType.BUY,
        exit_reason=None,
        should_notify=True,
        decision_message="Buy signal triggered.",
        updated_runtime_state=StrategyRuntimeState(),
    )
    assert notifier.should_send_step_result(result) is True


def test_notification_record_shape_is_suitable_for_persistence() -> None:
    record = NotificationRecord(
        title="Data source warning",
        notification_type="warning",
        success=False,
        error_message="timeout",
        sent_at=datetime(2026, 3, 23, 10, 10, 0),
    )
    assert record.title == "Data source warning"
    assert record.success is False
