# Architecture

The implementation keeps the existing package layout and aligns it to the supplement with these responsibilities:

- collectors:
  - fetch raw ICBC / SGE pages
  - parse quote fields
- bar aggregator:
  - build completed 5m bars from 1m prices
- indicators:
  - produce a stable snapshot with EMA20/50, ATR14, Bollinger20(2), and Donchian20/10
- regime:
  - classify `TREND_UP`, `PULLBACK_READY`, `BREAKOUT_READY`, or `EXHAUSTION_REVERSAL_READY`
- strategy:
  - evaluate `SELL_NOW` before any new entry
  - choose between `R2`, `R1`, and `L1`
  - emit action-shaped decision output
  - record positions in Mode A on the same transaction as `BUY_NOW`
- risk gate:
  - enforce stop-required, fee-aware, max-loss, batch-limit, and no-average-down rules
- state store:
  - persist runtime state, events, bars, prices, notifications, and decisions
- notifier:
  - send actionable buy/sell alerts by default
  - keep `confidence` in the output for explanation only

Research-oriented entry points are intentionally still visible at the package boundary:

- replay backtest
- walk-forward
- parameter sensitivity scan
