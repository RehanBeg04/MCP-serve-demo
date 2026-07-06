"""
Request-scoped principal propagation via contextvars.

Authentication happens once, at the MCP transport boundary (see
app/mcp/authentication.py), producing a UserPrincipal that is bound
here for the lifetime of that request/session context. RBAC checks
and tools read the principal from here — they never see the raw
token and never re-run verification.

contextvars are used (not a global/thread-local dict) so this is safe
under asyncio concurrency: each concurrent request gets its own
isolated context.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Optional

from app.auth.principal import UserPrincipal

_current_principal: ContextVar[Optional[UserPrincipal]] = ContextVar(
    "current_principal", default=None
)
_current_correlation_id: ContextVar[Optional[str]] = ContextVar(
    "current_correlation_id", default=None
)


def bind_principal(principal: UserPrincipal) -> Token:
    """Bind a verified principal to the current context. Returns a reset token."""
    return _current_principal.set(principal)


def reset_principal(token: Token) -> None:
    _current_principal.reset(token)


def get_current_principal() -> Optional[UserPrincipal]:
    return _current_principal.get()


def bind_correlation_id(correlation_id: str) -> Token:
    return _current_correlation_id.set(correlation_id)


def reset_correlation_id(token: Token) -> None:
    _current_correlation_id.reset(token)


def get_current_correlation_id() -> Optional[str]:
    return _current_correlation_id.get()