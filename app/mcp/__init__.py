"""
MCP protocol layer.

Contains MCP-specific authentication (transport-boundary token
verification), authorization (per-tool RBAC gate), session dispatch,
tool implementations, and server/transport construction.

Authentication for MCP requests is deliberately isolated here rather
than in generic FastAPI middleware — see app.mcp.authentication.
"""

from app.mcp.server import build_mcp_server, build_streamable_http_app

__all__ = [
    "build_mcp_server",
    "build_streamable_http_app",
]