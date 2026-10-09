"""DRF authentication for Keycloak bearer tokens (DES-AUTH-01 to DES-AUTH-04)."""

import logging
from datetime import UTC, datetime
from typing import Any

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from accounts.claims import extract_roles, identity_from_claims
from accounts.errors import AccountDisabledError, AmbiguousRoleError
from accounts.models import Profile
from accounts.principals import Principal, ServicePrincipal, UserPrincipal
from accounts.profiles import grant_default_role, sync_profile
from accounts.roles import PANEL_ROLES, SERVICE_ROLE, resolve_panel
from accounts.tokens import validate_token
from common import context

logger = logging.getLogger("gradian.accounts")


def build_principal(claims: dict[str, Any]) -> Principal:
    roles = extract_roles(claims)
    if SERVICE_ROLE in roles:
        if any(role in PANEL_ROLES for role in roles):
            logger.warning(
                "role resolution failed",
                extra={"event": "role_failure", "reason": "service_and_panel"},
            )
            raise AmbiguousRoleError(
                details={"roles": sorted(set(roles) & {SERVICE_ROLE, *PANEL_ROLES})}
            )
        return ServicePrincipal(sub=str(claims["sub"]), client_id=str(claims.get("azp", "")))

    try:
        panel = resolve_panel(roles)
    except AmbiguousRoleError as exc:
        logger.warning(
            "role resolution failed", extra={"event": "role_failure", "reason": exc.default_code}
        )
        raise
    identity = identity_from_claims(claims, panel)
    registered_just_now = not any(role in PANEL_ROLES for role in roles) and not (
        Profile.objects.filter(sub=identity.sub).exists()
    )
    iat = claims.get("iat")
    issued_at = datetime.fromtimestamp(iat, UTC) if isinstance(iat, int | float) else None
    profile = sync_profile(identity, issued_at)
    if registered_just_now:
        grant_default_role(str(identity.sub))
    if not profile.is_active:
        logger.info("disabled account refused", extra={"event": "account_disabled"})
        raise AccountDisabledError
    return UserPrincipal(profile=profile, panel=panel)


class KeycloakBearerAuthentication(BaseAuthentication):
    """`Authorization: Bearer <access token>`. No header means anonymous (the permission
    class then answers 401); a bad token is refused here with 401."""

    def authenticate(self, request: Request) -> tuple[Principal, dict[str, Any]] | None:
        parts = get_authorization_header(request).split()
        if not parts or parts[0].lower() != b"bearer":
            return None
        if len(parts) != 2:
            raise AuthenticationFailed(code="invalid_token")
        try:
            token = parts[1].decode("ascii")
        except UnicodeDecodeError:
            raise AuthenticationFailed(code="invalid_token") from None
        claims = validate_token(token)
        principal = build_principal(claims)
        context.user_sub.set(principal.sub)
        return principal, claims

    def authenticate_header(self, request: Request) -> str:
        return 'Bearer realm="gradian"'
