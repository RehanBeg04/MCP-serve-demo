import importlib

from app.mcp.server import build_streamable_http_app


def test_app_mcp_imports_without_circular_import() -> None:
    module = importlib.import_module("app.mcp")
    assert module is not None


def test_streamable_http_app_builds() -> None:
    app = build_streamable_http_app()
    assert app is not None
