from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GovernmentContract(Base):
    """
    Federal contract awards from USASpending.gov.
    One row per contract award.
    Links government spending directly to public companies.
    """

    __tablename__ = "government_contracts"

    # Core identification
    award_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique award ID from USASpending.gov",
    )
    award_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Contract, Grant, Loan, Direct Payment",
    )

    # Description
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Financial amounts
    total_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
        comment="Total obligated amount in USD",
    )
    base_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Base contract value before options",
    )
    potential_amount: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Maximum potential value including all options",
    )

    # Dates
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    signed_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Agency fields — flattened for query performance
    agency_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    agency_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    sub_agency_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    agency_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Recipient fields — flattened for query performance
    recipient_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    recipient_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    recipient_uei: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Unique Entity Identifier — replaced DUNS in 2022",
    )
    parent_recipient_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        index=True,
    )

    # The key financial link — ticker symbol
    ticker: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Stock ticker if recipient is publicly traded",
    )

    # Location
    recipient_country: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="US",
        index=True,
    )
    recipient_state: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
        index=True,
    )
    congressional_district: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        index=True,
        comment="Links spending to congressional districts and legislators",
    )
    place_of_performance: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Classification
    naics_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        index=True,
    )
    naics_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    psc_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        index=True,
        comment="Product Service Code — what was purchased",
    )
    psc_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Competition
    is_compete: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether contract was competitively bid",
    )
    number_of_offers: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of companies that bid",
    )

    # Geography
    country: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="US",
        index=True,
    )
    region: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="AMER",
    )

    # Source link
    url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    # Raw data
    raw_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Original USASpending.gov API response",
    )

    __table_args__ = (
        {"comment": "Federal contract awards from USASpending.gov"},
    )

    def __repr__(self) -> str:
        return (
            f"<GovernmentContract id={self.id} "
            f"award_id={self.award_id} "
            f"recipient={self.recipient_name} "
            f"amount={self.total_amount}>"
        )