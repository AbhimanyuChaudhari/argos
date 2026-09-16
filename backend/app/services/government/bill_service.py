from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.models.government.bill import Bill
from app.schemas.government.bill import (
    BillCreate,
    BillUpdate,
    BillFilter,
    BillListResponse,
    BillResponse,
    BillMarketImpactUpdate,
)


class BillService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_bills(
        self,
        filters: BillFilter,
    ) -> BillListResponse:
        """
        Returns paginated list of bills with optional filters.
        """
        query = select(Bill)
        count_query = select(func.count(Bill.id))

        conditions = []

        if filters.bill_type:
            conditions.append(
                Bill.bill_type == filters.bill_type.value
            )
        if filters.status:
            conditions.append(
                Bill.status == filters.status.value
            )
        if filters.chamber:
            conditions.append(
                Bill.chamber == filters.chamber.value
            )
        if filters.policy_area:
            conditions.append(
                Bill.policy_area == filters.policy_area.value
            )
        if filters.country:
            conditions.append(
                Bill.country == filters.country.value
            )
        if filters.sponsor_party:
            conditions.append(
                Bill.sponsor_party == filters.sponsor_party
            )
        if filters.sponsor_state:
            conditions.append(
                Bill.sponsor_state == filters.sponsor_state.upper()
            )
        if filters.congress_number:
            conditions.append(
                Bill.congress_number == filters.congress_number
            )
        if filters.introduced_after:
            conditions.append(
                Bill.introduced_at >= filters.introduced_after
            )
        if filters.introduced_before:
            conditions.append(
                Bill.introduced_at <= filters.introduced_before
            )
        if filters.has_market_impact is True:
            conditions.append(
                Bill.market_sentiment.isnot(None)
            )
        if filters.has_market_impact is False:
            conditions.append(
                Bill.market_sentiment.is_(None)
            )
        if filters.affected_ticker:
            # Search inside the JSON array for the ticker
            conditions.append(
                Bill.affected_tickers.contains(
                    [filters.affected_ticker.upper()]
                )
            )

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        query = (
            query
            .order_by(Bill.introduced_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )

        result = await self.db.execute(query)
        bills = result.scalars().all()

        return BillListResponse(
            items=[BillResponse.model_validate(b) for b in bills],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            has_more=(offset + len(bills)) < total,
        )

    async def get_bill_by_id(
        self,
        bill_id: int,
    ) -> Optional[Bill]:
        """
        Returns a single bill by database ID.
        """
        result = await self.db.execute(
            select(Bill).where(Bill.id == bill_id)
        )
        return result.scalar_one_or_none()

    async def get_bill_by_number(
        self,
        bill_number: str,
        congress_number: int,
    ) -> Optional[Bill]:
        """
        Returns a bill by its number and congress.
        e.g. bill_number="HR-1234", congress_number=119
        """
        result = await self.db.execute(
            select(Bill).where(
                and_(
                    Bill.bill_number == bill_number.upper(),
                    Bill.congress_number == congress_number,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_bills_by_policy_area(
        self,
        policy_area: str,
        limit: int = 20,
    ) -> list[Bill]:
        """
        Returns most recent bills in a policy area.
        Used to show relevant legislation on
        sector pages in the terminal.
        """
        result = await self.db.execute(
            select(Bill)
            .where(Bill.policy_area == policy_area)
            .order_by(Bill.introduced_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_bills_by_ticker(
        self,
        ticker: str,
        limit: int = 20,
    ) -> list[Bill]:
        """
        Returns bills with AI-assessed impact
        on a specific stock ticker.
        """
        result = await self.db.execute(
            select(Bill)
            .where(
                Bill.affected_tickers.contains(
                    [ticker.upper()]
                )
            )
            .order_by(Bill.introduced_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_bills_by_sponsor(
        self,
        bioguide_id: str,
        limit: int = 20,
    ) -> list[Bill]:
        """
        Returns all bills sponsored by a legislator.
        """
        result = await self.db.execute(
            select(Bill)
            .where(Bill.sponsor_bioguide_id == bioguide_id)
            .order_by(Bill.introduced_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def create_bill(
        self,
        data: BillCreate,
    ) -> Optional[Bill]:
        """
        Creates a new bill record.
        Returns None if duplicate bill exists
        for the same congress.
        """
        bill = Bill(**data.model_dump())
        self.db.add(bill)
        try:
            await self.db.flush()
            return bill
        except IntegrityError:
            await self.db.rollback()
            return None

    async def update_bill(
        self,
        bill_id: int,
        data: BillUpdate,
    ) -> Optional[Bill]:
        """
        Updates a bill record.
        Used by ingestion when bill status changes.
        """
        bill = await self.get_bill_by_id(bill_id)
        if not bill:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bill, field, value)

        await self.db.flush()
        return bill

    async def update_market_impact(
        self,
        bill_id: int,
        data: BillMarketImpactUpdate,
    ) -> Optional[Bill]:
        """
        Updates AI-generated market impact assessment.
        Called by the AI layer after analyzing a bill.
        """
        bill = await self.get_bill_by_id(bill_id)
        if not bill:
            return None

        bill.affected_sectors = data.affected_sectors
        bill.affected_tickers = data.affected_tickers
        bill.market_sentiment = data.market_sentiment
        bill.market_reasoning = data.market_reasoning
        bill.market_confidence = data.market_confidence

        await self.db.flush()
        return bill

    async def search_bills(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[Bill]:
        """
        Keyword search across bill title and summary.
        """
        result = await self.db.execute(
            select(Bill)
            .where(
                or_(
                    Bill.title.ilike(f"%{keyword}%"),
                    Bill.summary.ilike(f"%{keyword}%"),
                )
            )
            .order_by(Bill.introduced_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_bills(
        self,
        limit: int = 50,
    ) -> list[Bill]:
        """
        Returns bills currently active in Congress.
        Excludes failed, withdrawn, expired bills.
        Used for the live legislative tracker
        on the terminal dashboard.
        """
        terminal_statuses = [
            "failed",
            "withdrawn",
            "expired",
            "signed",
            "veto_overridden",
        ]
        result = await self.db.execute(
            select(Bill)
            .where(
                Bill.status.notin_(terminal_statuses)
            )
            .order_by(Bill.last_action_at.desc())
            .limit(limit)
        )
        return result.scalars().all()