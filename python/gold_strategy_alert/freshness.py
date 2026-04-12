"""Fresh quote validation and deduplication helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import AppConfig
from models import MarketPriceQuote, QuoteSample, StrategyRuntimeState


@dataclass(slots=True)
class FreshnessResult:
    sample: QuoteSample
    duplicate: bool
    duplicate_reason: str | None = None


def build_quote_sample(
    quote: MarketPriceQuote,
    fetch_time: datetime,
    config: AppConfig,
    state: StrategyRuntimeState,
) -> FreshnessResult:
    timezone = ZoneInfo(config.trading_window.timezone_name)
    if fetch_time.tzinfo is None:
        fetch_time = fetch_time.replace(tzinfo=timezone)
    quote_time = quote.quote_time
    if quote_time.tzinfo is None:
        quote_time = quote_time.replace(tzinfo=timezone)

    age_seconds = max((fetch_time - quote_time).total_seconds(), 0.0)
    stale_reason = None
    if age_seconds > config.freshness.stale_after_seconds:
        stale_reason = f"quote_age_exceeded:{age_seconds:.0f}s"

    duplicate = False
    duplicate_reason = None
    if (
        state.last_quote_page_time is not None
        and state.last_quote_page_time == quote_time
        and state.last_quote_price is not None
        and abs(state.last_quote_price - quote.current_price) < 1e-9
    ):
        duplicate = True
        duplicate_reason = "same_quote_time_and_price"

    sample = QuoteSample(
        symbol="ICBC_ACC_GOLD",
        price=quote.current_price,
        quote_time=quote_time,
        quote_time_source=quote.quote_time_source,
        fetch_time=fetch_time,
        source_name=quote.source_name,
        is_fresh=stale_reason is None,
        stale_reason=stale_reason,
        metadata={
            "instrument_name": quote.instrument_name,
            "currency": quote.currency,
            "final_url": quote.raw_payload.get("final_url"),
            "http_status": quote.raw_payload.get("http_status"),
            "quote_age_seconds": age_seconds,
        },
    )
    return FreshnessResult(sample=sample, duplicate=duplicate, duplicate_reason=duplicate_reason)


def repeated_page_time_too_long(
    state: StrategyRuntimeState,
    sample: QuoteSample,
    config: AppConfig,
) -> bool:
    if state.last_quote_page_time is None:
        return False
    if sample.quote_time != state.last_quote_page_time:
        return False
    if state.last_decision_time is None:
        return False
    return (sample.fetch_time - state.last_decision_time) >= timedelta(
        seconds=config.freshness.repeated_page_time_bad_after_seconds
    )
