"""Who is calling: a signed-in person, or a platform service with its own credential."""

from dataclasses import dataclass

from accounts.models import Profile


@dataclass(frozen=True)
class UserPrincipal:
    profile: Profile
    panel: str
    is_authenticated: bool = True

    @property
    def sub(self) -> str:
        return str(self.profile.sub)


@dataclass(frozen=True)
class ServicePrincipal:
    sub: str
    client_id: str
    is_authenticated: bool = True


Principal = UserPrincipal | ServicePrincipal
