"""Pydantic request and response schemas for triage API endpoints."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Incoming payload for disease advisory prediction."""

    crop_name: str = Field(min_length=2, max_length=100)
    disease_name: str = Field(min_length=2, max_length=150)
    symptoms: Optional[str] = Field(default=None, max_length=2000)


class AdvisoryData(BaseModel):
    """Structured advisory payload returned by database or LLM source."""

    crop_name: str
    disease_name: str
    description: str
    remedy: str
    prevention: str


class PredictResponse(BaseModel):
    """Standardized triage response format."""

    status: Literal["success", "fallback"]
    source: Literal["database", "llm"]
    data: AdvisoryData


class HealthResponse(BaseModel):
    """Simple health endpoint response schema."""

    status: Literal["ok"]
