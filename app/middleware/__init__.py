"""
ASGI middleware.

Cross-cutting HTTP concerns applied to all REST routes: correlation
ID propagation and defensive security headers. MCP authentication is
NOT here by design — see app.mcp.authentication.
"""

from app.middleware.correlation import CORRELATION_ID_HEADER, CorrelationIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

__all__ = [
    "CorrelationIdMiddleware",
    "CORRELATION_ID_HEADER",
    "SecurityHeadersMiddleware",
]