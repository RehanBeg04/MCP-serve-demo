"""
MCP protocol layer.

Contains MCP-specific authentication (transport-boundary token
verification), authorization (per-tool RBAC gate), session dispatch,
tool implementations, and server/transport construction.

Authentication for MCP requests is deliberately isolated here rather
than in generic FastAPI middleware — see app.mcp.authentication.
"""

from app.mcp.server import mcp_server, session_manager, mcp_asgi_app

__all__ = [
    "mcp_server",
    "session_manager",
    "mcp_asgi_app",
]