from sqlalchemy import Column, Integer, String, Boolean, JSON, Text, DateTime, text
from app.db.base import Base


class FundamentalsError(Base):
    __tablename__ = "fundamentals_errors"
    __table_args__ = {"comment": "Dead letter queue for failed fundamentals pipeline runs"}

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    ticker = Column(String(20), nullable=True, index=True)
    cik = Column(String(20), nullable=True)
    stage = Column(String(50), nullable=False, index=True,
                   comment="fetch, parse, normalize, write")
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text(), nullable=True)
    raw_data = Column(JSON(), nullable=True)
    resolved = Column(Boolean(), nullable=False, server_default=text("false"),
                      index=True)
    retry_count = Column(Integer(), nullable=False, server_default=text("0"))
    created_at = Column(DateTime(timezone=True), server_default=text("now()"),
                        nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"),
                        nullable=False)