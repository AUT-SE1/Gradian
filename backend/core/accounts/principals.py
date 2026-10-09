"""The caller as the Core Service sees it: the token's identity plus the cached profile."""

from dataclasses import dataclass

from accounts.models import Profile
from gradian_auth.principals import UserPrincipal


@dataclass(frozen=True)
class CoreUserPrincipal(UserPrincipal):
    profile: Profile
