"""Health, readiness, and liveness endpoints. Intentionally unauthenticated."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.models.schemas import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env.value,
    )


@router.get("/live", response_model=HealthResponse)
async def live(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="alive",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env.value,
    )


@router.get("/ready", response_model=ReadyResponse)
async def ready(settings: Settings = Depends(get_settings)) -> ReadyResponse:
    checks = {"config": "ok"}
    if settings.auth_mode.value == "azure_ad":
        checks["azure_jwks_url_configured"] = "ok" if settings.azure_jwks_url else "fail"
    return ReadyResponse(status="ready", checks=checks)