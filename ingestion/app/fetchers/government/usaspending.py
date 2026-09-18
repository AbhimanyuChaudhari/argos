from datetime import datetime, timezone, timedelta
from typing import Optional
from loguru import logger

from app.fetchers.base import BaseFetcher
from app.core.config import settings


class USASpendingFetcher(BaseFetcher):
    """
    Fetches federal contract awards from USASpending.gov API.
    No API key required — completely free.
    Data comes directly from the US Treasury.

    API docs: https://api.usaspending.gov
    Base URL: https://api.usaspending.gov/api/v2
    """

    SOURCE_NAME = "usaspending"
    BASE_URL = "https://api.usaspending.gov/api/v2"

    # Award types we care about
    AWARD_TYPES = [
        "A",  # BPA Call
        "B",  # Purchase Order
        "C",  # Delivery Order
        "D",  # Definitive Contract
    ]

    # Major defense and government agencies
    # We use these to filter for financially significant contracts
    MAJOR_AGENCIES = [
        "Department of Defense",
        "Department of Health and Human Services",
        "Department of Energy",
        "Department of Homeland Security",
        "Department of Transportation",
        "National Aeronautics and Space Administration",
        "Department of Veterans Affairs",
        "Department of Justice",
        "Department of the Treasury",
        "Department of State",
    ]

    async def fetch(
        self,
        days_back: int = 7,
        limit: int = 100,
        min_amount: float = 1000000,
        **kwargs,
    ) -> list[dict]:
        """
        Fetches recent contract awards from USASpending.
        Filters for contracts above min_amount to focus
        on financially significant awards.

        Args:
            days_back: How many days back to search
            limit: Max records to return
            min_amount: Minimum contract value in USD
        """
        date_from = (
            datetime.now(timezone.utc) - timedelta(days=days_back)
        ).strftime("%Y-%m-%d")

        date_to = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # USASpending uses POST requests for search
        url = f"{self.BASE_URL}/search/spending_by_award/"

        payload = {
            "filters": {
                "time_period": [
                    {
                        "start_date": date_from,
                        "end_date": date_to,
                    }
                ],
                "award_type_codes": self.AWARD_TYPES,
                "award_amounts": [
                    {
                        "lower_bound": min_amount,
                    }
                ],
            },
            "fields": [
                "Award ID",
                "Recipient Name",
                "Start Date",
                "End Date",
                "Award Amount",
                "Awarding Agency",
                "Awarding Sub Agency",
                "Contract Award Type",
                "recipient_id",
                "place_of_performance_city_name",
                "place_of_performance_state_code",
                "place_of_performance_country_code",
                "naics_code",
                "naics_description",
                "psc_code",
                "psc_description",
                "type_description",
                "description",
                "base_and_all_options_value",
                "base_exercised_options_val",
                "awarding_agency_id",
                "funding_agency_id",
            ],
            "sort": "Award Amount",
            "order": "desc",
            "limit": limit,
            "page": 1,
        }

        logger.info(
            f"Fetching contracts from USASpending "
            f"since {date_from} "
            f"min_amount=${min_amount:,.0f}"
        )

        try:
            data = await self._post(url, payload=payload)
            results = data.get("results", [])
            logger.info(
                f"USASpending returned {len(results)} contracts"
            )
            return results
        except Exception as e:
            logger.error(f"USASpending fetch failed: {e}")
            return []

    async def fetch_by_agency(
        self,
        agency_name: str,
        days_back: int = 30,
        limit: int = 50,
    ) -> list[dict]:
        """
        Fetches contracts for a specific agency.
        Useful for sector-specific analysis.
        """
        date_from = (
            datetime.now(timezone.utc) - timedelta(days=days_back)
        ).strftime("%Y-%m-%d")
        date_to = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        url = f"{self.BASE_URL}/search/spending_by_award/"

        payload = {
            "filters": {
                "time_period": [
                    {
                        "start_date": date_from,
                        "end_date": date_to,
                    }
                ],
                "award_type_codes": self.AWARD_TYPES,
                "agencies": [
                    {
                        "type": "awarding",
                        "tier": "toptier",
                        "name": agency_name,
                    }
                ],
            },
            "fields": [
                "Award ID",
                "Recipient Name",
                "Start Date",
                "End Date",
                "Award Amount",
                "Awarding Agency",
                "Awarding Sub Agency",
                "Contract Award Type",
                "naics_code",
                "naics_description",
                "psc_code",
                "description",
                "base_and_all_options_value",
            ],
            "sort": "Award Amount",
            "order": "desc",
            "limit": limit,
            "page": 1,
        }

        logger.info(
            f"Fetching contracts for agency: {agency_name}"
        )

        try:
            data = await self._post(url, payload=payload)
            results = data.get("results", [])
            logger.info(
                f"Agency {agency_name}: {len(results)} contracts"
            )
            return results
        except Exception as e:
            logger.error(
                f"USASpending agency fetch failed "
                f"for {agency_name}: {e}"
            )
            return []

    async def fetch_by_recipient(
        self,
        recipient_name: str,
        days_back: int = 365,
        limit: int = 50,
    ) -> list[dict]:
        """
        Fetches all contracts for a specific company.
        Used to build the government revenue profile
        for a stock in the terminal.
        """
        date_from = (
            datetime.now(timezone.utc) - timedelta(days=days_back)
        ).strftime("%Y-%m-%d")
        date_to = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        url = f"{self.BASE_URL}/search/spending_by_award/"

        payload = {
            "filters": {
                "time_period": [
                    {
                        "start_date": date_from,
                        "end_date": date_to,
                    }
                ],
                "award_type_codes": self.AWARD_TYPES,
                "recipient_search_text": [recipient_name],
            },
            "fields": [
                "Award ID",
                "Recipient Name",
                "Start Date",
                "End Date",
                "Award Amount",
                "Awarding Agency",
                "Awarding Sub Agency",
                "Contract Award Type",
                "naics_code",
                "naics_description",
                "psc_code",
                "description",
                "base_and_all_options_value",
            ],
            "sort": "Award Amount",
            "order": "desc",
            "limit": limit,
            "page": 1,
        }

        logger.info(
            f"Fetching contracts for recipient: {recipient_name}"
        )

        try:
            data = await self._post(url, payload=payload)
            results = data.get("results", [])
            logger.info(
                f"Recipient {recipient_name}: "
                f"{len(results)} contracts"
            )
            return results
        except Exception as e:
            logger.error(
                f"USASpending recipient fetch failed "
                f"for {recipient_name}: {e}"
            )
            return []

    def normalise(self, raw: dict) -> Optional[dict]:
        """
        Converts raw USASpending contract into
        a dict matching the GovernmentContract model.
        Returns None if essential fields missing.
        """
        award_id = raw.get("Award ID", "")
        if not award_id:
            return None

        recipient_name = raw.get("Recipient Name", "")
        if not recipient_name:
            return None

        # Financial amounts
        total_amount = raw.get("Award Amount", 0) or 0
        potential_amount = raw.get("base_and_all_options_value", 0)
        base_amount = raw.get("base_exercised_options_val", 0) or total_amount

        # Dates
        start_date = None
        start_str = raw.get("Start Date", "")
        if start_str:
            try:
                start_date = datetime.strptime(
                    start_str, "%Y-%m-%d"
                ).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        if not start_date:
            start_date = datetime.now(timezone.utc)

        end_date = None
        end_str = raw.get("End Date", "")
        if end_str:
            try:
                end_date = datetime.strptime(
                    end_str, "%Y-%m-%d"
                ).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        # Agency info
        agency_name = raw.get("Awarding Agency", "")
        sub_agency_name = raw.get("Awarding Sub Agency", "")
        agency_id = str(raw.get("awarding_agency_id", "")) or award_id[:10]

        # Recipient info
        recipient_id = str(raw.get("recipient_id", "")) or recipient_name[:20]
        recipient_uei = raw.get("recipient_uei", "")

        # Location
        recipient_state = raw.get(
            "place_of_performance_state_code", ""
        )
        place = raw.get("place_of_performance_city_name", "")
        state = recipient_state or ""
        place_of_performance = (
            f"{place}, {state}".strip(", ")
            if place or state else None
        )

        # Classification
        naics_code = str(raw.get("naics_code", "")) or None
        naics_description = raw.get("naics_description", "")
        psc_code = raw.get("psc_code", "")
        psc_description = raw.get("psc_description", "")

        # Award type
        award_type = (
            raw.get("type_description", "")
            or raw.get("Contract Award Type", "Contract")
        )

        # Description
        description = raw.get("description", "") or f"Contract award to {recipient_name}"

        # Build USASpending URL
        url = (
            f"https://www.usaspending.gov/award/{award_id}/"
        )

        return {
            "award_id": award_id,
            "award_type": award_type or "Contract",
            "description": description[:2000],
            "total_amount": float(total_amount),
            "base_amount": float(base_amount),
            "potential_amount": float(potential_amount) if potential_amount else None,
            "start_date": start_date,
            "end_date": end_date,
            "signed_date": start_date,
            "agency_id": agency_id or "unknown",
            "agency_name": agency_name or "Unknown Agency",
            "sub_agency_name": sub_agency_name or None,
            "agency_code": None,
            "recipient_id": recipient_id or "unknown",
            "recipient_name": recipient_name,
            "recipient_uei": recipient_uei or None,
            "parent_recipient_name": None,
            "ticker": None,
            "recipient_country": "US",
            "recipient_state": state or None,
            "congressional_district": None,
            "place_of_performance": place_of_performance,
            "naics_code": naics_code,
            "naics_description": naics_description or None,
            "psc_code": psc_code or None,
            "psc_description": psc_description or None,
            "is_compete": True,
            "number_of_offers": None,
            "country": "US",
            "region": "AMER",
            "url": url,
            "raw_data": raw,
        }

    async def _post(
        self,
        url: str,
        payload: dict,
    ) -> dict:
        """
        Makes a POST request to USASpending API.
        USASpending uses POST for all search endpoints.
        """
        if not self.client:
            raise RuntimeError(
                "Client not initialised. "
                "Use async with fetcher as f: syntax."
            )

        logger.debug(f"POST {url}")

        response = await self.client.post(
            url,
            json=payload,
            headers={
                **self._get_headers(),
                "Content-Type": "application/json",
            },
        )

        if response.status_code == 429:
            import asyncio
            retry_after = int(
                response.headers.get("Retry-After", 60)
            )
            logger.warning(
                f"Rate limited by USASpending. "
                f"Waiting {retry_after}s"
            )
            await asyncio.sleep(retry_after)
            response = await self.client.post(url, json=payload)

        response.raise_for_status()
        return response.json()