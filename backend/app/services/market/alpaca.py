import httpx
from datetime import datetime, timedelta
from typing import Optional
from app.core.config import settings


def get_headers():
    return {
        "APCA-API-KEY-ID": settings.ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": settings.ALPACA_SECRET_KEY,
        "accept": "application/json",
    }


DATA_URL = "https://data.alpaca.markets"


async def get_snapshot(ticker: str) -> dict:
    url = f"{DATA_URL}/v2/stocks/{ticker}/snapshot"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=get_headers(), timeout=10)
        r.raise_for_status()
        data = r.json()

    latest_trade = data.get("latestTrade", {})
    latest_quote = data.get("latestQuote", {})
    daily_bar = data.get("dailyBar", {})
    prev_bar = data.get("prevDailyBar", {})

    price = latest_trade.get("p", 0)
    prev_close = prev_bar.get("c", 0)
    change = price - prev_close if price and prev_close else 0
    change_pct = (change / prev_close * 100) if prev_close else 0

    return {
        "ticker": ticker,
        "price": price,
        "change": round(change, 4),
        "change_pct": round(change_pct, 4),
        "open": daily_bar.get("o"),
        "high": daily_bar.get("h"),
        "low": daily_bar.get("l"),
        "close": daily_bar.get("c"),
        "volume": daily_bar.get("v"),
        "vwap": daily_bar.get("vw"),
        "prev_close": prev_close,
        "ask": latest_quote.get("ap"),
        "bid": latest_quote.get("bp"),
        "timestamp": latest_trade.get("t"),
    }


async def get_bars(
    ticker: str,
    timeframe: str = "1Day",
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 365,
) -> list:
    if not start:
        start = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.utcnow().strftime("%Y-%m-%d")

    url = f"{DATA_URL}/v2/stocks/{ticker}/bars"
    params = {
        "timeframe": timeframe,
        "start": start,
        "end": end,
        "limit": limit,
        "adjustment": "split",
    }

    bars = []
    async with httpx.AsyncClient() as client:
        while True:
            r = await client.get(url, headers=get_headers(), params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            for b in data.get("bars", []):
                bars.append({
                    "ticker": ticker,
                    "timestamp": b.get("t"),
                    "open": b.get("o"),
                    "high": b.get("h"),
                    "low": b.get("l"),
                    "close": b.get("c"),
                    "volume": b.get("v"),
                    "vwap": b.get("vw"),
                    "trade_count": b.get("n"),
                })
            next_token = data.get("next_page_token")
            if not next_token or len(bars) >= limit:
                break
            params["page_token"] = next_token

    return bars


async def get_latest_quote(ticker: str) -> dict:
    url = f"{DATA_URL}/v2/stocks/{ticker}/quotes/latest"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=get_headers(), timeout=10)
        r.raise_for_status()
        data = r.json()
    quote = data.get("quote", {})
    return {
        "ticker": ticker,
        "ask": quote.get("ap"),
        "ask_size": quote.get("as"),
        "bid": quote.get("bp"),
        "bid_size": quote.get("bs"),
        "timestamp": quote.get("t"),
    }


async def get_multi_snapshot(tickers: list) -> dict:
    url = f"{DATA_URL}/v2/stocks/snapshots"
    params = {"symbols": ",".join(tickers)}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=get_headers(), params=params, timeout=15)
        r.raise_for_status()
        return r.json()