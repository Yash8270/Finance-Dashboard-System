from sqlalchemy import Column, Integer, Float, String, Enum, Date, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from db import Base
import enum


class TypeEnum(str, enum.Enum):
    income = "income"
    expense = "expense"


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TypeEnum), nullable=False)
    category = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
