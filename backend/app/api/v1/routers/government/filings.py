from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.services.government.filing_service import FilingService
from app.schemas.government.filing import (
    FilingCreate,
    FilingUpdate,
    FilingResponse,
    FilingListResponse,
    FilingFilter,
    FilingSearchRequest,
)
from shared.enums.filing_type import FilingType, FilingStatus, FilingSource
from shared.enums.country import CountryCode, RegionCode

router = APIRouter(prefix="/filings", tags=["Government Filings"])


@router.get("/", response_model=FilingListResponse)
async def get_filings(
    filing_type: Optional[FilingType] = Query(default=None),
    country: Optional[CountryCode] = Query(default=None),
    region: Optional[RegionCode] = Query(default=None),
    source: Optional[FilingSource] = Query(default=None),
    status: Optional[FilingStatus] = Query(default=None),
    ticker: Optional[str] = Query(default=None),
    company_name: Optional[str] = Query(default=None),
    cik: Optional[str] = Query(default=None),
    filed_after: Optional[datetime] = Query(default=None),
    filed_before: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> FilingListResponse:
    """
    Returns paginated list of government filings.
    Supports filtering by type, country, ticker,
    company, date range and more.
    """
    filters = FilingFilter(
        filing_type=filing_type,
        country=country,
        region=region,
        source=source,
        status=status,
        ticker=ticker,
        company_name=company_name,
        cik=cik,
        filed_after=filed_after,
        filed_before=filed_before,
        page=page,
        page_size=page_size,
    )
    service = FilingService(db)
    return await service.get_filings(filters)


@router.get("/ticker/{ticker}", response_model=list[FilingResponse])
async def get_filings_by_ticker(
    ticker: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[FilingResponse]:
    """
    Returns all filings for a specific stock ticker.
    Used on the stock detail page in the terminal.
    """
    service = FilingService(db)
    filings = await service.get_filings_by_ticker(ticker, limit)
    return [FilingResponse.model_validate(f) for f in filings]


@router.get("/cik/{cik}", response_model=list[FilingResponse])
async def get_filings_by_cik(
    cik: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[FilingResponse]:
    """
    Returns all filings for a company by SEC CIK number.
    """
    service = FilingService(db)
    filings = await service.get_filings_by_cik(cik, limit)
    return [FilingResponse.model_validate(f) for f in filings]


@router.get("/{filing_id}", response_model=FilingResponse)
async def get_filing(
    filing_id: int,
    db: AsyncSession = Depends(get_db),
) -> FilingResponse:
    """
    Returns a single filing by ID.
    """
    service = FilingService(db)
    filing = await service.get_filing_by_id(filing_id)
    if not filing:
        raise HTTPException(
            status_code=404,
            detail=f"Filing {filing_id} not found",
        )
    return FilingResponse.model_validate(filing)


@router.post("/", response_model=FilingResponse, status_code=201)
async def create_filing(
    data: FilingCreate,
    db: AsyncSession = Depends(get_db),
) -> FilingResponse:
    """
    Creates a new filing record.
    Called by the ingestion pipeline.
    Returns 409 if duplicate accession number.
    """
    service = FilingService(db)
    filing = await service.create_filing(data.model_dump())
    if not filing:
        raise HTTPException(
            status_code=409,
            detail="Filing with this accession number already exists",
        )
    return FilingResponse.model_validate(filing)


@router.patch("/{filing_id}/status", response_model=FilingResponse)
async def update_filing_status(
    filing_id: int,
    status: FilingStatus,
    db: AsyncSession = Depends(get_db),
) -> FilingResponse:
    """
    Updates the processing status of a filing.
    Called by the ingestion pipeline.
    """
    service = FilingService(db)
    filing = await service.update_filing_status(
        filing_id, status.value
    )
    if not filing:
        raise HTTPException(
            status_code=404,
            detail=f"Filing {filing_id} not found",
        )
    return FilingResponse.model_validate(filing)


@router.post("/search", response_model=list[FilingResponse])
async def search_filings(
    request: FilingSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> list[FilingResponse]:
    """
    Keyword search across filing title,
    company name and description.
    """
    service = FilingService(db)
    filings = await service.search_filings(
        request.keyword, request.limit
    )
    return [FilingResponse.model_validate(f) for f in filings]