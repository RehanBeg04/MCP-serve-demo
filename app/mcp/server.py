"""
MCP server construction.

Builds an MCP Server instance, registers tool definitions + handlers,
and exposes a Streamable HTTP ASGI app. Every tool call is routed
through app.mcp.session.dispatch_tool_call so RBAC + audit logging
always run before a handler executes — tools are never invoked
directly by the transport layer.
"""

from __future__ import annotations

from typing import Any, Dict, List

import mcp.types as types
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.fastmcp.server import StreamableHTTPASGIApp

from app.logging.logger import get_logger
from app.mcp import tools as tool_impls
from app.mcp.session import dispatch_tool_call

logger = get_logger(__name__)

TOOL_DEFINITIONS: List[types.Tool] = [
    types.Tool(
        name="hello",
        description="Returns a greeting for the authenticated user.",
        inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
    ),
    types.Tool(
        name="who_am_i",
        description="Returns the authenticated user's identity, roles, tenant, and claims.",
        inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
    ),
    types.Tool(
        name="get_weather",
        description="Returns sample weather data for a city. Requires Reader role or above.",
        inputSchema={
            "type": "object",
            "properties": {"city": {"type": "string", "minLength": 1, "maxLength": 100}},
            "required": ["city"],
            "additionalProperties": False,
        },
    ),
    types.Tool(
        name="delete_record",
        description="Deletes a record by ID. Requires Admin role.",
        inputSchema={
            "type": "object",
            "properties": {"record_id": {"type": "string", "minLength": 1, "maxLength": 128}},
            "required": ["record_id"],
            "additionalProperties": False,
        },
    ),
]

_TOOL_HANDLERS: Dict[str, Any] = {
    "hello": tool_impls.hello,
    "who_am_i": tool_impls.who_am_i,
    "get_weather": tool_impls.get_weather,
    "delete_record": tool_impls.delete_record,
}


def build_mcp_server() -> Server:
    server = Server("secure-mcp-server")

    @server.list_tools()
    async def list_tools() -> List[types.Tool]:
        return TOOL_DEFINITIONS

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any] | None) -> List[types.TextContent]:
        handler = _TOOL_HANDLERS.get(name)
        if handler is None:
            raise ValueError(f"Unknown tool: {name}")

        result = await dispatch_tool_call(name, handler, arguments or {})
        return [types.TextContent(type="text", text=result.model_dump_json())]

    return server


def build_streamable_http_app() -> Any:
    """
    Returns an ASGI app for the MCP Streamable HTTP transport, mounted
    (with authentication applied in front of it) by app/main.py.
    """
    server = build_mcp_server()
    session_manager = StreamableHTTPSessionManager(app=server)
    return StreamableHTTPASGIApp(session_manager)