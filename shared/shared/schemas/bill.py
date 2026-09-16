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


class SponsorSchema(BaseModel):
    """
    The legislator who introduced the bill.
    """

    bioguide_id: str = Field(
        ...,
        description="Unique ID for the legislator from bioguide.congress.gov",
    )
    full_name: str = Field(
        ...,
        description="Full name of the sponsor",
    )
    party: str = Field(
        ...,
        description="Political party e.g. Democrat, Republican, Independent",
    )
    state: str = Field(
        ...,
        description="US state they represent e.g. NJ, NY, CA",
    )
    chamber: BillChamber = Field(
        ...,
        description="Whether sponsor is in House or Senate",
    )


class BillActionSchema(BaseModel):
    """
    A single action taken on a bill.
    Bills accumulate actions as they move through Congress.
    e.g. referred to committee, passed House, signed by President.
    """

    action_date: datetime = Field(
        ...,
        description="When this action occurred",
    )
    action_text: str = Field(
        ...,
        description="Description of the action taken",
    )
    chamber: Optional[BillChamber] = Field(
        default=None,
        description="Which chamber took this action",
    )
    status_after: Optional[BillStatus] = Field(
        default=None,
        description="Bill status after this action",
    )


class BillBase(BaseModel):
    """
    Core fields every bill has.
    """

    bill_number: str = Field(
        ...,
        description="Bill identifier e.g. HR-1234 or S-567",
    )
    bill_type: BillType = Field(
        ...,
        description="Type of legislative instrument",
    )
    congress_number: int = Field(
        ...,
        ge=1,
        description="Which Congress e.g. 119 for 119th Congress",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Official title of the bill",
    )
    short_title: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Common short name if available",
    )
    status: BillStatus = Field(
        ...,
        description="Current status in the legislative process",
    )
    chamber: BillChamber = Field(
        ...,
        description="Chamber where bill currently sits",
    )
    policy_area: PolicyArea = Field(
        ...,
        description="Policy domain — used to link bills to market sectors",
    )
    country: CountryCode = Field(
        default=CountryCode.US,
        description="Country this bill belongs to",
    )
    region: RegionCode = Field(
        default=RegionCode.AMER,
    )
    introduced_at: datetime = Field(
        ...,
        description="Date the bill was introduced",
    )
    last_action_at: Optional[datetime] = Field(
        default=None,
        description="Date of most recent action",
    )
    summary: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Plain English summary of what the bill does",
    )
    url: Optional[str] = Field(
        default=None,
        description="Link to full bill text on congress.gov",
    )


class BillSchema(BillBase):
    """
    Full bill schema including sponsor and actions.
    Used when ingesting from GovTrack.
    """

    sponsor: Optional[SponsorSchema] = Field(
        default=None,
        description="Legislator who introduced the bill",
    )
    cosponsors_count: int = Field(
        default=0,
        description="Number of cosponsors — signals political support",
    )
    actions: list[BillActionSchema] = Field(
        default_factory=list,
        description="Full history of actions taken on this bill",
    )
    committees: list[str] = Field(
        default_factory=list,
        description="Committees this bill was referred to",
    )
    related_bills: list[str] = Field(
        default_factory=list,
        description="Bill numbers of related legislation",
    )
    subjects: list[str] = Field(
        default_factory=list,
        description="Legislative subject tags from congress.gov",
    )


class BillResponse(BillBase):
    """
    What the API returns to the frontend.
    """

    id: int
    created_at: datetime
    updated_at: datetime
    sponsor: Optional[SponsorSchema] = None
    cosponsors_count: int = 0
    actions: list[BillActionSchema] = []
    committees: list[str] = []
    subjects: list[str] = []

    model_config = {"from_attributes": True}


class BillListResponse(BaseModel):
    """
    Paginated list of bills returned by the API.
    """

    items: list[BillResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class BillFilter(BaseModel):
    """
    Query parameters for filtering bills.
    Used by the /bills endpoint.
    """

    bill_type: Optional[BillType] = None
    status: Optional[BillStatus] = None
    chamber: Optional[BillChamber] = None
    policy_area: Optional[PolicyArea] = None
    country: Optional[CountryCode] = None
    sponsor_party: Optional[str] = None
    congress_number: Optional[int] = None
    introduced_after: Optional[datetime] = None
    introduced_before: Optional[datetime] = None
    keyword: Optional[str] = Field(
        default=None,
        description="Search bills by keyword in title or summary",
    )
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class BillMarketImpact(BaseModel):
    """
    AI-generated assessment of a bill's market impact.
    This is one of Argos's key differentiators —
    connecting legislation directly to affected sectors
    and tickers. Generated by the AI layer, stored here.
    """

    bill_id: int = Field(
        ...,
        description="Reference to the bill",
    )
    affected_sectors: list[str] = Field(
        default_factory=list,
        description="Market sectors this bill impacts e.g. Energy, Healthcare",
    )
    affected_tickers: list[str] = Field(
        default_factory=list,
        description="Specific tickers likely affected",
    )
    sentiment: str = Field(
        ...,
        description="bullish, bearish, or neutral for each sector",
    )
    reasoning: str = Field(
        ...,
        max_length=2000,
        description="AI explanation of why this bill matters to markets",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score 0 to 1",
    )
    generated_at: datetime = Field(
        ...,
        description="When this assessment was generated",
    )