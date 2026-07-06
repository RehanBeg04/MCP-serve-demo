"""
Application entrypoint.

Run locally with:
    python -m uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import health, oauth_metadata
from app.auth.exceptions import SecurityError
from app.auth.jwt_validator import get_token_verifier
from app.config import get_settings
from app.logging.logger import configure_logging, get_logger
from app.mcp.authentication import MCPAuthenticationMiddleware
from app.mcp.server import build_streamable_http_app
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.models.schemas import ErrorResponse

settings = get_settings()
configure_logging(log_level=settings.log_level, json_logs=(settings.app_env.value != "development"))
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.app_env.value != "production" else None,
    redoc_url=None,
)

# --- Middleware (order matters: outermost registered first here == closest to client) ---
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins_list, allow_credentials=False,
                    allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"])
app.add_middleware(SecurityHeadersMiddleware, enable_hsts=settings.enable_hsts)
app.add_middleware(CorrelationIdMiddleware)

# --- REST routers (unauthenticated by design: health checks + OAuth discovery) ---
app.include_router(health.router)
app.include_router(oauth_metadata.router)


# --- Centralized, non-leaky error handling ---
@app.exception_handler(SecurityError)
async def security_error_handler(request: Request, exc: SecurityError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    logger.warning(
        "request_security_error",
        error_code=exc.error_code,
        path=request.url.path,
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error_code, message=exc.message, correlation_id=correlation_id
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    logger.error(
        "unhandled_exception",
        error_type=type(exc).__name__,
        path=request.url.path,
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred.",
            correlation_id=correlation_id,
        ).model_dump(),
    )


# --- MCP mount: authentication is applied HERE, at the MCP layer, not as ---
# --- generic FastAPI route middleware. Session is only reachable after ---
# --- successful token verification. ---
_token_verifier = get_token_verifier(settings)
_mcp_asgi_app = build_streamable_http_app()
_authenticated_mcp_app = MCPAuthenticationMiddleware(_mcp_asgi_app, _token_verifier)

app.mount("/mcp", _authenticated_mcp_app)

logger.info(
    "application_startup",
    auth_mode=settings.auth_mode.value,
    environment=settings.app_env.value,
)