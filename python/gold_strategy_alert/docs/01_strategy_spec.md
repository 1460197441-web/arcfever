# Strategy Spec

## Default Parameter Baseline

Classic defaults used by default:

- ATR `(14, Wilder)`
- Bollinger Bands `(20, 2)`
- Donchian entry `20`
- Donchian exit `10`
- EMA fast/slow `20/50`

These defaults are classic research baselines only.
They are not presented as the optimal parameters for ICBC personal accumulation gold.

## Trigger Roles

- `confidence` is kept for explanation and audit.
- `confidence` is not the main trigger threshold.
- Final trade permission comes from:
  - hard boolean pattern conditions
  - explicit `RiskGate`

## Mode A Ledger Behavior

- the system uses Mode A (`signal-implies-position`)
- once `BUY_NOW` is emitted, an internal position is recorded immediately
- the default fill model is `signal_bar_close`
- `entry_price` is therefore the confirming bar close used by the engine
- `confidence` does not upgrade or downgrade this rule
- `SELL_NOW` is only legal when that internal position exists with valid entry fields

## LIVE_TODAY_V1 Defaults

- the default live profile is fixed for "run today" usage
- `R2_PULLBACK` and `R1_BREAKOUT` are enabled
- `L1_EXHAUSTION` is disabled
- first-entry notional defaults to `2000 CNY`
- max batches defaults to `1`
- daily realized profit lock defaults to `20 CNY`

## Entry Priority

1. `R2_PULLBACK`
2. `R1_BREAKOUT`
3. `L1_EXHAUSTION`

## R2_PULLBACK

Required:

- regime in `{TREND_UP, PULLBACK_READY}`
- trend already confirmed by EMA20/50 structure
- recent 3m bar touched EMA20 structurally
- latest 3m close reclaimed EMA20
- `RiskGate` passed

Default structural touch definition:

- `bar.low <= EMA20 <= bar.high`

No blind catching is allowed.
R2 is the only mode allowed to add a second batch, and only when the existing position already has fee-adjusted floating profit.

## R1_BREAKOUT

Required:

- regime in `{BREAKOUT_READY, TREND_UP}`
- 3m close breaks above Donchian20 upper
- Bollinger bandwidth expansion is confirmed by boolean comparison
- `RiskGate` passed

Default bandwidth expansion logic:

- current bandwidth > previous bandwidth

R1 uses close confirmation only.

## L1_EXHAUSTION

Required:

- regime == `EXHAUSTION_REVERSAL_READY`
- prior price action broke below Bollinger lower band
- later 3m close re-entered the band
- `RiskGate` passed

L1 is a low-frequency mean-reversion probe:

- one batch only
- no averaging down
- lower priority than R2 and R1

## Exit Logic

Default exits do not use fixed `R` multiples.
Priority is:

1. structural stop
2. Donchian10 failure
3. EMA20 / Bollinger-mid structure invalidation
4. `22:20` force flatten

While holding, `SELL_NOW` is always checked before any new buy logic.
