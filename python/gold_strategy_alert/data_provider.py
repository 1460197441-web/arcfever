"""Data provider contracts and provider orchestration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Protocol

from collectors.icbc_accumulated_gold import IcbcAccumulatedGoldCollector
from collectors.icbc_portal_fallback import IcbcPortalFallbackCollector
from collectors.sge_au9999 import SgeAu9999Collector
from config import AppConfig
from models import (
    DailyMarketSnapshot,
    EventType,
    MarketPriceQuote,
    PriceTick,
    ReferenceDailyQuote,
    StrategyEvent,
)


LOGGER = logging.getLogger(__name__)


class MinutePriceProvider(ABC):
    """Provides the latest 1-minute level price observations for the trading symbol."""

    @abstractmethod
    def fetch_latest_tick(self, now: datetime) -> PriceTick | None:
        raise NotImplementedError


class DailyReferenceProvider(ABC):
    """Provides intraday reference data used for the allow_long daily filter."""

    @abstractmethod
    def fetch_daily_snapshot(self, now: datetime) -> DailyMarketSnapshot | None:
        raise NotImplementedError


class SupportsClose(Protocol):
    def close(self) -> None:
        """Close internal resources if needed."""


@dataclass(slots=True)
class ProviderBundle:
    minute_price_provider: MinutePriceProvider
    daily_reference_provider: DailyReferenceProvider
    fallback_reference_provider: DailyReferenceProvider | None = None


@dataclass(slots=True)
class DataFetchResult:
    tick: PriceTick | None
    primary_quote: MarketPriceQuote
    daily_reference: DailyMarketSnapshot
    fallback_used: bool
    events: list[StrategyEvent]


class OrchestratedMarketDataProvider:
    """Coordinates primary/fallback market and reference sources."""

    def __init__(
        self,
        primary_collector: IcbcAccumulatedGoldCollector,
        portal_fallback_collector: IcbcPortalFallbackCollector,
        sge_collector: SgeAu9999Collector,
    ) -> None:
        self.primary_collector = primary_collector
        self.portal_fallback_collector = portal_fallback_collector
        self.sge_collector = sge_collector

    def fetch(self, now: datetime) -> DataFetchResult:
        events: list[StrategyEvent] = []
        primary_quote = self._fetch_primary_quote(now, events)
        tick = PriceTick(
            symbol="ICBC_ACC_GOLD",
            price=primary_quote.current_price,
            observed_at=primary_quote.quote_time,
            source=primary_quote.source_name,
            metadata={
                "instrument_name": primary_quote.instrument_name,
                "currency": primary_quote.currency,
                "quote_time_source": primary_quote.quote_time_source,
                "http_status": primary_quote.raw_payload.get("http_status"),
                "final_url": primary_quote.raw_payload.get("final_url"),
            },
        )
        reference_quote, fallback_used = self._fetch_reference_quote(now, primary_quote, events)
        daily_reference = DailyMarketSnapshot(
            symbol=reference_quote.symbol,
            open=reference_quote.open,
            high=reference_quote.high,
            low=reference_quote.low,
            last=reference_quote.last,
            observed_at=reference_quote.quote_time,
            source=reference_quote.source_name,
        )
        return DataFetchResult(
            tick=tick,
            primary_quote=primary_quote,
            daily_reference=daily_reference,
            fallback_used=fallback_used,
            events=events,
        )

    def _fetch_primary_quote(self, now: datetime, events: list[StrategyEvent]) -> MarketPriceQuote:
        try:
            quote = self.primary_collector.fetch_quote(now)
            events.append(
                StrategyEvent(
                    event_type=EventType.SAMPLE_SUCCESS,
                    event_time=now,
                    title="Primary ICBC quote fetched",
                    message=f"Fetched {quote.instrument_name} from {quote.source_name}",
                    metadata={"source": quote.source_name},
                )
            )
            return quote
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Primary ICBC collector failed, falling back to portal collector: %s", exc)
            events.append(
                StrategyEvent(
                    event_type=EventType.DATA_FALLBACK,
                    event_time=now,
                    title="Primary ICBC quote failed",
                    message=str(exc),
                    level="WARNING",
                    metadata={"fallback_to": "icbc_portal_fallback"},
                )
            )
            quote = self.portal_fallback_collector.fetch_quote(now)
            events.append(
                StrategyEvent(
                    event_type=EventType.SAMPLE_SUCCESS,
                    event_time=now,
                    title="Portal fallback quote fetched",
                    message=f"Fetched {quote.instrument_name} from {quote.source_name}",
                    metadata={"source": quote.source_name},
                )
            )
            return quote

    def _fetch_reference_quote(
        self,
        now: datetime,
        primary_quote: MarketPriceQuote,
        events: list[StrategyEvent],
    ) -> tuple[ReferenceDailyQuote, bool]:
        try:
            quote = self.sge_collector.fetch_daily_quote(now)
            return quote, False
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("SGE collector failed, falling back to ICBC daily snapshot: %s", exc)
            events.append(
                StrategyEvent(
                    event_type=EventType.DATA_FALLBACK,
                    event_time=now,
                    title="SGE daily filter fallback activated",
                    message=str(exc),
                    level="WARNING",
                    metadata={"fallback_to": primary_quote.source_name},
                )
            )
            if primary_quote.open_price is None or primary_quote.high_price is None or primary_quote.low_price is None:
                raise ValueError("ICBC daily fallback requires open/high/low/current fields.") from exc
            return (
                ReferenceDailyQuote(
                    symbol="ICBC_ACC_GOLD",
                    open=primary_quote.open_price,
                    high=primary_quote.high_price,
                    low=primary_quote.low_price,
                    last=primary_quote.current_price,
                    quote_time=primary_quote.quote_time,
                    quote_time_source=primary_quote.quote_time_source,
                    source_name=f"{primary_quote.source_name}_daily_fallback",
                    raw_payload=primary_quote.raw_payload,
                ),
                True,
            )


def build_default_market_data_provider(config: AppConfig) -> OrchestratedMarketDataProvider:
    options = config.providers.provider_options
    return OrchestratedMarketDataProvider(
        primary_collector=IcbcAccumulatedGoldCollector(**options.get(config.providers.icbc_provider_name, {})),
        portal_fallback_collector=IcbcPortalFallbackCollector(
            **options.get(config.providers.icbc_portal_fallback_name, {})
        ),
        sge_collector=SgeAu9999Collector(**options.get(config.providers.sge_provider_name, {})),
    )
