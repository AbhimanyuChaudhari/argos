from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.models.government.lobbying import LobbyingDisclosure
from app.schemas.government.lobbying import (
    LobbyingCreate,
    LobbyingUpdate,
    LobbyingFilter,
    LobbyingListResponse,
    LobbyingResponse,
    LobbyingSpendSummary,
    LobbyingTickerSummary,
)


class LobbyingService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_disclosures(
        self,
        filters: LobbyingFilter,
    ) -> LobbyingListResponse:
        """
        Returns paginated list of lobbying disclosures
        with optional filters.
        """
        query = select(LobbyingDisclosure)
        count_query = select(func.count(LobbyingDisclosure.id))

        conditions = []

        if filters.client_name:
            conditions.append(
                LobbyingDisclosure.client_name.ilike(
                    f"%{filters.client_name}%"
                )
            )
        if filters.ticker:
            conditions.append(
                LobbyingDisclosure.ticker == filters.ticker.upper()
            )
        if filters.registrant_name:
            conditions.append(
                LobbyingDisclosure.registrant_name.ilike(
                    f"%{filters.registrant_name}%"
                )
            )
        if filters.client_industry:
            conditions.append(
                LobbyingDisclosure.client_industry.ilike(
                    f"%{filters.client_industry}%"
                )
            )
        if filters.filing_year:
            conditions.append(
                LobbyingDisclosure.filing_year == filters.filing_year
            )
        if filters.filing_period:
            conditions.append(
                LobbyingDisclosure.filing_period == filters.filing_period
            )
        if filters.min_amount is not None:
            conditions.append(
                LobbyingDisclosure.amount >= filters.min_amount
            )
        if filters.max_amount is not None:
            conditions.append(
                LobbyingDisclosure.amount <= filters.max_amount
            )
        if filters.has_former_government is not None:
            conditions.append(
                LobbyingDisclosure.has_former_government == filters.has_former_government
            )
        if filters.country:
            conditions.append(
                LobbyingDisclosure.country == filters.country.value
            )
        if filters.filed_after:
            conditions.append(
                LobbyingDisclosure.filed_at >= filters.filed_after
            )
        if filters.filed_before:
            conditions.append(
                LobbyingDisclosure.filed_at <= filters.filed_before
            )

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        offset = (filters.page - 1) * filters.page_size
        query = (
            query
            .order_by(LobbyingDisclosure.filed_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )

        result = await self.db.execute(query)
        disclosures = result.scalars().all()

        return LobbyingListResponse(
            items=[
                LobbyingResponse.model_validate(d)
                for d in disclosures
            ],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            has_more=(offset + len(disclosures)) < total,
        )

    async def get_disclosure_by_id(
        self,
        disclosure_id: int,
    ) -> Optional[LobbyingDisclosure]:
        """
        Returns a single disclosure by database ID.
        """
        result = await self.db.execute(
            select(LobbyingDisclosure).where(
                LobbyingDisclosure.id == disclosure_id
            )
        )
        return result.scalar_one_or_none()

    async def get_disclosure_by_filing_id(
        self,
        filing_id: str,
    ) -> Optional[LobbyingDisclosure]:
        """
        Returns a disclosure by OpenSecrets filing ID.
        Used for deduplication during ingestion.
        """
        result = await self.db.execute(
            select(LobbyingDisclosure).where(
                LobbyingDisclosure.filing_id == filing_id
            )
        )
        return result.scalar_one_or_none()

    async def get_disclosures_by_ticker(
        self,
        ticker: str,
        limit: int = 20,
    ) -> list[LobbyingDisclosure]:
        """
        Returns all lobbying disclosures for a ticker.
        Most recent first.
        """
        result = await self.db.execute(
            select(LobbyingDisclosure)
            .where(
                LobbyingDisclosure.ticker == ticker.upper()
            )
            .order_by(LobbyingDisclosure.filed_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_disclosures_by_registrant(
        self,
        registrant_name: str,
        limit: int = 20,
    ) -> list[LobbyingDisclosure]:
        """
        Returns all disclosures for a lobbying firm.
        Shows which clients a firm represents
        and what issues they lobby on.
        """
        result = await self.db.execute(
            select(LobbyingDisclosure)
            .where(
                LobbyingDisclosure.registrant_name.ilike(
                    f"%{registrant_name}%"
                )
            )
            .order_by(LobbyingDisclosure.filed_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_revolving_door_disclosures(
        self,
        limit: int = 20,
    ) -> list[LobbyingDisclosure]:
        """
        Returns disclosures where former government
        officials are lobbying. Sorted by amount.
        Powers the revolving door tracker
        in the terminal.
        """
        result = await self.db.execute(
            select(LobbyingDisclosure)
            .where(
                LobbyingDisclosure.has_former_government.is_(True)
            )
            .order_by(LobbyingDisclosure.amount.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_ticker_summary(
        self,
        ticker: str,
    ) -> Optional[LobbyingTickerSummary]:
        """
        Returns aggregated lobbying summary for a ticker.
        Total spend, top issues, top firms,
        revolving door count, breakdown by year.
        """
        disclosures = await self.get_disclosures_by_ticker(
            ticker, limit=1000
        )

        if not disclosures:
            return None

        total_amount = sum(d.amount for d in disclosures)
        filing_count = len(disclosures)
        revolving_door_count = sum(
            1 for d in disclosures if d.has_former_government
        )

        # Most recent period
        latest = disclosures[0]

        # Breakdown by year
        year_totals: dict = {}
        for d in disclosures:
            year = d.filing_year
            year_totals[year] = (
                year_totals.get(year, 0) + d.amount
            )
        by_year = [
            {"year": k, "amount": v}
            for k, v in sorted(year_totals.items())
        ]

        # Breakdown by lobbying firm
        firm_totals: dict = {}
        for d in disclosures:
            firm_totals[d.registrant_name] = (
                firm_totals.get(d.registrant_name, 0) + d.amount
            )
        by_firm = [
            {"firm": k, "amount": v}
            for k, v in sorted(
                firm_totals.items(),
                key=lambda x: x[1],
                reverse=True,
            )
        ]

        # Top issues from JSON arrays
        issue_counts: dict = {}
        for d in disclosures:
            if d.issues:
                for issue in d.issues:
                    code = issue.get("issue_code", "")
                    if code:
                        issue_counts[code] = (
                            issue_counts.get(code, 0) + 1
                        )
        top_issues = sorted(
            issue_counts, key=issue_counts.get, reverse=True
        )[:5]

        # Top bills from JSON arrays
        bill_counts: dict = {}
        for d in disclosures:
            if d.issues:
                for issue in d.issues:
                    for bill in issue.get("bill_references", []):
                        bill_counts[bill] = (
                            bill_counts.get(bill, 0) + 1
                        )
        top_bills = sorted(
            bill_counts, key=bill_counts.get, reverse=True
        )[:5]

        return LobbyingTickerSummary(
            ticker=ticker.upper(),
            company_name=latest.client_name,
            total_amount=total_amount,
            filing_count=filing_count,
            latest_period=latest.filing_period,
            latest_amount=latest.amount,
            yoy_change=latest.yoy_change,
            top_issues=top_issues,
            top_bills=top_bills,
            revolving_door_count=revolving_door_count,
            by_year=by_year,
            by_firm=by_firm,
        )

    async def get_spend_summary(
        self,
        entity_type: str,
        filing_year: Optional[int] = None,
        limit: int = 20,
    ) -> list[LobbyingSpendSummary]:
        """
        Returns top spenders by company, industry,
        or lobbying firm. Powers the lobbying dashboard.
        """
        if entity_type == "company":
            group_col = LobbyingDisclosure.client_name
        elif entity_type == "industry":
            group_col = LobbyingDisclosure.client_industry
        else:
            group_col = LobbyingDisclosure.registrant_name

        query = select(
            group_col.label("entity_name"),
            func.sum(LobbyingDisclosure.amount).label("total"),
            func.count(LobbyingDisclosure.id).label("count"),
            func.avg(LobbyingDisclosure.amount).label("avg"),
            func.min(LobbyingDisclosure.filed_at).label("start"),
            func.max(LobbyingDisclosure.filed_at).label("end"),
        )

        if filing_year:
            query = query.where(
                LobbyingDisclosure.filing_year == filing_year
            )

        query = (
            query
            .group_by(group_col)
            .order_by(func.sum(LobbyingDisclosure.amount).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            LobbyingSpendSummary(
                entity_name=row.entity_name or "Unknown",
                entity_type=entity_type,
                total_amount=row.total or 0,
                filing_count=row.count or 0,
                avg_quarterly_spend=row.avg or 0,
                period_start=row.start,
                period_end=row.end,
            )
            for row in rows
        ]

    async def create_disclosure(
        self,
        data: LobbyingCreate,
    ) -> Optional[LobbyingDisclosure]:
        """
        Creates a new lobbying disclosure.
        Returns None if duplicate filing_id exists.
        """
        disclosure = LobbyingDisclosure(**data.model_dump())
        self.db.add(disclosure)
        try:
            await self.db.flush()
            return disclosure
        except IntegrityError:
            await self.db.rollback()
            return None

    async def update_disclosure(
        self,
        disclosure_id: int,
        data: LobbyingUpdate,
    ) -> Optional[LobbyingDisclosure]:
        """
        Updates a lobbying disclosure.
        """
        disclosure = await self.get_disclosure_by_id(disclosure_id)
        if not disclosure:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(disclosure, field, value)

        await self.db.flush()
        return disclosure

    async def enrich_ticker(
        self,
        client_name: str,
        ticker: str,
    ) -> int:
        """
        Bulk enriches all disclosures for a client
        with their stock ticker.
        Returns count of updated records.
        """
        result = await self.db.execute(
            select(LobbyingDisclosure).where(
                and_(
                    LobbyingDisclosure.client_name.ilike(
                        f"%{client_name}%"
                    ),
                    LobbyingDisclosure.ticker.is_(None),
                )
            )
        )
        disclosures = result.scalars().all()

        for disclosure in disclosures:
            disclosure.ticker = ticker.upper()

        await self.db.flush()
        return len(disclosures)

    async def search_disclosures(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[LobbyingDisclosure]:
        """
        Keyword search across client name
        and registrant name.
        """
        result = await self.db.execute(
            select(LobbyingDisclosure)
            .where(
                or_(
                    LobbyingDisclosure.client_name.ilike(
                        f"%{keyword}%"
                    ),
                    LobbyingDisclosure.registrant_name.ilike(
                        f"%{keyword}%"
                    ),
                )
            )
            .order_by(LobbyingDisclosure.filed_at.desc())
            .limit(limit)
        )
        return result.scalars().all()