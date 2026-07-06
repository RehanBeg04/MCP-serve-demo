"""OAuth2 Protected Resource Metadata endpoint (RFC 9728)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings

router = APIRouter(tags=["oauth"])


@router.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource_metadata(
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    metadata = {
        "resource": settings.resource_identifier,
        "authorization_servers": settings.authorization_servers_list,
        "bearer_methods_supported": ["header"],
        "resource_documentation": f"{settings.resource_identifier}/docs",
    }
    return JSONResponse(content=metadata)