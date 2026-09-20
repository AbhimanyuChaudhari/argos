"""
Fundamentals Pipeline — Main Runner
-------------------------------------
Chains all steps:
1. Change detection — skip if no new filing
2. XBRL fetch — get all financial facts from SEC EDGAR
3. Traditional parse — extract ~96% of fields
4. LLM fallback — fill remaining missing fields with Claude
5. Normalize — calculate derived metrics and ratios
6. DB write — upsert into fundamentals_summary and fundamentals_facts

Usage:
    # Single ticker
    python run_fundamentals.py --ticker AAPL

    # Multiple tickers
    python run_fundamentals.py --tickers AAPL MSFT GOOGL TSLA NVDA

    # From a file
    python run_fundamentals.py --file tickers.txt

    # Skip LLM fallback (faster, cheaper)
    python run_fundamentals.py --ticker AAPL --no-llm

    # Force re-fetch even if no new filing
    python run_fundamentals.py --ticker AAPL --force
"""

import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fundamentals_pipeline")

# Config from env
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{os.getenv('POSTGRES_USER', 'argos')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'argos_password')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5434')}/"
    f"{os.getenv('POSTGRES_DB', 'argos_db')}"
)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Known CIK mappings for common tickers
# Add more as needed — or use the EDGAR lookup function
TICKER_TO_CIK = {
    "AAPL":  "0000320193",
    "MSFT":  "0000789019",
    "GOOGL": "0001652044",
    "GOOG":  "0001652044",
    "AMZN":  "0001018724",
    "NVDA":  "0001045810",
    "META":  "0001326801",
    "TSLA":  "0001318605",
    "BRK.B": "0001067983",
    "JPM":   "0000019617",
    "V":     "0001403161",
    "MA":    "0001141391",
    "UNH":   "0000731766",
    "JNJ":   "0000200406",
    "XOM":   "0000034088",
    "WMT":   "0000104169",
    "PG":    "0000080424",
    "HD":    "0000354950",
    "CVX":   "0000093410",
    "MRK":   "0000310158",
    "ABBV":  "0001551152",
    "KO":    "0000021344",
    "PEP":   "0000077476",
    "COST":  "0000909832",
    "AVGO":  "0001730168",
    "NFLX":  "0001065280",
    "AMD":   "0000002488",
    "INTC":  "0000050863",
    "CRM":   "0001108524",
    "ADBE":  "0000796343",
    "NOW":   "0001373715",
    "BAC":   "0000070858",
    "GS":    "0000886982",
    "MS":    "0000895421",
    "WFC":   "0000072971",
    "C":     "0000831001",
    "GE":    "0000040533",
    "BA":    "0000012927",
    "CAT":   "0000018230",
    "MMM":   "0000066740",
    "IBM":   "0000051143",
    "ORCL":  "0001341439",
    "QCOM":  "0000804328",
    "TXN":   "0000097476",
    "PYPL":  "0001633917",
    "UBER":  "0001543151",
    "LYFT":  "0001759509",
    "SNAP":  "0001564408",
    "SPOT":  "0001639920",
    "ABNB":  "0001559720",
    "COIN":  "0001679788",
}


async def get_cik(ticker: str) -> str:
    """Get CIK for a ticker — from local map or EDGAR lookup."""
    if ticker in TICKER_TO_CIK:
        return TICKER_TO_CIK[ticker]

    from app.fetchers.fundamentals.edgar_xbrl import lookup_cik_by_ticker
    logger.info(f"Looking up CIK for {ticker} on EDGAR...")
    cik = await lookup_cik_by_ticker(ticker)
    if cik:
        return cik

    raise ValueError(f"Could not find CIK for ticker {ticker}")


async def get_last_fetched_date(ticker: str) -> str | None:
    """Check when we last fetched fundamentals for this ticker."""
    try:
        import asyncpg
        url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url)
        row = await conn.fetchrow(
            "SELECT MAX(filed_at) FROM fundamentals_summary WHERE ticker = $1",
            ticker,
        )
        await conn.close()
        if row and row[0]:
            return row[0].strftime("%Y-%m-%d")
        return None
    except Exception:
        return None


async def run_pipeline_for_ticker(
    ticker: str,
    use_llm: bool = True,
    force: bool = False,
    max_periods: int = 20,
) -> dict:
    """
    Run the full fundamentals pipeline for one ticker.
    Returns result summary dict.
    """
    start_time = datetime.utcnow()
    logger.info(f"{'='*50}")
    logger.info(f"Starting pipeline for {ticker}")
    logger.info(f"{'='*50}")

    result = {
        "ticker": ticker,
        "success": False,
        "skipped": False,
        "periods_written": 0,
        "error": None,
    }

    try:
        # Step 1 — Get CIK
        cik = await get_cik(ticker)
        logger.info(f"{ticker} CIK: {cik}")

        # Step 2 — Change detection (skip if no new data)
        if not force:
            from app.fetchers.fundamentals.edgar_xbrl import get_latest_filing_date
            latest_edgar = await get_latest_filing_date(cik)
            last_fetched = await get_last_fetched_date(ticker)

            if latest_edgar and last_fetched:
                if str(latest_edgar) <= last_fetched:
                    logger.info(
                        f"{ticker}: No new filings since {last_fetched} — skipping"
                    )
                    result["skipped"] = True
                    result["success"] = True
                    return result

            logger.info(f"{ticker}: New filing detected — proceeding with fetch")

        # Step 3 — Fetch XBRL facts
        from app.fetchers.fundamentals.edgar_xbrl import (
            fetch_company_facts,
            save_raw_to_disk,
        )
        logger.info(f"{ticker}: Fetching XBRL facts from EDGAR...")
        facts = await fetch_company_facts(cik)

        if not facts:
            raise ValueError(f"Failed to fetch XBRL facts for {ticker}")

        # Save raw backup
        save_raw_to_disk(cik, ticker, facts)
        logger.info(f"{ticker}: Fetched {len(facts.get('facts', {}).get('us-gaap', {}))} concepts")

        # Step 4 — Traditional parse
        from app.parsers.fundamentals.xbrl_parser import parse_all_periods, get_missing_summary
        logger.info(f"{ticker}: Running traditional XBRL parser...")
        parsed = parse_all_periods(facts, ticker, cik, max_periods=max_periods)

        missing = get_missing_summary(parsed)
        logger.info(
            f"{ticker}: Parsed {len(parsed)} periods — "
            f"{missing['periods_needing_llm']} need LLM fallback"
        )

        # Step 5 — LLM fallback
        if use_llm and missing["periods_needing_llm"] > 0 and ANTHROPIC_API_KEY:
            from app.parsers.fundamentals.llm_fallback import enrich_all_periods
            logger.info(f"{ticker}: Running LLM fallback for missing fields...")
            parsed = await enrich_all_periods(parsed, facts, ANTHROPIC_API_KEY)
        elif use_llm and not ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set — skipping LLM fallback")

        # Step 6 — Normalize
        from app.normalizers.fundamentals.normalizer import normalize_all_periods
        logger.info(f"{ticker}: Normalizing {len(parsed)} periods...")
        normalized = normalize_all_periods(parsed)

        if not normalized:
            raise ValueError(f"No valid periods after normalization for {ticker}")

        # Step 7 — Write to DB
        from app.db.fundamentals_writer import write_fundamentals
        logger.info(f"{ticker}: Writing {len(normalized)} periods to DB...")
        write_result = await write_fundamentals(
            normalized_periods=normalized,
            parsed_periods=parsed,
            ticker=ticker,
            cik=cik,
            database_url=DATABASE_URL,
        )

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"{ticker}: Pipeline complete in {elapsed:.1f}s — "
            f"{write_result['summary_written']} periods written"
        )

        result["success"] = True
        result["periods_written"] = write_result["summary_written"]
        result["cik"] = cik

    except Exception as e:
        logger.error(f"{ticker}: Pipeline failed — {e}", exc_info=True)
        result["error"] = str(e)

        # Log to DB error table
        try:
            import asyncpg
            from app.db.fundamentals_writer import log_error
            url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            conn = await asyncpg.connect(url)
            await log_error(
                conn, ticker, None, "pipeline",
                type(e).__name__, str(e),
            )
            await conn.close()
        except Exception:
            pass

    return result


async def run_pipeline_for_tickers(
    tickers: list,
    use_llm: bool = True,
    force: bool = False,
    max_periods: int = 20,
) -> list:
    """Run pipeline for multiple tickers sequentially."""
    results = []
    total = len(tickers)

    for i, ticker in enumerate(tickers, 1):
        logger.info(f"\nProcessing {i}/{total}: {ticker}")
        result = await run_pipeline_for_ticker(
            ticker=ticker,
            use_llm=use_llm,
            force=force,
            max_periods=max_periods,
        )
        results.append(result)

        # Rate limit between tickers — be nice to EDGAR
        if i < total:
            await asyncio.sleep(1.0)

    # Print summary
    logger.info(f"\n{'='*50}")
    logger.info("PIPELINE SUMMARY")
    logger.info(f"{'='*50}")
    success = sum(1 for r in results if r["success"] and not r["skipped"])
    skipped = sum(1 for r in results if r["skipped"])
    failed = sum(1 for r in results if not r["success"])
    total_periods = sum(r["periods_written"] for r in results)

    logger.info(f"Total:    {total}")
    logger.info(f"Success:  {success}")
    logger.info(f"Skipped:  {skipped} (no new filings)")
    logger.info(f"Failed:   {failed}")
    logger.info(f"Periods written: {total_periods}")

    if failed > 0:
        logger.warning("Failed tickers:")
        for r in results:
            if not r["success"]:
                logger.warning(f"  {r['ticker']}: {r['error']}")

    return results


def parse_args():
    parser = argparse.ArgumentParser(description="Argos Fundamentals Pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ticker", type=str, help="Single ticker e.g. AAPL")
    group.add_argument("--tickers", nargs="+", help="Multiple tickers e.g. AAPL MSFT GOOGL")
    group.add_argument("--file", type=str, help="File with one ticker per line")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM fallback")
    parser.add_argument("--force", action="store_true", help="Force re-fetch even if no new filing")
    parser.add_argument("--max-periods", type=int, default=20, help="Max periods per ticker")
    return parser.parse_args()


async def main():
    args = parse_args()

    if args.ticker:
        tickers = [args.ticker.upper()]
    elif args.tickers:
        tickers = [t.upper() for t in args.tickers]
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
        tickers = [
            line.strip().upper()
            for line in path.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        logger.info(f"Loaded {len(tickers)} tickers from {args.file}")

    await run_pipeline_for_tickers(
        tickers=tickers,
        use_llm=not args.no_llm,
        force=args.force,
        max_periods=args.max_periods,
    )


if __name__ == "__main__":
    asyncio.run(main())