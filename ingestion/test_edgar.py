import asyncio
from app.fetchers.government.sec_edgar import SECEdgarFetcher
from app.db.writer import DatabaseWriter, AsyncSessionLocal


async def main():
    print("=" * 60)
    print("ARGOS - Full Pipeline Test: EDGAR to Postgres")
    print("=" * 60)

    async with SECEdgarFetcher() as fetcher:
        print("\n[1] Fetching 8-K filings from EDGAR...")
        records = await fetcher.fetch(
            filing_type="8-K",
            days_back=1,
            limit=1,
        )

        normalised = []
        for raw in records:
            result = fetcher.normalise(raw)
            if result:
                normalised.append(result)

        print(f"    Fetched and normalised: {len(normalised)} records")

    print("\n[2] Writing to Postgres...")
    async with AsyncSessionLocal() as session:
        writer = DatabaseWriter(session)
        result = await writer.write_filings(normalised)
        print(f"    Inserted : {result['inserted']}")
        print(f"    Skipped  : {result['skipped']}")
        print(f"    Failed   : {result['failed']}")

    print("\n[3] Verifying in database...")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import text
        count = await session.execute(
            text("SELECT COUNT(*) FROM government_filings")
        )
        total = count.scalar_one()
        print(f"    Total filings in DB: {total}")

    print("\n" + "=" * 60)
    print("Pipeline test complete")
    print("=" * 60)


asyncio.run(main())