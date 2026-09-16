from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime

from app.models.government.filing import GovernmentFiling
from app.schemas.government.filing import (
    FilingCreate,
    FilingFilter,
    FilingListResponse,
    FilingResponse,
)


class FilingService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_filings(
        self,
        filters: FilingFilter,
    ) -> FilingListResponse:
        """
        Returns paginated list of filings with optional filters.
        """
        query = select(GovernmentFiling)
        count_query = select(func.count(GovernmentFiling.id))

        conditions = []

        if filters.filing_type:
            conditions.append(
                GovernmentFiling.filing_type == filters.filing_type.value
            )
        if filters.country:
            conditions.append(
                GovernmentFiling.country == filters.country.value
            )
        if filters.region:
            conditions.append(
                GovernmentFiling.region == filters.region.value
            )
        if filters.source:
            conditions.append(
                GovernmentFiling.source == filters.source.value
            )
        if filters.ticker:
            conditions.append(
                GovernmentFiling.ticker == filters.ticker.upper()
            )
        if filters.company_name:
            conditions.append(
                GovernmentFiling.company_name.ilike(
                    f"%{filters.company_name}%"
                )
            )
        if filters.filed_after:
            conditions.append(
                GovernmentFiling.filed_at >= filters.filed_after
            )
        if filters.filed_before:
            conditions.append(
                GovernmentFiling.filed_at <= filters.filed_before
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
            .order_by(GovernmentFiling.filed_at.desc())
            .offset(offset)
            .limit(filters.page_size)
        )

        result = await self.db.execute(query)
        filings = result.scalars().all()

        return FilingListResponse(
            items=[FilingResponse.model_validate(f) for f in filings],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            has_more=(offset + len(filings)) < total,
        )

    async def get_filing_by_id(
        self,
        filing_id: int,
    ) -> Optional[GovernmentFiling]:
        """
        Returns a single filing by database ID.
        Returns None if not found.
        """
        result = await self.db.execute(
            select(GovernmentFiling).where(
                GovernmentFiling.id == filing_id
            )
        )
        return result.scalar_one_or_none()

    async def get_filings_by_ticker(
        self,
        ticker: str,
        limit: int = 20,
    ) -> list[GovernmentFiling]:
        """
        Returns all filings for a specific stock ticker.
        Most recent first.
        """
        result = await self.db.execute(
            select(GovernmentFiling)
            .where(GovernmentFiling.ticker == ticker.upper())
            .order_by(GovernmentFiling.filed_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_filings_by_cik(
        self,
        cik: str,
        limit: int = 20,
    ) -> list[GovernmentFiling]:
        """
        Returns all filings for a company by SEC CIK number.
        """
        result = await self.db.execute(
            select(GovernmentFiling)
            .where(GovernmentFiling.cik == cik)
            .order_by(GovernmentFiling.filed_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def create_filing(
        self,
        data: dict,
    ) -> Optional[GovernmentFiling]:
        """
        Creates a new filing record.
        Returns None if duplicate accession number exists.
        Called by the ingestion pipeline.
        """
        filing = GovernmentFiling(**data)
        self.db.add(filing)
        try:
            await self.db.flush()
            return filing
        except IntegrityError:
            await self.db.rollback()
            return None

    async def update_filing_status(
        self,
        filing_id: int,
        status: str,
    ) -> Optional[GovernmentFiling]:
        """
        Updates the processing status of a filing.
        Used by ingestion pipeline to mark
        filings as completed or failed.
        """
        filing = await self.get_filing_by_id(filing_id)
        if not filing:
            return None
        filing.status = status
        await self.db.flush()
        return filing

    async def search_filings(
        self,
        keyword: str,
        limit: int = 20,
    ) -> list[GovernmentFiling]:
        """
        Full text search across title, company name
        and description.
        """
        result = await self.db.execute(
            select(GovernmentFiling)
            .where(
                or_(
                    GovernmentFiling.title.ilike(f"%{keyword}%"),
                    GovernmentFiling.company_name.ilike(f"%{keyword}%"),
                    GovernmentFiling.description.ilike(f"%{keyword}%"),
                )
            )
            .order_by(GovernmentFiling.filed_at.desc())
            .limit(limit)
        )
        return result.scalars().all()