"""
Fundamentals API Router
------------------------
Serves financial statement data from fundamentals_summary table.

Endpoints:
    GET /fundamentals/{ticker}/income-statement
    GET /fundamentals/{ticker}/balance-sheet
    GET /fundamentals/{ticker}/cash-flow
    GET /fundamentals/{ticker}/metrics
    GET /fundamentals/{ticker}/summary
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.fundamentals.fundamentals_service import (
    get_income_statement,
    get_balance_sheet,
    get_cash_flow,
    get_metrics,
    get_summary,
)

router = APIRouter(prefix="/fundamentals", tags=["fundamentals"])


@router.get("/{ticker}/income-statement")
async def income_statement(
    ticker: str,
    period_type: Optional[str] = Query(None, description="annual or quarterly"),
    limit: int = Query(12, le=40),
):
    """Revenue, margins, EPS — last N periods."""
    try:
        data = await get_income_statement(ticker.upper(), period_type, limit)
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/balance-sheet")
async def balance_sheet(
    ticker: str,
    period_type: Optional[str] = Query(None, description="annual or quarterly"),
    limit: int = Query(12, le=40),
):
    """Assets, liabilities, equity — last N periods."""
    try:
        data = await get_balance_sheet(ticker.upper(), period_type, limit)
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/cash-flow")
async def cash_flow(
    ticker: str,
    period_type: Optional[str] = Query(None, description="annual or quarterly"),
    limit: int = Query(12, le=40),
):
    """OCF, capex, FCF — last N periods."""
    try:
        data = await get_cash_flow(ticker.upper(), period_type, limit)
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/metrics")
async def metrics(
    ticker: str,
    period_type: Optional[str] = Query(None, description="annual or quarterly"),
    limit: int = Query(12, le=40),
):
    """All derived ratios — margins, ROE, ROIC, debt ratios."""
    try:
        data = await get_metrics(ticker.upper(), period_type, limit)
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/summary")
async def summary(ticker: str):
    """Latest period snapshot — all fields in one call."""
    try:
        data = await get_summary(ticker.upper())
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))