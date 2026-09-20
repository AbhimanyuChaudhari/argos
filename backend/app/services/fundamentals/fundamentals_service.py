"""
Fundamentals Service
---------------------
DB query functions for the fundamentals API.
Uses SQLAlchemy async session — matches existing backend pattern.
"""

import logging
from typing import Optional
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def _fetch(sql: str, params: dict) -> list:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(sql), params)
        rows = result.mappings().all()
        return [dict(r) for r in rows]


async def _fetchone(sql: str, params: dict) -> Optional[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(sql), params)
        row = result.mappings().first()
        return dict(row) if row else None


async def get_income_statement(
    ticker: str,
    period_type: Optional[str] = None,
    limit: int = 12,
) -> list:
    if period_type:
        sql = """
            SELECT period_end, period_type, form, filed_at,
                   revenue, gross_profit, gross_margin,
                   operating_income, operating_margin,
                   net_income, net_margin,
                   ebitda, ebitda_margin,
                   eps_basic, eps_diluted, shares_outstanding,
                   parsed_by
            FROM fundamentals_summary
            WHERE ticker = :ticker AND period_type = :period_type
            ORDER BY period_end DESC
            LIMIT :limit
        """
        return await _fetch(sql, {"ticker": ticker, "period_type": period_type, "limit": limit})
    else:
        sql = """
            SELECT period_end, period_type, form, filed_at,
                   revenue, gross_profit, gross_margin,
                   operating_income, operating_margin,
                   net_income, net_margin,
                   ebitda, ebitda_margin,
                   eps_basic, eps_diluted, shares_outstanding,
                   parsed_by
            FROM fundamentals_summary
            WHERE ticker = :ticker
            ORDER BY period_end DESC
            LIMIT :limit
        """
        return await _fetch(sql, {"ticker": ticker, "limit": limit})


async def get_balance_sheet(
    ticker: str,
    period_type: Optional[str] = None,
    limit: int = 12,
) -> list:
    if period_type:
        sql = """
            SELECT period_end, period_type, form, filed_at,
                   total_assets, total_liabilities, total_equity,
                   cash, total_debt, net_debt,
                   current_ratio, debt_to_equity,
                   parsed_by
            FROM fundamentals_summary
            WHERE ticker = :ticker AND period_type = :period_type
            ORDER BY period_end DESC
            LIMIT :limit
        """
        return await _fetch(sql, {"ticker": ticker, "period_type": period_type, "limit": limit})
    else:
        sql = """
            SELECT period_end, period_type, form, filed_at,
                   total_assets, total_liabilities, total_equity,
                   cash, total_debt, net_debt,
                   current_ratio, debt_to_equity,
                   parsed_by
            FROM fundamentals_summary
            WHERE ticker = :ticker
            ORDER BY period_end DESC
            LIMIT :limit
        """
        return await _fetch(sql, {"ticker": ticker, "limit": limit})


async def get_cash_flow(
    ticker: str,
    period_type: Optional[str] = None,
    limit: int = 12,
) -> list:
    if period_type:
        sql = """
            SELECT period_end, period_type, form, filed_at,
                   operating_cash_flow, capex, free_cash_flow,
                   depreciation, parsed_by
            FROM fundamentals_summary
            WHERE ticker = :ticker AND period_type = :period_type
            ORDER BY period_end DESC
            LIMIT :limit
        """
        return await _fetch(sql, {"ticker": ticker, "period_type": period_type, "limit": limit})
    else:
        sql = """
            SELECT period_end, period_type, form, filed_at,
                   operating_cash_flow, capex, free_cash_flow,
                   depreciation, parsed_by
            FROM fundamentals_summary
            WHERE ticker = :ticker
            ORDER BY period_end DESC
            LIMIT :limit
        """
        return await _fetch(sql, {"ticker": ticker, "limit": limit})


async def get_metrics(
    ticker: str,
    period_type: Optional[str] = None,
    limit: int = 12,
) -> list:
    if period_type:
        sql = """
            SELECT period_end, period_type, form, filed_at,
                   gross_margin, operating_margin, net_margin, ebitda_margin,
                   roe, roic, debt_to_equity, current_ratio,
                   eps_basic, eps_diluted, parsed_by
            FROM fundamentals_summary
            WHERE ticker = :ticker AND period_type = :period_type
            ORDER BY period_end DESC
            LIMIT :limit
        """
        return await _fetch(sql, {"ticker": ticker, "period_type": period_type, "limit": limit})
    else:
        sql = """
            SELECT period_end, period_type, form, filed_at,
                   gross_margin, operating_margin, net_margin, ebitda_margin,
                   roe, roic, debt_to_equity, current_ratio,
                   eps_basic, eps_diluted, parsed_by
            FROM fundamentals_summary
            WHERE ticker = :ticker
            ORDER BY period_end DESC
            LIMIT :limit
        """
        return await _fetch(sql, {"ticker": ticker, "limit": limit})


async def get_summary(ticker: str) -> Optional[dict]:
    sql = """
        SELECT *
        FROM fundamentals_summary
        WHERE ticker = :ticker
        ORDER BY period_end DESC
        LIMIT 1
    """
    return await _fetchone(sql, {"ticker": ticker})