import asyncio
from loguru import logger
from app.fetchers.government.sec_edgar import SECEdgarFetcher
from app.fetchers.government.govtrack import GovTrackFetcher
from app.fetchers.government.usaspending import USASpendingFetcher
from app.db.writer import DatabaseWriter, AsyncSessionLocal


async def run_edgar(days_back: int = 1) -> dict:
    """Fetch and store SEC EDGAR filings."""
    logger.info("=" * 40)
    logger.info("Running SEC EDGAR fetcher")
    logger.info("=" * 40)

    async with SECEdgarFetcher() as fetcher:
        all_normalised = []
        filing_types = ["8-K", "10-K", "10-Q", "S-1", "4"]

        for filing_type in filing_types:
            records = await fetcher.fetch(
                filing_type=filing_type,
                days_back=days_back,
                limit=100,
            )
            for raw in records:
                result = fetcher.normalise(raw)
                if result:
                    all_normalised.append(result)

    async with AsyncSessionLocal() as session:
        writer = DatabaseWriter(session)
        result = await writer.write_filings(all_normalised)

    logger.info(f"EDGAR complete: {result}")
    return result


async def run_govtrack(days_back: int = 7) -> dict:
    """Fetch and store congressional bills."""
    logger.info("=" * 40)
    logger.info("Running GovTrack fetcher")
    logger.info("=" * 40)

    async with GovTrackFetcher() as fetcher:
        records = await fetcher.fetch_recent(
            days_back=days_back,
            limit=100,
        )
        normalised = []
        for raw in records:
            result = fetcher.normalise(raw)
            if result:
                normalised.append(result)

    async with AsyncSessionLocal() as session:
        writer = DatabaseWriter(session)
        result = await writer.write_bills(normalised)

    logger.info(f"GovTrack complete: {result}")
    return result


async def run_usaspending(days_back: int = 7) -> dict:
    """Fetch and store federal contracts."""
    logger.info("=" * 40)
    logger.info("Running USASpending fetcher")
    logger.info("=" * 40)

    async with USASpendingFetcher() as fetcher:
        records = await fetcher.fetch(
            days_back=days_back,
            limit=100,
            min_amount=1000000,
        )
        normalised = []
        for raw in records:
            result = fetcher.normalise(raw)
            if result:
                normalised.append(result)

    async with AsyncSessionLocal() as session:
        writer = DatabaseWriter(session)
        result = await writer.write_contracts(normalised)

    logger.info(f"USASpending complete: {result}")
    return result


async def main():
    logger.info("=" * 60)
    logger.info("ARGOS — Full Government Data Pipeline")
    logger.info("=" * 60)

    results = {}

    # Run all fetchers
    results["edgar"] = await run_edgar(days_back=1)
    results["govtrack"] = await run_govtrack(days_back=7)
    results["usaspending"] = await run_usaspending(days_back=7)

    # Summary
    logger.info("=" * 60)
    logger.info("Pipeline complete — Summary:")
    for source, result in results.items():
        logger.info(
            f"  {source:15} — "
            f"inserted={result['inserted']} "
            f"skipped={result['skipped']} "
            f"failed={result['failed']}"
        )
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())