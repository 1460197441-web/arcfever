"""1-minute to 5-minute aggregation contracts."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from models import Bar, PriceTick


@dataclass(slots=True)
class MinuteBarAggregator:
    """Aggregates 1-minute samples into completed 5-minute OHLC bars."""

    bar_minutes: int = 5
    ticks: list[PriceTick] = field(default_factory=list)
    last_emitted_start_at: datetime | None = None

    def add_tick(self, tick: PriceTick) -> None:
        self.ticks.append(tick)

    def build_completed_bars(self, now: datetime) -> Iterable[Bar]:
        bars = aggregate_minute_ticks_to_bars(self.ticks, bar_minutes=self.bar_minutes, allow_incomplete_window=False)
        fresh_bars: list[Bar] = []
        for bar in bars:
            if bar.end_at > now:
                continue
            if self.last_emitted_start_at is not None and bar.start_at <= self.last_emitted_start_at:
                continue
            fresh_bars.append(bar)
        if fresh_bars:
            self.last_emitted_start_at = fresh_bars[-1].start_at
            latest_start = fresh_bars[-1].start_at
            self.ticks = [
                tick
                for tick in self.ticks
                if self.align_bar_start(tick.observed_at, self.bar_minutes) >= latest_start
            ]
        return fresh_bars

    @staticmethod
    def align_bar_start(observed_at: datetime, bar_minutes: int = 5) -> datetime:
        minute = (observed_at.minute // bar_minutes) * bar_minutes
        return observed_at.replace(minute=minute, second=0, microsecond=0)

    @staticmethod
    def next_bar_end(start_at: datetime, bar_minutes: int = 5) -> datetime:
        return start_at + timedelta(minutes=bar_minutes)

    @staticmethod
    def has_gap(ticks: Sequence[PriceTick], expected_seconds: int = 60) -> bool:
        if len(ticks) < 2:
            return False
        for prev, curr in zip(ticks, ticks[1:]):
            if (curr.observed_at - prev.observed_at).total_seconds() > expected_seconds * 1.5:
                return True
        return False


def aggregate_minute_ticks_to_bars(
    ticks: Sequence[PriceTick],
    bar_minutes: int = 5,
    allow_incomplete_window: bool = False,
) -> list[Bar]:
    if not ticks:
        return []

    normalized_ticks = sorted(
        (
            PriceTick(
                symbol=tick.symbol,
                price=tick.price,
                observed_at=tick.observed_at.replace(second=0, microsecond=0),
                source=tick.source,
                metadata=tick.metadata,
            )
            for tick in ticks
        ),
        key=lambda item: item.observed_at,
    )

    grouped: dict[datetime, list[PriceTick]] = {}
    for tick in normalized_ticks:
        start_at = MinuteBarAggregator.align_bar_start(tick.observed_at, bar_minutes)
        grouped.setdefault(start_at, []).append(tick)

    bars: list[Bar] = []
    for start_at in sorted(grouped):
        window_ticks = sorted(grouped[start_at], key=lambda item: item.observed_at)
        end_at = MinuteBarAggregator.next_bar_end(start_at, bar_minutes)
        expected_minutes = [start_at + timedelta(minutes=index) for index in range(bar_minutes)]
        actual_minutes = {tick.observed_at for tick in window_ticks}
        if not allow_incomplete_window and any(expected not in actual_minutes for expected in expected_minutes):
            continue
        bar = Bar(
            start_at=start_at,
            end_at=end_at,
            open=window_ticks[0].price,
            high=max(tick.price for tick in window_ticks),
            low=min(tick.price for tick in window_ticks),
            close=window_ticks[-1].price,
            source=window_ticks[-1].source,
            is_complete=(len(actual_minutes) == bar_minutes),
        )
        if allow_incomplete_window or bar.is_complete:
            bars.append(bar)
    return bars
