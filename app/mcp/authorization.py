"""MCP-layer authorization helpers (defense-in-depth alongside @require_roles)."""

from __future__ import annotations

from app.auth.context import get_current_principal
from app.auth.exceptions import AuthenticationError, AuthorizationError
from app.auth.principal import UserPrincipal
from app.auth.rbac import check_access
from app.logging.audit import audit_log


# Maps tool name -> required roles. Kept alongside the decorators in
# tools.py as a second, protocol-level enforcement point.
TOOL_ROLE_MAP: dict[str, frozenset[str]] = {
    "hello": frozenset(),  # any authenticated principal
    "who_am_i": frozenset(),  # any authenticated principal
    "get_weather": frozenset({"Reader", "Admin", "Developer", "Operator", "AIAgent"}),
    "delete_record": frozenset({"Admin"}),
}


def authorize_tool_call(tool_name: str) -> UserPrincipal:
    """
    Resolve the current principal and enforce RBAC for the given tool
    name at the MCP session layer, before the tool handler executes.
    """
    principal = get_current_principal()
    required_roles = TOOL_ROLE_MAP.get(tool_name, frozenset({"Admin"}))  # fail-closed default

    try:
        check_access(principal, required_roles)
    except (AuthenticationError, AuthorizationError) as exc:
        audit_log(
            event="mcp_tool_call_denied",
            outcome="denied",
            user_id=principal.user_id if principal else "anonymous",
            tool=tool_name,
            reason=exc.message,
        )
        raise

    assert principal is not None  # check_access would have raised otherwise
    return principal