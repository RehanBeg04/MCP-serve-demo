"""Typed exception hierarchy for authentication and authorization failures."""

from __future__ import annotations


class SecurityError(Exception):
    """Base class for all auth-related errors. Carries an HTTP status code."""

    status_code: int = 500
    error_code: str = "security_error"

    def __init__(self, message: str = "Security error") -> None:
        self.message = message
        super().__init__(message)


class AuthenticationError(SecurityError):
    """Raised when a token is missing, malformed, expired, or fails verification."""

    status_code = 401
    error_code = "authentication_failed"

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    error_code = "token_expired"

    def __init__(self, message: str = "Token has expired") -> None:
        super().__init__(message)


class InvalidTokenError(AuthenticationError):
    error_code = "invalid_token"

    def __init__(self, message: str = "Token is invalid") -> None:
        super().__init__(message)


class MissingTokenError(AuthenticationError):
    error_code = "missing_token"

    def __init__(self, message: str = "Bearer token is required") -> None:
        super().__init__(message)


class AuthorizationError(SecurityError):
    """Raised when an authenticated principal lacks the required role(s)."""

    status_code = 403
    error_code = "authorization_failed"

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message)


class ConfigurationError(SecurityError):
    """Raised when security-relevant configuration is invalid or missing."""

    status_code = 500
    error_code = "configuration_error"

    def __init__(self, message: str = "Server security configuration error") -> None:
        super().__init__(message)