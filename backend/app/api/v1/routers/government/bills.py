from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.services.government.bill_service import BillService
from app.schemas.government.bill import (
    BillCreate,
    BillUpdate,
    BillResponse,
    BillListResponse,
    BillFilter,
    BillSearchRequest,
    BillMarketImpactUpdate,
)
from shared.enums.bill_status import (
    BillStatus,
    BillType,
    BillChamber,
    PolicyArea,
)
from shared.enums.country import CountryCode

router = APIRouter(prefix="/bills", tags=["Government Bills"])


@router.get("/", response_model=BillListResponse)
async def get_bills(
    bill_type: Optional[BillType] = Query(default=None),
    status: Optional[BillStatus] = Query(default=None),
    chamber: Optional[BillChamber] = Query(default=None),
    policy_area: Optional[PolicyArea] = Query(default=None),
    country: Optional[CountryCode] = Query(default=None),
    sponsor_party: Optional[str] = Query(default=None),
    sponsor_state: Optional[str] = Query(default=None),
    congress_number: Optional[int] = Query(default=None),
    introduced_after: Optional[datetime] = Query(default=None),
    introduced_before: Optional[datetime] = Query(default=None),
    has_market_impact: Optional[bool] = Query(default=None),
    affected_ticker: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> BillListResponse:
    """
    Returns paginated list of bills.
    Supports filtering by status, chamber,
    policy area, sponsor, and market impact.
    """
    filters = BillFilter(
        bill_type=bill_type,
        status=status,
        chamber=chamber,
        policy_area=policy_area,
        country=country,
        sponsor_party=sponsor_party,
        sponsor_state=sponsor_state,
        congress_number=congress_number,
        introduced_after=introduced_after,
        introduced_before=introduced_before,
        has_market_impact=has_market_impact,
        affected_ticker=affected_ticker,
        page=page,
        page_size=page_size,
    )
    service = BillService(db)
    return await service.get_bills(filters)


@router.get("/active", response_model=list[BillResponse])
async def get_active_bills(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[BillResponse]:
    """
    Returns bills currently active in Congress.
    Excludes failed, withdrawn, expired, signed bills.
    Powers the live legislative tracker
    on the terminal dashboard.
    """
    service = BillService(db)
    bills = await service.get_active_bills(limit)
    return [BillResponse.model_validate(b) for b in bills]


@router.get("/ticker/{ticker}", response_model=list[BillResponse])
async def get_bills_by_ticker(
    ticker: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[BillResponse]:
    """
    Returns bills with AI-assessed impact
    on a specific stock ticker.
    Used on the stock detail page.
    """
    service = BillService(db)
    bills = await service.get_bills_by_ticker(ticker, limit)
    return [BillResponse.model_validate(b) for b in bills]


@router.get("/policy/{policy_area}", response_model=list[BillResponse])
async def get_bills_by_policy_area(
    policy_area: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[BillResponse]:
    """
    Returns most recent bills in a policy area.
    Used on sector pages to show relevant legislation.
    """
    service = BillService(db)
    bills = await service.get_bills_by_policy_area(
        policy_area, limit
    )
    return [BillResponse.model_validate(b) for b in bills]


@router.get("/sponsor/{bioguide_id}", response_model=list[BillResponse])
async def get_bills_by_sponsor(
    bioguide_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[BillResponse]:
    """
    Returns all bills sponsored by a legislator.
    """
    service = BillService(db)
    bills = await service.get_bills_by_sponsor(
        bioguide_id, limit
    )
    return [BillResponse.model_validate(b) for b in bills]


@router.get("/{bill_id}", response_model=BillResponse)
async def get_bill(
    bill_id: int,
    db: AsyncSession = Depends(get_db),
) -> BillResponse:
    """
    Returns a single bill by database ID.
    """
    service = BillService(db)
    bill = await service.get_bill_by_id(bill_id)
    if not bill:
        raise HTTPException(
            status_code=404,
            detail=f"Bill {bill_id} not found",
        )
    return BillResponse.model_validate(bill)


@router.post("/", response_model=BillResponse, status_code=201)
async def create_bill(
    data: BillCreate,
    db: AsyncSession = Depends(get_db),
) -> BillResponse:
    """
    Creates a new bill record.
    Called by the ingestion pipeline.
    Returns 409 if duplicate bill exists
    for the same congress.
    """
    service = BillService(db)
    bill = await service.create_bill(data)
    if not bill:
        raise HTTPException(
            status_code=409,
            detail="Bill already exists for this congress",
        )
    return BillResponse.model_validate(bill)


@router.patch("/{bill_id}", response_model=BillResponse)
async def update_bill(
    bill_id: int,
    data: BillUpdate,
    db: AsyncSession = Depends(get_db),
) -> BillResponse:
    """
    Updates a bill record.
    Used by ingestion when bill status changes.
    """
    service = BillService(db)
    bill = await service.update_bill(bill_id, data)
    if not bill:
        raise HTTPException(
            status_code=404,
            detail=f"Bill {bill_id} not found",
        )
    return BillResponse.model_validate(bill)


@router.patch(
    "/{bill_id}/market-impact",
    response_model=BillResponse,
)
async def update_market_impact(
    bill_id: int,
    data: BillMarketImpactUpdate,
    db: AsyncSession = Depends(get_db),
) -> BillResponse:
    """
    Updates AI-generated market impact assessment.
    Called by the AI layer after analyzing a bill.
    Separate endpoint keeps AI updates auditable
    and distinct from legislative data updates.
    """
    service = BillService(db)
    bill = await service.update_market_impact(bill_id, data)
    if not bill:
        raise HTTPException(
            status_code=404,
            detail=f"Bill {bill_id} not found",
        )
    return BillResponse.model_validate(bill)


@router.post("/search", response_model=list[BillResponse])
async def search_bills(
    request: BillSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> list[BillResponse]:
    """
    Keyword search across bill title and summary.
    """
    service = BillService(db)
    bills = await service.search_bills(
        request.keyword, request.limit
    )
    return [BillResponse.model_validate(b) for b in bills]