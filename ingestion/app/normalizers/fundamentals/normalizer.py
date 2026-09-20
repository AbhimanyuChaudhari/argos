"""
Fundamentals Normalizer (Step 5)
---------------------------------
Takes parsed period dicts from the XBRL parser and:
1. Calculates derived metrics (margins, ratios, FCF)
2. Validates values (removes obviously wrong data)
3. Returns clean fundamentals_summary rows ready for DB insert
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Safe division — returns None instead of dividing by zero."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return numerator / denominator


def safe_round(value: Optional[float], decimals: int = 4) -> Optional[float]:
    if value is None:
        return None
    return round(value, decimals)


def normalize_period(parsed: dict) -> Optional[dict]:
    """
    Take a single parsed period dict and return a clean
    fundamentals_summary row ready for DB upsert.
    Returns None if the period has too little data to be useful.
    """
    ticker = parsed.get("ticker")
    period_end = parsed.get("period_end")

    # Must have at least revenue or net income to be worth storing
    if not parsed.get("revenue") and not parsed.get("net_income"):
        logger.warning(f"Skipping {ticker} {period_end} — no revenue or net income")
        return None

    revenue = parsed.get("revenue")
    gross_profit = parsed.get("gross_profit")
    operating_income = parsed.get("operating_income")
    net_income = parsed.get("net_income")
    depreciation = parsed.get("depreciation")
    operating_cash_flow = parsed.get("operating_cash_flow")
    capex = parsed.get("capex")
    long_term_debt = parsed.get("long_term_debt")
    short_term_debt = parsed.get("short_term_debt")
    cash = parsed.get("cash")
    total_assets = parsed.get("total_assets")
    total_liabilities = parsed.get("total_liabilities")
    total_equity = parsed.get("total_equity")
    current_assets = parsed.get("current_assets")
    current_liabilities = parsed.get("current_liabilities")

    # Calculated fields
    ebitda = None
    if operating_income is not None and depreciation is not None:
        ebitda = operating_income + depreciation

    free_cash_flow = parsed.get("free_cash_flow")
    if free_cash_flow is None and operating_cash_flow is not None and capex is not None:
        free_cash_flow = operating_cash_flow - abs(capex)

    total_debt = parsed.get("total_debt")
    if total_debt is None:
        lt = long_term_debt or 0
        st = short_term_debt or 0
        total_debt = lt + st if (lt or st) else None

    net_debt = None
    if total_debt is not None and cash is not None:
        net_debt = total_debt - cash

    # Margins
    gross_margin = safe_round(safe_divide(gross_profit, revenue))
    operating_margin = safe_round(safe_divide(operating_income, revenue))
    net_margin = safe_round(safe_divide(net_income, revenue))
    ebitda_margin = safe_round(safe_divide(ebitda, revenue))

    # Ratios
    debt_to_equity = safe_round(safe_divide(total_debt, total_equity))
    current_ratio = safe_round(safe_divide(current_assets, current_liabilities))
    roe = safe_round(safe_divide(net_income, total_equity))

    # ROIC = operating_income / invested_capital
    # invested_capital = total_assets - current_liabilities
    roic = None
    if operating_income is not None and total_assets is not None and current_liabilities is not None:
        invested_capital = total_assets - current_liabilities
        roic = safe_round(safe_divide(operating_income, invested_capital))

    # Validate — catch obviously wrong values
    if revenue and revenue < 0:
        logger.warning(f"Negative revenue for {ticker} {period_end} — skipping")
        return None

    if total_assets and total_assets < 0:
        logger.warning(f"Negative total assets for {ticker} {period_end} — skipping")
        return None

    return {
        "ticker": ticker,
        "cik": parsed.get("cik"),
        "period_end": period_end,
        "period_type": parsed.get("period_type"),
        "form": parsed.get("form"),
        "filed_at": parsed.get("filed_at"),
        # Income statement
        "revenue": revenue,
        "gross_profit": gross_profit,
        "gross_margin": gross_margin,
        "operating_income": operating_income,
        "operating_margin": operating_margin,
        "net_income": net_income,
        "net_margin": net_margin,
        "ebitda": ebitda,
        "ebitda_margin": ebitda_margin,
        "eps_basic": parsed.get("eps_basic"),
        "eps_diluted": parsed.get("eps_diluted"),
        "shares_outstanding": parsed.get("shares_outstanding"),
        # Balance sheet
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "cash": cash,
        "total_debt": total_debt,
        "net_debt": net_debt,
        # Cash flow
        "operating_cash_flow": operating_cash_flow,
        "capex": capex,
        "free_cash_flow": free_cash_flow,
        "depreciation": depreciation,
        # Ratios
        "gross_margin": gross_margin,
        "operating_margin": operating_margin,
        "net_margin": net_margin,
        "ebitda_margin": ebitda_margin,
        "debt_to_equity": debt_to_equity,
        "current_ratio": current_ratio,
        "roe": roe,
        "roic": roic,
        # Meta
        "parsed_by": parsed.get("parsed_by", "xbrl"),
    }


def normalize_all_periods(parsed_periods: list) -> list:
    """
    Normalize a list of parsed periods.
    Filters out invalid periods and returns clean rows.
    """
    results = []
    for parsed in parsed_periods:
        normalized = normalize_period(parsed)
        if normalized:
            results.append(normalized)

    logger.info(
        f"Normalized {len(results)}/{len(parsed_periods)} periods for "
        f"{parsed_periods[0]['ticker'] if parsed_periods else 'unknown'}"
    )
    return results


if __name__ == "__main__":
    import asyncio
    from app.fetchers.fundamentals.edgar_xbrl import fetch_company_facts
    from app.parsers.fundamentals.xbrl_parser import parse_all_periods

    async def test():
        print("Fetching and parsing AAPL...")
        facts = await fetch_company_facts("0000320193")
        parsed = parse_all_periods(facts, "AAPL", "0000320193", max_periods=10)
        normalized = normalize_all_periods(parsed)

        print(f"\nNormalized {len(normalized)} periods:")
        for n in normalized[:5]:
            print(f"\n  {n['period_end']} ({n['period_type']}):")
            print(f"    Revenue:        ${n['revenue']/1e9:.1f}B" if n.get('revenue') else "    Revenue:        N/A")
            print(f"    Gross Margin:   {n['gross_margin']*100:.1f}%" if n.get('gross_margin') else "    Gross Margin:   N/A")
            print(f"    Net Margin:     {n['net_margin']*100:.1f}%" if n.get('net_margin') else "    Net Margin:     N/A")
            print(f"    EBITDA Margin:  {n['ebitda_margin']*100:.1f}%" if n.get('ebitda_margin') else "    EBITDA Margin:  N/A")
            print(f"    FCF:            ${n['free_cash_flow']/1e9:.1f}B" if n.get('free_cash_flow') else "    FCF:            N/A")
            print(f"    EPS (diluted):  ${n['eps_diluted']:.2f}" if n.get('eps_diluted') else "    EPS (diluted):  N/A")
            print(f"    ROE:            {n['roe']*100:.1f}%" if n.get('roe') else "    ROE:            N/A")
            print(f"    Current Ratio:  {n['current_ratio']:.2f}" if n.get('current_ratio') else "    Current Ratio:  N/A")

    asyncio.run(test())