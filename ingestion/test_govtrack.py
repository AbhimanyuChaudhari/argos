import asyncio
import json
from app.fetchers.government.govtrack import GovTrackFetcher
from app.db.writer import DatabaseWriter, AsyncSessionLocal


async def main():
    print("=" * 60)
    print("ARGOS — GovTrack Pipeline Test")
    print("=" * 60)

    async with GovTrackFetcher() as fetcher:

        print("\n[1] Fetching recent bills...")
        records = await fetcher.fetch_recent(days_back=30, limit=5)
        print(f"    Raw records: {len(records)}")

        print("\n[2] Normalising...")
        normalised = []
        for raw in records:
            result = fetcher.normalise(raw)
            if result:
                normalised.append(result)
        print(f"    Normalised: {len(normalised)}")

        print("\n[3] Sample bills:")
        for i, b in enumerate(normalised[:3], 1):
            print(f"\n    Bill {i}:")
            print(f"      Number  : {b['bill_number']}")
            print(f"      Title   : {b['title'][:60]}...")
            print(f"      Status  : {b['status']}")
            print(f"      Chamber : {b['chamber']}")
            print(f"      Policy  : {b['policy_area']}")
            print(f"      Sponsor : {b['sponsor_name']}")
            print(f"      Party   : {b['sponsor_party']}")

    print("\n[4] Writing to Postgres...")
    async with AsyncSessionLocal() as session:
        writer = DatabaseWriter(session)
        result = await writer.write_bills(normalised)
        print(f"    Inserted : {result['inserted']}")
        print(f"    Skipped  : {result['skipped']}")
        print(f"    Failed   : {result['failed']}")

    print("\n[5] Verifying...")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import text
        count = await session.execute(
            text("SELECT COUNT(*) FROM government_bills")
        )
        print(f"    Total bills in DB: {count.scalar_one()}")

    print("\n" + "=" * 60)
    print("GovTrack test complete")
    print("=" * 60)


asyncio.run(main())