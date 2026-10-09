from collections.abc import Mapping
from typing import Any

from django.test import override_settings

from gradian_auth import context
from gradian_auth.authenticate import authenticate_token, parse_bearer, principal_builder
from gradian_auth.errors import InvalidTokenError
from gradian_auth.principals import Principal, ServicePrincipal, UserPrincipal, build_principal
from gradian_testing.cases import AuthTestCase
from gradian_testing.tokens import make_token


def always_a_service(claims: Mapping[str, Any]) -> Principal:
    return ServicePrincipal(sub="custom", client_id="custom-client")


class ParseBearerTests(AuthTestCase):
    def test_a_bearer_header_gives_its_token(self) -> None:
        self.assertEqual(parse_bearer(b"Bearer abc.def.ghi"), "abc.def.ghi")
        self.assertEqual(parse_bearer(b"bearer abc"), "abc")

    def test_no_header_or_another_scheme_is_anonymous(self) -> None:
        self.assertIsNone(parse_bearer(b""))
        self.assertIsNone(parse_bearer(b"Basic dXNlcjpwYXNz"))

    def test_a_bearer_header_without_exactly_one_token_is_refused(self) -> None:
        for header in (b"Bearer", b"Bearer a b", b"Bearer \xe9"):
            with self.subTest(header=header), self.assertRaises(InvalidTokenError):
                parse_bearer(header)


class AuthenticateTokenTests(AuthTestCase):
    def test_the_default_builder_gives_the_principal_and_the_claims(self) -> None:
        principal, claims = authenticate_token(make_token(roles=("admin",)))
        assert isinstance(principal, UserPrincipal)
        self.assertEqual(principal.panel, "admin")
        self.assertEqual(claims["sub"], principal.sub)

    def test_the_caller_is_noted_for_the_log_lines(self) -> None:
        reset = context.user_sub.set("-")
        self.addCleanup(context.user_sub.reset, reset)
        principal, _ = authenticate_token(make_token())
        self.assertEqual(context.user_sub.get(), principal.sub)

    def test_a_service_can_swap_the_builder(self) -> None:
        with override_settings(GRADIAN_PRINCIPAL_BUILDER=f"{__name__}.always_a_service"):
            principal, _ = authenticate_token(make_token())
        self.assertEqual(principal, ServicePrincipal(sub="custom", client_id="custom-client"))

    def test_the_default_builder_is_the_packages_own(self) -> None:
        self.assertIs(principal_builder(), build_principal)
