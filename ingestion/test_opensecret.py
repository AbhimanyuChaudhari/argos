import asyncio
from app.fetchers.government.opensecrets import OpenSecretsFetcher
from app.db.writer import DatabaseWriter, AsyncSessionLocal


async def main():
    print("=" * 60)
    print("ARGOS — OpenSecrets Pipeline Test")
    print("=" * 60)

    async with OpenSecretsFetcher() as fetcher:

        print("\n[1] Fetching top finance industry lobbying...")
        records = await fetcher.fetch_industry_lobbying(
            industry_id="F09",
            cycle="2024",
        )
        print(f"    Raw records: {len(records)}")

        print("\n[2] Normalising...")
        normalised = []
        for raw in records:
            result = fetcher.normalise(raw)
            if result:
                normalised.append(result)
        print(f"    Normalised: {len(normalised)}")

        print("\n[3] Sample disclosures:")
        for i, d in enumerate(normalised[:3], 1):
            print(f"\n    Disclosure {i}:")
            print(f"      Client   : {d['client_name']}")
            print(f"      Industry : {d['client_industry']}")
            print(f"      Amount   : ${d['amount']:,.0f}")
            print(f"      Period   : {d['filing_period']}")
            print(f"      ID       : {d['filing_id']}")

    print("\n[4] Writing to Postgres...")
    async with AsyncSessionLocal() as session:
        writer = DatabaseWriter(session)
        result = await writer.write_lobbying(normalised)
        print(f"    Inserted : {result['inserted']}")
        print(f"    Skipped  : {result['skipped']}")
        print(f"    Failed   : {result['failed']}")

    print("\n[5] Verifying...")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import text
        count = await session.execute(
            text("SELECT COUNT(*) FROM government_lobbying")
        )
        print(f"    Total disclosures in DB: {count.scalar_one()}")

    print("\n" + "=" * 60)
    print("OpenSecrets test complete")
    print("=" * 60)


asyncio.run(main())