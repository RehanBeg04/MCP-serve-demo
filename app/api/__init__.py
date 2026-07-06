"""
Unauthenticated REST endpoints.

Health/readiness/liveness probes and OAuth2 Protected Resource
Metadata (RFC 9728). These routes are intentionally reachable without
a bearer token so orchestrators and MCP clients can probe/discover
before authentication is possible.
"""

from app.api.health import router as health_router
from app.api.oauth_metadata import router as oauth_metadata_router

__all__ = [
    "health_router",
    "oauth_metadata_router",
]