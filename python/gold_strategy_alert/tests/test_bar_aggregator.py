from __future__ import annotations

from datetime import datetime

import pytest

from bar_aggregator import MinuteBarAggregator, aggregate_minute_ticks_to_bars
from models import PriceTick


def _tick(minute: int, price: float) -> PriceTick:
    return PriceTick(
        symbol="ICBC_ACC_GOLD",
        price=price,
        observed_at=datetime(2026, 3, 23, 9, minute, 0),
        source="test",
    )


def test_align_bar_start_rounds_down_to_5_minute_boundary() -> None:
    observed_at = datetime(2026, 3, 23, 9, 17, 42)
    aligned = MinuteBarAggregator.align_bar_start(observed_at, bar_minutes=5)
    assert aligned == datetime(2026, 3, 23, 9, 15, 0)


def test_has_gap_detects_missing_minute_in_tick_stream() -> None:
    ticks = [_tick(15, 810.0), _tick(16, 811.0), _tick(18, 812.0)]
    assert MinuteBarAggregator.has_gap(ticks) is True


def test_aggregate_completed_5m_bar_uses_first_highest_lowest_last_tick_values() -> None:
    ticks = [
        _tick(15, 810.0),
        _tick(16, 811.2),
        _tick(17, 809.8),
        _tick(18, 813.4),
        _tick(19, 812.1),
    ]

    bars = aggregate_minute_ticks_to_bars(ticks, bar_minutes=5, allow_incomplete_window=False)

    assert len(bars) == 1
    bar = bars[0]
    assert bar.start_at == datetime(2026, 3, 23, 9, 15, 0)
    assert bar.end_at == datetime(2026, 3, 23, 9, 20, 0)
    assert bar.open == pytest.approx(810.0)
    assert bar.high == pytest.approx(813.4)
    assert bar.low == pytest.approx(809.8)
    assert bar.close == pytest.approx(812.1)
    assert bar.is_complete is True


def test_aggregate_does_not_emit_bar_if_any_minute_is_missing_by_default() -> None:
    ticks = [
        _tick(15, 810.0),
        _tick(16, 811.0),
        _tick(18, 812.0),
        _tick(19, 813.0),
    ]

    bars = aggregate_minute_ticks_to_bars(ticks, bar_minutes=5, allow_incomplete_window=False)

    assert bars == []


def test_aggregate_does_not_use_unfinished_current_5m_window() -> None:
    ticks = [
        _tick(15, 810.0),
        _tick(16, 811.0),
        _tick(17, 812.0),
        _tick(18, 813.0),
    ]

    bars = aggregate_minute_ticks_to_bars(ticks, bar_minutes=5, allow_incomplete_window=False)

    assert bars == []

