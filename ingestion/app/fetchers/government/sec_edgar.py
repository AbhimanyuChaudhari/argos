from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from app.fetchers.base import BaseFetcher
from app.core.config import settings


class SECEdgarFetcher(BaseFetcher):
    """
    Fetches SEC EDGAR filings.
    Uses the EDGAR full-text search API
    and submissions API.
    No API key required — completely free.

    SEC EDGAR APIs:
    - Search: https://efts.sec.gov/LATEST/search-index
    - Submissions: https://data.sec.gov/submissions/CIK{cik}.json
    - Filing index: https://www.sec.gov/cgi-bin/browse-edgar
    """

    SOURCE_NAME = "sec_edgar"
    BASE_URL = "https://efts.sec.gov/LATEST/search-index"

    # Filing types we care about
    FILING_TYPES = [
        "10-K",
        "10-Q",
        "8-K",
        "S-1",
        "DEF 14A",
        "4",
        "SC 13G",
        "SC 13D",
        "20-F",
        "6-K",
    ]

    async def fetch(
        self,
        filing_type: str = "10-K",
        days_back: int = 7,
        limit: int = 40,
        **kwargs,
    ) -> list[dict]:
        """
        Fetches recent filings from EDGAR full text search.

        Args:
            filing_type: SEC form type e.g. 10-K, 8-K
            days_back: How many days back to search
            limit: Max records to fetch per call
        """
        from datetime import timedelta

        date_from = (
            datetime.now(timezone.utc) - timedelta(days=days_back)
        ).strftime("%Y-%m-%d")

        params = {
            "q": f'"{filing_type}"',
            "dateRange": "custom",
            "startdt": date_from,
            "forms": filing_type,
            "_source": "file_date,period_of_report,entity_name,"
                       "file_num,form_type,biz_location,"
                       "inc_states,period_of_report",
            "hits.hits._source": "file_date,period_of_report,"
                                  "entity_name,file_num,form_type",
            "hits.hits.total": limit,
        }

        logger.info(
            f"Fetching {filing_type} filings from EDGAR "
            f"since {date_from}"
        )

        try:
            data = await self._get(self.BASE_URL, params=params)
            hits = data.get("hits", {}).get("hits", [])
            logger.info(f"EDGAR returned {len(hits)} {filing_type} filings")
            return hits
        except Exception as e:
            logger.error(f"EDGAR fetch failed: {e}")
            return []

    async def fetch_by_cik(
        self,
        cik: str,
    ) -> list[dict]:
        """
        Fetches all recent filings for a specific company
        using their SEC CIK number.
        CIK must be zero-padded to 10 digits.
        e.g. Apple = CIK 0000320193
        """
        cik_padded = str(cik).zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

        logger.info(f"Fetching submissions for CIK {cik_padded}")

        try:
            data = await self._get_with_fallback(url, fallback={})
            if not data:
                return []

            filings = data.get("filings", {}).get("recent", {})
            if not filings:
                return []

            # EDGAR returns parallel arrays — zip them together
            form_types = filings.get("form", [])
            accession_numbers = filings.get("accessionNumber", [])
            filing_dates = filings.get("filingDate", [])
            descriptions = filings.get("primaryDescription", [])
            primary_docs = filings.get("primaryDocument", [])

            company_name = data.get("name", "")
            ticker = ""
            tickers = data.get("tickers", [])
            if tickers:
                ticker = tickers[0]

            records = []
            for i, form_type in enumerate(form_types):
                if form_type not in self.FILING_TYPES:
                    continue
                records.append({
                    "_source": {
                        "form_type": form_type,
                        "accession_number": accession_numbers[i] if i < len(accession_numbers) else "",
                        "file_date": filing_dates[i] if i < len(filing_dates) else "",
                        "entity_name": company_name,
                        "ticker": ticker,
                        "description": descriptions[i] if i < len(descriptions) else "",
                        "primary_document": primary_docs[i] if i < len(primary_docs) else "",
                        "cik": cik_padded,
                    }
                })

            logger.info(
                f"CIK {cik_padded}: found {len(records)} "
                f"relevant filings"
            )
            return records

        except Exception as e:
            logger.error(f"EDGAR CIK fetch failed for {cik}: {e}")
            return []

    def normalise(self, raw: dict) -> Optional[dict]:
        """
        Converts raw EDGAR API response into
        a dict matching the GovernmentFiling model.
        """
        source = raw.get("_source", {})

        # Form type
        form_type = source.get("form") or source.get("form_type", "")
        if not form_type:
            return None

        # Company name — comes as array
        display_names = source.get("display_names", [])
        if display_names:
            # Format: "COMPANY NAME  (CIK 0000123456)"
            entity_name = display_names[0].split("(CIK")[0].strip()
        else:
            entity_name = source.get("entity_name", "")

        if not entity_name:
            return None

        # CIK — comes as array
        ciks = source.get("ciks", [])
        cik = ciks[0] if ciks else source.get("cik", "")

        # Accession number
        accession = source.get("adsh") or source.get("accession_number", "")

        # Parse filing date
        file_date_str = source.get("file_date", "")
        try:
            filed_at = datetime.strptime(
                file_date_str, "%Y-%m-%d"
            ).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            logger.warning(f"Invalid file_date: {file_date_str}")
            return None

        # Parse period of report
        period_str = source.get("period_ending", "") or source.get("period_of_report", "")
        period_of_report = None
        if period_str:
            try:
                period_of_report = datetime.strptime(
                    period_str, "%Y-%m-%d"
                ).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        # Build URL
        url = None
        if accession and cik:
            acc_clean = accession.replace("-", "")
            url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{int(cik)}/{acc_clean}/"
            )

        # Items reported (8-K specific)
        items = source.get("items", [])

        # Is amendment
        is_amendment = form_type.endswith("/A")

        return {
            "title": f"{form_type} — {entity_name}",
            "filing_type": form_type,
            "source": "sec_edgar",
            "status": "completed",
            "country": "US",
            "region": "AMER",
            "filed_at": filed_at,
            "url": url,
            "description": source.get("file_description", ""),
            "cik": cik,
            "accession_number": accession,
            "company_name": entity_name,
            "ticker": source.get("ticker") or None,
            "period_of_report": period_of_report,
            "is_amendment": is_amendment,
            "items": items if items else None,
            "raw_data": source,
        }

    async def fetch_all_types(
        self,
        days_back: int = 1,
    ) -> list[dict]:
        """
        Fetches all supported filing types
        for the last N days.
        Called by the daily scheduler.
        """
        all_records = []
        for filing_type in self.FILING_TYPES:
            records = await self.fetch(
                filing_type=filing_type,
                days_back=days_back,
            )
            normalised = []
            for raw in records:
                result = self.normalise(raw)
                if result:
                    normalised.append(result)
            all_records.extend(normalised)
            logger.info(
                f"Fetched {len(normalised)} {filing_type} filings"
            )

        logger.info(
            f"Total normalised filings: {len(all_records)}"
        )
        return all_records