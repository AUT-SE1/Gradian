"""Test base class for Django REST Framework services. Needs the `drf` extra."""

from django.test import override_settings
from rest_framework.test import APITestCase

from gradian_testing.cases import FakeKeycloakMixin
from gradian_testing.settings import KEYCLOAK_TEST_SETTINGS


@override_settings(**KEYCLOAK_TEST_SETTINGS)
class AuthAPITestCase(FakeKeycloakMixin, APITestCase):
    """`self.client` is DRF's `APIClient`. Needs the database of the service under test."""
