"""Identity fields are read-only in serializers and in the Django admin (DES-ID-01)."""

import uuid

from django.contrib import admin
from django.test import RequestFactory, TestCase

from accounts.admin import ProfileAdmin
from accounts.models import Profile
from accounts.serializers import MeSerializer
from tests.helpers.covers import covers


@covers("SYS-ID-03")
class IdentityIsReadOnlyTests(TestCase):
    def setUp(self) -> None:
        self.profile = Profile.objects.create(
            sub=uuid.uuid4(),
            mobile="09120000001",
            email="a@gradian.test",
            first_name="علی",
            last_name="رضایی",
            role="student",
        )

    def test_serializer_exposes_identity_but_accepts_no_input(self) -> None:
        serializer = MeSerializer(self.profile)
        for field in Profile.IDENTITY_FIELDS:
            self.assertTrue(serializer.fields[field].read_only, field)

    def test_admin_marks_identity_fields_read_only(self) -> None:
        model_admin = ProfileAdmin(Profile, admin.site)
        request = RequestFactory().get("/admin/")
        readonly = set(model_admin.get_readonly_fields(request, self.profile))
        self.assertTrue(set(Profile.IDENTITY_FIELDS) <= readonly)
        self.assertIn("sub", readonly)

    def test_admin_cannot_add_or_delete_profiles(self) -> None:
        model_admin = ProfileAdmin(Profile, admin.site)
        request = RequestFactory().get("/admin/")
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request, self.profile))
