from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.market.alpaca import (
    get_snapshot,
    get_bars,
    get_multi_snapshot,
    get_latest_quote,
)

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/snapshot/{ticker}")
async def snapshot(ticker: str):
    """Latest price, change, OHLCV, bid/ask for a ticker."""
    try:
        return await get_snapshot(ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Alpaca error: {str(e)}")


@router.get("/bars/{ticker}")
async def bars(
    ticker: str,
    timeframe: str = Query("1Day", description="1Min 5Min 15Min 1Hour 1Day 1Week"),
    start: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(365, le=1000),
):
    """OHLCV bars for charting."""
    try:
        return await get_bars(ticker.upper(), timeframe, start, end, limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Alpaca error: {str(e)}")


@router.get("/quote/{ticker}")
async def quote(ticker: str):
    """Latest bid/ask quote."""
    try:
        return await get_latest_quote(ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Alpaca error: {str(e)}")


@router.get("/snapshots")
async def multi_snapshot(symbols: str = Query(..., description="Comma-separated tickers e.g. AAPL,MSFT,TSLA")):
    """Snapshots for multiple tickers — used for watchlist/dashboard."""
    try:
        tickers = [s.strip().upper() for s in symbols.split(",")]
        return await get_multi_snapshot(tickers)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Alpaca error: {str(e)}")