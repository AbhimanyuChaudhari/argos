"""
EDGAR XBRL Fetcher
------------------
Fetches financial facts directly from SEC EDGAR XBRL API.
Free, no API key required.

Endpoints used:
  - https://data.sec.gov/submissions/CIK{cik}.json       — latest filing dates (change detection)
  - https://data.sec.gov/api/xbrl/companyfacts/{CIK}.json — all financial facts

Rate limit: 10 requests/second per SEC fair use policy.
We stay well under with a 0.15s delay between requests.
"""

import asyncio
import httpx
import json
import logging
from datetime import datetime, date
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

HEADERS = {
    "User-Agent": "Argos Financial Terminal contact@argos.finance",
    "Accept": "application/json",
}

REQUEST_DELAY = 0.15


def _pad_cik(cik: str) -> str:
    """SEC CIK must be zero-padded to 10 digits."""
    return str(cik).lstrip("0").zfill(10)


async def get_latest_filing_date(cik: str) -> Optional[date]:
    """
    Check the latest 10-K or 10-Q filing date for a company.
    Used by change detector to decide whether to re-fetch.
    """
    padded = _pad_cik(cik)
    url = SUBMISSIONS_URL.format(cik=padded)

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            data = r.json()

        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])

        for form, filing_date in zip(forms, dates):
            if form in ("10-K", "10-Q"):
                return datetime.strptime(filing_date, "%Y-%m-%d").date()

        return None

    except Exception as e:
        logger.error(f"Failed to get latest filing date for CIK {cik}: {e}")
        return None


async def fetch_company_facts(cik: str) -> Optional[dict]:
    """
    Fetch all XBRL financial facts for a company from SEC EDGAR.
    Returns raw JSON dict or None on failure.
    """
    padded = _pad_cik(cik)
    url = COMPANY_FACTS_URL.format(cik=padded)

    for attempt in range(3):
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(url, headers=HEADERS, timeout=30)

                if r.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limited for CIK {cik}, waiting {wait}s")
                    await asyncio.sleep(wait)
                    continue

                r.raise_for_status()
                return r.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"CIK {cik} not found on EDGAR")
                return None
            logger.error(f"HTTP error for CIK {cik} (attempt {attempt+1}): {e}")
            await asyncio.sleep(2 ** attempt)

        except Exception as e:
            logger.error(f"Error fetching CIK {cik} (attempt {attempt+1}): {e}")
            await asyncio.sleep(2 ** attempt)

    return None


async def fetch_company_facts_with_delay(cik: str) -> Optional[dict]:
    """Fetch with rate limit delay — use this in batch processing."""
    await asyncio.sleep(REQUEST_DELAY)
    return await fetch_company_facts(cik)


def save_raw_to_disk(cik: str, ticker: str, data: dict, output_dir: str = "/tmp/argos_xbrl") -> str:
    """
    Save raw XBRL JSON to disk as backup before parsing.
    In production this goes to S3. For now saves locally.
    Returns the file path.
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    filename = f"{ticker}_{cik}_{datetime.utcnow().strftime('%Y%m%d')}.json"
    filepath = path / filename

    with open(filepath, "w") as f:
        json.dump(data, f)

    logger.info(f"Saved raw XBRL for {ticker} ({cik}) to {filepath}")
    return str(filepath)


def extract_concept_values(
    facts: dict,
    concept: str,
    namespace: str = "us-gaap",
    unit: str = "USD",
    forms: tuple = ("10-K", "10-Q"),
) -> list:
    """
    Extract all values for a specific XBRL concept from company facts.

    Returns list of dicts:
    [
        {
            "value": 383285000000,
            "period_end": "2023-09-30",
            "period_start": "2022-10-01",
            "form": "10-K",
            "filed_at": "2023-11-02",
            "period_type": "annual",
            "unit": "USD",
        },
        ...
    ]
    """
    try:
        concept_data = facts.get("facts", {}).get(namespace, {}).get(concept, {})
        if not concept_data:
            return []

        units_data = concept_data.get("units", {}).get(unit, [])

        # Try shares unit (for shares outstanding)
        if not units_data:
            units_data = concept_data.get("units", {}).get("shares", [])
            if units_data:
                unit = "shares"

        # Try USD/shares unit (for EPS)
        if not units_data:
            units_data = concept_data.get("units", {}).get("USD/shares", [])
            if units_data:
                unit = "USD/shares"

        if not units_data:
            return []

        results = []
        seen = set()

        for entry in units_data:
            form = entry.get("form", "")
            if form not in forms:
                continue

            period_end = entry.get("end")
            if not period_end:
                continue

            key = (period_end, form)
            if key in seen:
                continue
            seen.add(key)

            start = entry.get("start")
            if start:
                start_date = datetime.strptime(start, "%Y-%m-%d").date()
                end_date = datetime.strptime(period_end, "%Y-%m-%d").date()
                days = (end_date - start_date).days
                period_type = "annual" if days > 300 else "quarterly"
            else:
                period_type = "instant"

            filed = entry.get("filed")

            results.append({
                "value": entry.get("val"),
                "period_end": period_end,
                "period_start": start,
                "form": form,
                "filed_at": filed,
                "period_type": period_type,
                "unit": unit,
            })

        results.sort(key=lambda x: x["period_end"], reverse=True)
        return results

    except Exception as e:
        logger.error(f"Error extracting concept {concept}: {e}")
        return []


async def lookup_cik_by_ticker(ticker: str) -> Optional[str]:
    """
    Look up CIK for a ticker using SEC EDGAR company search.
    Returns CIK string or None.
    """
    url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt=2020-01-01&forms=10-K"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            data = r.json()
            hits = data.get("hits", {}).get("hits", [])
            if hits:
                return hits[0].get("_source", {}).get("entity_id")
        return None
    except Exception as e:
        logger.error(f"CIK lookup failed for {ticker}: {e}")
        return None


async def test_fetch(ticker: str = "AAPL", cik: str = "0000320193"):
    """Quick test — fetch AAPL facts and print revenue values."""
    print(f"Fetching XBRL facts for {ticker} (CIK: {cik})...")
    data = await fetch_company_facts(cik)
    if not data:
        print("Failed to fetch data")
        return

    print(f"Entity: {data.get('entityName')}")
    print(f"Total concepts: {len(data.get('facts', {}).get('us-gaap', {}))}")

    revenues = extract_concept_values(data, "Revenues")
    if not revenues:
        revenues = extract_concept_values(
            data, "RevenueFromContractWithCustomerExcludingAssessedTax"
        )

    print(f"\nRevenue data ({len(revenues)} periods):")
    for r in revenues[:5]:
        val_b = r['value'] / 1e9 if r['value'] else 0
        print(f"  {r['period_end']} ({r['period_type']}, {r['form']}): ${val_b:.1f}B")


if __name__ == "__main__":
    asyncio.run(test_fetch())