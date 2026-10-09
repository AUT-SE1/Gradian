from django.test import SimpleTestCase

from accounts.models import ConsultantType, Role
from gradian_auth.roles import CONSULTANT_TYPES, PANEL_ROLES


class RoleDefinitionTests(SimpleTestCase):
    def test_the_model_choices_match_the_roles_the_packages_know(self) -> None:
        """The packages and the Profile model define the same vocabulary twice."""
        self.assertEqual(set(Role.values), set(PANEL_ROLES))
        self.assertEqual(set(ConsultantType.values), set(CONSULTANT_TYPES))
