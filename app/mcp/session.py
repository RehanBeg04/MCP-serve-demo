"""
MCP session-layer glue.

Provides a single entrypoint, `dispatch_tool_call`, used by the MCP
server (server.py) to run every tool invocation through:

    RBAC check (authorize_tool_call) -> audit-wrapped execution -> tool handler

The UserPrincipal itself was already bound to context by
MCPAuthenticationMiddleware before the session/request reached here.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from app.logging.audit import audit_tool_execution
from app.logging.logger import get_logger
from app.mcp.authorization import authorize_tool_call

logger = get_logger(__name__)

ToolHandler = Callable[..., Awaitable[Any]]


async def dispatch_tool_call(
    tool_name: str,
    handler: ToolHandler,
    arguments: Dict[str, Any],
) -> Any:
    """
    Central dispatch point for every MCP tool call.

    1. RBAC check against the principal bound for this session/request.
    2. Execute the tool handler inside an audit-logged span.
    """
    principal = authorize_tool_call(tool_name)

    logger.info("mcp_tool_call_started", tool=tool_name, user_id=principal.user_id)
    with audit_tool_execution(tool_name, principal.user_id):
        result = await handler(**arguments)

    logger.info("mcp_tool_call_finished", tool=tool_name, user_id=principal.user_id)
    return result