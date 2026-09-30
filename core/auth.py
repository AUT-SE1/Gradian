"""Keycloak bearer-token auth. Username (preferred_username) is the phone number."""
import re
from functools import lru_cache, wraps

import jwt
from django.conf import settings
from django.http import JsonResponse

PHONE_RE = re.compile(r"^\+\d{10,15}$")

# Keycloak realm roles, highest priority first (a user with several gets the first match).
ROLES = ["admin", "instructor", "advisor", "candidate"]


@lru_cache
def _jwks():
    return jwt.PyJWKClient(settings.KEYCLOAK_JWKS_URL)


def authenticate(request):
    """Return (phone, role) or raise ValueError with the reason."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise ValueError("missing bearer token")
    token = header[7:]
    try:
        key = _jwks().get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token, key, algorithms=["RS256"], issuer=settings.KEYCLOAK_ISSUER,
            options={"verify_aud": False},  # ponytail: no audience check; add `audience=` once a backend client exists in Keycloak
        )
    except jwt.PyJWTError as e:
        raise ValueError(f"invalid token: {e}")

    phone = claims.get("preferred_username", "")
    if not PHONE_RE.match(phone):
        raise ValueError("username is not a phone number")
    user_roles = claims.get("realm_access", {}).get("roles", [])
    role = next((r for r in ROLES if r in user_roles), None)
    if role is None:
        raise ValueError("user has no platform role")
    return phone, role


def role_required(*allowed):
    """Decorator: authenticate, then allow only the given roles. Sets request.phone / request.role."""
    def deco(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            try:
                request.phone, request.role = authenticate(request)
            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=401)
            if allowed and request.role not in allowed:
                return JsonResponse({"error": "forbidden for role " + request.role}, status=403)
            return view(request, *args, **kwargs)
        return wrapper
    return deco
