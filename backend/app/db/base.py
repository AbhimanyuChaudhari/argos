from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import DateTime, func
from sqlalchemy.orm import mapped_column, Mapped
from datetime import datetime


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models in Argos.
    Every table automatically gets id, created_at, updated_at.
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )