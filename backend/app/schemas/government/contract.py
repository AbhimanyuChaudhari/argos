from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from shared.enums.country import CountryCode, RegionCode


class ContractCreate(BaseModel):
    """
    Schema for creating a new contract record.
    Used by the ingestion pipeline when
    inserting a new award from USASpending.gov.
    """

    award_id: str = Field(..., min_length=1, max_length=100)
    award_type: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1)
    total_amount: float = Field(..., ge=0)
    base_amount: float = Field(..., ge=0)
    potential_amount: Optional[float] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    signed_date: Optional[datetime] = None

    # Agency — flattened
    agency_id: str
    agency_name: str
    sub_agency_name: Optional[str] = None
    agency_code: Optional[str] = None

    # Recipient — flattened
    recipient_id: str
    recipient_name: str
    recipient_uei: Optional[str] = None
    parent_recipient_name: Optional[str] = None
    ticker: Optional[str] = None
    recipient_country: CountryCode = CountryCode.US
    recipient_state: Optional[str] = None
    congressional_district: Optional[str] = None
    place_of_performance: Optional[str] = None

    # Classification
    naics_code: Optional[str] = None
    naics_description: Optional[str] = None
    psc_code: Optional[str] = None
    psc_description: Optional[str] = None

    # Competition
    is_compete: bool = True
    number_of_offers: Optional[int] = None

    # Geography
    country: CountryCode = CountryCode.US
    region: RegionCode = RegionCode.AMER

    url: Optional[str] = None
    raw_data: Optional[dict] = None


class ContractUpdate(BaseModel):
    """
    Schema for updating a contract record.
    All fields optional.
    Most common use — adding ticker symbol
    after recipient is matched to a public company.
    """

    ticker: Optional[str] = None
    total_amount: Optional[float] = None
    end_date: Optional[datetime] = None
    potential_amount: Optional[float] = None
    is_compete: Optional[bool] = None
    number_of_offers: Optional[int] = None
    raw_data: Optional[dict] = None


class ContractResponse(BaseModel):
    """
    What the API returns to the frontend
    for a single contract.
    """

    id: int
    award_id: str
    award_type: str
    description: str
    total_amount: float
    base_amount: float
    potential_amount: Optional[float] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    signed_date: Optional[datetime] = None

    # Agency
    agency_id: str
    agency_name: str
    sub_agency_name: Optional[str] = None

    # Recipient
    recipient_id: str
    recipient_name: str
    recipient_uei: Optional[str] = None
    parent_recipient_name: Optional[str] = None
    ticker: Optional[str] = None
    recipient_country: str
    recipient_state: Optional[str] = None
    congressional_district: Optional[str] = None

    # Classification
    naics_code: Optional[str] = None
    naics_description: Optional[str] = None
    psc_code: Optional[str] = None
    psc_description: Optional[str] = None

    # Competition
    is_compete: bool
    number_of_offers: Optional[int] = None

    country: str
    region: str
    url: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContractListResponse(BaseModel):
    """
    Paginated list of contracts.
    """

    items: list[ContractResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ContractFilter(BaseModel):
    """
    Query parameters for filtering contracts.
    """

    agency_name: Optional[str] = None
    agency_id: Optional[str] = None
    recipient_name: Optional[str] = None
    ticker: Optional[str] = Field(
        default=None,
        description="Filter by recipient stock ticker",
    )
    naics_code: Optional[str] = None
    psc_code: Optional[str] = None
    award_type: Optional[str] = None
    min_amount: Optional[float] = Field(
        default=None, ge=0,
        description="Minimum contract value in USD",
    )
    max_amount: Optional[float] = Field(
        default=None, ge=0,
        description="Maximum contract value in USD",
    )
    is_compete: Optional[bool] = None
    country: Optional[CountryCode] = None
    recipient_state: Optional[str] = None
    congressional_district: Optional[str] = None
    signed_after: Optional[datetime] = None
    signed_before: Optional[datetime] = None
    keyword: Optional[str] = Field(
        default=None,
        description="Search by keyword in contract description",
    )
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ContractSearchRequest(BaseModel):
    """
    Request body for keyword search across contracts.
    """

    keyword: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(default=20, ge=1, le=100)


class ContractSpendingSummary(BaseModel):
    """
    Aggregated spending summary.
    Powers the spending dashboard in the terminal.
    """

    entity_name: str
    entity_type: str = Field(
        ...,
        description="agency or recipient",
    )
    ticker: Optional[str] = None
    total_amount: float
    contract_count: int
    avg_contract_size: float
    largest_contract: float
    period_start: datetime
    period_end: datetime


class ContractTickerSummary(BaseModel):
    """
    All contracts for a specific ticker.
    Shown on the stock detail page in the terminal.
    Total government revenue by agency breakdown.
    """

    ticker: str
    company_name: str
    total_amount: float
    contract_count: int
    by_agency: list[dict] = Field(
        default_factory=list,
        description="Spending breakdown by awarding agency",
    )
    by_year: list[dict] = Field(
        default_factory=list,
        description="Spending breakdown by year",
    )
    latest_contract: Optional[ContractResponse] = None