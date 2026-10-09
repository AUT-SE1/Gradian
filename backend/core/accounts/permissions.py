"""Permission classes (DES-AUTH-03). A missing token is answered 401 by DRF, a wrong role 403."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from accounts.models import Role
from accounts.principals import ServicePrincipal, UserPrincipal


class IsPanelUser(BasePermission):
    """Any signed-in person with a panel role."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return isinstance(request.user, UserPrincipal)


class HasPanelRole(BasePermission):
    """Subclass and set `allowed_roles` to restrict an endpoint to given panel roles."""

    allowed_roles: tuple[str, ...] = ()

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        return isinstance(user, UserPrincipal) and user.panel in self.allowed_roles


class IsPlatformService(BasePermission):
    """A machine client holding the `service` role (client-credentials token)."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return isinstance(request.user, ServicePrincipal)


class IsAdminPanelUser(HasPanelRole):
    """A signed-in person whose panel is the admin panel."""

    allowed_roles = (Role.ADMIN,)
