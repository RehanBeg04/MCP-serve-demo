"""
Authentication and authorization primitives.

Exposes the core identity/security types used throughout the
application: UserPrincipal, the RBAC decorator and Role enum, the
security exception hierarchy, and context-propagation helpers.

Token verifier implementations (DevelopmentTokenVerifier,
AzureADTokenVerifier) are intentionally NOT re-exported here to avoid
importing jwt/httpx at package-import time for modules that only need
principal/RBAC types. Import them directly from
app.auth.jwt_validator when needed.
"""

from app.auth.context import (
    bind_correlation_id,
    bind_principal,
    get_current_correlation_id,
    get_current_principal,
    reset_correlation_id,
    reset_principal,
)
from app.auth.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    InvalidTokenError,
    MissingTokenError,
    SecurityError,
    TokenExpiredError,
)
from app.auth.principal import ANONYMOUS, UserPrincipal
from app.auth.rbac import ALL_ROLES, Role, check_access, require_roles

__all__ = [
    # context
    "bind_principal",
    "reset_principal",
    "get_current_principal",
    "bind_correlation_id",
    "reset_correlation_id",
    "get_current_correlation_id",
    # exceptions
    "SecurityError",
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "InvalidTokenError",
    "MissingTokenError",
    "TokenExpiredError",
    # principal
    "UserPrincipal",
    "ANONYMOUS",
    # rbac
    "Role",
    "ALL_ROLES",
    "require_roles",
    "check_access",
]