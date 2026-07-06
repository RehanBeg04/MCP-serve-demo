"""
Token verification.

Defines the TokenVerifier interface and two implementations:

- DevelopmentTokenVerifier: HS256 shared-secret JWTs, for local dev.
- AzureADTokenVerifier: RS256 JWTs validated against Azure AD's JWKS
  endpoint (OIDC), for production.

Both validate signature, issuer, audience, expiration, and clock skew.
The active implementation is selected purely by configuration
(AUTH_MODE), never by code changes.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Protocol

import httpx
import jwt
from jwt import PyJWKClient

from app.auth.exceptions import (
    ConfigurationError,
    InvalidTokenError,
    TokenExpiredError,
)
from app.auth.principal import UserPrincipal
from app.config import Settings
from app.logging.logger import get_logger

logger = get_logger(__name__)


class TokenVerifier(Protocol):
    """Interface every token verifier implementation must satisfy."""

    async def verify(self, token: str) -> UserPrincipal:
        """Verify a bearer token and return the resulting UserPrincipal.

        Raises AuthenticationError subclasses on any failure.
        """
        ...


class BaseTokenVerifier(ABC):
    """Shared claim-extraction logic for concrete verifiers."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @abstractmethod
    async def _decode(self, token: str) -> Dict[str, Any]:
        """Decode + cryptographically verify the token, return raw claims."""
        raise NotImplementedError

    async def verify(self, token: str) -> UserPrincipal:
        if not token or not token.strip():
            raise InvalidTokenError("Empty bearer token")

        try:
            claims = await self._decode(token)
        except jwt.ExpiredSignatureError as exc:
            logger.warning("token_expired", error=str(exc))
            raise TokenExpiredError() from exc
        except jwt.InvalidTokenError as exc:
            logger.warning("token_invalid", error=str(exc))
            raise InvalidTokenError(str(exc)) from exc

        self._check_required_claims(claims)
        return self._claims_to_principal(claims)

    def _check_required_claims(self, claims: Dict[str, Any]) -> None:
        missing = [c for c in self._settings.required_claims_list if c not in claims]
        if missing:
            raise InvalidTokenError(f"Token missing required claims: {missing}")

    def _claims_to_principal(self, claims: Dict[str, Any]) -> UserPrincipal:
        raw_roles = claims.get("roles") or claims.get("role") or []
        if isinstance(raw_roles, str):
            raw_roles = [raw_roles]
        roles = frozenset(str(r) for r in raw_roles)

        return UserPrincipal(
            user_id=str(claims.get("sub", "unknown")),
            name=claims.get("name"),
            email=claims.get("email") or claims.get("preferred_username"),
            tenant=claims.get("tid") or claims.get("tenant"),
            roles=roles,
            claims=claims,
        )


class DevelopmentTokenVerifier(BaseTokenVerifier):
    """
    HS256 shared-secret verifier for local development.

    Never used when APP_ENV=production (enforced in Settings.validate_for_mode).
    """

    async def _decode(self, token: str) -> Dict[str, Any]:
        return jwt.decode(
            token,
            key=self._settings.dev_jwt_secret,
            algorithms=[self._settings.dev_jwt_algorithm],
            issuer=self._settings.dev_jwt_issuer,
            audience=self._settings.dev_jwt_audience,
            leeway=self._settings.jwt_clock_skew_seconds,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )

    @staticmethod
    def issue_dev_token(
        settings: Settings,
        *,
        subject: str,
        name: str,
        email: str,
        roles: list[str],
        tenant: str = "dev-tenant",
        expires_in_seconds: int = 3600,
    ) -> str:
        """Utility for local development: mint a signed dev JWT."""
        now = int(time.time())
        payload = {
            "sub": subject,
            "name": name,
            "email": email,
            "roles": roles,
            "tid": tenant,
            "iss": settings.dev_jwt_issuer,
            "aud": settings.dev_jwt_audience,
            "iat": now,
            "exp": now + expires_in_seconds,
        }
        return jwt.encode(
            payload, settings.dev_jwt_secret, algorithm=settings.dev_jwt_algorithm
        )


class AzureADTokenVerifier(BaseTokenVerifier):
    """
    RS256 verifier backed by Azure AD's JWKS endpoint (OIDC).

    Uses PyJWKClient with an internal TTL cache so we don't hit the
    JWKS endpoint on every single request.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        if not settings.azure_jwks_url:
            raise ConfigurationError("AZURE_JWKS_URL is required for AzureADTokenVerifier")
        self._jwks_client = PyJWKClient(
            settings.azure_jwks_url,
            cache_keys=True,
            lifespan=settings.azure_jwks_cache_ttl_seconds,
        )

    async def _decode(self, token: str) -> Dict[str, Any]:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        except (jwt.exceptions.PyJWKClientError, httpx.HTTPError) as exc:
            logger.error("jwks_fetch_failed", error=str(exc))
            raise InvalidTokenError("Unable to verify token signature") from exc

        return jwt.decode(
            token,
            key=signing_key.key,
            algorithms=["RS256"],
            issuer=self._settings.azure_issuer,
            audience=self._settings.azure_audience,
            leeway=self._settings.jwt_clock_skew_seconds,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )


def get_token_verifier(settings: Settings) -> TokenVerifier:
    """Factory: selects the TokenVerifier implementation from configuration."""
    if settings.auth_mode.value == "azure_ad":
        return AzureADTokenVerifier(settings)
    return DevelopmentTokenVerifier(settings)