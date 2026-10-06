from django.conf import settings
from rest_framework.throttling import AnonRateThrottle


class PublicRateThrottle(AnonRateThrottle):
    """Rate limit for public endpoints; the rate comes from PUBLIC_RATE_LIMIT (DES-API-07)."""

    scope = "public"

    def get_rate(self) -> str:
        return str(settings.PUBLIC_RATE_LIMIT)
