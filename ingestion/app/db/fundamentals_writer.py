"""
Fundamentals DB Writer (Step 6)
--------------------------------
Writes normalized fundamentals data to Postgres.
Uses UPSERT — safe to run multiple times, never duplicates.

Tables written:
- fundamentals_summary  — one row per ticker per period (main table)
- fundamentals_facts    — raw concept values (audit trail)
- fundamentals_errors   — failed tickers (dead letter queue)
"""

import json
import logging
from datetime import datetime
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)


async def get_connection(database_url: str) -> asyncpg.Connection:
    """Get a raw asyncpg connection."""
    # Convert SQLAlchemy URL to asyncpg URL
    url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    return await asyncpg.connect(url)


async def upsert_summary(
    conn: asyncpg.Connection,
    row: dict,
) -> bool:
    """
    Upsert one row into fundamentals_summary.
    Returns True on success, False on failure.
    """
    sql = """
        INSERT INTO fundamentals_summary (
            ticker, cik, period_end, period_type, form, filed_at,
            revenue, gross_profit, gross_margin,
            operating_income, operating_margin,
            net_income, net_margin,
            ebitda, ebitda_margin,
            eps_basic, eps_diluted, shares_outstanding,
            total_assets, total_liabilities, total_equity,
            cash, total_debt, net_debt,
            operating_cash_flow, capex, free_cash_flow, depreciation,
            debt_to_equity, current_ratio, roe, roic,
            parsed_by, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6,
            $7, $8, $9,
            $10, $11,
            $12, $13,
            $14, $15,
            $16, $17, $18,
            $19, $20, $21,
            $22, $23, $24,
            $25, $26, $27, $28,
            $29, $30, $31, $32,
            $33, NOW()
        )
        ON CONFLICT (ticker, period_end, period_type)
        DO UPDATE SET
            cik = EXCLUDED.cik,
            form = EXCLUDED.form,
            filed_at = EXCLUDED.filed_at,
            revenue = EXCLUDED.revenue,
            gross_profit = EXCLUDED.gross_profit,
            gross_margin = EXCLUDED.gross_margin,
            operating_income = EXCLUDED.operating_income,
            operating_margin = EXCLUDED.operating_margin,
            net_income = EXCLUDED.net_income,
            net_margin = EXCLUDED.net_margin,
            ebitda = EXCLUDED.ebitda,
            ebitda_margin = EXCLUDED.ebitda_margin,
            eps_basic = EXCLUDED.eps_basic,
            eps_diluted = EXCLUDED.eps_diluted,
            shares_outstanding = EXCLUDED.shares_outstanding,
            total_assets = EXCLUDED.total_assets,
            total_liabilities = EXCLUDED.total_liabilities,
            total_equity = EXCLUDED.total_equity,
            cash = EXCLUDED.cash,
            total_debt = EXCLUDED.total_debt,
            net_debt = EXCLUDED.net_debt,
            operating_cash_flow = EXCLUDED.operating_cash_flow,
            capex = EXCLUDED.capex,
            free_cash_flow = EXCLUDED.free_cash_flow,
            depreciation = EXCLUDED.depreciation,
            debt_to_equity = EXCLUDED.debt_to_equity,
            current_ratio = EXCLUDED.current_ratio,
            roe = EXCLUDED.roe,
            roic = EXCLUDED.roic,
            parsed_by = EXCLUDED.parsed_by,
            updated_at = NOW()
    """

    def to_date(val):
        if val is None:
            return None
        if isinstance(val, str):
            return datetime.strptime(val, "%Y-%m-%d").date()
        return val

    try:
        await conn.execute(
            sql,
            row.get("ticker"),
            row.get("cik"),
            to_date(row.get("period_end")),
            row.get("period_type"),
            row.get("form"),
            to_date(row.get("filed_at")),
            row.get("revenue"),
            row.get("gross_profit"),
            row.get("gross_margin"),
            row.get("operating_income"),
            row.get("operating_margin"),
            row.get("net_income"),
            row.get("net_margin"),
            row.get("ebitda"),
            row.get("ebitda_margin"),
            row.get("eps_basic"),
            row.get("eps_diluted"),
            row.get("shares_outstanding"),
            row.get("total_assets"),
            row.get("total_liabilities"),
            row.get("total_equity"),
            row.get("cash"),
            row.get("total_debt"),
            row.get("net_debt"),
            row.get("operating_cash_flow"),
            row.get("capex"),
            row.get("free_cash_flow"),
            row.get("depreciation"),
            row.get("debt_to_equity"),
            row.get("current_ratio"),
            row.get("roe"),
            row.get("roic"),
            row.get("parsed_by", "xbrl"),
        )
        return True

    except Exception as e:
        logger.error(f"Failed to upsert summary for {row.get('ticker')} {row.get('period_end')}: {e}")
        return False


async def upsert_facts(
    conn: asyncpg.Connection,
    ticker: str,
    cik: str,
    parsed: dict,
) -> int:
    """
    Write raw parsed values to fundamentals_facts as audit trail.
    Returns number of rows written.
    """
    FIELD_TO_CONCEPT = {
        "revenue": "Revenue",
        "gross_profit": "GrossProfit",
        "operating_income": "OperatingIncomeLoss",
        "net_income": "NetIncomeLoss",
        "eps_basic": "EarningsPerShareBasic",
        "eps_diluted": "EarningsPerShareDiluted",
        "shares_outstanding": "CommonStockSharesOutstanding",
        "total_assets": "Assets",
        "total_liabilities": "Liabilities",
        "total_equity": "StockholdersEquity",
        "cash": "CashAndCashEquivalentsAtCarryingValue",
        "current_assets": "AssetsCurrent",
        "current_liabilities": "LiabilitiesCurrent",
        "long_term_debt": "LongTermDebt",
        "short_term_debt": "ShortTermBorrowings",
        "operating_cash_flow": "NetCashProvidedByUsedInOperatingActivities",
        "capex": "PaymentsToAcquirePropertyPlantAndEquipment",
        "depreciation": "DepreciationDepletionAndAmortization",
        "dividends_paid": "PaymentsOfDividends",
        "stock_buybacks": "PaymentsForRepurchaseOfCommonStock",
    }

    sql = """
        INSERT INTO fundamentals_facts (
            ticker, cik, concept, value, unit,
            period_end, period_type, form, filed_at, parsed_by
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        ON CONFLICT (ticker, concept, period_end, period_type)
        DO UPDATE SET
            value = EXCLUDED.value,
            parsed_by = EXCLUDED.parsed_by
    """

    def to_date(val):
        if val is None:
            return None
        if isinstance(val, str):
            return datetime.strptime(val, "%Y-%m-%d").date()
        return val

    count = 0
    period_end = to_date(parsed.get("period_end"))
    period_type = parsed.get("period_type")
    form = parsed.get("form")
    filed_at = to_date(parsed.get("filed_at"))
    parsed_by = parsed.get("parsed_by", "xbrl")

    for field, concept in FIELD_TO_CONCEPT.items():
        value = parsed.get(field)
        if value is None:
            continue
        try:
            await conn.execute(
                sql,
                ticker, cik, concept, float(value), "USD",
                period_end, period_type, form, filed_at, parsed_by,
            )
            count += 1
        except Exception as e:
            logger.warning(f"Failed to write fact {concept} for {ticker}: {e}")

    return count


async def log_error(
    conn: asyncpg.Connection,
    ticker: Optional[str],
    cik: Optional[str],
    stage: str,
    error_type: str,
    error_message: str,
    raw_data: Optional[dict] = None,
) -> None:
    """Log a failed pipeline run to fundamentals_errors."""
    sql = """
        INSERT INTO fundamentals_errors (
            ticker, cik, stage, error_type, error_message, raw_data
        ) VALUES ($1, $2, $3, $4, $5, $6)
    """
    try:
        await conn.execute(
            sql,
            ticker, cik, stage, error_type, error_message,
            json.dumps(raw_data) if raw_data else None,
        )
    except Exception as e:
        logger.error(f"Failed to log error: {e}")


async def write_fundamentals(
    normalized_periods: list,
    parsed_periods: list,
    ticker: str,
    cik: str,
    database_url: str,
) -> dict:
    """
    Write all normalized periods to DB.
    Returns summary of what was written.
    """
    conn = await get_connection(database_url)
    summary_written = 0
    facts_written = 0
    errors = 0

    try:
        for normalized, parsed in zip(normalized_periods, parsed_periods):
            # Write summary row
            success = await upsert_summary(conn, normalized)
            if success:
                summary_written += 1
            else:
                errors += 1
                await log_error(
                    conn, ticker, cik, "write",
                    "UpsertError", f"Failed to write summary for {normalized.get('period_end')}",
                )

            # Write raw facts audit trail
            facts_count = await upsert_facts(conn, ticker, cik, parsed)
            facts_written += facts_count

    finally:
        await conn.close()

    result = {
        "ticker": ticker,
        "summary_written": summary_written,
        "facts_written": facts_written,
        "errors": errors,
    }
    logger.info(f"DB write complete for {ticker}: {result}")
    return result


if __name__ == "__main__":
    import asyncio
    import os
    from app.fetchers.fundamentals.edgar_xbrl import fetch_company_facts
    from app.parsers.fundamentals.xbrl_parser import parse_all_periods
    from app.normalizers.fundamentals.normalizer import normalize_all_periods

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://argos:argos_password@localhost:5434/argos_db"
    )

    async def test():
        print("Fetching AAPL...")
        facts = await fetch_company_facts("0000320193")
        parsed = parse_all_periods(facts, "AAPL", "0000320193", max_periods=10)
        normalized = normalize_all_periods(parsed)

        print(f"Writing {len(normalized)} periods to DB...")
        result = await write_fundamentals(
            normalized_periods=normalized,
            parsed_periods=parsed,
            ticker="AAPL",
            cik="0000320193",
            database_url=DATABASE_URL,
        )
        print(f"Done: {result}")

    asyncio.run(test())