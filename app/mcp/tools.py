"""
MCP tool implementations.

Each tool is guarded by @require_roles at the function level (in
addition to the session-layer RBAC gate in authorization.py — defense
in depth). Inputs and outputs are validated via Pydantic models.
"""

from __future__ import annotations

import random

from app.auth.context import get_current_principal
from app.auth.exceptions import AuthorizationError
from app.auth.principal import UserPrincipal
from app.auth.rbac import Role, require_roles
from app.logging.logger import get_logger
from app.models.schemas import (
    DeleteRecordRequest,
    DeleteRecordResponse,
    HelloResponse,
    WeatherRequest,
    WeatherResponse,
    WhoAmIResponse,
)

logger = get_logger(__name__)

_SAMPLE_CONDITIONS = ("Sunny", "Cloudy", "Rainy", "Windy", "Snowy")


def _require_principal() -> UserPrincipal:
    principal = get_current_principal()
    if principal is None:
        raise AuthorizationError("No authenticated principal bound to this context")
    return principal


@require_roles()  # any authenticated principal
async def hello() -> HelloResponse:
    principal = _require_principal()
    display_name = principal.name or principal.email or principal.user_id
    return HelloResponse(message=f"Hello, {display_name}!")


@require_roles()  # any authenticated principal
async def who_am_i() -> WhoAmIResponse:
    principal = _require_principal()
    return WhoAmIResponse(
        user_id=principal.user_id,
        name=principal.name,
        email=principal.email,
        roles=sorted(principal.roles),
        tenant=principal.tenant,
        claims=dict(principal.claims),
    )


@require_roles(Role.READER, Role.ADMIN, Role.DEVELOPER, Role.OPERATOR, Role.AI_AGENT)
async def get_weather(city: str) -> WeatherResponse:
    validated = WeatherRequest(city=city)
    # Deterministic-ish sample data; not a real weather integration.
    seed = sum(ord(c) for c in validated.city.lower())
    rng = random.Random(seed)
    return WeatherResponse(
        city=validated.city,
        temperature_celsius=round(rng.uniform(-5, 35), 1),
        condition=rng.choice(_SAMPLE_CONDITIONS),
        humidity_percent=rng.randint(20, 90),
    )


@require_roles(Role.ADMIN)
async def delete_record(record_id: str) -> DeleteRecordResponse:
    principal = _require_principal()
    validated = DeleteRecordRequest(record_id=record_id)
    logger.info("record_deleted", record_id=validated.record_id, deleted_by=principal.user_id)
    return DeleteRecordResponse(
        record_id=validated.record_id,
        deleted=True,
        deleted_by=principal.user_id,
    )