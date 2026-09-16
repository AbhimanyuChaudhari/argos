from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from shared.enums.country import CountryCode, RegionCode
from shared.enums.bill_status import (
    BillStatus,
    BillType,
    BillChamber,
    PolicyArea,
)


class BillCreate(BaseModel):
    """
    Schema for creating a new bill record.
    Used by the ingestion pipeline when
    inserting a new bill from GovTrack.
    """

    bill_number: str = Field(..., min_length=1, max_length=50)
    bill_type: BillType
    congress_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=1000)
    short_title: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    status: BillStatus
    chamber: BillChamber
    policy_area: PolicyArea
    country: CountryCode = CountryCode.US
    region: RegionCode = RegionCode.AMER
    introduced_at: datetime
    last_action_at: Optional[datetime] = None

    # Sponsor
    sponsor_bioguide_id: Optional[str] = None
    sponsor_name: Optional[str] = None
    sponsor_party: Optional[str] = None
    sponsor_state: Optional[str] = None
    sponsor_chamber: Optional[str] = None

    # Support metrics
    cosponsors_count: int = 0

    # JSON arrays
    actions: Optional[list] = None
    committees: Optional[list] = None
    related_bills: Optional[list] = None
    subjects: Optional[list] = None

    # Raw data
    raw_data: Optional[dict] = None


class BillUpdate(BaseModel):
    """
    Schema for updating a bill record.
    All fields optional — only pass what changed.
    Ingestion pipeline calls this when a bill
    status changes or new actions are added.
    """

    status: Optional[BillStatus] = None
    chamber: Optional[BillChamber] = None
    last_action_at: Optional[datetime] = None
    cosponsors_count: Optional[int] = None
    actions: Optional[list] = None
    committees: Optional[list] = None
    summary: Optional[str] = None

    # AI market impact fields
    affected_sectors: Optional[list[str]] = None
    affected_tickers: Optional[list[str]] = None
    market_sentiment: Optional[str] = None
    market_reasoning: Optional[str] = None
    market_confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0
    )

    raw_data: Optional[dict] = None


class BillResponse(BaseModel):
    """
    What the API returns to the frontend
    for a single bill.
    """

    id: int
    bill_number: str
    bill_type: str
    congress_number: int
    title: str
    short_title: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    status: str
    chamber: str
    policy_area: str
    country: str
    region: str
    introduced_at: datetime
    last_action_at: Optional[datetime] = None

    # Sponsor
    sponsor_name: Optional[str] = None
    sponsor_party: Optional[str] = None
    sponsor_state: Optional[str] = None
    sponsor_chamber: Optional[str] = None
    cosponsors_count: int = 0

    # Arrays
    actions: Optional[list] = None
    committees: Optional[list] = None
    subjects: Optional[list] = None

    # AI market impact
    affected_sectors: Optional[list] = None
    affected_tickers: Optional[list] = None
    market_sentiment: Optional[str] = None
    market_reasoning: Optional[str] = None
    market_confidence: Optional[float] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BillListResponse(BaseModel):
    """
    Paginated list of bills.
    """

    items: list[BillResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class BillFilter(BaseModel):
    """
    Query parameters for filtering bills.
    """

    bill_type: Optional[BillType] = None
    status: Optional[BillStatus] = None
    chamber: Optional[BillChamber] = None
    policy_area: Optional[PolicyArea] = None
    country: Optional[CountryCode] = None
    sponsor_party: Optional[str] = None
    sponsor_state: Optional[str] = None
    congress_number: Optional[int] = None
    introduced_after: Optional[datetime] = None
    introduced_before: Optional[datetime] = None
    has_market_impact: Optional[bool] = Field(
        default=None,
        description="Filter for bills that have AI market impact assessment",
    )
    affected_ticker: Optional[str] = Field(
        default=None,
        description="Filter bills affecting a specific stock ticker",
    )
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class BillSearchRequest(BaseModel):
    """
    Request body for keyword search across bills.
    """

    keyword: str = Field(..., min_length=1, max_length=200)
    limit: int = Field(default=20, ge=1, le=100)


class BillMarketImpactUpdate(BaseModel):
    """
    Schema for updating AI-generated market impact.
    Called by the AI layer after analyzing a bill.
    Separate schema keeps the AI update clean
    and auditable from regular bill updates.
    """

    affected_sectors: list[str]
    affected_tickers: list[str]
    market_sentiment: str = Field(
        ...,
        pattern="^(bullish|bearish|neutral)$",
        description="Must be bullish, bearish, or neutral",
    )
    market_reasoning: str = Field(..., max_length=2000)
    market_confidence: float = Field(..., ge=0.0, le=1.0)