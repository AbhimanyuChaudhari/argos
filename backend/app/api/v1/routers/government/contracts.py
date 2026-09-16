from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.services.government.contract_service import ContractService
from app.schemas.government.contract import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractListResponse,
    ContractFilter,
    ContractSearchRequest,
    ContractSpendingSummary,
    ContractTickerSummary,
)
from shared.enums.country import CountryCode

router = APIRouter(prefix="/contracts", tags=["Government Contracts"])


@router.get("/", response_model=ContractListResponse)
async def get_contracts(
    agency_name: Optional[str] = Query(default=None),
    agency_id: Optional[str] = Query(default=None),
    recipient_name: Optional[str] = Query(default=None),
    ticker: Optional[str] = Query(default=None),
    naics_code: Optional[str] = Query(default=None),
    psc_code: Optional[str] = Query(default=None),
    award_type: Optional[str] = Query(default=None),
    min_amount: Optional[float] = Query(default=None, ge=0),
    max_amount: Optional[float] = Query(default=None, ge=0),
    is_compete: Optional[bool] = Query(default=None),
    country: Optional[CountryCode] = Query(default=None),
    recipient_state: Optional[str] = Query(default=None),
    congressional_district: Optional[str] = Query(default=None),
    signed_after: Optional[datetime] = Query(default=None),
    signed_before: Optional[datetime] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ContractListResponse:
    """
    Returns paginated list of federal contracts.
    Supports filtering by agency, recipient,
    ticker, amount range, and more.
    """
    filters = ContractFilter(
        agency_name=agency_name,
        agency_id=agency_id,
        recipient_name=recipient_name,
        ticker=ticker,
        naics_code=naics_code,
        psc_code=psc_code,
        award_type=award_type,
        min_amount=min_amount,
        max_amount=max_amount,
        is_compete=is_compete,
        country=country,
        recipient_state=recipient_state,
        congressional_district=congressional_district,
        signed_after=signed_after,
        signed_before=signed_before,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    service = ContractService(db)
    return await service.get_contracts(filters)


@router.get(
    "/ticker/{ticker}",
    response_model=list[ContractResponse],
)
async def get_contracts_by_ticker(
    ticker: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ContractResponse]:
    """
    Returns all contracts for a stock ticker.
    Most recent first.
    """
    service = ContractService(db)
    contracts = await service.get_contracts_by_ticker(
        ticker, limit
    )
    return [ContractResponse.model_validate(c) for c in contracts]


@router.get(
    "/ticker/{ticker}/summary",
    response_model=ContractTickerSummary,
)
async def get_ticker_summary(
    ticker: str,
    db: AsyncSession = Depends(get_db),
) -> ContractTickerSummary:
    """
    Returns aggregated contract summary for a ticker.
    Total value, count, breakdown by agency and year.
    Powers the government revenue section
    on stock detail pages.
    """
    service = ContractService(db)
    summary = await service.get_ticker_summary(ticker)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No contracts found for ticker {ticker.upper()}",
        )
    return summary


@router.get(
    "/agency/{agency_name}",
    response_model=list[ContractResponse],
)
async def get_contracts_by_agency(
    agency_name: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ContractResponse]:
    """
    Returns all contracts awarded by an agency.
    Sorted by total amount descending.
    """
    service = ContractService(db)
    contracts = await service.get_contracts_by_agency(
        agency_name, limit
    )
    return [ContractResponse.model_validate(c) for c in contracts]


@router.get(
    "/spending/summary",
    response_model=list[ContractSpendingSummary],
)
async def get_spending_summary(
    entity_type: str = Query(
        default="recipient",
        description="agency or recipient",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ContractSpendingSummary]:
    """
    Returns top spenders by agency or recipient.
    Powers the spending dashboard in the terminal.
    """
    if entity_type not in ("agency", "recipient"):
        raise HTTPException(
            status_code=400,
            detail="entity_type must be agency or recipient",
        )
    service = ContractService(db)
    return await service.get_spending_summary(entity_type, limit)


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    """
    Returns a single contract by database ID.
    """
    service = ContractService(db)
    contract = await service.get_contract_by_id(contract_id)
    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Contract {contract_id} not found",
        )
    return ContractResponse.model_validate(contract)


@router.post("/", response_model=ContractResponse, status_code=201)
async def create_contract(
    data: ContractCreate,
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    """
    Creates a new contract record.
    Called by the ingestion pipeline.
    Returns 409 if duplicate award_id exists.
    """
    service = ContractService(db)
    contract = await service.create_contract(data)
    if not contract:
        raise HTTPException(
            status_code=409,
            detail="Contract with this award ID already exists",
        )
    return ContractResponse.model_validate(contract)


@router.patch("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    """
    Updates a contract record.
    Most common use — enriching with ticker symbol.
    """
    service = ContractService(db)
    contract = await service.update_contract(contract_id, data)
    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Contract {contract_id} not found",
        )
    return ContractResponse.model_validate(contract)


@router.post(
    "/enrich/ticker",
    response_model=dict,
)
async def enrich_ticker(
    recipient_name: str = Query(...),
    ticker: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Bulk enriches all contracts for a recipient
    with their stock ticker.
    Called by the normalisation layer.
    Returns count of updated records.
    """
    service = ContractService(db)
    count = await service.enrich_ticker(recipient_name, ticker)
    return {
        "updated": count,
        "recipient_name": recipient_name,
        "ticker": ticker.upper(),
    }


@router.post("/search", response_model=list[ContractResponse])
async def search_contracts(
    request: ContractSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> list[ContractResponse]:
    """
    Keyword search across contract descriptions.
    """
    service = ContractService(db)
    contracts = await service.search_contracts(
        request.keyword, request.limit
    )
    return [ContractResponse.model_validate(c) for c in contracts]