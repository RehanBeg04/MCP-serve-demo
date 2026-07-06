"""
Pydantic schemas: request/response contracts.

Used for input validation (rejecting malformed tool arguments before
they reach business logic) and output validation (guaranteeing tool
responses match a known shape).
"""

from app.models.schemas import (
    DeleteRecordRequest,
    DeleteRecordResponse,
    ErrorResponse,
    HealthResponse,
    HelloResponse,
    ReadyResponse,
    WeatherRequest,
    WeatherResponse,
    WhoAmIResponse,
)

__all__ = [
    "HealthResponse",
    "ReadyResponse",
    "ErrorResponse",
    "WeatherRequest",
    "WeatherResponse",
    "DeleteRecordRequest",
    "DeleteRecordResponse",
    "WhoAmIResponse",
    "HelloResponse",
]