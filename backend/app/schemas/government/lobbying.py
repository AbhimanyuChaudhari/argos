from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from shared.enums.country import CountryCode, RegionCode


class LobbyingCreate(BaseModel):
    """
    Schema for creating a new lobbying disclosure.
    Used by the ingestion pipeline when
    inserting a new filing from OpenSecrets.
    """

    filing_id: str = Field(..., min_length=1, max_length=100)
    filing_type: str = Field(..., min_length=1, max_length=20)
    filing_year: int = Field(..., ge=1998)
    filing_period: str = Field(..., min_length=1, max_length=20)
    filed_at: datetime
    amount: float = Field(..., ge=0)

    # Client — flattened
    client_id: str
    client_name: str
    client_industry: Optional[str] = None

    # Key financial link
    ticker: Optional[str] = None

    # Registrant — lobbying firm
    registrant_id: str
    registrant_name: str

    # Geography
    client_country: CountryCode = CountryCode.US
    country: CountryCode = CountryCode.US
    region: RegionCode = RegionCode.AMER

    # JSON arrays
    lobbyists: Optional[list] = None
    issues: Optional[list] = None

    # Revolving door flag
    has_former_government: bool = False

    # YoY change — calculated during ingestion
    yoy_change: Optional[float] = None

    url: Optional[str] = None
    raw_data: Optional[dict] = None


class LobbyingUpdate(BaseModel):
    """
    Schema for updating a lobbying record.
    All fields optional.
    Most common use — adding ticker symbol
    or updating yoy_change calculation.
    """

    ticker: Optional[str] = None
    amount: Optional[float] = None
    lobbyists: Optional[list] = None
    issues: Optional[list] = None
    has_former_government: Optional[bool] = None
    yoy_change: Optional[float] = None
    raw_data: Optional[dict] = None


class LobbyingResponse(BaseModel):
    """
    What the API returns to the frontend
    for a single lobbying disclosure.
    """

    id: int
    filing_id: str
    filing_type: str
    filing_year: int
    filing_period: str
    filed_at: datetime
    amount: float

    # Client
    client_id: str
    client_name: str
    client_industry: Optional[str] = None
    ticker: Optional[str] = None

    # Registrant
    registrant_id: str
    registrant_name: str

    # Geography
    client_country: str
    country: str
    region: str

    # Arrays
    lobbyists: Optional[list] = None
    issues: Optional[list] = None

    # Flags
    has_former_government: bool = False
    yoy_change: Optional[float] = None

    url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LobbyingListResponse(BaseModel):
    """
    Paginated list of lobbying disclosures.
    """

    items: list[LobbyingResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class LobbyingFilter(BaseModel):
    """
    Query parameters for filtering lobbying disclosures.
    """

    client_name: Optional[str] = None
    ticker: Optional[str] = Field(
        default=None,
        description="Filter by company stock ticker",
    )
    registrant_name: Optional[str] = Field(
        default=None,
        description="Filter by lobbying firm name",
    )
    client_industry: Optional[str] = None
    filing_year: Optional[int] = None
    filing_period: Optional[str] = None
    min_amount: Optional[float] = Field(
        default=None, ge=0,
        description="Minimum lobbying spend in USD",
    )
    max_amount: Optional[float] = Field(
        default=None, ge=0,
        description="Maximum lobbying spend in USD",
    )
    has_former_government: Optional[bool] = Field(
        default=None,
        description="Filter for revolving door disclosures",
    )
    country: Optional[CountryCode] = None
    filed_after: Optional[datetime] = None
    filed_before: Optional[datetime] = None
    keyword: Optional[str] = Field(
        default=None,
        description="Search by keyword in issue descriptions",
    )
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class LobbyingSearchRequest(BaseModel):
    """
    Request body for keyword search across lobbying filings.
    """

    keyword: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(default=20, ge=1, le=100)


class LobbyingSpendSummary(BaseModel):
    """
    Aggregated lobbying spend summary.
    Powers the lobbying dashboard in the terminal.
    """

    entity_name: str
    entity_type: str = Field(
        ...,
        description="company, industry, or lobbying_firm",
    )
    ticker: Optional[str] = None
    total_amount: float
    filing_count: int
    avg_quarterly_spend: float
    top_issues: list[str] = Field(
        default_factory=list,
        description="Most lobbied issue codes",
    )
    top_bills: list[str] = Field(
        default_factory=list,
        description="Most referenced bill numbers",
    )
    period_start: datetime
    period_end: datetime
    yoy_change: Optional[float] = None


class LobbyingTickerSummary(BaseModel):
    """
    All lobbying activity for a specific ticker.
    Shown on the stock detail page in the terminal.
    """

    ticker: str
    company_name: str
    total_amount: float
    filing_count: int
    latest_period: str
    latest_amount: float
    yoy_change: Optional[float] = None
    top_issues: list[str] = Field(default_factory=list)
    top_bills: list[str] = Field(default_factory=list)
    revolving_door_count: int = Field(
        default=0,
        description="Number of filings with former government lobbyists",
    )
    by_year: list[dict] = Field(
        default_factory=list,
        description="Spend breakdown by year",
    )
    by_firm: list[dict] = Field(
        default_factory=list,
        description="Spend breakdown by lobbying firm",
    )