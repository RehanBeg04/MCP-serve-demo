"""Pydantic models: input/output schemas for tools and API responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


class ReadyResponse(BaseModel):
    status: str
    checks: Dict[str, str]


class ErrorResponse(BaseModel):
    """Consistent, non-leaky error envelope. Never contains stack traces."""

    error: str
    message: str
    correlation_id: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class WeatherRequest(BaseModel):
    city: str = Field(min_length=1, max_length=100)

    @field_validator("city")
    @classmethod
    def _sanitize_city(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("city must not be blank")
        if any(ch in cleaned for ch in ("<", ">", ";", "{", "}")):
            raise ValueError("city contains invalid characters")
        return cleaned


class WeatherResponse(BaseModel):
    city: str
    temperature_celsius: float
    condition: str
    humidity_percent: int


class DeleteRecordRequest(BaseModel):
    record_id: str = Field(min_length=1, max_length=128)

    @field_validator("record_id")
    @classmethod
    def _sanitize_record_id(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned.isalnum() and "-" not in cleaned and "_" not in cleaned:
            raise ValueError("record_id contains invalid characters")
        return cleaned


class DeleteRecordResponse(BaseModel):
    record_id: str
    deleted: bool
    deleted_by: str


class WhoAmIResponse(BaseModel):
    user_id: str
    name: Optional[str]
    email: Optional[str]
    roles: List[str]
    tenant: Optional[str]
    claims: Dict[str, Any]


class HelloResponse(BaseModel):
    message: str