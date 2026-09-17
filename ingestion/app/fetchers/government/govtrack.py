from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from app.fetchers.base import BaseFetcher
from app.core.config import settings


class GovTrackFetcher(BaseFetcher):
    """
    Fetches US Congressional bills from GovTrack.us API.
    No API key required — completely free.

    API docs: https://www.govtrack.us/developers/api
    Base URL: https://www.govtrack.us/api/v2
    """

    SOURCE_NAME = "govtrack"
    BASE_URL = "https://www.govtrack.us/api/v2"

    # Current Congress number
    CURRENT_CONGRESS = 119

    # GovTrack bill type to our enum mapping
    BILL_TYPE_MAP = {
        "house_bill": "hr",
        "senate_bill": "s",
        "house_resolution": "hres",
        "senate_resolution": "sres",
        "house_joint_resolution": "hjres",
        "senate_joint_resolution": "sjres",
        "house_concurrent_resolution": "hconres",
        "senate_concurrent_resolution": "sconres",
        # Short form fallbacks
        "h": "hr",
        "s": "s",
        "hr": "hres",
        "sr": "sres",
        "hj": "hjres",
        "sj": "sjres",
        "hc": "hconres",
        "sc": "sconres",
    }

    # GovTrack status to our BillStatus enum mapping
    STATUS_MAP = {
        "introduced": "introduced",
        "referred": "referred",
        "reported": "passed_committee",
        "pass_over_house": "passed_house",
        "pass_over_senate": "passed_senate",
        "passed_simpleres": "passed_both",
        "pass_back_house": "passed_house",
        "pass_back_senate": "passed_senate",
        "conference_passed_house": "passed_both",
        "conference_passed_senate": "passed_both",
        "enacted_signed": "signed",
        "enacted_veto_override": "veto_overridden",
        "vetoed_pocket": "vetoed",
        "vetoed_override_fail_originating_house": "vetoed",
        "vetoed_override_fail_originating_senate": "vetoed",
        "failed_originating_house": "failed",
        "failed_originating_senate": "failed",
        "failed_second_house": "failed",
        "failed_second_senate": "failed",
        "prov_kill_suspensionfailed": "failed",
        "prov_kill_cloturefailed": "failed",
        "prov_kill_pingpongfail": "failed",
        "prov_kill_veto": "vetoed",
        "enacted_carryover": "signed",
    }

    # Subject tag to PolicyArea mapping
    POLICY_AREA_MAP = {
        "economics": "economics",
        "finance": "finance",
        "banking": "finance",
        "securities": "finance",
        "insurance": "finance",
        "taxation": "economics",
        "budget": "economics",
        "trade": "trade",
        "import": "trade",
        "export": "trade",
        "tariff": "trade",
        "energy": "energy",
        "oil": "energy",
        "gas": "energy",
        "renewable": "energy",
        "health": "healthcare",
        "medicare": "healthcare",
        "medicaid": "healthcare",
        "pharma": "healthcare",
        "drug": "healthcare",
        "technology": "technology",
        "internet": "technology",
        "cybersecurity": "technology",
        "artificial intelligence": "technology",
        "defense": "defense",
        "military": "defense",
        "armed forces": "defense",
        "weapons": "defense",
        "environment": "environment",
        "climate": "environment",
        "emission": "environment",
        "infrastructure": "infrastructure",
        "transportation": "infrastructure",
        "broadband": "infrastructure",
        "agriculture": "agriculture",
        "farm": "agriculture",
        "food": "agriculture",
        "housing": "housing",
        "mortgage": "housing",
        "real estate": "housing",
        "labor": "labor",
        "employment": "labor",
        "wage": "labor",
        "immigration": "immigration",
        "visa": "immigration",
        "border": "immigration",
        "foreign": "foreign_policy",
        "sanction": "foreign_policy",
        "treaty": "foreign_policy",
        "diplomacy": "foreign_policy",
    }

    async def fetch(
        self,
        congress: int = None,
        bill_type: str = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs,
    ) -> list[dict]:
        """
        Fetches bills from GovTrack API.
        """
        if congress is None:
            congress = self.CURRENT_CONGRESS

        params = {
            "congress": congress,
            "limit": limit,
            "offset": offset,
            "order_by": "-introduced_date",
        }

        if bill_type:
            params["bill_type"] = bill_type

        url = f"{self.BASE_URL}/bill"

        logger.info(
            f"Fetching bills from GovTrack "
            f"congress={congress} "
            f"bill_type={bill_type or 'all'} "
            f"offset={offset}"
        )

        try:
            data = await self._get(url, params=params)
            bills = data.get("objects", [])
            total = data.get("meta", {}).get("total_count", 0)
            logger.info(
                f"GovTrack returned {len(bills)} bills "
                f"(total={total})"
            )
            return bills
        except Exception as e:
            logger.error(f"GovTrack fetch failed: {e}")
            return []

    async def fetch_recent(
        self,
        days_back: int = 7,
        limit: int = 100,
    ) -> list[dict]:
        """
        Fetches bills introduced in the last N days.
        Used by the daily scheduler.
        """
        from datetime import timedelta

        date_from = (
            datetime.now(timezone.utc) - timedelta(days=days_back)
        ).strftime("%Y-%m-%d")

        params = {
            "congress": self.CURRENT_CONGRESS,
            "introduced_date__gte": date_from,
            "limit": limit,
            "order_by": "-introduced_date",
        }

        url = f"{self.BASE_URL}/bill"

        logger.info(
            f"Fetching recent bills since {date_from}"
        )

        try:
            data = await self._get(url, params=params)
            bills = data.get("objects", [])
            logger.info(
                f"GovTrack returned {len(bills)} recent bills"
            )
            return bills
        except Exception as e:
            logger.error(f"GovTrack recent fetch failed: {e}")
            return []

    async def fetch_active(
        self,
        limit: int = 100,
    ) -> list[dict]:
        """
        Fetches bills currently active in Congress.
        """
        active_statuses = [
            "introduced",
            "referred",
            "reported",
        ]

        all_bills = []
        for status in active_statuses:
            params = {
                "congress": self.CURRENT_CONGRESS,
                "current_status": status,
                "limit": limit,
                "order_by": "-current_status_date",
            }

            try:
                data = await self._get(
                    f"{self.BASE_URL}/bill",
                    params=params,
                )
                bills = data.get("objects", [])
                all_bills.extend(bills)
                logger.info(
                    f"Status {status}: {len(bills)} bills"
                )
            except Exception as e:
                logger.error(
                    f"GovTrack active fetch failed "
                    f"for status {status}: {e}"
                )

        return all_bills

    async def fetch_by_id(
        self,
        bill_id: int,
    ) -> Optional[dict]:
        """
        Fetches a single bill by GovTrack ID.
        """
        url = f"{self.BASE_URL}/bill/{bill_id}"
        try:
            return await self._get_with_fallback(url)
        except Exception as e:
            logger.error(
                f"GovTrack bill {bill_id} fetch failed: {e}"
            )
            return None

    def _map_bill_type(self, bill_type: str) -> str:
        """
        Maps GovTrack bill type to our BillType enum value.
        """
        return self.BILL_TYPE_MAP.get(bill_type, "hr")

    def _map_status(self, status: str) -> str:
        """
        Maps GovTrack status string to our BillStatus enum value.
        """
        return self.STATUS_MAP.get(status, "introduced")

    def _map_policy_area(self, subjects: list) -> str:
        """
        Maps GovTrack subject tags to our PolicyArea enum.
        """
        if not subjects:
            return "other"

        subjects_lower = " ".join(
            str(s).lower() for s in subjects
        )

        for keyword, policy_area in self.POLICY_AREA_MAP.items():
            if keyword in subjects_lower:
                return policy_area

        return "other"

    def _map_chamber(self, bill_type: str) -> str:
        """
        Determines which chamber a bill originates from.
        """
        house_types = [
            "house_bill",
            "house_resolution",
            "house_joint_resolution",
            "house_concurrent_resolution",
            "h", "hr", "hj", "hc",
        ]
        if bill_type in house_types:
            return "house"
        return "senate"

    def normalise(self, raw: dict) -> Optional[dict]:
        """
        Converts raw GovTrack bill into
        a dict matching the Bill model.
        """
        # Use congress + bill_type + number as unique identifier
        congress = raw.get("congress", self.CURRENT_CONGRESS)
        bill_number_raw = raw.get("number")
        bill_type_raw = raw.get("bill_type", "house_bill")

        if not bill_number_raw:
            return None

        title = raw.get("title", "")
        if not title:
            return None

        # Bill type mapping
        bill_type = self._map_bill_type(bill_type_raw)

        # Use display_number if available e.g. "H.J.Res. 216"
        display_number = raw.get("display_number", "")
        bill_number = (
            display_number if display_number
            else f"{bill_type}-{bill_number_raw}"
        )

        # Status
        status_raw = raw.get("current_status", "introduced")
        status = self._map_status(status_raw)

        # Chamber
        chamber = raw.get("current_chamber", "house")
        if chamber not in ("house", "senate"):
            chamber = self._map_chamber(bill_type_raw)

        # ... rest of normalise stays the same

        # Parse introduced date
        introduced_str = raw.get("introduced_date", "")
        try:
            introduced_at = datetime.strptime(
                introduced_str, "%Y-%m-%d"
            ).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid introduced_date: {introduced_str}"
            )
            return None

        # Parse last action date
        last_action_str = raw.get("current_status_date", "")
        last_action_at = None
        if last_action_str:
            try:
                last_action_at = datetime.strptime(
                    last_action_str, "%Y-%m-%d"
                ).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        # Sponsor — firstname and lastname separate
        sponsor = raw.get("sponsor") or {}
        sponsor_bioguide_id = sponsor.get("bioguideid")
        firstname = sponsor.get("firstname", "")
        lastname = sponsor.get("lastname", "")
        sponsor_name = f"{firstname} {lastname}".strip() or None
        sponsor_party = sponsor.get("party")
        sponsor_state = sponsor.get("state")
        sponsor_chamber = chamber

        # URL — comes directly on the record
        url = raw.get("link", "")
        if not url:
            url = (
                f"https://www.govtrack.us/congress/bills/"
                f"{congress}/{bill_type_raw}{bill_number_raw}"
            )

        # Committees
        committees = []
        for c in raw.get("committees", []):
            name = c.get("committee", {}).get("name", "")
            if name:
                committees.append(name)

        # Subjects from terms array
        subjects = []
        for term in raw.get("terms", []):
            name = term.get("name", "")
            if name:
                subjects.append(name)

        # Policy area — try subjects first then title
        policy_area = self._map_policy_area(subjects)
        if policy_area == "other":
            policy_area = self._map_policy_area([title])

        # Related bills
        related_bills = []
        for rb in raw.get("related_bills", []):
            related = rb.get("related_bill", {})
            if related:
                rb_display = related.get("display_number", "")
                if rb_display:
                    related_bills.append(rb_display)

        return {
            "bill_number": bill_number,
            "bill_type": bill_type,
            "congress_number": congress,
            "title": title,
            "short_title": raw.get("short_title"),
            "summary": raw.get("current_status_description"),
            "url": url,
            "status": status,
            "chamber": chamber,
            "policy_area": policy_area,
            "country": "US",
            "region": "AMER",
            "introduced_at": introduced_at,
            "last_action_at": last_action_at,
            "sponsor_bioguide_id": sponsor_bioguide_id,
            "sponsor_name": sponsor_name,
            "sponsor_party": sponsor_party,
            "sponsor_state": sponsor_state,
            "sponsor_chamber": sponsor_chamber,
            "cosponsors_count": raw.get("cosponsor_count", 0),
            "actions": raw.get("major_actions") or None,
            "committees": committees if committees else None,
            "related_bills": related_bills if related_bills else None,
            "subjects": subjects if subjects else None,
            "raw_data": raw,
        }