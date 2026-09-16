from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl

from shared.enums.country import CountryCode, RegionCode
from shared.enums.filing_type import FilingType, FilingStatus, FilingSource


class FilingBase(BaseModel):
    """
    Core fields every filing has regardless of source.
    Both SEC EDGAR and government filings share these.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Title or subject of the filing",
    )
    filing_type: FilingType = Field(
        ...,
        description="Type of filing e.g. 10-K, 8-K",
    )
    source: FilingSource = Field(
        ...,
        description="Which data source this came from",
    )
    country: CountryCode = Field(
        default=CountryCode.US,
        description="Country this filing belongs to",
    )
    region: RegionCode = Field(
        default=RegionCode.AMER,
        description="Geographic region",
    )
    filed_at: datetime = Field(
        ...,
        description="When the filing was submitted",
    )
    url: Optional[HttpUrl] = Field(
        default=None,
        description="Direct URL to the filing document",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Summary or description of the filing",
    )


class SECFilingSchema(FilingBase):
    """
    Schema for SEC EDGAR filings.
    Extends FilingBase with SEC-specific fields.
    """

    cik: str = Field(
        ...,
        description="SEC Central Index Key — unique company identifier",
    )
    accession_number: str = Field(
        ...,
        description="SEC unique filing identifier e.g. 0001234567-24-000001",
    )
    company_name: str = Field(
        ...,
        description="Name of the company that filed",
    )
    ticker: Optional[str] = Field(
        default=None,
        description="Stock ticker symbol if applicable",
    )
    period_of_report: Optional[datetime] = Field(
        default=None,
        description="The period this filing covers e.g. fiscal year end",
    )
    is_amendment: bool = Field(
        default=False,
        description="Whether this is an amendment to a prior filing",
    )
    items: Optional[list[str]] = Field(
        default=None,
        description="8-K items reported e.g. Item 1.01 Entry into Agreement",
    )


class GovernmentContractSchema(BaseModel):
    """
    Schema for USASpending.gov federal contracts.
    """

    award_id: str = Field(
        ...,
        description="Unique award identifier from USASpending",
    )
    recipient_name: str = Field(
        ...,
        description="Company or entity receiving the contract",
    )
    awarding_agency: str = Field(
        ...,
        description="Federal agency awarding the contract",
    )
    amount: float = Field(
        ...,
        description="Total contract value in USD",
    )
    start_date: datetime = Field(
        ...,
        description="Contract start date",
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="Contract end date",
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of goods or services",
    )
    naics_code: Optional[str] = Field(
        default=None,
        description="Industry classification code",
    )
    country: CountryCode = Field(
        default=CountryCode.US,
    )


class FilingResponse(FilingBase):
    """
    What the API returns to the frontend.
    Extends FilingBase with database fields.
    """

    id: int
    status: FilingStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FilingListResponse(BaseModel):
    """
    Paginated list of filings returned by the API.
    """

    items: list[FilingResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class FilingFilter(BaseModel):
    """
    Query parameters for filtering filings.
    Used by the /filings endpoint.
    """

    filing_type: Optional[FilingType] = None
    country: Optional[CountryCode] = None
    region: Optional[RegionCode] = None
    source: Optional[FilingSource] = None
    ticker: Optional[str] = None
    company_name: Optional[str] = None
    filed_after: Optional[datetime] = None
    filed_before: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)