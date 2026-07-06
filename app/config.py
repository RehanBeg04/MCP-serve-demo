"""
Centralized application configuration.

All configuration is loaded from environment variables (or a .env file
in local development) via pydantic-settings. No secrets are ever
hardcoded. This module is the single source of truth for config and
is imported everywhere else via the `get_settings()` cached accessor.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class AuthMode(str, Enum):
    DEVELOPMENT = "development"
    AZURE_AD = "azure_ad"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Environment ---
    app_env: Environment = Environment.DEVELOPMENT
    app_name: str = "secure-mcp-server"
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    debug: bool = False

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Auth mode ---
    auth_mode: AuthMode = AuthMode.DEVELOPMENT

    # --- Development JWT ---
    dev_jwt_secret: str = "change-this-dev-secret-please-32-chars-min"
    dev_jwt_issuer: str = "https://dev.secure-mcp-server.local"
    dev_jwt_audience: str = "secure-mcp-server"
    dev_jwt_algorithm: str = "HS256"

    # --- Azure AD ---
    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_audience: str | None = None
    azure_issuer: str | None = None
    azure_jwks_url: str | None = None
    azure_jwks_cache_ttl_seconds: int = 3600

    # --- JWT validation tuning ---
    jwt_clock_skew_seconds: int = 60
    jwt_required_claims: str = "sub,iss,aud,exp"

    # --- OAuth2 Protected Resource Metadata ---
    resource_identifier: str = "https://mcp.example.com"
    authorization_servers: str = ""

    # --- CORS ---
    cors_allowed_origins: str = "http://localhost:3000"

    # --- Security headers ---
    enable_hsts: bool = False

    @field_validator("dev_jwt_secret")
    @classmethod
    def _validate_dev_secret_strength(cls, v: str) -> str:
        if len(v) < 16:
            raise ValueError("dev_jwt_secret must be at least 16 characters long")
        return v

    @property
    def required_claims_list(self) -> List[str]:
        return [c.strip() for c in self.jwt_required_claims.split(",") if c.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def authorization_servers_list(self) -> List[str]:
        return [s.strip() for s in self.authorization_servers.split(",") if s.strip()]

    def validate_for_mode(self) -> None:
        """Fail fast if required config for the active auth mode is missing."""
        if self.auth_mode == AuthMode.AZURE_AD:
            missing = [
                name
                for name, val in (
                    ("azure_tenant_id", self.azure_tenant_id),
                    ("azure_audience", self.azure_audience),
                    ("azure_issuer", self.azure_issuer),
                    ("azure_jwks_url", self.azure_jwks_url),
                )
                if not val
            ]
            if missing:
                raise ValueError(
                    f"AUTH_MODE=azure_ad requires environment variables: {', '.join(missing)}"
                )
        if self.app_env == Environment.PRODUCTION and self.auth_mode == AuthMode.DEVELOPMENT:
            raise ValueError(
                "Refusing to start: APP_ENV=production cannot use AUTH_MODE=development"
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_for_mode()
    return settings