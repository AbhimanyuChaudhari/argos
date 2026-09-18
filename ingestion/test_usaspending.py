import asyncio
from app.fetchers.government.usaspending import USASpendingFetcher
from app.db.writer import DatabaseWriter, AsyncSessionLocal


async def main():
    print("=" * 60)
    print("ARGOS — USASpending Pipeline Test")
    print("=" * 60)

    async with USASpendingFetcher() as fetcher:

        print("\n[1] Fetching recent contracts over $1M...")
        records = await fetcher.fetch(
            days_back=30,
            limit=5,
            min_amount=1000000,
        )
        print(f"    Raw records: {len(records)}")

        print("\n[2] Normalising...")
        normalised = []
        for raw in records:
            result = fetcher.normalise(raw)
            if result:
                normalised.append(result)
        print(f"    Normalised: {len(normalised)}")

        print("\n[3] Sample contracts:")
        for i, c in enumerate(normalised[:3], 1):
            print(f"\n    Contract {i}:")
            print(f"      Award ID   : {c['award_id']}")
            print(f"      Recipient  : {c['recipient_name']}")
            print(f"      Agency     : {c['agency_name']}")
            print(f"      Amount     : ${c['total_amount']:,.0f}")
            print(f"      NAICS      : {c['naics_code']}")
            print(f"      Start      : {c['start_date']}")

        print("\n[4] Writing to Postgres...")
        async with AsyncSessionLocal() as session:
            writer = DatabaseWriter(session)
            result = await writer.write_contracts(normalised)
            print(f"    Inserted : {result['inserted']}")
            print(f"    Skipped  : {result['skipped']}")
            print(f"    Failed   : {result['failed']}")

    print("\n[5] Verifying...")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import text
        count = await session.execute(
            text("SELECT COUNT(*) FROM government_contracts")
        )
        print(f"    Total contracts in DB: {count.scalar_one()}")

    print("\n" + "=" * 60)
    print("USASpending test complete")
    print("=" * 60)


asyncio.run(main())