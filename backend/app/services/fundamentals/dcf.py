"""
DCF Calculator (Step 10)
-------------------------
Calculates intrinsic value per share using discounted cash flow analysis.

Model:
  1. Pull last 3-5 years of annual FCF from fundamentals_summary
  2. Calculate historical FCF CAGR
  3. Project FCF for 5 years using growth rate
  4. Calculate terminal value using Gordon Growth Model
  5. Discount all cash flows at WACC
  6. Divide by shares outstanding to get intrinsic value per share
  7. Generate sensitivity table (growth rate vs discount rate)

Inputs (auto from DB):
  - Historical FCF (3-5 years)
  - Shares outstanding
  - Total debt
  - Cash

Inputs (market or assumed):
  - Current stock price (from Alpaca)
  - Risk-free rate (10Y Treasury — default 4.5%)
  - Market risk premium (default 5.5%)
  - Beta (default 1.0 — can be fetched later)
  - Terminal growth rate (default 2.5% — long run GDP growth)
"""

import logging
import math
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DCFInputs:
    ticker: str
    # Historical FCF — list of (year, fcf) tuples, oldest first
    historical_fcf: list[tuple[str, float]]
    shares_outstanding: float
    total_debt: float
    cash: float
    current_price: float
    # WACC components
    risk_free_rate: float = 0.045      # 10Y Treasury yield
    market_risk_premium: float = 0.055  # Equity risk premium
    beta: float = 1.0                   # Stock beta
    debt_cost: float = 0.04            # Pre-tax cost of debt
    tax_rate: float = 0.21             # Corporate tax rate
    # Projection assumptions
    projection_years: int = 5
    terminal_growth_rate: float = 0.025  # Long-run GDP growth


@dataclass
class DCFResult:
    ticker: str
    # Inputs summary
    current_price: float
    shares_outstanding: float
    # WACC
    cost_of_equity: float
    wacc: float
    # FCF projection
    base_fcf: float
    fcf_growth_rate: float
    projected_fcf: list[float]
    # Valuation
    terminal_value: float
    pv_projected_fcf: float
    pv_terminal_value: float
    enterprise_value: float
    equity_value: float
    intrinsic_value_per_share: float
    # Verdict
    upside_pct: float
    margin_of_safety: float
    verdict: str
    # Sensitivity table
    sensitivity: list[dict]


def calculate_cagr(values: list[float]) -> float:
    """
    Calculate Compound Annual Growth Rate from a list of values.
    Returns annualized growth rate.
    """
    if len(values) < 2:
        return 0.10  # Default 10% if not enough data

    # Filter out None and zero values
    valid = [v for v in values if v and v > 0]
    if len(valid) < 2:
        return 0.10

    start = valid[0]
    end = valid[-1]
    years = len(valid) - 1

    if start <= 0:
        return 0.10

    cagr = (end / start) ** (1 / years) - 1

    # Cap growth rate — be conservative
    # Never project more than 25% or less than -10%
    return max(-0.10, min(0.25, cagr))


def calculate_wacc(inputs: DCFInputs, equity_value: float, debt_value: float) -> float:
    """
    Calculate Weighted Average Cost of Capital (WACC).
    WACC = (E/V) * Re + (D/V) * Rd * (1 - Tax)
    where Re = cost of equity (CAPM), Rd = cost of debt
    """
    total_capital = equity_value + debt_value
    if total_capital <= 0:
        total_capital = equity_value if equity_value > 0 else 1

    # Cost of equity via CAPM
    # Re = Rf + Beta * (Rm - Rf)
    cost_of_equity = (
        inputs.risk_free_rate +
        inputs.beta * inputs.market_risk_premium
    )

    # Weight of equity and debt
    weight_equity = equity_value / total_capital
    weight_debt = debt_value / total_capital

    # After-tax cost of debt
    after_tax_debt_cost = inputs.debt_cost * (1 - inputs.tax_rate)

    wacc = (weight_equity * cost_of_equity) + (weight_debt * after_tax_debt_cost)

    # WACC sanity check — between 5% and 20%
    return max(0.05, min(0.20, wacc))


def project_fcf(base_fcf: float, growth_rate: float, years: int) -> list[float]:
    """Project FCF for N years using constant growth rate."""
    projected = []
    fcf = base_fcf
    for _ in range(years):
        fcf = fcf * (1 + growth_rate)
        projected.append(fcf)
    return projected


def calculate_terminal_value(
    final_year_fcf: float,
    terminal_growth_rate: float,
    wacc: float,
) -> float:
    """
    Gordon Growth Model terminal value.
    TV = FCF_n * (1 + g) / (WACC - g)
    """
    if wacc <= terminal_growth_rate:
        # WACC must be greater than terminal growth
        wacc = terminal_growth_rate + 0.02

    return final_year_fcf * (1 + terminal_growth_rate) / (wacc - terminal_growth_rate)


def discount_cash_flows(cash_flows: list[float], wacc: float) -> float:
    """
    Discount a series of cash flows to present value.
    PV = sum(CF_t / (1 + WACC)^t)
    """
    pv = 0.0
    for t, cf in enumerate(cash_flows, 1):
        pv += cf / ((1 + wacc) ** t)
    return pv


def calculate_dcf(inputs: DCFInputs) -> DCFResult:
    """
    Run the full DCF calculation.
    Returns DCFResult with intrinsic value and sensitivity table.
    """
    # Extract historical FCF values
    historical_values = [fcf for _, fcf in inputs.historical_fcf if fcf and fcf > 0]

    # Base FCF — use most recent year
    if not historical_values:
        raise ValueError(f"No valid FCF data for {inputs.ticker}")

    base_fcf = historical_values[-1]

    # FCF growth rate — historical CAGR
    fcf_growth_rate = calculate_cagr(historical_values)

    # Use current market cap as equity value for WACC
    market_cap = inputs.current_price * inputs.shares_outstanding
    debt_value = inputs.total_debt

    # Calculate WACC
    cost_of_equity = inputs.risk_free_rate + inputs.beta * inputs.market_risk_premium
    wacc = calculate_wacc(inputs, market_cap, debt_value)

    # Project FCF for N years
    projected_fcf = project_fcf(base_fcf, fcf_growth_rate, inputs.projection_years)

    # Terminal value
    terminal_value = calculate_terminal_value(
        projected_fcf[-1],
        inputs.terminal_growth_rate,
        wacc,
    )

    # Present values
    pv_projected = discount_cash_flows(projected_fcf, wacc)
    pv_terminal = terminal_value / ((1 + wacc) ** inputs.projection_years)

    # Enterprise value
    enterprise_value = pv_projected + pv_terminal

    # Equity value = EV - debt + cash
    equity_value = enterprise_value - inputs.total_debt + inputs.cash

    # Intrinsic value per share
    if inputs.shares_outstanding <= 0:
        raise ValueError("Invalid shares outstanding")

    intrinsic_value = equity_value / inputs.shares_outstanding

    # Upside/downside
    upside_pct = (intrinsic_value - inputs.current_price) / inputs.current_price

    # Margin of safety (how much buffer before overvalued)
    margin_of_safety = 1 - (inputs.current_price / intrinsic_value) if intrinsic_value > 0 else -1

    # Verdict
    if upside_pct > 0.20:
        verdict = "UNDERVALUED"
    elif upside_pct > 0.05:
        verdict = "SLIGHTLY UNDERVALUED"
    elif upside_pct > -0.05:
        verdict = "FAIRLY VALUED"
    elif upside_pct > -0.20:
        verdict = "SLIGHTLY OVERVALUED"
    else:
        verdict = "OVERVALUED"

    # Sensitivity table
    # Vary growth rate ±2% and discount rate ±2%
    sensitivity = []
    growth_range = [
        fcf_growth_rate - 0.04,
        fcf_growth_rate - 0.02,
        fcf_growth_rate,
        fcf_growth_rate + 0.02,
        fcf_growth_rate + 0.04,
    ]
    wacc_range = [
        wacc - 0.02,
        wacc - 0.01,
        wacc,
        wacc + 0.01,
        wacc + 0.02,
    ]

    for g in growth_range:
        for w in wacc_range:
            if w <= inputs.terminal_growth_rate:
                continue
            try:
                proj = project_fcf(base_fcf, g, inputs.projection_years)
                tv = calculate_terminal_value(proj[-1], inputs.terminal_growth_rate, w)
                pv_p = discount_cash_flows(proj, w)
                pv_t = tv / ((1 + w) ** inputs.projection_years)
                ev = pv_p + pv_t
                eq = ev - inputs.total_debt + inputs.cash
                iv = eq / inputs.shares_outstanding
                sensitivity.append({
                    "growth_rate": round(g, 4),
                    "wacc": round(w, 4),
                    "intrinsic_value": round(iv, 2),
                    "upside_pct": round((iv - inputs.current_price) / inputs.current_price, 4),
                })
            except Exception:
                continue

    return DCFResult(
        ticker=inputs.ticker,
        current_price=inputs.current_price,
        shares_outstanding=inputs.shares_outstanding,
        cost_of_equity=round(cost_of_equity, 4),
        wacc=round(wacc, 4),
        base_fcf=base_fcf,
        fcf_growth_rate=round(fcf_growth_rate, 4),
        projected_fcf=[round(f, 0) for f in projected_fcf],
        terminal_value=round(terminal_value, 0),
        pv_projected_fcf=round(pv_projected, 0),
        pv_terminal_value=round(pv_terminal, 0),
        enterprise_value=round(enterprise_value, 0),
        equity_value=round(equity_value, 0),
        intrinsic_value_per_share=round(intrinsic_value, 2),
        upside_pct=round(upside_pct, 4),
        margin_of_safety=round(margin_of_safety, 4),
        verdict=verdict,
        sensitivity=sensitivity,
    )


def dcf_result_to_dict(result: DCFResult) -> dict:
    """Convert DCFResult to JSON-serializable dict."""
    return {
        "ticker": result.ticker,
        "current_price": result.current_price,
        "intrinsic_value_per_share": result.intrinsic_value_per_share,
        "upside_pct": result.upside_pct,
        "margin_of_safety": result.margin_of_safety,
        "verdict": result.verdict,
        "wacc": result.wacc,
        "cost_of_equity": result.cost_of_equity,
        "fcf_growth_rate": result.fcf_growth_rate,
        "base_fcf": result.base_fcf,
        "projected_fcf": result.projected_fcf,
        "terminal_value": result.terminal_value,
        "pv_projected_fcf": result.pv_projected_fcf,
        "pv_terminal_value": result.pv_terminal_value,
        "enterprise_value": result.enterprise_value,
        "equity_value": result.equity_value,
        "shares_outstanding": result.shares_outstanding,
        "sensitivity": result.sensitivity,
    }


if __name__ == "__main__":
    # Test with AAPL hardcoded values
    inputs = DCFInputs(
        ticker="AAPL",
        historical_fcf=[
            ("2021", 92953000000),
            ("2022", 111443000000),
            ("2023", 99584000000),
            ("2024", 108807000000),
            ("2025", 98800000000),
        ],
        shares_outstanding=14608963000,
        total_debt=84297000000,
        cash=39544000000,
        current_price=335.73,
        beta=1.2,
    )

    result = calculate_dcf(inputs)
    d = dcf_result_to_dict(result)

    print(f"\n{'='*50}")
    print(f"DCF Analysis — {result.ticker}")
    print(f"{'='*50}")
    print(f"Current Price:     ${result.current_price:.2f}")
    print(f"Intrinsic Value:   ${result.intrinsic_value_per_share:.2f}")
    print(f"Upside/Downside:   {result.upside_pct*100:.1f}%")
    print(f"Verdict:           {result.verdict}")
    print(f"")
    print(f"WACC:              {result.wacc*100:.2f}%")
    print(f"Cost of Equity:    {result.cost_of_equity*100:.2f}%")
    print(f"FCF Growth Rate:   {result.fcf_growth_rate*100:.1f}%")
    print(f"")
    print(f"Base FCF:          ${result.base_fcf/1e9:.1f}B")
    print(f"Projected FCF:     {[f'${f/1e9:.1f}B' for f in result.projected_fcf]}")
    print(f"Terminal Value:    ${result.terminal_value/1e9:.1f}B")
    print(f"PV Projected FCF:  ${result.pv_projected_fcf/1e9:.1f}B")
    print(f"PV Terminal Value: ${result.pv_terminal_value/1e9:.1f}B")
    print(f"Enterprise Value:  ${result.enterprise_value/1e9:.1f}B")
    print(f"Equity Value:      ${result.equity_value/1e9:.1f}B")
    print(f"")
    print(f"Sensitivity Table (Intrinsic Value per Share):")
    print(f"{'Growth':>8} {'WACC':>8} {'IV':>8} {'Upside':>8}")
    for s in result.sensitivity:
        print(
            f"  {s['growth_rate']*100:.1f}%"
            f"  {s['wacc']*100:.1f}%"
            f"  ${s['intrinsic_value']:.2f}"
            f"  {s['upside_pct']*100:.1f}%"
        )