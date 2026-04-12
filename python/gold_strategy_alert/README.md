# ICBC Personal Accumulation Gold Assist

This repository is a local real-trading assist system for ICBC personal accumulation gold.

It does not place orders.
It does not promise returns.
It is designed to be usable today, with stable state handling, hard risk rules, local persistence, email alerts, and a local dashboard.

It only emits:

- `BUY_NOW`
- `SELL_NOW`
- `HOLD_POSITION`
- `WAIT_NO_TRADE`

## Current Runtime Defaults

The current default profile is `conservative`.

- `R2_PULLBACK` enabled
- `R1_BREAKOUT` disabled
- `L1_EXHAUSTION` disabled
- default execution mode is `manual_position_sync`
- actual position state can be written from the local dashboard
- only `BUY_NOW` / `SELL_NOW` send email

There is also a second built-in profile:

- `slightly_aggressive_today`

This profile enables `R1_BREAKOUT`, increases first-entry notional and daily limits, but still:

- keeps `L1_EXHAUSTION` disabled
- forbids averaging down
- forbids losing add-ons
- stops new entries after `21:50`
- forces flatten at `22:20`
- never auto-orders

## Execution Modes

Two execution modes are supported:

- `manual_position_sync`
- `signal_implies_position`

`manual_position_sync` is the default.

- strategy signals are still generated
- but actual hold/sell semantics follow the synced real position ledger
- if the user writes a real position in the dashboard, the system treats that as the source of truth for PnL, hold time, and sell decisions

`signal_implies_position` is also supported.

- once `BUY_NOW` is emitted, the internal ledger is immediately treated as filled
- the default internal fill model is `signal_bar_close`
- this is an internal simulation rule for replay and state-machine consistency

## Mode A Execution Model

This system supports **Mode A** (`signal-implies-position`) as an optional execution mode.

- once `BUY_NOW` is emitted, the internal ledger is immediately treated as filled
- the default internal fill model is `signal_bar_close`
- `entry_price` is the confirming bar close used by the engine
- this is an internal simulation rule for state-machine consistency and replay consistency
- it does **not** claim that the user's real manual fill must equal that internal price

If a future version needs "user confirms execution before position creation", it must use a different state machine instead of mixing that behavior into Mode A.

## Important Default-Parameter Disclaimer

The default parameters in this repository are classic long-horizon research defaults:

- ATR `(14, Wilder)`
- Bollinger Bands `(20, 2)`
- Donchian entry `20`
- Donchian exit `10`
- EMA fast/slow `20/50`

These values are research starting points only.
They are **not claimed to be optimal** for ICBC personal accumulation gold.

The project keeps visible entry points for:

- replay backtesting
- walk-forward research
- parameter sensitivity analysis

## Triggering Principles

- `confidence` is retained for explanation, audit, logging, and JSON output only.
- `confidence` is not a primary trade trigger.
- `BUY_NOW` requires both:
  - a hard pattern match
  - an explicit `RiskGate` pass

The default entry priority is:

1. `R2_PULLBACK`
2. `R1_BREAKOUT`
3. `L1_EXHAUSTION`

The default exit priority is:

1. structural stop
2. Donchian10 failure
3. structure invalidation back below EMA20 / Bollinger mid
4. `22:20` force flatten

## Removed From The Default Logic

The production default logic no longer relies on the old magic-threshold family such as:

- `1.4 * ATR` breakout multipliers
- percentage chase filters like `0.10%`
- ATR stop shortcuts like `0.9 * ATR`
- fixed segmented take-profit rules like `1.6R ~ 2.2R`
- confidence thresholds like `0.78 / 0.82 / 0.88`

## Local Dashboard

The local dashboard exposes:

- current runtime state
- current signal summary
- actual position ledger
- profile switching
- execution mode switching
- pause/resume new entries
- force flatten request
- cooldown clearing
- direct position sync / adjust / clear

## Current Scope

Implemented now:

- live ICBC + SGE collection with fallback
- SQLite-first persistence
- 1m sampling and completed 5m bar decisions
- 3m structural pattern checks for R2 / R1 / L1
- fee-aware `RiskGate`
- action-shaped decision JSON output
- buy/sell-only email notifications by default
- local dashboard and JSON API
- actual position sync ledger
- replay and signal inspection entry points

Research hooks kept visible but not fully built out yet:

- walk-forward harness
- parameter sensitivity harness
- parquet archival and full research workflows

## Run

Direct script path:

```powershell
& "C:\Users\arcfever\Documents\New project\runtime\python_embed\py312\python.exe" `
  "C:\Users\arcfever\Documents\New project\python\gold_strategy_alert\main.py"
```

CLI path:

```powershell
Set-Location "C:\Users\arcfever\Documents\New project\python\gold_strategy_alert"
& "C:\Users\arcfever\Documents\New project\runtime\python_embed\py312\python.exe" ".\cli.py" run --once
```

## CLI

```powershell
python .\cli.py run --config config\config.example.yaml
python .\cli.py run --config config\config.example.yaml --once
python .\cli.py replay-backtest --config config\config.example.yaml --input sample_data\sample_ticks.csv --fast
python .\cli.py signal-replay --config config\config.example.yaml --signal-id 1
python .\cli.py walk-forward --config config\config.example.yaml
python .\cli.py parameter-scan --config config\config.example.yaml --input sample_data\sample_ticks.csv
python .\cli.py show-config --config config\config.example.yaml
```

`walk-forward` and `parameter-scan` are intentionally retained as explicit research entry points even though the full research harness is still pending.

## Config

See:

- [config/config.example.yaml](C:/Users/arcfever/Documents/New%20project/python/gold_strategy_alert/config/config.example.yaml)

Important defaults:

- classic indicator defaults: `ATR14`, `Bollinger(20,2)`, `Donchian20/10`, `EMA20/50`
- official trading window `09:10-22:30`
- no new entries after `21:50`
- force flatten at `22:20`
- `conservative` and `slightly_aggressive_today` profiles are both built in
- no averaging down
- current version aims to be usable today, not to claim optimal parameters or stable profitability

## Persistence

SQLite records:

- runtime state
- minute prices
- 5m bars
- events
- notifications
- structured decisions

This makes it possible to inspect:

- why a buy happened
- why a buy did not happen
- whether a notification was deduped
- what the latest decision JSON looked like

## Tests

Run:

```powershell
& "C:\Users\arcfever\Documents\New project\runtime\python_embed\py312\python.exe" -m pytest `
  "C:\Users\arcfever\Documents\New project\python\gold_strategy_alert\tests" -q
```

## Docs

- [docs/00_constraints.md](C:/Users/arcfever/Documents/New%20project/python/gold_strategy_alert/docs/00_constraints.md)
- [docs/01_strategy_spec.md](C:/Users/arcfever/Documents/New%20project/python/gold_strategy_alert/docs/01_strategy_spec.md)
- [docs/02_architecture.md](C:/Users/arcfever/Documents/New%20project/python/gold_strategy_alert/docs/02_architecture.md)
- [docs/03_acceptance_checklist.md](C:/Users/arcfever/Documents/New%20project/python/gold_strategy_alert/docs/03_acceptance_checklist.md)
