"""
LLM Fallback Parser (Layer 2)
------------------------------
Uses Claude to extract financial values that the traditional
XBRL parser couldn't find.

Only called when:
- Traditional parser returns None for a field
- That field hasn't been extracted by LLM for this ticker+period before

Cost control:
- Only sends the missing concepts section, not the full XBRL
- Result cached in DB — never calls Claude twice for same filing
- Estimated cost: ~$0.01-0.05 per company per quarter
"""

import json
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"

# Fields the LLM can help with and their descriptions
FIELD_DESCRIPTIONS = {
    "revenue": "Total revenue or net sales for the period",
    "gross_profit": "Revenue minus cost of goods sold",
    "operating_income": "Income from operations before interest and taxes",
    "net_income": "Net income or net profit after all expenses and taxes",
    "eps_basic": "Earnings per share (basic)",
    "eps_diluted": "Earnings per share (diluted)",
    "shares_outstanding": "Total shares outstanding",
    "total_assets": "Total assets on the balance sheet",
    "total_liabilities": "Total liabilities on the balance sheet",
    "total_equity": "Total stockholders equity",
    "cash": "Cash and cash equivalents",
    "current_assets": "Total current assets",
    "current_liabilities": "Total current liabilities",
    "long_term_debt": "Long term debt",
    "short_term_debt": "Short term debt or current portion of long term debt",
    "goodwill": "Goodwill on the balance sheet",
    "operating_cash_flow": "Net cash from operating activities",
    "capex": "Capital expenditures (payments to acquire property, plant and equipment)",
    "depreciation": "Depreciation and amortization",
    "dividends_paid": "Cash dividends paid to shareholders",
    "stock_buybacks": "Cash paid for repurchase of common stock",
}


def _build_prompt(
    ticker: str,
    period_end: str,
    period_type: str,
    form: str,
    missing_fields: list,
    xbrl_snippet: dict,
) -> str:
    """Build the prompt for Claude to extract missing financial values."""

    field_list = "\n".join([
        f"- {field}: {FIELD_DESCRIPTIONS.get(field, field)}"
        for field in missing_fields
    ])

    xbrl_json = json.dumps(xbrl_snippet, indent=2)[:8000]  # cap at 8K chars

    return f"""You are a financial data extraction assistant. Extract specific financial values from SEC EDGAR XBRL data.

Company: {ticker}
Period: {period_end} ({period_type})
Filing form: {form}

I need these specific financial values for this period:
{field_list}

Here is the relevant XBRL data:
{xbrl_json}

Instructions:
1. Find each requested field in the XBRL data
2. Return ONLY values that actually appear in the data for the period {period_end}
3. All monetary values should be in USD (raw numbers, not billions)
4. Return null for any field you cannot find with confidence
5. Do not guess or interpolate values

Respond with ONLY a JSON object, no explanation, no markdown:
{{
  "field_name": value_or_null,
  ...
}}"""


def _extract_xbrl_snippet(facts: dict, missing_fields: list) -> dict:
    """
    Extract only the relevant XBRL concepts for missing fields.
    Keeps the prompt small and focused.
    """
    from app.parsers.fundamentals.xbrl_parser import (
        INCOME_STATEMENT_CONCEPTS,
        BALANCE_SHEET_CONCEPTS,
        CASH_FLOW_CONCEPTS,
    )

    all_concepts = {
        **INCOME_STATEMENT_CONCEPTS,
        **BALANCE_SHEET_CONCEPTS,
        **CASH_FLOW_CONCEPTS,
    }

    snippet = {}
    us_gaap = facts.get("facts", {}).get("us-gaap", {})

    for field in missing_fields:
        concepts = all_concepts.get(field, [])
        for concept in concepts:
            if concept in us_gaap:
                concept_data = us_gaap[concept]
                # Only include the units data, not descriptions
                units = concept_data.get("units", {})
                # Limit to last 20 entries per unit to keep size down
                trimmed_units = {}
                for unit_key, entries in units.items():
                    trimmed_units[unit_key] = entries[-20:] if len(entries) > 20 else entries
                snippet[concept] = {"units": trimmed_units}

    return snippet


async def extract_missing_fields(
    ticker: str,
    cik: str,
    period_end: str,
    period_type: str,
    form: str,
    missing_fields: list,
    facts: dict,
    api_key: str,
) -> dict:
    """
    Call Claude to extract missing financial fields.
    Returns dict of field -> value (None for fields not found).
    """
    if not missing_fields:
        return {}

    if not api_key:
        logger.warning("No Anthropic API key — skipping LLM fallback")
        return {field: None for field in missing_fields}

    # Build focused XBRL snippet for missing fields only
    xbrl_snippet = _extract_xbrl_snippet(facts, missing_fields)

    if not xbrl_snippet:
        logger.info(f"No XBRL data found for missing fields {missing_fields} — skipping LLM")
        return {field: None for field in missing_fields}

    prompt = _build_prompt(
        ticker=ticker,
        period_end=period_end,
        period_type=period_type,
        form=form,
        missing_fields=missing_fields,
        xbrl_snippet=xbrl_snippet,
    )

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()

        content = data.get("content", [{}])[0].get("text", "")

        # Clean up response — remove markdown fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        extracted = json.loads(content)

        # Validate — only keep numeric values or None
        result = {}
        for field in missing_fields:
            val = extracted.get(field)
            if val is not None:
                try:
                    result[field] = float(val)
                except (TypeError, ValueError):
                    result[field] = None
            else:
                result[field] = None

        logger.info(
            f"LLM extracted {sum(1 for v in result.values() if v is not None)}"
            f"/{len(missing_fields)} missing fields for {ticker} {period_end}"
        )
        return result

    except json.JSONDecodeError as e:
        logger.error(f"LLM returned invalid JSON for {ticker} {period_end}: {e}")
        return {field: None for field in missing_fields}

    except Exception as e:
        logger.error(f"LLM fallback failed for {ticker} {period_end}: {e}")
        return {field: None for field in missing_fields}


async def enrich_parsed_period(
    parsed: dict,
    facts: dict,
    api_key: str,
) -> dict:
    """
    Take a parsed period dict, call LLM for missing fields,
    and return enriched dict with LLM values filled in.
    Marks parsed_by as 'hybrid' if LLM filled any fields.
    """
    missing = parsed.get("missing_fields", [])

    if not missing:
        return parsed

    llm_values = await extract_missing_fields(
        ticker=parsed["ticker"],
        cik=parsed["cik"],
        period_end=parsed["period_end"],
        period_type=parsed["period_type"],
        form=parsed["form"],
        missing_fields=missing,
        facts=facts,
        api_key=api_key,
    )

    # Merge LLM values into parsed dict
    filled = []
    for field, value in llm_values.items():
        if value is not None:
            parsed[field] = value
            filled.append(field)

    if filled:
        parsed["parsed_by"] = "hybrid"
        # Update missing_fields to only show what's still missing
        parsed["missing_fields"] = [f for f in missing if f not in filled]
        logger.info(f"LLM filled {filled} for {parsed['ticker']} {parsed['period_end']}")

    return parsed


async def enrich_all_periods(
    parsed_periods: list,
    facts: dict,
    api_key: str,
) -> list:
    """
    Enrich all periods that have missing fields.
    Calls LLM only for periods that need it.
    """
    import asyncio

    results = []
    llm_calls = 0

    for parsed in parsed_periods:
        if parsed.get("missing_fields"):
            enriched = await enrich_parsed_period(parsed, facts, api_key)
            results.append(enriched)
            llm_calls += 1
            # Small delay between LLM calls to avoid rate limits
            await asyncio.sleep(0.5)
        else:
            results.append(parsed)

    logger.info(
        f"LLM enrichment complete — {llm_calls} API calls made for "
        f"{parsed_periods[0]['ticker'] if parsed_periods else 'unknown'}"
    )
    return results


if __name__ == "__main__":
    import asyncio
    import os
    from app.fetchers.fundamentals.edgar_xbrl import fetch_company_facts
    from app.parsers.fundamentals.xbrl_parser import parse_all_periods

    async def test():
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("Set ANTHROPIC_API_KEY env var to test LLM fallback")
            return

        print("Fetching AAPL facts...")
        facts = await fetch_company_facts("0000320193")
        parsed = parse_all_periods(facts, "AAPL", "0000320193", max_periods=3)

        print(f"Before LLM: missing fields = {parsed[0].get('missing_fields')}")

        enriched = await enrich_all_periods(parsed, facts, api_key)

        print(f"After LLM: missing fields = {enriched[0].get('missing_fields')}")
        print(f"parsed_by = {enriched[0].get('parsed_by')}")
        for field in ["goodwill", "short_term_debt"]:
            print(f"  {field} = {enriched[0].get(field)}")

    asyncio.run(test())