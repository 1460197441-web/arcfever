"""Configuration models and defaults for the strategy alert service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
import json
from pathlib import Path
from typing import Any

from models import ExecutionMode, ProfileName


def _load_legacy_email_defaults() -> dict[str, Any]:
    legacy_path = Path(__file__).resolve().parents[1] / "gold_alert" / "config.json"
    if not legacy_path.exists():
        return {}
    try:
        payload = json.loads(legacy_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}

    email = payload.get("email", {})
    recipients = email.get("to") or []
    if not isinstance(recipients, list):
        recipients = [str(recipients)]
    return {
        "smtp_host": email.get("smtp_host", "smtp.qq.com"),
        "smtp_port": int(email.get("smtp_port", 465)),
        "username": email.get("username", ""),
        "password": email.get("password", ""),
        "use_ssl": bool(email.get("use_ssl", True)),
        "recipients": [str(item) for item in recipients if str(item).strip()],
    }


LEGACY_EMAIL_DEFAULTS = _load_legacy_email_defaults()


@dataclass(slots=True)
class RuntimeConfig:
    run_mode: str = "live"
    session_mode: str = "market_hours"
    live_profile: str = "LIVE_TODAY_V1"
    execution_mode: str = ExecutionMode.MANUAL_POSITION_SYNC.value
    profile_name: str = ProfileName.CONSERVATIVE.value
    enable_test_mode: bool = False
    fetch_failure_alert_threshold: int = 3
    send_fetch_recovery_notification: bool = True
    replay_data_path: str = ""
    replay_speed: str = "realtime"
    send_real_email_in_test_mode: bool = False
    mock_current_price: float | None = None
    mock_daily_open: float | None = None
    mock_daily_high: float | None = None
    mock_daily_low: float | None = None
    mock_daily_last: float | None = None
    history_preload_minutes: int = 2880
    signal_bar_tf: str = "3m"
    trend_tf: str = "5m"
    fill_model: str = "signal_bar_close"


@dataclass(slots=True)
class TradingWindowConfig:
    start: time = time(hour=9, minute=10)
    end: time = time(hour=22, minute=30)
    timezone_name: str = "Asia/Shanghai"


@dataclass(slots=True)
class FeeConfig:
    buy_fee_rate: float = 0.005
    sell_fee_rate: float = 0.005

    @property
    def fee_break_even_multiplier(self) -> float:
        return (1 + self.buy_fee_rate) / (1 - self.sell_fee_rate)


@dataclass(slots=True)
class SamplingConfig:
    price_sample_seconds: int = 60
    decision_interval_minutes: int = 5
    position_size_grams: float = 2.0


@dataclass(slots=True)
class ProductConfig:
    product_name: str = "ICBC personal accumulation gold"
    trading_currency: str = "CNY"
    price_refresh_reference_seconds: int = 3
    min_purchase_grams: float = 1.0


@dataclass(slots=True)
class IndicatorConfig:
    ema_fast_period: int = 20
    ema_slow_period: int = 50
    atr_period: int = 14
    atr_method: str = "wilder"
    bollinger_period: int = 20
    bollinger_stddev: float = 2.0
    bollinger_std: float = 2.0
    donchian_entry_period: int = 20
    donchian_exit_period: int = 10
    donchian_entry: int = 20
    donchian_exit: int = 10
    ema_fast: int = 20
    ema_slow: int = 50
    breakout_lookback_bars: int = 20
    reentry_lookback_bars: int = 12
    min_ready_bars: int = 50


@dataclass(slots=True)
class StrategyConfig:
    stop_loss_cooldown_minutes: int = 20
    market_open_entry_freeze_minutes: int = 12
    allow_entry_without_direction_ready: bool = False
    allow_exit_without_full_warmup: bool = True
    no_new_after: time = time(hour=21, minute=50)
    force_flatten_at: time = time(hour=22, minute=20)
    band_width_expand_bars: int = 2


@dataclass(slots=True)
class RiskConfig:
    first_entry_yuan: float = 2000.0
    default_entry_notional_yuan: float = 2000.0
    max_batches: int = 1
    max_batches_per_idea: int = 1
    max_new_entries_per_day: int = 2
    max_trade_idea_loss_yuan: float = 45.0
    daily_profit_lock_yuan: float = 20.0
    daily_loss_stop_yuan: float = 60.0
    account_equity_yuan: float = 10000.0
    daily_drawdown_stop_pct: float = 0.03
    consecutive_losses_cooldown: int = 2
    max_consecutive_losses_before_cooldown: int = 2
    allow_average_down: bool = False
    allow_losing_add: bool = False
    email_dedupe_minutes: int = 15
    slightly_aggressive_mode: bool = False
    allow_operational_email: bool = False


@dataclass(slots=True)
class ProfilePreset:
    name: str
    enable_r2: bool
    enable_r1: bool
    enable_l1: bool
    first_entry_yuan: float
    max_batches: int
    max_new_entries_per_day: int
    max_trade_idea_loss_yuan: float
    daily_profit_lock_yuan: float
    daily_loss_stop_yuan: float
    no_new_after: time
    force_flatten_at: time


@dataclass(slots=True)
class StrategySwitchesConfig:
    enable_r2: bool = True
    enable_r1: bool = True
    enable_l1: bool = False


@dataclass(slots=True)
class EmailConfig:
    smtp_host: str = str(LEGACY_EMAIL_DEFAULTS.get("smtp_host", "smtp.qq.com"))
    smtp_port: int = int(LEGACY_EMAIL_DEFAULTS.get("smtp_port", 465))
    username: str = str(LEGACY_EMAIL_DEFAULTS.get("username", ""))
    password: str = str(LEGACY_EMAIL_DEFAULTS.get("password", ""))
    use_ssl: bool = bool(LEGACY_EMAIL_DEFAULTS.get("use_ssl", True))
    recipients: list[str] = field(default_factory=lambda: list(LEGACY_EMAIL_DEFAULTS.get("recipients", [])))
    subject_prefix: str = "Strategy Alert"
    dashboard_link: str = "http://114.55.225.26:18787/app?token=dd2e15efa3da24d8c55967fd37a0db1b"
    entry_cancel_notify: bool = False
    notify_only_actionable: bool = True
    send_operational_email: bool = False


@dataclass(slots=True)
class ControlConfig:
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8787
    access_token: str = "dd2e15efa3da24d8c55967fd37a0db1b"
    manual_entry_confirmation: bool = False
    recent_events_limit: int = 12


@dataclass(slots=True)
class StorageConfig:
    sqlite_path: Path = Path("runtime/gold_strategy.db")
    log_path: Path = Path("runtime/service.log")
    data_path: Path = Path("data")
    keep_minute_prices_days: int = 30
    keep_events_days: int = 90


@dataclass(slots=True)
class ProviderConfig:
    icbc_provider_name: str = "icbc_accumulated_gold"
    icbc_portal_fallback_name: str = "icbc_portal_fallback"
    sge_provider_name: str = "sge_au9999"
    provider_options: dict[str, dict] = field(default_factory=dict)


@dataclass(slots=True)
class AppConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    trading_window: TradingWindowConfig = field(default_factory=TradingWindowConfig)
    fees: FeeConfig = field(default_factory=FeeConfig)
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    product: ProductConfig = field(default_factory=ProductConfig)
    indicators: IndicatorConfig = field(default_factory=IndicatorConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    strategy_switches: StrategySwitchesConfig = field(default_factory=StrategySwitchesConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    control: ControlConfig = field(default_factory=ControlConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    providers: ProviderConfig = field(default_factory=ProviderConfig)


def default_config() -> AppConfig:
    """Return the default in-memory application configuration."""
    config = AppConfig()
    apply_profile(config, config.runtime.profile_name)
    return config


def get_profile_presets() -> dict[str, ProfilePreset]:
    return {
        ProfileName.CONSERVATIVE.value: ProfilePreset(
            name=ProfileName.CONSERVATIVE.value,
            enable_r2=True,
            enable_r1=False,
            enable_l1=False,
            first_entry_yuan=1000.0,
            max_batches=1,
            max_new_entries_per_day=1,
            max_trade_idea_loss_yuan=20.0,
            daily_profit_lock_yuan=20.0,
            daily_loss_stop_yuan=40.0,
            no_new_after=time(hour=21, minute=50),
            force_flatten_at=time(hour=22, minute=20),
        ),
        ProfileName.SLIGHTLY_AGGRESSIVE_TODAY.value: ProfilePreset(
            name=ProfileName.SLIGHTLY_AGGRESSIVE_TODAY.value,
            enable_r2=True,
            enable_r1=True,
            enable_l1=False,
            first_entry_yuan=2000.0,
            max_batches=1,
            max_new_entries_per_day=2,
            max_trade_idea_loss_yuan=45.0,
            daily_profit_lock_yuan=30.0,
            daily_loss_stop_yuan=80.0,
            no_new_after=time(hour=21, minute=50),
            force_flatten_at=time(hour=22, minute=20),
        ),
    }


def apply_profile(config: AppConfig, profile_name: str) -> None:
    presets = get_profile_presets()
    if profile_name not in presets:
        raise ValueError(f"Unknown profile: {profile_name}")
    preset = presets[profile_name]
    config.runtime.profile_name = preset.name
    config.strategy_switches.enable_r2 = preset.enable_r2
    config.strategy_switches.enable_r1 = preset.enable_r1
    config.strategy_switches.enable_l1 = preset.enable_l1
    config.risk.first_entry_yuan = preset.first_entry_yuan
    config.risk.default_entry_notional_yuan = preset.first_entry_yuan
    config.risk.max_batches = preset.max_batches
    config.risk.max_batches_per_idea = preset.max_batches
    config.risk.max_new_entries_per_day = preset.max_new_entries_per_day
    config.risk.max_trade_idea_loss_yuan = preset.max_trade_idea_loss_yuan
    config.risk.daily_profit_lock_yuan = preset.daily_profit_lock_yuan
    config.risk.daily_loss_stop_yuan = preset.daily_loss_stop_yuan
    config.risk.slightly_aggressive_mode = profile_name == ProfileName.SLIGHTLY_AGGRESSIVE_TODAY.value
    config.strategy.no_new_after = preset.no_new_after
    config.strategy.force_flatten_at = preset.force_flatten_at
