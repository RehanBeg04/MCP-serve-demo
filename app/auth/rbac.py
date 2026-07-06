"""
Role-Based Access Control.

Defines the supported roles and the @require_roles decorator used to
guard every MCP tool. Authorization is checked immediately before
tool execution, after authentication has already produced a
UserPrincipal for the current context.
"""

from __future__ import annotations

import functools
import inspect
from enum import Enum
from typing import Any, Callable, Iterable, TypeVar

from app.auth.context import get_current_principal
from app.auth.exceptions import AuthenticationError, AuthorizationError
from app.auth.principal import UserPrincipal
from app.logging.logger import get_logger

logger = get_logger(__name__)


def audit_log(*args: Any, **kwargs: Any) -> None:
    from app.logging.audit import audit_log as _audit_log

    _audit_log(*args, **kwargs)

F = TypeVar("F", bound=Callable[..., Any])


class Role(str, Enum):
    ADMIN = "Admin"
    DEVELOPER = "Developer"
    READER = "Reader"
    OPERATOR = "Operator"
    AI_AGENT = "AIAgent"


ALL_ROLES: frozenset[str] = frozenset(r.value for r in Role)

# Any authenticated principal, regardless of specific role, satisfies this.
AUTHENTICATED_ANY: frozenset[str] = ALL_ROLES


def check_access(principal: UserPrincipal | None, allowed_roles: Iterable[str]) -> None:
    """
    Pure authorization check.

    Raises AuthenticationError if there is no principal (never authenticated).
    Raises AuthorizationError if the principal lacks all allowed roles.
    """
    if principal is None:
        raise AuthenticationError("No authenticated principal for this request")

    allowed = frozenset(allowed_roles)
    if allowed and not principal.has_any_role(*allowed):
        raise AuthorizationError(
            f"Principal '{principal.user_id}' lacks required role(s): {sorted(allowed)}"
        )


def require_roles(*allowed_roles: str | Role) -> Callable[[F], F]:
    """
    Decorator enforcing RBAC on an MCP tool function.

    Usage:
        @require_roles(Role.ADMIN)
        async def delete_record(record_id: str) -> DeleteRecordResponse: ...

    Behavior:
        - Resolves the current UserPrincipal from context (set during
          authentication, before the MCP session/tool call).
        - Raises AuthenticationError (-> 401) if unauthenticated.
        - Raises AuthorizationError (-> 403) if the role check fails.
        - Emits an audit log entry for every authorization decision.
    """
    role_values = frozenset(r.value if isinstance(r, Role) else str(r) for r in allowed_roles)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            principal = get_current_principal()
            tool_name = func.__name__
            try:
                check_access(principal, role_values)
            except AuthenticationError as exc:
                audit_log(
                    event="authorization_denied",
                    tool=tool_name,
                    user_id="anonymous",
                    reason=exc.message,
                    outcome="denied",
                )
                raise
            except AuthorizationError as exc:
                audit_log(
                    event="authorization_denied",
                    tool=tool_name,
                    user_id=principal.user_id if principal else "unknown",
                    reason=exc.message,
                    outcome="denied",
                )
                raise

            audit_log(
                event="authorization_granted",
                tool=tool_name,
                user_id=principal.user_id,  # type: ignore[union-attr]
                reason=f"roles={sorted(role_values) or 'ANY_AUTHENTICATED'}",
                outcome="granted",
            )
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            principal = get_current_principal()
            check_access(principal, role_values)
            return func(*args, **kwargs)

        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper  # type: ignore[return-value]

    return decorator