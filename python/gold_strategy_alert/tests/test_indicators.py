from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from indicators import calculate_ema, calculate_hh_ll, calculate_wilder_atr, compute_indicator_snapshot
from models import Bar


def _bar(index: int, open_: float, high: float, low: float, close: float) -> Bar:
    start = datetime(2026, 3, 23, 9, 15, 0) + timedelta(minutes=5 * index)
    end = start + timedelta(minutes=5)
    return Bar(
        start_at=start,
        end_at=end,
        open=open_,
        high=high,
        low=low,
        close=close,
        source="test",
    )


def test_calculate_ema_12_matches_recursive_definition() -> None:
    values = [100.0, 101.0, 102.0, 103.0, 104.0]
    ema = calculate_ema(values, period=12)
    alpha = 2 / (12 + 1)
    expected = [100.0]
    for value in values[1:]:
        expected.append((value * alpha) + (expected[-1] * (1 - alpha)))
    assert ema == pytest.approx(expected)


def test_calculate_ema_36_matches_recursive_definition() -> None:
    values = [200.0, 199.0, 201.0, 203.0, 202.0]
    ema = calculate_ema(values, period=36)
    alpha = 2 / (36 + 1)
    expected = [200.0]
    for value in values[1:]:
        expected.append((value * alpha) + (expected[-1] * (1 - alpha)))
    assert ema == pytest.approx(expected)


def test_calculate_wilder_atr_14_uses_standard_true_range() -> None:
    bars = [
        _bar(0, 10.0, 11.0, 9.0, 10.5),
        _bar(1, 10.6, 11.4, 10.0, 11.2),
        _bar(2, 11.1, 12.0, 10.8, 11.8),
    ]
    atr = calculate_wilder_atr(bars, period=14)
    tr1 = 2.0
    tr2 = max(1.4, abs(11.4 - 10.5), abs(10.0 - 10.5))
    tr3 = max(1.2, abs(12.0 - 11.2), abs(10.8 - 11.2))
    assert atr[:3] == pytest.approx([tr1, ((tr1 * 13) + tr2) / 14, ((((tr1 * 13) + tr2) / 14) * 13 + tr3) / 14])


def test_calculate_hh_ll_uses_close_series_and_shift_1() -> None:
    closes = [10.0, 11.0, 9.0, 12.0, 8.0, 13.0]
    hh, ll = calculate_hh_ll(closes, lookback=3)
    assert hh == [None, None, None, 11.0, 12.0, 12.0]
    assert ll == [None, None, None, 9.0, 9.0, 8.0]


def test_first_atr_uses_high_low_when_prev_close_is_missing() -> None:
    bars = [_bar(0, 10.0, 13.5, 9.5, 12.0)]
    atr = calculate_wilder_atr(bars, period=14)
    assert atr == pytest.approx([4.0])


def test_hh_ll_shift_1_does_not_peek_current_close() -> None:
    closes = [10.0, 11.0, 9.0, 20.0]
    hh, ll = calculate_hh_ll(closes, lookback=3)
    assert hh[-1] == 11.0
    assert ll[-1] == 9.0


def test_compute_indicator_snapshot_returns_not_ready_when_warmup_is_insufficient() -> None:
    bars = [_bar(index, 100.0 + index, 101.0 + index, 99.0 + index, 100.5 + index) for index in range(12)]
    snapshot = compute_indicator_snapshot(bars)
    assert snapshot.bar_time == bars[-1].end_at
    assert snapshot.last_close == bars[-1].close
    assert snapshot.is_ready is False
    assert snapshot.warmup_complete is False
    assert snapshot.hh is None
    assert snapshot.ll is None


def test_compute_indicator_snapshot_ignores_incomplete_bars_and_becomes_ready_after_warmup() -> None:
    bars = [
        _bar(index, 100.0 + index, 101.5 + index, 99.5 + index, 100.8 + index)
        for index in range(50)
    ]
    bars.append(
        Bar(
            start_at=bars[-1].end_at,
            end_at=bars[-1].end_at + timedelta(minutes=5),
            open=999.0,
            high=999.0,
            low=999.0,
            close=999.0,
            source="test",
            is_complete=False,
        )
    )
    snapshot = compute_indicator_snapshot(bars)
    assert snapshot.bar_time == bars[49].end_at
    assert snapshot.last_close == bars[49].close
    assert snapshot.is_ready is True
    assert snapshot.warmup_complete is True
    assert snapshot.ema_fast is not None
    assert snapshot.ema_slow is not None
    assert snapshot.atr is not None
    assert snapshot.hh is not None
    assert snapshot.ll is not None
    assert snapshot.bollinger_mid is not None
    assert snapshot.donchian_entry_high is not None
    assert snapshot.donchian_exit_low is not None


def test_compute_indicator_snapshot_becomes_ready_after_min_ready_bars_threshold() -> None:
    bars = [
        _bar(index, 100.0 + index, 101.5 + index, 99.5 + index, 100.8 + index)
        for index in range(21)
    ]
    snapshot = compute_indicator_snapshot(bars, min_ready_bars=14)
    assert snapshot.is_ready is True
    assert snapshot.warmup_complete is True
    assert snapshot.ema_slow is not None
    assert snapshot.bollinger_mid is not None
