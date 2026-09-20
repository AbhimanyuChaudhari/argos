from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, text
from app.db.base import Base


class FundamentalsFact(Base):
    __tablename__ = "fundamentals_facts"
    __table_args__ = {"comment": "Raw XBRL facts from SEC EDGAR — audit trail"}

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    cik = Column(String(20), nullable=False, index=True)
    concept = Column(String(200), nullable=False, index=True,
                     comment="XBRL concept name e.g. us-gaap/Revenues")
    label = Column(String(200), nullable=True)
    value = Column(Numeric(), nullable=False)
    unit = Column(String(50), nullable=True, comment="USD, shares, pure")
    period_start = Column(Date(), nullable=True)
    period_end = Column(Date(), nullable=False, index=True)
    period_type = Column(String(10), nullable=True, index=True,
                         comment="annual or quarterly")
    form = Column(String(20), nullable=True, index=True)
    filed_at = Column(Date(), nullable=True)
    parsed_by = Column(String(20), nullable=True, index=True,
                       comment="xbrl or llm")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"),
                        nullable=False)