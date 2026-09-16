from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.models.government.contract import GovernmentContract
from app.schemas.government.contract import (
    ContractCreate,
    ContractUpdate,
    ContractFilter,
    ContractListResponse,
    ContractResponse,
    ContractSpendingSummary,
    ContractTickerSummary,
)


class ContractService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_contracts(
        self,
        filters: ContractFilter,
    ) -> ContractListResponse:
        """
        Returns paginated list of contracts with filters.
        """
        query = select(GovernmentContract)
        count_query = select(func.count(GovernmentContract.id))

        conditions = []

        if filters.agency_name:
            conditions.append(
                GovernmentContract.agency_name.ilike(
                    f"%{filters.agency_name}%"
                )
            )
        if filters.agency_id:
            conditions.append(
                GovernmentContract.agency_id == filters.agency_id
            )
        if filters.recipient_name:
            conditions.append(
                GovernmentContract.recipient_name.ilike(
                    f"%{filters.recipient_name}%"
                )
            )
        if filters.ticker:
            conditions.append(
                GovernmentContract.ticker == filters.ticker.upper()
            )
        if filters.naics_code:
            conditions.append(
                GovernmentContract.naics_code == filters.naics_code
            )
        if filters.psc_code:
            conditions.append(
                GovernmentContract.psc_code == filters.psc_code
            )
        if filters.award_type:
            conditions.append(
                GovernmentContract.award_type == filters.award_type
            )
        if filters.min_amount is not None:
            conditions.append(
                GovernmentContract.total_amount >= filters.min_amount
            )
        if filters.max_amount is not None:
            conditions.append(
                GovernmentContract.total_amount <= filters.max_amount
            )
        if filters.is_compete is not None:
            conditions.append(
                GovernmentContract.is_compete == filters.is_compete
            )
        if filters.country:
            conditions.append(
                GovernmentContract.country == filters.country.value
            )
        if filters.recipient_state:
            conditions.append(
                GovernmentContract.recipient_state == filters.recipient_state.upper()
            )
        if filters.congressional_district:
            conditions.append(
                GovernmentContract.congressional_district == filters.congressional_district
            )
        if filters.signed_after:
            conditions.append(
                GovernmentContract.signed_date >= filters.signed_after
            )
        if filters.signed_before:
            conditions.append(
                GovernmentContract.signed_date <= filters.signed_before
            )
        if filters.keyword:
            conditions.append(
                GovernmentContract.description.ilike(
                    f"%{filters.keyword}%"
                )
            )

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        offset = (filters.page - 1) * filters.page_size
        query = (
            query
            .order_by(GovernmentContract.signed_date.desc())
            .offset(offset)
            .limit(filters.page_size)
        )

        result = await self.db.execute(query)
        contracts = result.scalars().all()

        return ContractListResponse(
            items=[
                ContractResponse.model_validate(c)
                for c in contracts
            ],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            has_more=(offset + len(contracts)) < total,
        )

    async def get_contract_by_id(
        self,
        contract_id: int,
    ) -> Optional[GovernmentContract]:
        """
        Returns a single contract by database ID.
        """
        result = await self.db.execute(
            select(GovernmentContract).where(
                GovernmentContract.id == contract_id
            )
        )
        return result.scalar_one_or_none()

    async def get_contract_by_award_id(
        self,
        award_id: str,
    ) -> Optional[GovernmentContract]:
        """
        Returns a contract by USASpending award ID.
        Used for deduplication during ingestion.
        """
        result = await self.db.execute(
            select(GovernmentContract).where(
                GovernmentContract.award_id == award_id
            )
        )
        return result.scalar_one_or_none()

    async def get_contracts_by_ticker(
        self,
        ticker: str,
        limit: int = 20,
    ) -> list[GovernmentContract]:
        """
        Returns all contracts for a stock ticker.
        Most recent first.
        Powers the government revenue section
        on stock detail pages.
        """
        result = await self.db.execute(
            select(GovernmentContract)
            .where(
                GovernmentContract.ticker == ticker.upper()
            )
            .order_by(GovernmentContract.signed_date.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_contracts_by_agency(
        self,
        agency_name: str,
        limit: int = 20,
    ) -> list[GovernmentContract]:
        """
        Returns all contracts awarded by an agency.
        """
        result = await self.db.execute(
            select(GovernmentContract)
            .where(
                GovernmentContract.agency_name.ilike(
                    f"%{agency_name}%"
                )
            )
            .order_by(GovernmentContract.total_amount.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_ticker_summary(
        self,
        ticker: str,
    ) -> Optional[ContractTickerSummary]:
        """
        Returns aggregated contract summary for a ticker.
        Total value, count, breakdown by agency and year.
        """
        contracts = await self.get_contracts_by_ticker(
            ticker, limit=1000
        )

        if not contracts:
            return None

        total_amount = sum(c.total_amount for c in contracts)
        contract_count = len(contracts)

        # Breakdown by agency
        agency_totals: dict = {}
        for c in contracts:
            agency_totals[c.agency_name] = (
                agency_totals.get(c.agency_name, 0) + c.total_amount
            )
        by_agency = [
            {"agency": k, "amount": v}
            for k, v in sorted(
                agency_totals.items(),
                key=lambda x: x[1],
                reverse=True,
            )
        ]

        # Breakdown by year
        year_totals: dict = {}
        for c in contracts:
            if c.signed_date:
                year = c.signed_date.year
                year_totals[year] = (
                    year_totals.get(year, 0) + c.total_amount
                )
        by_year = [
            {"year": k, "amount": v}
            for k, v in sorted(year_totals.items())
        ]

        latest = contracts[0] if contracts else None

        return ContractTickerSummary(
            ticker=ticker.upper(),
            company_name=contracts[0].recipient_name if contracts else "",
            total_amount=total_amount,
            contract_count=contract_count,
            by_agency=by_agency,
            by_year=by_year,
            latest_contract=(
                ContractResponse.model_validate(latest)
                if latest else None
            ),
        )

    async def get_spending_summary(
        self,
        entity_type: str,
        limit: int = 20,
    ) -> list[ContractSpendingSummary]:
        """
        Returns top spenders by agency or recipient.
        Powers the spending dashboard.
        """
        if entity_type == "agency":
            group_col = GovernmentContract.agency_name
        else:
            group_col = GovernmentContract.recipient_name

        result = await self.db.execute(
            select(
                group_col.label("entity_name"),
                func.sum(GovernmentContract.total_amount).label("total"),
                func.count(GovernmentContract.id).label("count"),
                func.avg(GovernmentContract.total_amount).label("avg"),
                func.max(GovernmentContract.total_amount).label("largest"),
                func.min(GovernmentContract.signed_date).label("start"),
                func.max(GovernmentContract.signed_date).label("end"),
            )
            .group_by(group_col)
            .order_by(func.sum(GovernmentContract.total_amount).desc())
            .limit(limit)
        )

        rows = result.all()
        return [
            ContractSpendingSummary(
                entity_name=row.entity_name,
                entity_type=entity_type,
                total_amount=row.total or 0,
                contract_count=row.count or 0,
                avg_contract_size=row.avg or 0,
                largest_contract=row.largest or 0,
                period_start=row.start,
                period_end=row.end,
            )
            for row in rows
        ]

    async def create_contract(
        self,
        data: ContractCreate,
    ) -> Optional[GovernmentContract]:
        """
        Creates a new contract record.
        Returns None if duplicate award_id exists.
        """
        contract = GovernmentContract(**data.model_dump())
        self.db.add(contract)
        try:
            await self.db.flush()
            return contract
        except IntegrityError:
            await self.db.rollback()
            return None

    async def update_contract(
        self,
        contract_id: int,
        data: ContractUpdate,
    ) -> Optional[GovernmentContract]:
        """
        Updates a contract record.
        Most common use — enriching with ticker symbol.
        """
        contract = await self.get_contract_by_id(contract_id)
        if not contract:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)

        await self.db.flush()
        return contract

    async def enrich_ticker(
        self,
        recipient_name: str,
        ticker: str,
    ) -> int:
        """
        Bulk enriches all contracts for a recipient
        with their stock ticker.
        Returns count of updated records.
        Called by the normalisation layer when
        it matches a company name to a ticker.
        """
        result = await self.db.execute(
            select(GovernmentContract).where(
                and_(
                    GovernmentContract.recipient_name.ilike(
                        f"%{recipient_name}%"
                    ),
                    GovernmentContract.ticker.is_(None),
                )
            )
        )
        contracts = result.scalars().all()

        for contract in contracts:
            contract.ticker = ticker.upper()

        await self.db.flush()
        return len(contracts)