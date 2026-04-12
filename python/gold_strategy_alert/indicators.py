"""Indicator contracts for the 5-minute strategy series."""

from __future__ import annotations

from collections.abc import Sequence
from math import sqrt

from models import Bar, IndicatorSnapshot


def calculate_ema(values: Sequence[float], period: int) -> list[float | None]:
    """Return EMA series aligned to input values."""
    if period <= 0:
        raise ValueError("period must be positive")
    if not values:
        return []

    alpha = 2 / (period + 1)
    result: list[float | None] = [float(values[0])]
    for value in values[1:]:
        previous = result[-1]
        assert previous is not None
        result.append((float(value) * alpha) + (previous * (1 - alpha)))
    return result


def calculate_wilder_atr(bars: Sequence[Bar], period: int = 14) -> list[float | None]:
    """Return Wilder ATR series aligned to input bars."""
    if period <= 0:
        raise ValueError("period must be positive")
    if not bars:
        return []

    true_ranges: list[float] = []
    previous_close: float | None = None
    for bar in bars:
        high_low = bar.high - bar.low
        if previous_close is None:
            tr = high_low
        else:
            tr = max(high_low, abs(bar.high - previous_close), abs(bar.low - previous_close))
        true_ranges.append(tr)
        previous_close = bar.close

    atr_values: list[float | None] = []
    for index, tr in enumerate(true_ranges):
        if index == 0:
            atr_values.append(tr)
            continue
        previous_atr = atr_values[-1]
        assert previous_atr is not None
        atr_values.append(((previous_atr * (period - 1)) + tr) / period)
    return atr_values


def calculate_hh_ll(
    closes: Sequence[float],
    lookback: int = 12,
) -> tuple[list[float | None], list[float | None]]:
    """Return HH and LL series over closes with shift(1)."""
    if lookback <= 0:
        raise ValueError("lookback must be positive")

    hh: list[float | None] = []
    ll: list[float | None] = []
    for index in range(len(closes)):
        if index < lookback:
            hh.append(None)
            ll.append(None)
            continue
        window = [float(value) for value in closes[index - lookback : index]]
        hh.append(max(window))
        ll.append(min(window))
    return hh, ll


def calculate_bollinger_bands(
    values: Sequence[float],
    period: int = 20,
    stddev: float = 2.0,
) -> tuple[list[float | None], list[float | None], list[float | None], list[float | None]]:
    if period <= 0:
        raise ValueError("period must be positive")
    mid: list[float | None] = []
    upper: list[float | None] = []
    lower: list[float | None] = []
    bandwidth: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < period:
            mid.append(None)
            upper.append(None)
            lower.append(None)
            bandwidth.append(None)
            continue
        window = [float(item) for item in values[index + 1 - period : index + 1]]
        average = sum(window) / period
        variance = sum((item - average) ** 2 for item in window) / period
        std = sqrt(variance)
        up = average + stddev * std
        low = average - stddev * std
        mid.append(average)
        upper.append(up)
        lower.append(low)
        bandwidth.append((up - low) / average if average else None)
    return mid, upper, lower, bandwidth


def calculate_donchian_channels(
    bars: Sequence[Bar],
    period: int,
) -> tuple[list[float | None], list[float | None]]:
    if period <= 0:
        raise ValueError("period must be positive")
    upper: list[float | None] = []
    lower: list[float | None] = []
    for index in range(len(bars)):
        if index < period:
            upper.append(None)
            lower.append(None)
            continue
        window = bars[index - period : index]
        upper.append(max(bar.high for bar in window))
        lower.append(min(bar.low for bar in window))
    return upper, lower


def compute_indicator_snapshot(
    bars: Sequence[Bar],
    *,
    min_ready_bars: int = 50,
    ema_fast_period: int = 20,
    ema_slow_period: int = 50,
    atr_period: int = 14,
    breakout_lookback_bars: int = 20,
    bollinger_period: int = 20,
    bollinger_stddev: float = 2.0,
    donchian_exit_period: int = 10,
) -> IndicatorSnapshot:
    """Compute EMA, ATR, HH, and LL from 5-minute bars."""
    if min_ready_bars <= 0:
        raise ValueError("min_ready_bars must be positive")

    completed_bars = [bar for bar in bars if bar.is_complete]
    if not completed_bars:
        return IndicatorSnapshot(is_ready=False, warmup_complete=False)

    closes = [bar.close for bar in completed_bars]
    ema_fast_series = calculate_ema(closes, period=ema_fast_period)
    ema_slow_series = calculate_ema(closes, period=ema_slow_period)
    atr_series = calculate_wilder_atr(completed_bars, period=atr_period)
    hh_series, ll_series = calculate_hh_ll(closes, lookback=breakout_lookback_bars)
    boll_mid, boll_upper, boll_lower, boll_bandwidth = calculate_bollinger_bands(
        closes,
        period=bollinger_period,
        stddev=bollinger_stddev,
    )
    donchian_entry_high, donchian_entry_low = calculate_donchian_channels(
        completed_bars,
        period=breakout_lookback_bars,
    )
    donchian_exit_high, donchian_exit_low = calculate_donchian_channels(
        completed_bars,
        period=donchian_exit_period,
    )

    last_bar = completed_bars[-1]
    snapshot = IndicatorSnapshot(
        bar_time=last_bar.end_at,
        close_5m=last_bar.close,
        last_close=last_bar.close,
        ema_fast=ema_fast_series[-1],
        ema_slow=ema_slow_series[-1],
        atr=atr_series[-1],
        hh=hh_series[-1],
        ll=ll_series[-1],
        bollinger_mid=boll_mid[-1],
        bollinger_upper=boll_upper[-1],
        bollinger_lower=boll_lower[-1],
        bollinger_bandwidth=boll_bandwidth[-1],
        donchian_entry_high=donchian_entry_high[-1],
        donchian_entry_low=donchian_entry_low[-1],
        donchian_exit_high=donchian_exit_high[-1],
        donchian_exit_low=donchian_exit_low[-1],
    )

    if snapshot.hh is None and len(completed_bars) >= breakout_lookback_bars:
        fallback_window = [float(value) for value in closes[-breakout_lookback_bars:]]
        snapshot.hh = max(fallback_window)
        snapshot.ll = min(fallback_window)

    warmup_complete = (
        len(completed_bars) >= max(min_ready_bars, breakout_lookback_bars)
        and snapshot.atr is not None
        and snapshot.hh is not None
        and snapshot.ll is not None
        and snapshot.ema_fast is not None
        and snapshot.ema_slow is not None
        and snapshot.bollinger_mid is not None
        and snapshot.donchian_entry_high is not None
        and snapshot.donchian_exit_low is not None
    )
    snapshot.warmup_complete = bool(warmup_complete)
    snapshot.is_ready = bool(warmup_complete)
    return snapshot
