"""SQLAlchemy models for triage persistence."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class FarmerQuery(Base):
    """Stores farmer requests and generated responses for audit and analytics."""

    __tablename__ = "farmer_queries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(100), nullable=False)
    urgency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    response: Mapped[str] = mapped_column(Text, nullable=False)


class CropDisease(Base):
    """Stores canonical crop disease guidance and treatment details."""

    __tablename__ = "crop_diseases"
    __table_args__ = (
        UniqueConstraint("crop_name", "disease_name", name="uq_crop_disease"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    crop_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    disease_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    symptoms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    treatment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prevention: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Scheme(Base):
    """Stores government scheme metadata by region."""

    __tablename__ = "schemes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    eligibility: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    benefits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
