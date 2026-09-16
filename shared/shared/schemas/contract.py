from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from shared.enums.country import CountryCode, RegionCode


class AgencySchema(BaseModel):
    """
    Federal agency awarding the contract.
    """

    agency_id: str = Field(
        ...,
        description="Unique agency identifier from USASpending",
    )
    agency_name: str = Field(
        ...,
        description="Full name of the awarding agency",
    )
    sub_agency_name: Optional[str] = Field(
        default=None,
        description="Sub-agency or office within the agency",
    )
    agency_code: Optional[str] = Field(
        default=None,
        description="Federal agency code",
    )


class RecipientSchema(BaseModel):
    """
    Company or entity receiving the contract.
    This is the financially important part —
    links government spending directly to companies
    that may be publicly traded.
    """

    recipient_id: str = Field(
        ...,
        description="Unique recipient identifier from USASpending",
    )
    recipient_name: str = Field(
        ...,
        description="Legal name of the recipient",
    )
    recipient_uei: Optional[str] = Field(
        default=None,
        description="Unique Entity Identifier — replaced DUNS number in 2022",
    )
    parent_recipient_name: Optional[str] = Field(
        default=None,
        description="Parent company name if recipient is a subsidiary",
    )
    ticker: Optional[str] = Field(
        default=None,
        description="Stock ticker if recipient is publicly traded",
    )
    country: CountryCode = Field(
        default=CountryCode.US,
        description="Country where recipient is based",
    )
    state: Optional[str] = Field(
        default=None,
        description="US state where recipient is based",
    )
    congressional_district: Optional[str] = Field(
        default=None,
        description="Congressional district — links spending to legislators",
    )


class ContractBase(BaseModel):
    """
    Core fields for a federal contract award.
    """

    award_id: str = Field(
        ...,
        description="Unique contract award ID from USASpending",
    )
    award_type: str = Field(
        ...,
        description="Type of award e.g. Contract, Grant, Loan, Direct Payment",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="What goods or services the contract covers",
    )
    total_amount: float = Field(
        ...,
        description="Total obligated amount in USD",
    )
    base_amount: float = Field(
        ...,
        description="Base contract value before options",
    )
    potential_amount: Optional[float] = Field(
        default=None,
        description="Maximum potential value including all options",
    )
    start_date: datetime = Field(
        ...,
        description="Contract period of performance start",
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="Contract period of performance end",
    )
    signed_date: Optional[datetime] = Field(
        default=None,
        description="Date contract was signed",
    )
    country: CountryCode = Field(
        default=CountryCode.US,
    )
    region: RegionCode = Field(
        default=RegionCode.AMER,
    )


class ContractSchema(ContractBase):
    """
    Full contract schema including agency and recipient.
    Used when ingesting from USASpending.gov.
    """

    agency: AgencySchema = Field(
        ...,
        description="Federal agency that awarded the contract",
    )
    recipient: RecipientSchema = Field(
        ...,
        description="Entity that received the contract",
    )
    naics_code: Optional[str] = Field(
        default=None,
        description="North American Industry Classification System code",
    )
    naics_description: Optional[str] = Field(
        default=None,
        description="Human readable NAICS description",
    )
    psc_code: Optional[str] = Field(
        default=None,
        description="Product Service Code — what was actually purchased",
    )
    psc_description: Optional[str] = Field(
        default=None,
        description="Human readable PSC description",
    )
    place_of_performance: Optional[str] = Field(
        default=None,
        description="Where the work will be performed",
    )
    is_compete: bool = Field(
        default=True,
        description="Whether contract was competitively bid",
    )
    number_of_offers: Optional[int] = Field(
        default=None,
        description="How many companies bid on this contract",
    )
    url: Optional[str] = Field(
        default=None,
        description="Link to contract on USASpending.gov",
    )


class ContractResponse(ContractBase):
    """
    What the API returns to the frontend.
    """

    id: int
    agency: AgencySchema
    recipient: RecipientSchema
    naics_code: Optional[str] = None
    naics_description: Optional[str] = None
    psc_code: Optional[str] = None
    is_compete: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContractListResponse(BaseModel):
    """
    Paginated list of contracts returned by the API.
    """

    items: list[ContractResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ContractFilter(BaseModel):
    """
    Query parameters for filtering contracts.
    Used by the /contracts endpoint.
    """

    agency_name: Optional[str] = None
    recipient_name: Optional[str] = None
    ticker: Optional[str] = Field(
        default=None,
        description="Filter contracts by recipient stock ticker",
    )
    naics_code: Optional[str] = None
    psc_code: Optional[str] = None
    min_amount: Optional[float] = Field(
        default=None,
        description="Minimum contract value in USD",
    )
    max_amount: Optional[float] = Field(
        default=None,
        description="Maximum contract value in USD",
    )
    is_compete: Optional[bool] = None
    country: Optional[CountryCode] = None
    signed_after: Optional[datetime] = None
    signed_before: Optional[datetime] = None
    keyword: Optional[str] = Field(
        default=None,
        description="Search by keyword in contract description",
    )
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ContractSpendingSummary(BaseModel):
    """
    Aggregated spending summary by agency or recipient.
    Used for the spending dashboard in the terminal.
    """

    entity_name: str = Field(
        ...,
        description="Agency or recipient name",
    )
    entity_type: str = Field(
        ...,
        description="agency or recipient",
    )
    total_amount: float = Field(
        ...,
        description="Total spending in USD",
    )
    contract_count: int = Field(
        ...,
        description="Number of contracts",
    )
    ticker: Optional[str] = Field(
        default=None,
        description="Stock ticker if entity is publicly traded",
    )
    period_start: datetime
    period_end: datetime