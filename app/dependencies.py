"""Shared FastAPI dependencies for REST routes (non-MCP)."""

from __future__ import annotations

from fastapi import Depends

from app.config import Settings, get_settings


def settings_dependency(settings: Settings = Depends(get_settings)) -> Settings:
    return settings