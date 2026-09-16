from datetime import datetime
from sqlalchemy import String, Text, Float, DateTime, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LobbyingDisclosure(Base):
    """
    Lobbying disclosure filings from OpenSecrets.
    All companies spending over $10K on lobbying
    must file quarterly disclosures with Congress.
    One row per quarterly disclosure filing.
    """

    __tablename__ = "government_lobbying"

    # Core identification
    filing_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique filing ID from OpenSecrets",
    )
    filing_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Q1, Q2, Q3, Q4, Mid-Year, Year-End",
    )
    filing_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    filing_period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="e.g. 2024 Q1, 2024 Mid-Year",
    )
    filed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Financial
    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
        comment="Total lobbying spend in USD for this period",
    )

    # Client fields — flattened
    client_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    client_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    client_industry: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # The key financial link
    ticker: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        comment="Stock ticker if client is publicly traded",
    )

    # Registrant — the lobbying firm hired
    registrant_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    registrant_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    # Geography
    client_country: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="US",
        index=True,
    )
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

    # JSON fields for arrays
    lobbyists: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Individual lobbyists working this filing",
    )
    issues: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Specific issues and bills being lobbied on",
    )

    # Revolving door flag
    has_former_government: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="True if any lobbyist is a former government official",
    )

    # Year over year change
    yoy_change: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Year over year spend change as percentage",
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
        comment="Original OpenSecrets API response",
    )

    __table_args__ = (
        {"comment": "Lobbying disclosures from OpenSecrets"},
    )

    def __repr__(self) -> str:
        return (
            f"<LobbyingDisclosure id={self.id} "
            f"client={self.client_name} "
            f"amount={self.amount} "
            f"period={self.filing_period}>"
        )