from sqlalchemy import (
    Column, Integer, Numeric, String, Enum, Date, Text,
    ForeignKey, DateTime, Boolean, Index,
)
from sqlalchemy.sql import func
from db import Base
from enums import TypeEnum


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)

    # CASCADE: if a user is ever deleted, their records are removed too
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Numeric(12, 2) avoids the floating-point precision loss of Float —
    # critical for financial data where 0.1 + 0.2 must never equal 0.30000000000004
    amount = Column(Numeric(12, 2), nullable=False)

    type = Column(Enum(TypeEnum), nullable=False)
    category = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)

    # Soft delete — record is hidden from all queries but preserved for audit history
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Composite and single-column indexes for the most common filter patterns
    __table_args__ = (
        Index("ix_records_date", "date"),
        Index("ix_records_type", "type"),
        Index("ix_records_user_id_date", "user_id", "date"),
    )
