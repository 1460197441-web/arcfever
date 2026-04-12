"""Fee-aware risk gate for long-only decision filtering."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, getcontext

from config import AppConfig
from models import RiskGateResult, StrategyMode, StrategyRuntimeState


getcontext().prec = 28


def _d(value: float | int | str) -> Decimal:
    return Decimal(str(value))


def _q(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def evaluate_long_risk_gate(
    *,
    entry_price: float,
    stop_price: float | None,
    atr_value: float | None = None,
    config: AppConfig,
    state: StrategyRuntimeState,
    strategy_mode: StrategyMode,
) -> RiskGateResult:
    notional_yuan = _d(config.risk.first_entry_yuan)
    buy_fee_rate = _d(config.fees.buy_fee_rate)
    sell_fee_rate = _d(config.fees.sell_fee_rate)
    max_trade_idea_loss_yuan = _d(config.risk.max_trade_idea_loss_yuan)
    entry = _d(entry_price)

    fee_floor = notional_yuan * (Decimal("1") - (Decimal("1") - buy_fee_rate) * (Decimal("1") - sell_fee_rate))
    estimated_grams = notional_yuan * (Decimal("1") - buy_fee_rate) / entry
    max_price_risk_budget = max_trade_idea_loss_yuan - fee_floor
    if estimated_grams <= 0 or max_price_risk_budget <= 0:
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=None,
            estimated_grams=max(_q(estimated_grams), 0.0),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=max(_q(max_price_risk_budget), 0.0),
            max_stop_distance_per_gram=0.0,
            risk_amount_yuan=0.0,
            notional_yuan=_q(notional_yuan),
            reason="Invalid risk budget after fees.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    max_stop_distance_per_gram = max_price_risk_budget / estimated_grams

    if stop_price is None:
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=None,
            stop_distance_per_gram=None,
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=0.0,
            notional_yuan=_q(notional_yuan),
            reason="Stop price is required before entry.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    stop = _d(stop_price)
    stop_distance = entry - stop
    if stop_distance <= 0:
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=0.0,
            notional_yuan=_q(notional_yuan),
            reason="Stop must be below entry for long-only trades.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    risk_amount = stop_distance * estimated_grams + fee_floor
    if atr_value is not None and stop_distance > _d(atr_value):
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=_q(risk_amount),
            notional_yuan=_q(notional_yuan),
            reason="Structure stop exceeds ATR14 volatility cap.",
            atr_cap_per_gram=_q(_d(atr_value)),
        )
    if stop_distance > max_stop_distance_per_gram:
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=_q(risk_amount),
            notional_yuan=_q(notional_yuan),
            reason="Stop distance exceeds max idea loss budget.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    if state.consecutive_loss_trades >= config.risk.consecutive_losses_cooldown:
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=_q(risk_amount),
            notional_yuan=_q(notional_yuan),
            reason="Blocked by consecutive-loss cooldown.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    if state.paused_new_entries:
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=_q(risk_amount),
            notional_yuan=_q(notional_yuan),
            reason="Operator paused new entries.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    if state.daily_realized_pnl_yuan <= -float(config.risk.daily_loss_stop_yuan):
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=_q(risk_amount),
            notional_yuan=_q(notional_yuan),
            reason="Blocked by daily loss stop.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    if strategy_mode == StrategyMode.L1_EXHAUSTION and state.batches_used >= 1:
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=_q(risk_amount),
            notional_yuan=_q(notional_yuan),
            reason="L1 only allows one probe entry.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    if state.entries_today_count >= config.risk.max_new_entries_per_day:
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=_q(risk_amount),
            notional_yuan=_q(notional_yuan),
            reason="Daily entry limit reached.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    if state.batches_used >= config.risk.max_batches:
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=_q(risk_amount),
            notional_yuan=_q(notional_yuan),
            reason="Max batches per trade idea reached.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    if state.position.has_position and strategy_mode != StrategyMode.R2_PULLBACK:
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=_q(risk_amount),
            notional_yuan=_q(notional_yuan),
            reason="Only R2 pullback entries may add a second batch.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    if (
        state.position.has_position
        and not config.risk.allow_average_down
        and state.position.entry_price is not None
        and entry_price < state.position.entry_price
    ):
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=_q(risk_amount),
            notional_yuan=_q(notional_yuan),
            reason="Averaging down is forbidden.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    if (
        state.position.has_position
        and not config.risk.allow_losing_add
        and state.position.entry_price is not None
        and entry_price <= state.position.entry_price * config.fees.fee_break_even_multiplier
    ):
        return RiskGateResult(
            allowed=False,
            entry_price=entry_price,
            stop_price=stop_price,
            stop_distance_per_gram=_q(stop_distance),
            estimated_grams=_q(estimated_grams),
            fee_floor_yuan=_q(fee_floor),
            max_price_risk_budget_yuan=_q(max_price_risk_budget),
            max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
            risk_amount_yuan=_q(risk_amount),
            notional_yuan=_q(notional_yuan),
            reason="Add-on entries require an existing fee-adjusted floating profit.",
            atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
        )

    return RiskGateResult(
        allowed=True,
        entry_price=entry_price,
        stop_price=stop_price,
        stop_distance_per_gram=_q(stop_distance),
        estimated_grams=_q(estimated_grams),
        fee_floor_yuan=_q(fee_floor),
        max_price_risk_budget_yuan=_q(max_price_risk_budget),
        max_stop_distance_per_gram=_q(max_stop_distance_per_gram),
        risk_amount_yuan=_q(risk_amount),
        notional_yuan=_q(notional_yuan),
        reason="Risk gate passed.",
        atr_cap_per_gram=_q(_d(atr_value)) if atr_value is not None else None,
    )
