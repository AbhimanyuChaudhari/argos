from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from app.fetchers.base import BaseFetcher
from app.core.config import settings


class OpenSecretsFetcher(BaseFetcher):
    """
    Fetches lobbying disclosures from OpenSecrets API.
    Requires a free API key from opensecrets.org.

    API docs: https://www.opensecrets.org/api/
    Base URL: https://www.opensecrets.org/api
    """

    SOURCE_NAME = "opensecrets"
    BASE_URL = "https://www.opensecrets.org/api"

    def _get_headers(self) -> dict:
        return {
            "User-Agent": "Argos Financial Terminal contact@argos.finance",
            "Accept": "application/json",
        }

    async def fetch(
        self,
        cycle: str = "2024",
        limit: int = 100,
        **kwargs,
    ) -> list[dict]:
        """
        Fetches top lobbying spenders for a cycle.

        Args:
            cycle: Election cycle year e.g. 2024
            limit: Max records to return
        """
        if not settings.OPENSECRETS_API_KEY:
            logger.warning(
                "No OpenSecrets API key configured. "
                "Set OPENSECRETS_API_KEY in .env"
            )
            return []

        params = {
            "method": "getLobbyists",
            "apikey": settings.OPENSECRETS_API_KEY,
            "output": "json",
        }

        logger.info(
            f"Fetching lobbying data from OpenSecrets "
            f"cycle={cycle}"
        )

        try:
            data = await self._get(self.BASE_URL, params=params)
            results = (
                data.get("response", {})
                    .get("lobbyist", [])
            )
            if isinstance(results, dict):
                results = [results]
            logger.info(
                f"OpenSecrets returned {len(results)} records"
            )
            return results
        except Exception as e:
            logger.error(f"OpenSecrets fetch failed: {e}")
            return []

    async def fetch_org_lobbying(
        self,
        org_id: str,
        cycle: str = "2024",
    ) -> list[dict]:
        """
        Fetches lobbying data for a specific organization.

        Args:
            org_id: OpenSecrets organization ID
            cycle: Election cycle year
        """
        if not settings.OPENSECRETS_API_KEY:
            logger.warning("No OpenSecrets API key configured")
            return []

        params = {
            "method": "orgSummary",
            "id": org_id,
            "cycle": cycle,
            "apikey": settings.OPENSECRETS_API_KEY,
            "output": "json",
        }

        try:
            data = await self._get(self.BASE_URL, params=params)
            results = (
                data.get("response", {})
                    .get("organization", [])
            )
            if isinstance(results, dict):
                results = [results]
            return results
        except Exception as e:
            logger.error(
                f"OpenSecrets org fetch failed for {org_id}: {e}"
            )
            return []

    async def fetch_industry_lobbying(
        self,
        industry_id: str,
        cycle: str = "2024",
    ) -> list[dict]:
        """
        Fetches lobbying data for a specific industry.
        Industry IDs from OpenSecrets sector codes.

        Common IDs:
            F10 — Finance / Credit
            F09 — Securities & Investment
            H04 — Pharmaceuticals
            E01 — Oil & Gas
            D06 — Defense Aerospace
        """
        if not settings.OPENSECRETS_API_KEY:
            logger.warning("No OpenSecrets API key configured")
            return []

        params = {
            "method": "getOrgs",
            "id": industry_id,
            "cycle": cycle,
            "apikey": settings.OPENSECRETS_API_KEY,
            "output": "json",
        }

        try:
            data = await self._get(self.BASE_URL, params=params)
            results = (
                data.get("response", {})
                    .get("organization", [])
            )
            if isinstance(results, dict):
                results = [results]
            logger.info(
                f"Industry {industry_id}: "
                f"{len(results)} organizations"
            )
            return results
        except Exception as e:
            logger.error(
                f"OpenSecrets industry fetch failed "
                f"for {industry_id}: {e}"
            )
            return []

    async def fetch_top_spenders(
        self,
        cycle: str = "2024",
        limit: int = 50,
    ) -> list[dict]:
        """
        Fetches top lobbying spenders across all industries.
        Used for the lobbying dashboard in the terminal.
        """
        if not settings.OPENSECRETS_API_KEY:
            logger.warning("No OpenSecrets API key configured")
            return []

        # Top financially relevant industries
        industry_ids = [
            "F10",  # Finance / Credit
            "F09",  # Securities & Investment
            "H04",  # Pharmaceuticals
            "E01",  # Oil & Gas
            "D06",  # Defense Aerospace
            "K02",  # Technology
        ]

        all_results = []
        for industry_id in industry_ids:
            results = await self.fetch_industry_lobbying(
                industry_id, cycle
            )
            all_results.extend(results)

        logger.info(
            f"Total top spenders fetched: {len(all_results)}"
        )
        return all_results[:limit]

    def normalise(self, raw: dict) -> Optional[dict]:
        """
        Converts raw OpenSecrets lobbying record into
        a dict matching the LobbyingDisclosure model.
        Returns None if essential fields missing.
        """
        # OpenSecrets uses @attributes pattern
        attrs = raw.get("@attributes", raw)

        org_name = (
            attrs.get("orgname")
            or attrs.get("name")
            or attrs.get("client_name", "")
        )
        if not org_name:
            return None

        # Generate a unique filing ID
        org_id = attrs.get("orgid", "")
        cycle = attrs.get("cycle", "2024")
        filing_id = f"OS-{org_id}-{cycle}" if org_id else None
        if not filing_id:
            filing_id = f"OS-{org_name[:20]}-{cycle}"

        # Financial amount
        total_str = (
            attrs.get("total")
            or attrs.get("lobbying")
            or "0"
        )
        try:
            amount = float(str(total_str).replace(",", ""))
        except (ValueError, TypeError):
            amount = 0.0

        # Industry
        industry = (
            attrs.get("industry")
            or attrs.get("sector")
            or None
        )

        # Client and registrant
        client_id = attrs.get("orgid", org_name[:20])
        registrant_id = attrs.get("orgid", org_name[:20])
        registrant_name = org_name

        # Filing period
        filing_period = f"{cycle}"
        filing_year = int(cycle) if cycle.isdigit() else 2024

        # Filed date — OpenSecrets doesn't always provide
        # use Jan 1 of the cycle year as default
        filed_at = datetime(
            filing_year, 1, 1, tzinfo=timezone.utc
        )

        return {
            "filing_id": filing_id,
            "filing_type": "annual",
            "filing_year": filing_year,
            "filing_period": filing_period,
            "filed_at": filed_at,
            "amount": amount,
            "client_id": str(client_id),
            "client_name": org_name,
            "client_industry": industry,
            "ticker": None,
            "registrant_id": str(registrant_id),
            "registrant_name": registrant_name,
            "client_country": "US",
            "country": "US",
            "region": "AMER",
            "lobbyists": None,
            "issues": None,
            "has_former_government": False,
            "yoy_change": None,
            "url": (
                f"https://www.opensecrets.org/orgs/summary"
                f"?id={org_id}"
                if org_id else None
            ),
            "raw_data": attrs,
        }