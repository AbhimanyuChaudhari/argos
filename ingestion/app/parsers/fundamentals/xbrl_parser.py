"""
Traditional XBRL Parser (Layer 1)
----------------------------------
Maps standard SEC XBRL concepts to clean field names.
Handles ~90% of US public companies.
"""

import logging
from typing import Optional
from app.fetchers.fundamentals.edgar_xbrl import extract_concept_values

logger = logging.getLogger(__name__)

INCOME_STATEMENT_CONCEPTS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
        "RevenueFromContractWithCustomer",
        "SalesRevenueNetOfInterestExpense",
        "TotalRevenuesAndOtherIncome",
        "RevenuesNetOfInterestExpense",
    ],
    "gross_profit": [
        "GrossProfit",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    ],
    "net_income": [
        "NetIncomeLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
        "ProfitLoss",
    ],
    "eps_basic": [
        "EarningsPerShareBasic",
    ],
    "eps_diluted": [
        "EarningsPerShareDiluted",
    ],
    "shares_outstanding": [
        "CommonStockSharesOutstanding",
        "WeightedAverageNumberOfSharesOutstandingBasic",
    ],
    "rd_expense": [
        "ResearchAndDevelopmentExpense",
        "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
    ],
    "sga_expense": [
        "SellingGeneralAndAdministrativeExpense",
        "GeneralAndAdministrativeExpense",
    ],
}

BALANCE_SHEET_CONCEPTS = {
    "total_assets": [
        "Assets",
    ],
    "total_liabilities": [
        "Liabilities",
        "LiabilitiesAndStockholdersEquity",
    ],
    "total_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments",
        "CashAndCashEquivalentsAndShortTermInvestments",
        "Cash",
    ],
    "current_assets": [
        "AssetsCurrent",
    ],
    "current_liabilities": [
        "LiabilitiesCurrent",
    ],
    "long_term_debt": [
        "LongTermDebt",
        "LongTermDebtNoncurrent",
        "LongTermNotesPayable",
    ],
    "short_term_debt": [
        "ShortTermBorrowings",
        "DebtCurrent",
        "NotesPayableCurrent",
        "CommercialPaper",
        "LongTermDebtCurrent",
    ],
    "goodwill": [
        "Goodwill",
    ],
    "intangible_assets": [
        "FiniteLivedIntangibleAssetsNet",
        "IntangibleAssetsNetExcludingGoodwill",
    ],
    "retained_earnings": [
        "RetainedEarningsAccumulatedDeficit",
    ],
}

CASH_FLOW_CONCEPTS = {
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsForCapitalImprovements",
        "PaymentsToAcquireProductiveAssets",
    ],
    "depreciation": [
        "DepreciationDepletionAndAmortization",
        "Depreciation",
        "DepreciationAndAmortization",
        "AmortizationOfIntangibleAssets",
    ],
    "investing_cash_flow": [
        "NetCashProvidedByUsedInInvestingActivities",
    ],
    "financing_cash_flow": [
        "NetCashProvidedByUsedInFinancingActivities",
    ],
    "dividends_paid": [
        "PaymentsOfDividends",
        "PaymentsOfDividendsCommonStock",
    ],
    "stock_buybacks": [
        "PaymentsForRepurchaseOfCommonStock",
    ],
}


def _get_best_value(
    facts: dict,
    concepts: list,
    period_end: str,
    period_type: str,
) -> Optional[float]:
    """
    Try each concept in order and return the first value found
    for the given period_end and period_type.
    Also checks instant period_type for balance sheet items.
    """
    for concept in concepts:
        values = extract_concept_values(facts, concept)
        for v in values:
            if v["period_end"] == period_end and v["period_type"] in (period_type, "instant"):
                return float(v["value"]) if v["value"] is not None else None
    return None


def get_all_periods(facts: dict) -> list:
    """
    Scan all concepts to find all unique (period_end, period_type, form) combos.
    Returns sorted list newest first.
    """
    periods = set()

    for concept in INCOME_STATEMENT_CONCEPTS["revenue"]:
        values = extract_concept_values(facts, concept)
        for v in values:
            if v["period_type"] in ("annual", "quarterly"):
                periods.add((
                    v["period_end"],
                    v["period_type"],
                    v.get("form", ""),
                    v.get("filed_at", ""),
                ))

    for concept in CASH_FLOW_CONCEPTS["operating_cash_flow"]:
        values = extract_concept_values(facts, concept)
        for v in values:
            if v["period_type"] in ("annual", "quarterly"):
                periods.add((
                    v["period_end"],
                    v["period_type"],
                    v.get("form", ""),
                    v.get("filed_at", ""),
                ))

    result = [
        {
            "period_end": p[0],
            "period_type": p[1],
            "form": p[2],
            "filed_at": p[3],
        }
        for p in periods
    ]
    result.sort(key=lambda x: x["period_end"], reverse=True)
    return result


def parse_period(
    facts: dict,
    period_end: str,
    period_type: str,
    form: str,
    filed_at: str,
    ticker: str,
    cik: str,
) -> dict:
    """
    Parse all financial fields for a single period.
    Returns a dict with all fields — None where not found.
    Tracks which fields were found vs missing for LLM fallback.
    """
    result = {
        "ticker": ticker,
        "cik": cik,
        "period_end": period_end,
        "period_type": period_type,
        "form": form,
        "filed_at": filed_at,
        "parsed_by": "xbrl",
        "missing_fields": [],
    }

    def get(concept_map: dict, field: str) -> Optional[float]:
        concepts = concept_map.get(field, [])
        if not concepts:
            return None
        val = _get_best_value(facts, concepts, period_end, period_type)
        if val is None:
            result["missing_fields"].append(field)
        return val

    # Income statement
    result["revenue"] = get(INCOME_STATEMENT_CONCEPTS, "revenue")
    result["gross_profit"] = get(INCOME_STATEMENT_CONCEPTS, "gross_profit")
    result["operating_income"] = get(INCOME_STATEMENT_CONCEPTS, "operating_income")
    result["net_income"] = get(INCOME_STATEMENT_CONCEPTS, "net_income")
    result["eps_basic"] = get(INCOME_STATEMENT_CONCEPTS, "eps_basic")
    result["eps_diluted"] = get(INCOME_STATEMENT_CONCEPTS, "eps_diluted")
    result["shares_outstanding"] = get(INCOME_STATEMENT_CONCEPTS, "shares_outstanding")
    result["rd_expense"] = get(INCOME_STATEMENT_CONCEPTS, "rd_expense")
    result["sga_expense"] = get(INCOME_STATEMENT_CONCEPTS, "sga_expense")

    # Balance sheet
    result["total_assets"] = get(BALANCE_SHEET_CONCEPTS, "total_assets")
    result["total_liabilities"] = get(BALANCE_SHEET_CONCEPTS, "total_liabilities")
    result["total_equity"] = get(BALANCE_SHEET_CONCEPTS, "total_equity")
    result["cash"] = get(BALANCE_SHEET_CONCEPTS, "cash")
    result["current_assets"] = get(BALANCE_SHEET_CONCEPTS, "current_assets")
    result["current_liabilities"] = get(BALANCE_SHEET_CONCEPTS, "current_liabilities")
    result["long_term_debt"] = get(BALANCE_SHEET_CONCEPTS, "long_term_debt")
    result["short_term_debt"] = get(BALANCE_SHEET_CONCEPTS, "short_term_debt")
    result["goodwill"] = get(BALANCE_SHEET_CONCEPTS, "goodwill")
    result["retained_earnings"] = get(BALANCE_SHEET_CONCEPTS, "retained_earnings")

    # Cash flow
    result["operating_cash_flow"] = get(CASH_FLOW_CONCEPTS, "operating_cash_flow")
    result["capex"] = get(CASH_FLOW_CONCEPTS, "capex")
    result["depreciation"] = get(CASH_FLOW_CONCEPTS, "depreciation")
    result["dividends_paid"] = get(CASH_FLOW_CONCEPTS, "dividends_paid")
    result["stock_buybacks"] = get(CASH_FLOW_CONCEPTS, "stock_buybacks")
    result["investing_cash_flow"] = get(CASH_FLOW_CONCEPTS, "investing_cash_flow")
    result["financing_cash_flow"] = get(CASH_FLOW_CONCEPTS, "financing_cash_flow")

    # Calculated fields
    long_term = result.get("long_term_debt") or 0
    short_term = result.get("short_term_debt") or 0
    result["total_debt"] = long_term + short_term if (long_term or short_term) else None

    ocf = result.get("operating_cash_flow")
    capex = result.get("capex")
    if ocf is not None and capex is not None:
        result["free_cash_flow"] = ocf - abs(capex)
    else:
        result["free_cash_flow"] = None

    return result


def parse_all_periods(
    facts: dict,
    ticker: str,
    cik: str,
    max_periods: int = 20,
) -> list:
    """
    Parse all periods for a company.
    Returns list of period dicts, newest first.
    """
    periods = get_all_periods(facts)
    results = []

    for period in periods[:max_periods]:
        parsed = parse_period(
            facts=facts,
            period_end=period["period_end"],
            period_type=period["period_type"],
            form=period["form"],
            filed_at=period["filed_at"],
            ticker=ticker,
            cik=cik,
        )
        results.append(parsed)

    logger.info(
        f"Parsed {len(results)} periods for {ticker} — "
        f"{sum(1 for r in results if not r['missing_fields'])} complete, "
        f"{sum(1 for r in results if r['missing_fields'])} need LLM fallback"
    )
    return results


def get_missing_summary(parsed_periods: list) -> dict:
    """Summarize which fields are missing across all periods."""
    all_missing = {}
    for period in parsed_periods:
        for field in period.get("missing_fields", []):
            all_missing[field] = all_missing.get(field, 0) + 1

    return {
        "total_periods": len(parsed_periods),
        "periods_needing_llm": sum(1 for p in parsed_periods if p["missing_fields"]),
        "missing_fields": all_missing,
    }


if __name__ == "__main__":
    import asyncio
    from app.fetchers.fundamentals.edgar_xbrl import fetch_company_facts

    async def test():
        print("Fetching AAPL facts...")
        facts = await fetch_company_facts("0000320193")
        if not facts:
            print("Failed")
            return

        print("Parsing all periods...")
        results = parse_all_periods(facts, "AAPL", "0000320193", max_periods=10)

        print(f"\nParsed {len(results)} periods:")
        for r in results[:5]:
            rev = f"${r['revenue']/1e9:.1f}B" if r.get('revenue') else "N/A"
            ni = f"${r['net_income']/1e9:.1f}B" if r.get('net_income') else "N/A"
            fcf = f"${r['free_cash_flow']/1e9:.1f}B" if r.get('free_cash_flow') else "N/A"
            eps = f"${r['eps_diluted']:.2f}" if r.get('eps_diluted') else "N/A"
            assets = f"${r['total_assets']/1e9:.1f}B" if r.get('total_assets') else "N/A"
            missing = len(r.get('missing_fields', []))
            print(f"  {r['period_end']} ({r['period_type']}): Rev={rev} NI={ni} FCF={fcf} EPS={eps} Assets={assets} missing={missing}")

        summary = get_missing_summary(results)
        print(f"\nMissing field summary: {summary}")

    asyncio.run(test())