import asyncio
import json
from app.fetchers.government.sec_edgar import SECEdgarFetcher


async def main():
    print("=" * 60)
    print("ARGOS — SEC EDGAR Fetcher Test")
    print("=" * 60)

    async with SECEdgarFetcher() as fetcher:

        # Test 1 — Fetch 8-K filings
        print("\n[1] Fetching 8-K filings from last 1 day...")
        records = await fetcher.fetch(
            filing_type="8-K",
            days_back=1,
            limit=5,
        )
        print(f"    Raw records fetched: {len(records)}")

        # Test 2 — Normalise
        print("\n[2] Normalising records...")
        normalised = []
        for raw in records:
            result = fetcher.normalise(raw)
            if result:
                normalised.append(result)

        print(f"    Normalised successfully: {len(normalised)}")
        print(f"    Skipped: {len(records) - len(normalised)}")

        # Test 3 — Show first 3 normalised records
        print("\n[3] Sample normalised records:")
        for i, r in enumerate(normalised[:3], 1):
            print(f"\n    Record {i}:")
            print(f"      Company : {r['company_name']}")
            print(f"      Type    : {r['filing_type']}")
            print(f"      Filed   : {r['filed_at']}")
            print(f"      CIK     : {r['cik']}")
            print(f"      URL     : {r['url']}")

        # Test 4 — Fetch by CIK (Apple)
        print("\n[4] Fetching Apple filings by CIK...")
        apple_records = await fetcher.fetch_by_cik("0000320193")
        print(f"    Apple filings found: {len(apple_records)}")
        if apple_records:
            sample = fetcher.normalise(apple_records[0])
            if sample:
                print(f"    Latest: {sample['filing_type']} — {sample['filed_at']}")

        # Test 5 — Check a normalised record has all required fields
        print("\n[5] Validating required fields...")
        required = [
            "title", "filing_type", "source", "status",
            "country", "region", "filed_at", "company_name",
        ]
        if normalised:
            missing = [f for f in required if not normalised[0].get(f)]
            if missing:
                print(f"    MISSING fields: {missing}")
            else:
                print(f"    All required fields present")

    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)


asyncio.run(main())