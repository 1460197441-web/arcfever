"""Domain models used across the strategy alert service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class StrategyPhase(str, Enum):
    OBSERVING = "observing"
    WAITING_FOR_ENTRY_FILL = "waiting_for_entry_fill"
    HOLDING = "holding"
    COOLDOWN_AFTER_STOP = "cooldown_after_stop"
    WAITING_REENTRY_CONFIRMATION = "waiting_reentry_confirmation"
    ERROR = "error"


class ReadinessLevel(str, Enum):
    FULL_READY = "full_ready"
    EXIT_ONLY_READY = "exit_only_ready"
    DATA_BAD_MODE = "data_bad_mode"


class ActionType(str, Enum):
    BUY_NOW = "BUY_NOW"
    SELL_NOW = "SELL_NOW"
    HOLD_POSITION = "HOLD_POSITION"
    WAIT_NO_TRADE = "WAIT_NO_TRADE"


class ExecutionMode(str, Enum):
    SIGNAL_IMPLIES_POSITION = "signal_implies_position"
    MANUAL_POSITION_SYNC = "manual_position_sync"


class ProfileName(str, Enum):
    CONSERVATIVE = "conservative"
    SLIGHTLY_AGGRESSIVE_TODAY = "slightly_aggressive_today"


class StrategyMode(str, Enum):
    R2_PULLBACK = "R2_PULLBACK"
    R1_BREAKOUT = "R1_BREAKOUT"
    L1_EXHAUSTION = "L1_EXHAUSTION"
    RISK_EXIT = "RISK_EXIT"
    TIME_EXIT = "TIME_EXIT"
    NONE = "NONE"


class MarketRegime(str, Enum):
    NOISE = "NOISE"
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    PULLBACK_READY = "PULLBACK_READY"
    BREAKOUT_READY = "BREAKOUT_READY"
    EXHAUSTION_REVERSAL_READY = "EXHAUSTION_REVERSAL_READY"


class ExitReason(str, Enum):
    INITIAL_STOP = "initial_stop"
    TIME_STOP = "time_stop"
    TRAILING_STOP = "trailing_stop"
    HARD_TAKE_PROFIT = "hard_take_profit"
    DONCHIAN_EXIT = "donchian_exit"
    STRUCTURE_EXIT = "structure_exit"
    FORCE_FLATTEN = "force_flatten"


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    RISK = "risk"
    WARNING = "warning"
    INFO = "info"
    ERROR = "error"


class EventType(str, Enum):
    SAMPLE_SUCCESS = "sample_success"
    SAMPLE_FAILURE = "sample_failure"
    FETCH_RECOVERED = "fetch_recovered"
    BAR_COMPLETED = "bar_completed"
    BUY_SIGNAL = "buy_signal"
    ENTRY_FILLED = "entry_filled"
    ENTRY_TIMEOUT_CANCELLED = "entry_timeout_cancelled"
    EXIT_TRIGGERED = "exit_triggered"
    COOLDOWN_STARTED = "cooldown_started"
    REENTRY_CONFIRMATION_READY = "reentry_confirmation_ready"
    DATA_FALLBACK = "data_fallback"
    DATA_INSUFFICIENT = "data_insufficient"
    NOTIFICATION = "notification"
    MANUAL_ENTRY_CONFIRMED = "manual_entry_confirmed"
    MANUAL_ENTRY_REJECTED = "manual_entry_rejected"
    MANUAL_POSITION_SET = "manual_position_set"
    MANUAL_POSITION_CLOSED = "manual_position_closed"
    POSITION_SYNCED = "position_synced"
    POSITION_ADJUSTED = "position_adjusted"
    POSITION_CLEARED = "position_cleared"
    PRICE_ALERT_UPDATED = "price_alert_updated"
    PRICE_ALERT_TRIGGERED = "price_alert_triggered"
    PRICE_ALERT_CLEARED = "price_alert_cleared"
    PRICE_ALERT_REARMED = "price_alert_rearmed"
    PROFILE_CHANGED = "profile_changed"
    EXECUTION_MODE_CHANGED = "execution_mode_changed"
    OPERATOR_ACTION = "operator_action"
    SIGNAL_EMITTED = "signal_emitted"
    ERROR = "error"


@dataclass(slots=True)
class PriceTick:
    symbol: str
    price: float
    observed_at: datetime
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class QuoteSample:
    symbol: str
    price: float
    quote_time: datetime
    quote_time_source: str
    fetch_time: datetime
    source_name: str
    is_fresh: bool
    stale_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Bar:
    start_at: datetime
    end_at: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    source: str = ""
    is_complete: bool = True


@dataclass(slots=True)
class DailyMarketSnapshot:
    symbol: str
    open: float
    high: float
    low: float
    last: float
    observed_at: datetime
    source: str


@dataclass(slots=True)
class IndicatorSnapshot:
    bar_time: datetime | None = None
    close_5m: float | None = None
    last_close: float | None = None
    ema_fast: float | None = None
    ema_slow: float | None = None
    atr: float | None = None
    hh: float | None = None
    ll: float | None = None
    bollinger_mid: float | None = None
    bollinger_upper: float | None = None
    bollinger_lower: float | None = None
    bollinger_bandwidth: float | None = None
    donchian_entry_high: float | None = None
    donchian_entry_low: float | None = None
    donchian_exit_high: float | None = None
    donchian_exit_low: float | None = None
    is_ready: bool = False
    warmup_complete: bool = False
    allow_long: bool = False
    day_snapshot_source: str | None = None
    day_r_value: float | None = None
    ema_trend_fast: float | None = None
    ema_trend_slow: float | None = None


@dataclass(slots=True)
class PositionState:
    has_position: bool = False
    size_grams: float = 0.0
    entry_price: float | None = None
    entry_time: datetime | None = None
    entry_bar_time: datetime | None = None
    position_notional_yuan: float = 0.0
    initial_stop_price: float | None = None
    current_stop_loss: float | None = None
    stop_source: str | None = None
    trade_idea_id: str | None = None
    strategy_mode: StrategyMode = StrategyMode.NONE
    regime_at_entry: MarketRegime = MarketRegime.NOISE
    trailing_active: bool = False
    h_star: float | None = None
    last_sync_source: str | None = None
    last_sync_at: datetime | None = None
    note: str | None = None


@dataclass(slots=True)
class PriceAlertState:
    enabled: bool = False
    target_price: float | None = None
    trigger_when_below: bool = True
    active_below_triggered: bool = False
    last_triggered_at: datetime | None = None
    last_triggered_price: float | None = None


@dataclass(slots=True)
class StrategyRuntimeState:
    phase: StrategyPhase = StrategyPhase.OBSERVING
    position: PositionState = field(default_factory=PositionState)
    price_alert: PriceAlertState = field(default_factory=PriceAlertState)
    execution_mode: ExecutionMode = ExecutionMode.MANUAL_POSITION_SYNC
    profile_name: ProfileName = ProfileName.CONSERVATIVE
    paused_new_entries: bool = False
    force_flatten_requested: bool = False
    position_state_version: int = 0
    batches_used: int = 0
    entries_today_count: int = 0
    trading_day: str | None = None
    consecutive_loss_trades: int = 0
    daily_realized_pnl_yuan: float = 0.0
    consecutive_fetch_failures: int = 0
    fetch_alert_active: bool = False
    last_fetch_success_time: datetime | None = None
    last_exit_time: datetime | None = None
    last_exit_reason: ExitReason | None = None
    cooldown_end_time: datetime | None = None
    post_exit_12bar_high: float | None = None
    last_effective_5m_bar_end: datetime | None = None
    pending_entry_signal_time: datetime | None = None
    pending_entry_deadline: datetime | None = None
    pending_entry_reference_bar_time: datetime | None = None
    pending_entry_atr: float | None = None
    pending_entry_stop_price: float | None = None
    pending_entry_reason: str | None = None
    last_decision_time: datetime | None = None
    last_quote_page_time: datetime | None = None
    last_quote_price: float | None = None
    last_email_sent_at: datetime | None = None
    last_email_event_key: str | None = None


@dataclass(slots=True)
class StrategyDecision:
    signal_type: SignalType
    should_send_email: bool
    title: str
    summary: str
    event_key: str
    price: float | None = None
    exit_reason: ExitReason | None = None
    allow_long: bool | None = None
    indicators: IndicatorSnapshot | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StrategyEvent:
    event_type: EventType
    event_time: datetime
    message: str
    phase_before: StrategyPhase | None = None
    phase_after: StrategyPhase | None = None
    title: str = ""
    level: str = "INFO"
    event_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FeeBreakdown:
    buy_fee_rate: float
    sell_fee_rate: float
    round_trip_fee_floor_yuan: float


@dataclass(slots=True)
class RiskGateResult:
    allowed: bool
    entry_price: float
    stop_price: float | None
    stop_distance_per_gram: float | None
    estimated_grams: float
    fee_floor_yuan: float
    max_price_risk_budget_yuan: float
    max_stop_distance_per_gram: float
    risk_amount_yuan: float
    notional_yuan: float
    reason: str
    atr_cap_per_gram: float | None = None


@dataclass(slots=True)
class DecisionOutput:
    action: ActionType
    strategy_mode: StrategyMode
    confidence: float
    regime: MarketRegime
    entry_reason: str
    invalidation_reason: str
    stop_rule: str
    take_profit_rule: str
    position_size_yuan: float
    fees_considered: FeeBreakdown
    whether_send_email: bool
    short_email_subject: str
    short_email_body: str
    timestamp: datetime
    execution_mode: str | None = None
    profile_name: str | None = None
    has_position: bool = False
    position_size_grams: float = 0.0
    avg_entry_price: float | None = None
    unrealized_pnl_yuan: float | None = None
    paused_new_entries: bool = False
    cooldown_status: str | None = None
    operator_hint: str | None = None
    dedupe_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "strategy_mode": self.strategy_mode.value,
            "confidence": self.confidence,
            "regime": self.regime.value,
            "entry_reason": self.entry_reason,
            "invalidation_reason": self.invalidation_reason,
            "stop_rule": self.stop_rule,
            "take_profit_rule": self.take_profit_rule,
            "position_size_yuan": self.position_size_yuan,
            "fees_considered": {
                "buy_fee_rate": self.fees_considered.buy_fee_rate,
                "sell_fee_rate": self.fees_considered.sell_fee_rate,
                "round_trip_fee_floor_yuan": self.fees_considered.round_trip_fee_floor_yuan,
            },
            "whether_send_email": self.whether_send_email,
            "short_email_subject": self.short_email_subject,
            "short_email_body": self.short_email_body,
            "timestamp": self.timestamp.isoformat(),
            "execution_mode": self.execution_mode,
            "profile_name": self.profile_name,
            "has_position": self.has_position,
            "position_size_grams": self.position_size_grams,
            "avg_entry_price": self.avg_entry_price,
            "unrealized_pnl_yuan": self.unrealized_pnl_yuan,
            "paused_new_entries": self.paused_new_entries,
            "cooldown_status": self.cooldown_status,
            "operator_hint": self.operator_hint,
            "dedupe_key": self.dedupe_key,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class StrategyStepResult:
    next_state: StrategyPhase
    signal_type: SignalType | None
    exit_reason: ExitReason | None
    should_notify: bool
    decision_message: str
    action: ActionType = ActionType.WAIT_NO_TRADE
    strategy_mode: StrategyMode = StrategyMode.NONE
    regime: MarketRegime = MarketRegime.NOISE
    confidence: float = 0.0
    decision_output: DecisionOutput | None = None
    generated_events: list[StrategyEvent] = field(default_factory=list)
    updated_runtime_state: StrategyRuntimeState = field(default_factory=StrategyRuntimeState)


@dataclass(slots=True)
class NotificationRecord:
    title: str
    notification_type: str
    success: bool
    sent_at: datetime
    simulated_send: bool = False
    error_message: str | None = None
    dedupe_key: str | None = None
    decision_action: str | None = None
    strategy_mode: str | None = None


@dataclass(slots=True)
class MarketPriceQuote:
    current_price: float
    instrument_name: str
    quote_time: datetime
    quote_time_source: str
    currency: str
    source_name: str
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReferenceDailyQuote:
    open: float
    high: float
    low: float
    last: float
    quote_time: datetime
    quote_time_source: str
    source_name: str
    symbol: str
    raw_payload: dict[str, Any] = field(default_factory=dict)
