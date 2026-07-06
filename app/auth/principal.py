"""UserPrincipal: the verified identity attached to a request/session."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Optional


@dataclass(frozen=True)
class UserPrincipal:
    """
    Immutable representation of an authenticated caller.

    Constructed only after successful token verification. Never
    constructed directly from unverified/untrusted input.
    """

    user_id: str
    name: Optional[str]
    email: Optional[str]
    tenant: Optional[str]
    roles: FrozenSet[str]
    claims: Dict[str, Any] = field(default_factory=dict)

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, *roles: str) -> bool:
        return bool(self.roles.intersection(roles))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "tenant": self.tenant,
            "roles": sorted(self.roles),
        }


ANONYMOUS = UserPrincipal(
    user_id="anonymous",
    name=None,
    email=None,
    tenant=None,
    roles=frozenset(),
    claims={},
)