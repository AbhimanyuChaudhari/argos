from sqlalchemy import String, Text, Boolean, DateTime, Float, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GovernmentFiling(Base):
    """
    SEC EDGAR and government filing records.
    One row per filing document.
    """

    __tablename__ = "government_filings"

    # Core fields
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    filing_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
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
        index=True,
    )
    filed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # SEC EDGAR specific fields
    cik: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )
    accession_number: Mapped[str | None] = mapped_column(
        String(25),
        nullable=True,
        unique=True,
        index=True,
    )
    company_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        index=True,
    )
    ticker: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )
    period_of_report: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_amendment: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    items: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Raw data storage
    raw_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Original API response — kept for debugging and reprocessing",
    )

    def __repr__(self) -> str:
        return (
            f"<GovernmentFiling id={self.id} "
            f"type={self.filing_type} "
            f"company={self.company_name} "
            f"filed={self.filed_at}>"
        )