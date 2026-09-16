from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Bill(Base):
    """
    US Congressional bills and resolutions.
    Sourced from GovTrack API.
    One row per bill per Congress.
    """

    __tablename__ = "government_bills"

    # Core identification
    bill_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    bill_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    congress_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    # Composite unique constraint — same bill number
    # can exist across different Congresses
    __table_args__ = (
        {"comment": "US Congressional bills sourced from GovTrack"},
    )

    # Bill details
    title: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        index=True,
    )
    short_title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    # Status and location
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    chamber: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    policy_area: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
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

    # Dates
    introduced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    last_action_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Sponsor
    sponsor_bioguide_id: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )
    sponsor_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    sponsor_party: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    sponsor_state: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
        index=True,
    )
    sponsor_chamber: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # Support metrics
    cosponsors_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # JSON fields for arrays
    actions: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Full action history as JSON array",
    )
    committees: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Committee names this bill was referred to",
    )
    related_bills: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Related bill numbers",
    )
    subjects: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Legislative subject tags",
    )

    # AI generated market impact
    affected_sectors: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Market sectors affected by this bill",
    )
    affected_tickers: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Stock tickers likely affected",
    )
    market_sentiment: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="bullish, bearish, or neutral",
    )
    market_reasoning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="AI explanation of market impact",
    )
    market_confidence: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="AI confidence score 0 to 1",
    )

    # Raw data
    raw_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Original GovTrack API response",
    )

    def __repr__(self) -> str:
        return (
            f"<Bill id={self.id} "
            f"number={self.bill_number} "
            f"congress={self.congress_number} "
            f"status={self.status}>"
        )