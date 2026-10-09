from django.test import SimpleTestCase

from gradian_auth.claims import identity_from_claims, is_valid_name
from gradian_auth.errors import IncompleteIdentityError
from gradian_testing.covers import covers

SUB = "00000000-0000-4000-8000-000000000001"


def claims(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "sub": SUB,
        "preferred_username": "+989120000001",
        "email": "Student.1.1@Gradian.test",
        "given_name": "علی",
        "family_name": "رضایی",
    }
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not None}


@covers("SYS-ID-01", "SYS-ID-02")
class IdentityFromClaimsTests(SimpleTestCase):
    def test_complete_claims_give_a_normalized_identity(self) -> None:
        identity = identity_from_claims(claims(), "student")
        self.assertEqual(identity.mobile, "09120000001")
        self.assertEqual(identity.email, "student.1.1@gradian.test")
        self.assertEqual((identity.first_name, identity.last_name), ("علی", "رضایی"))
        self.assertEqual(identity.consultant_type, "")

    def test_each_missing_claim_is_refused_and_named(self) -> None:
        for claim, field in [
            ("preferred_username", "preferred_username"),
            ("email", "email"),
            ("given_name", "given_name"),
            ("family_name", "family_name"),
        ]:
            with self.subTest(claim=claim):
                with self.assertRaises(IncompleteIdentityError) as ctx:
                    identity_from_claims(claims(**{claim: None}), "student")
                self.assertEqual(ctx.exception.details, {"fields": [field]})

    def test_consultant_needs_a_known_type(self) -> None:
        with self.assertRaises(IncompleteIdentityError):
            identity_from_claims(claims(), "consultant")
        identity = identity_from_claims(claims(consultant_type="top_ranker"), "consultant")
        self.assertEqual(identity.consultant_type, "top_ranker")
        with self.assertRaises(IncompleteIdentityError):
            identity_from_claims(claims(consultant_type="wizard"), "consultant")

    def test_consultant_type_is_ignored_for_other_roles(self) -> None:
        identity = identity_from_claims(claims(consultant_type="top_ranker"), "student")
        self.assertEqual(identity.consultant_type, "")


@covers("SYS-ID-01")
class NameValidationTests(SimpleTestCase):
    def test_valid_names(self) -> None:
        for name in ["علی", "سارا", "می\u200cخواهم", "Ali Reza", "ا" * 100]:
            with self.subTest(name=name):
                self.assertTrue(is_valid_name(name))

    def test_invalid_names(self) -> None:
        for name in ["", "ا" * 101, "علی1", "a@b", "<script>"]:
            with self.subTest(name=name):
                self.assertFalse(is_valid_name(name))
