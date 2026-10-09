"""Permission classes of the Core Service (DES-AUTH-03). The generic ones are in
`gradian_auth.drf`; a missing token is answered 401 by DRF, a wrong role 403."""

from accounts.models import Role
from gradian_auth.drf import HasPanelRole


class IsAdminPanelUser(HasPanelRole):
    """A signed-in person whose panel is the admin panel."""

    allowed_roles = (Role.ADMIN,)


class IsStudentPanelUser(HasPanelRole):
    """A signed-in person whose panel is the student panel."""

    allowed_roles = (Role.STUDENT,)
