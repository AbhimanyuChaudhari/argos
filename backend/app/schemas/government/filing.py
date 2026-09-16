from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl

from shared.enums.country import CountryCode, RegionCode
from shared.enums.filing_type import FilingType, FilingStatus, FilingSource


class FilingCreate(BaseModel):
    """
    Schema for creating a new filing.
    Used by the ingestion pipeline when
    inserting a new record into the database.
    """

    title: str = Field(..., min_length=1, max_length=500)
    filing_type: FilingType
    source: FilingSource
    country: CountryCode = CountryCode.US
    region: RegionCode = RegionCode.AMER
    filed_at: datetime
    url: Optional[str] = None
    description: Optional[str] = None

    # SEC specific
    cik: Optional[str] = None
    accession_number: Optional[str] = None
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    period_of_report: Optional[datetime] = None
    is_amendment: bool = False
    items: Optional[list[str]] = None

    # Raw data — always store original response
    raw_data: Optional[dict] = None


class FilingUpdate(BaseModel):
    """
    Schema for updating a filing.
    All fields optional — only pass what changed.
    """

    title: Optional[str] = None
    status: Optional[FilingStatus] = None
    description: Optional[str] = None
    ticker: Optional[str] = None
    raw_data: Optional[dict] = None


class FilingResponse(BaseModel):
    """
    What the API returns to the frontend
    for a single filing.
    """

    id: int
    title: str
    filing_type: str
    source: str
    status: str
    country: str
    region: str
    filed_at: datetime
    url: Optional[str] = None
    description: Optional[str] = None

    # SEC specific
    cik: Optional[str] = None
    accession_number: Optional[str] = None
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    period_of_report: Optional[datetime] = None
    is_amendment: bool = False
    items: Optional[list] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FilingListResponse(BaseModel):
    """
    Paginated list of filings.
    """

    items: list[FilingResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class FilingFilter(BaseModel):
    """
    Query parameters for filtering filings.
    """

    filing_type: Optional[FilingType] = None
    country: Optional[CountryCode] = None
    region: Optional[RegionCode] = None
    source: Optional[FilingSource] = None
    status: Optional[FilingStatus] = None
    ticker: Optional[str] = None
    company_name: Optional[str] = None
    cik: Optional[str] = None
    filed_after: Optional[datetime] = None
    filed_before: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class FilingSearchRequest(BaseModel):
    """
    Request body for keyword search.
    """

    keyword: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(default=20, ge=1, le=100)