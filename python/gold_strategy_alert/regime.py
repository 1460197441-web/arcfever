"""Lightweight regime classification aligned with the task-book semantics."""

from __future__ import annotations

from collections.abc import Sequence

from bar_aggregator import aggregate_minute_ticks_to_bars
from indicators import calculate_bollinger_bands, calculate_donchian_channels, calculate_ema
from models import Bar, IndicatorSnapshot, MarketRegime, PriceTick


def classify_regime(
    completed_bars: Sequence[Bar],
    indicator_snapshot: IndicatorSnapshot,
    recent_minute_ticks: Sequence[PriceTick],
) -> tuple[MarketRegime, float]:
    if len(completed_bars) < 20 or indicator_snapshot.close_5m is None:
        return MarketRegime.NOISE, 0.15

    closes_5m = [bar.close for bar in completed_bars]
    ema20 = calculate_ema(closes_5m, 20)
    ema50 = calculate_ema(closes_5m, 50)
    if len(ema20) < 2 or len(ema50) < 2 or ema50[-1] is None or ema50[-2] is None:
        return MarketRegime.NOISE, 0.15

    ema20_now = ema20[-1]
    ema20_prev = ema20[-2]
    ema50_now = ema50[-1]
    ema50_prev = ema50[-2]
    assert ema20_now is not None
    assert ema20_prev is not None
    assert ema50_now is not None
    assert ema50_prev is not None

    trend_up = ema20_now > ema50_now and ema20_now > ema20_prev and ema50_now >= ema50_prev
    trend_down = ema20_now < ema50_now and ema20_now < ema20_prev and ema50_now <= ema50_prev

    close = indicator_snapshot.close_5m
    bars_3m = aggregate_minute_ticks_to_bars(recent_minute_ticks, bar_minutes=3, allow_incomplete_window=False)
    bars_1m = aggregate_minute_ticks_to_bars(recent_minute_ticks, bar_minutes=1, allow_incomplete_window=False)

    if trend_up and bars_3m:
        last_3m = bars_3m[-1]
        touched_ema20 = last_3m.low <= ema20_now <= last_3m.high
        reclaimed_ema20 = last_3m.close >= ema20_now
        if touched_ema20 and reclaimed_ema20:
            return MarketRegime.PULLBACK_READY, 0.81

        if len(bars_3m) >= 21:
            donchian_upper, _ = calculate_donchian_channels(bars_3m, 20)
            _, _, _, bandwidth = calculate_bollinger_bands([bar.close for bar in bars_3m], 20, 2.0)
            upper_now = donchian_upper[-1]
            bw_now = bandwidth[-1]
            bw_prev = bandwidth[-2] if len(bandwidth) >= 2 else None
            if upper_now is not None and bw_now is not None and bw_prev is not None:
                bandwidth_expanding = bw_now > bw_prev
                if last_3m.close > upper_now and bandwidth_expanding:
                    return MarketRegime.BREAKOUT_READY, 0.84

        return MarketRegime.TREND_UP, 0.72

    if trend_down and bars_3m:
        closes_3m = [bar.close for bar in bars_3m]
        _, _, lower_band, _ = calculate_bollinger_bands(closes_3m, 20, 2.0)
        if len(bars_3m) >= 2 and lower_band[-1] is not None and lower_band[-2] is not None:
            prev_close = bars_3m[-2].close
            last_close = bars_3m[-1].close
            if prev_close < lower_band[-2] and last_close >= lower_band[-1]:
                return MarketRegime.EXHAUSTION_REVERSAL_READY, 0.66
        return MarketRegime.TREND_DOWN, 0.72

    if bars_1m:
        recent_prices = [bar.close for bar in bars_1m[-8:]]
        if max(recent_prices) - min(recent_prices) <= max(close * 0.0008, 0.30):
            return MarketRegime.NOISE, 0.25

    return MarketRegime.NOISE, 0.35
