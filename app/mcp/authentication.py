"""
MCP-layer authentication.

This ASGI wrapper sits directly in front of the MCP Streamable HTTP
app (not generic FastAPI route middleware) and enforces:

    Bearer token -> TokenVerifier -> UserPrincipal -> bound to context
                 -> only then does the request reach the MCP session.

This satisfies the requirement that authentication happens BEFORE an
MCP session is established, and that it is integrated into the MCP
layer rather than bolted on as generic HTTP middleware.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send

from app.auth.context import bind_principal, reset_principal
from app.auth.exceptions import AuthenticationError, MissingTokenError
from app.auth.jwt_validator import TokenVerifier
from app.logging.audit import audit_log
from app.logging.logger import get_logger

logger = get_logger(__name__)

BEARER_PREFIX = "bearer "


def _extract_bearer_token(scope: Scope) -> str:
    headers = dict(scope.get("headers") or [])
    raw = headers.get(b"authorization")
    if not raw:
        raise MissingTokenError("Authorization header is required")

    value = raw.decode("latin-1")
    if not value.lower().startswith(BEARER_PREFIX):
        raise MissingTokenError("Authorization header must be a Bearer token")

    token = value[len(BEARER_PREFIX):].strip()
    if not token:
        raise MissingTokenError("Bearer token is empty")
    return token


async def _send_json_error(send: Send, status: int, error_code: str, message: str) -> None:
    import json

    body = json.dumps({"error": error_code, "message": message}).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("latin-1")),
                (b"www-authenticate", b'Bearer realm="mcp"'),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


class MCPAuthenticationMiddleware:
    """
    ASGI middleware wrapping *only* the MCP Streamable HTTP mount.

    On every request:
      1. Extract + verify the bearer token (TokenVerifier).
      2. Build a UserPrincipal.
      3. Bind it to the request-scoped context.
      4. Only then forward the request into the MCP app / session.
      5. Always unbind on completion, even on error.
    """

    def __init__(self, app: ASGIApp, token_verifier: TokenVerifier) -> None:
        self.app = app
        self.token_verifier = token_verifier

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        try:
            token = _extract_bearer_token(scope)
            principal = await self.token_verifier.verify(token)
        except AuthenticationError as exc:
            audit_log(
                event="authentication_failed",
                outcome="denied",
                user_id="anonymous",
                reason=exc.message,
                error_code=exc.error_code,
            )
            logger.warning("mcp_authentication_failed", error_code=exc.error_code)
            await _send_json_error(send, exc.status_code, exc.error_code, exc.message)
            return

        audit_log(
            event="authentication_succeeded",
            outcome="success",
            user_id=principal.user_id,
            roles=sorted(principal.roles),
        )

        ctx_token = bind_principal(principal)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_principal(ctx_token)