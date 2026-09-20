from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, text
from app.db.base import Base


class FundamentalsSummary(Base):
    __tablename__ = "fundamentals_summary"
    __table_args__ = {"comment": "Pre-aggregated fundamentals — one row per ticker per period"}

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    cik = Column(String(20), nullable=True, index=True)
    period_end = Column(Date(), nullable=False, index=True)
    period_type = Column(String(10), nullable=True, index=True)
    form = Column(String(20), nullable=True, index=True)
    filed_at = Column(Date(), nullable=True, index=True)
    # Income statement
    revenue = Column(Numeric(), nullable=True)
    gross_profit = Column(Numeric(), nullable=True)
    gross_margin = Column(Numeric(), nullable=True)
    operating_income = Column(Numeric(), nullable=True)
    operating_margin = Column(Numeric(), nullable=True)
    net_income = Column(Numeric(), nullable=True)
    net_margin = Column(Numeric(), nullable=True)
    ebitda = Column(Numeric(), nullable=True)
    ebitda_margin = Column(Numeric(), nullable=True)
    eps_basic = Column(Numeric(), nullable=True)
    eps_diluted = Column(Numeric(), nullable=True)
    shares_outstanding = Column(Numeric(), nullable=True)
    # Balance sheet
    total_assets = Column(Numeric(), nullable=True)
    total_liabilities = Column(Numeric(), nullable=True)
    total_equity = Column(Numeric(), nullable=True)
    cash = Column(Numeric(), nullable=True)
    total_debt = Column(Numeric(), nullable=True)
    net_debt = Column(Numeric(), nullable=True)
    # Cash flow
    operating_cash_flow = Column(Numeric(), nullable=True)
    capex = Column(Numeric(), nullable=True)
    free_cash_flow = Column(Numeric(), nullable=True)
    depreciation = Column(Numeric(), nullable=True)
    # Derived ratios
    debt_to_equity = Column(Numeric(), nullable=True)
    current_ratio = Column(Numeric(), nullable=True)
    roe = Column(Numeric(), nullable=True)
    roic = Column(Numeric(), nullable=True)
    # Meta
    parsed_by = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"),
                        nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"),
                        nullable=False)