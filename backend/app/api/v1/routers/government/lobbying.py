from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.services.government.lobbying_service import LobbyingService
from app.schemas.government.lobbying import (
    LobbyingCreate,
    LobbyingUpdate,
    LobbyingResponse,
    LobbyingListResponse,
    LobbyingFilter,
    LobbyingSearchRequest,
    LobbyingSpendSummary,
    LobbyingTickerSummary,
)
from shared.enums.country import CountryCode

router = APIRouter(prefix="/lobbying", tags=["Government Lobbying"])


@router.get("/", response_model=LobbyingListResponse)
async def get_disclosures(
    client_name: Optional[str] = Query(default=None),
    ticker: Optional[str] = Query(default=None),
    registrant_name: Optional[str] = Query(default=None),
    client_industry: Optional[str] = Query(default=None),
    filing_year: Optional[int] = Query(default=None),
    filing_period: Optional[str] = Query(default=None),
    min_amount: Optional[float] = Query(default=None, ge=0),
    max_amount: Optional[float] = Query(default=None, ge=0),
    has_former_government: Optional[bool] = Query(default=None),
    country: Optional[CountryCode] = Query(default=None),
    filed_after: Optional[datetime] = Query(default=None),
    filed_before: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> LobbyingListResponse:
    """
    Returns paginated list of lobbying disclosures.
    Supports filtering by client, ticker, firm,
    amount range, and revolving door flag.
    """
    filters = LobbyingFilter(
        client_name=client_name,
        ticker=ticker,
        registrant_name=registrant_name,
        client_industry=client_industry,
        filing_year=filing_year,
        filing_period=filing_period,
        min_amount=min_amount,
        max_amount=max_amount,
        has_former_government=has_former_government,
        country=country,
        filed_after=filed_after,
        filed_before=filed_before,
        page=page,
        page_size=page_size,
    )
    service = LobbyingService(db)
    return await service.get_disclosures(filters)


@router.get(
    "/revolving-door",
    response_model=list[LobbyingResponse],
)
async def get_revolving_door(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[LobbyingResponse]:
    """
    Returns disclosures where former government
    officials are lobbying. Sorted by amount.
    Powers the revolving door tracker.
    """
    service = LobbyingService(db)
    disclosures = await service.get_revolving_door_disclosures(limit)
    return [LobbyingResponse.model_validate(d) for d in disclosures]


@router.get(
    "/ticker/{ticker}",
    response_model=list[LobbyingResponse],
)
async def get_disclosures_by_ticker(
    ticker: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[LobbyingResponse]:
    """
    Returns all lobbying disclosures for a ticker.
    Most recent first.
    """
    service = LobbyingService(db)
    disclosures = await service.get_disclosures_by_ticker(
        ticker, limit
    )
    return [LobbyingResponse.model_validate(d) for d in disclosures]


@router.get(
    "/ticker/{ticker}/summary",
    response_model=LobbyingTickerSummary,
)
async def get_ticker_summary(
    ticker: str,
    db: AsyncSession = Depends(get_db),
) -> LobbyingTickerSummary:
    """
    Returns aggregated lobbying summary for a ticker.
    Total spend, top issues, top firms,
    revolving door count, breakdown by year.
    Powers the lobbying section on stock detail pages.
    """
    service = LobbyingService(db)
    summary = await service.get_ticker_summary(ticker)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No lobbying disclosures found for {ticker.upper()}",
        )
    return summary


@router.get(
    "/firm/{registrant_name}",
    response_model=list[LobbyingResponse],
)
async def get_disclosures_by_firm(
    registrant_name: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[LobbyingResponse]:
    """
    Returns all disclosures for a lobbying firm.
    Shows which clients a firm represents
    and what issues they lobby on.
    """
    service = LobbyingService(db)
    disclosures = await service.get_disclosures_by_registrant(
        registrant_name, limit
    )
    return [LobbyingResponse.model_validate(d) for d in disclosures]


@router.get(
    "/spending/summary",
    response_model=list[LobbyingSpendSummary],
)
async def get_spend_summary(
    entity_type: str = Query(
        default="company",
        description="company, industry, or lobbying_firm",
    ),
    filing_year: Optional[int] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[LobbyingSpendSummary]:
    """
    Returns top spenders by company, industry,
    or lobbying firm.
    Powers the lobbying dashboard.
    """
    if entity_type not in ("company", "industry", "lobbying_firm"):
        raise HTTPException(
            status_code=400,
            detail="entity_type must be company, industry, or lobbying_firm",
        )
    service = LobbyingService(db)
    return await service.get_spend_summary(
        entity_type, filing_year, limit
    )


@router.get("/{disclosure_id}", response_model=LobbyingResponse)
async def get_disclosure(
    disclosure_id: int,
    db: AsyncSession = Depends(get_db),
) -> LobbyingResponse:
    """
    Returns a single lobbying disclosure by ID.
    """
    service = LobbyingService(db)
    disclosure = await service.get_disclosure_by_id(disclosure_id)
    if not disclosure:
        raise HTTPException(
            status_code=404,
            detail=f"Disclosure {disclosure_id} not found",
        )
    return LobbyingResponse.model_validate(disclosure)


@router.post(
    "/",
    response_model=LobbyingResponse,
    status_code=201,
)
async def create_disclosure(
    data: LobbyingCreate,
    db: AsyncSession = Depends(get_db),
) -> LobbyingResponse:
    """
    Creates a new lobbying disclosure.
    Called by the ingestion pipeline.
    Returns 409 if duplicate filing_id exists.
    """
    service = LobbyingService(db)
    disclosure = await service.create_disclosure(data)
    if not disclosure:
        raise HTTPException(
            status_code=409,
            detail="Disclosure with this filing ID already exists",
        )
    return LobbyingResponse.model_validate(disclosure)


@router.patch("/{disclosure_id}", response_model=LobbyingResponse)
async def update_disclosure(
    disclosure_id: int,
    data: LobbyingUpdate,
    db: AsyncSession = Depends(get_db),
) -> LobbyingResponse:
    """
    Updates a lobbying disclosure.
    """
    service = LobbyingService(db)
    disclosure = await service.update_disclosure(
        disclosure_id, data
    )
    if not disclosure:
        raise HTTPException(
            status_code=404,
            detail=f"Disclosure {disclosure_id} not found",
        )
    return LobbyingResponse.model_validate(disclosure)


@router.post(
    "/enrich/ticker",
    response_model=dict,
)
async def enrich_ticker(
    client_name: str = Query(...),
    ticker: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Bulk enriches all disclosures for a client
    with their stock ticker.
    Called by the normalisation layer.
    Returns count of updated records.
    """
    service = LobbyingService(db)
    count = await service.enrich_ticker(client_name, ticker)
    return {
        "updated": count,
        "client_name": client_name,
        "ticker": ticker.upper(),
    }


@router.post("/search", response_model=list[LobbyingResponse])
async def search_disclosures(
    request: LobbyingSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> list[LobbyingResponse]:
    """
    Keyword search across client name
    and registrant name.
    """
    service = LobbyingService(db)
    disclosures = await service.search_disclosures(
        request.keyword, request.limit
    )
    return [LobbyingResponse.model_validate(d) for d in disclosures]