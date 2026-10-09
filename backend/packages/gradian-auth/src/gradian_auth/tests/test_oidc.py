"""Sign-in on the pages of a group service that people reach by redirect (DEC-26)."""

import base64
import hashlib
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import requests
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from gradian_auth import oidc
from gradian_auth.cookies import TOKEN_COOKIE
from gradian_auth.decorators import require_page_user
from gradian_auth.principals import ServicePrincipal
from gradian_testing.cases import AuthTestCase
from gradian_testing.covers import covers
from gradian_testing.tokens import make_token

SETTINGS = {
    "ROOT_URLCONF": "gradian_auth.tests.urls",
    "MIDDLEWARE": ["gradian_auth.middleware.KeycloakAuthMiddleware"],
    "GRADIAN_SERVICE_URL": "http://svc.test",
    "GRADIAN_FRONTEND_URL": "http://frontend.test",
    "GRADIAN_COOKIE_AUTH": True,
    "GRADIAN_PUBLIC_PATHS": ("/health", "/auth"),
}


def outcome(response: Any) -> tuple[int, str]:
    """The status and the error code of a JSON error response."""
    return int(response.status_code), str(response.json()["code"])


class Reply:
    def __init__(self, status: int = 200, body: Any = None) -> None:
        self.status_code = status
        self._body = body

    def json(self) -> Any:
        if self._body is None:
            raise ValueError("no body")
        return self._body


@override_settings(**SETTINGS)
class OidcTestCase(AuthTestCase):
    def start(self, next_path: str | None = None) -> Any:
        suffix = f"?next={next_path}" if next_path else ""
        return self.client.get(f"/auth/login{suffix}")

    def finish(self, login: Any, reply: Reply | Exception, code: str = "the-code") -> Any:
        state = parse_qs(urlsplit(login["Location"]).query)["state"][0]
        outcome: dict[str, Any] = (
            {"side_effect": reply} if isinstance(reply, Exception) else {"return_value": reply}
        )
        with patch("gradian_auth.oidc.requests.post", **outcome) as post:
            response = self.client.get(f"/auth/callback?code={code}&state={state}")
        self.post = post
        return response


@covers("SYS-AUTH-03")
class LoginTests(OidcTestCase):
    def test_login_sends_the_browser_to_keycloak_for_this_services_client(self) -> None:
        response = self.start()
        self.assertEqual(response.status_code, 302)
        target = urlsplit(response["Location"])
        self.assertEqual(
            f"{target.scheme}://{target.netloc}{target.path}",
            "http://keycloak.test/realms/gradian/protocol/openid-connect/auth",
        )
        query = {key: values[0] for key, values in parse_qs(target.query).items()}
        self.assertEqual(query["client_id"], "gradian-core")
        self.assertEqual(query["redirect_uri"], "http://svc.test/auth/callback")
        self.assertEqual(query["response_type"], "code")
        self.assertEqual(query["code_challenge_method"], "S256")
        self.assertTrue(query["state"] and query["code_challenge"])

    def test_every_visit_gets_a_fresh_state_and_challenge(self) -> None:
        first = parse_qs(urlsplit(self.start()["Location"]).query)
        second = parse_qs(urlsplit(self.start()["Location"]).query)
        self.assertNotEqual(first["state"], second["state"])
        self.assertNotEqual(first["code_challenge"], second["code_challenge"])

    def test_the_state_cookie_is_private_and_not_sent_with_other_sites_requests(self) -> None:
        cookie = self.start().cookies[oidc.STATE_COOKIE]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertFalse(cookie["secure"])
        self.assertLessEqual(int(cookie["max-age"]), oidc.STATE_MAX_AGE_SECONDS)

    @override_settings(GRADIAN_SERVICE_URL="https://svc.example")
    def test_cookies_are_secure_when_the_service_is_served_over_https(self) -> None:
        self.assertTrue(self.start().cookies[oidc.STATE_COOKIE]["secure"])

    def test_only_a_path_on_this_service_is_accepted_as_the_place_to_return_to(self) -> None:
        good = ["/", "/classes/3", "/a/b?x=1&y=2", "/page#top"]
        bad = ["//evil.test", "https://evil.test/x", "javascript:alert(1)", "\\evil", "", "x"]
        for value in good:
            with self.subTest(value=value):
                self.assertEqual(oidc.safe_next(value), value)
        for value in bad:
            with self.subTest(value=value):
                self.assertEqual(oidc.safe_next(value), "/")
        self.assertEqual(oidc.safe_next(None), "/")
        self.assertEqual(oidc.safe_next("/a\r\nSet-Cookie: x=1"), "/")

    def test_pkce_pair_matches(self) -> None:
        verifier, challenge = oidc.pkce_pair()
        digest = hashlib.sha256(verifier.encode()).digest()
        self.assertEqual(challenge, base64.urlsafe_b64encode(digest).rstrip(b"=").decode())


@covers("SYS-AUTH-03", "SYS-INT-02")
class CallbackTests(OidcTestCase):
    def good_reply(self, **token: Any) -> Reply:
        return Reply(200, {"access_token": make_token(**token)})

    def test_a_valid_sign_in_sets_the_token_cookie_and_returns_to_the_page(self) -> None:
        login = self.start("/classes/3")
        response = self.finish(login, self.good_reply())
        self.assertEqual((response.status_code, response["Location"]), (302, "/classes/3"))
        cookie = response.cookies[TOKEN_COOKIE]
        self.assertTrue(cookie.value and cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertTrue(0 < int(cookie["max-age"]) <= 600)

    def test_the_code_is_traded_with_the_services_own_credentials_and_the_verifier(self) -> None:
        login = self.start()
        challenge = parse_qs(urlsplit(login["Location"]).query)["code_challenge"][0]
        self.finish(login, self.good_reply(), code="abc")
        data = self.post.call_args.kwargs["data"]
        self.assertEqual(data["grant_type"], "authorization_code")
        self.assertEqual(data["code"], "abc")
        self.assertEqual(data["redirect_uri"], "http://svc.test/auth/callback")
        self.assertEqual(
            (data["client_id"], data["client_secret"]), ("gradian-core", "test-client-secret")
        )
        digest = hashlib.sha256(data["code_verifier"].encode()).digest()
        self.assertEqual(base64.urlsafe_b64encode(digest).rstrip(b"=").decode(), challenge)
        self.assertEqual(
            self.post.call_args.args[0],
            "http://keycloak.internal.test/realms/gradian/protocol/openid-connect/token",
        )

    def test_the_cookie_signs_the_person_in_on_the_next_request(self) -> None:
        self.finish(self.start(), self.good_reply(roles=("student",)))
        page = self.client.get("/page")
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.json()["panel"], "student")

    def test_a_visit_that_did_not_start_here_is_refused(self) -> None:
        response = self.client.get("/auth/callback?code=x&state=y")
        self.assertEqual((response.status_code, response.json()["code"]), (400, "invalid_login"))

    def test_a_wrong_or_missing_state_code_or_an_error_from_keycloak_is_refused(self) -> None:
        login = self.start()
        cases = {
            "wrong state": "/auth/callback?code=x&state=not-the-state",
            "no state": "/auth/callback?code=x",
            "no code": "/auth/callback?state=anything",
            "keycloak error": "/auth/callback?error=access_denied&state=anything",
        }
        for name, path in cases.items():
            with self.subTest(name), patch("gradian_auth.oidc.requests.post") as post:
                response = self.client.get(path)
                self.assertEqual(response.status_code, 400, login["Location"])
                self.assertEqual(response.json()["code"], "invalid_login")
                post.assert_not_called()

    def test_a_tampered_state_cookie_is_refused(self) -> None:
        self.start()
        self.client.cookies[oidc.STATE_COOKIE] = "forged:value"
        response = self.client.get("/auth/callback?code=x&state=y")
        self.assertEqual(response.status_code, 400)

    def test_keycloak_refusing_the_code_is_a_failed_login(self) -> None:
        response = self.finish(self.start(), Reply(400, {"error": "invalid_grant"}))
        self.assertEqual((response.status_code, response.json()["code"]), (400, "invalid_login"))
        self.assertNotIn(TOKEN_COOKIE, response.cookies)

    def test_keycloak_being_down_is_a_bad_gateway(self) -> None:
        for outcome in (Reply(503, {}), requests.ConnectionError("down")):
            with self.subTest(outcome=repr(outcome)):
                response = self.finish(self.start(), outcome)
                self.assertEqual(response.status_code, 502)

    def test_a_reply_without_a_token_is_a_failed_login(self) -> None:
        bodies: list[Any] = [{}, None]
        for body in bodies:
            with self.subTest(body=body):
                response = self.finish(self.start(), Reply(200, body))
                self.assertEqual(response.status_code, 400)

    def test_a_token_meant_for_another_service_is_refused_and_no_cookie_is_set(self) -> None:
        response = self.finish(self.start(), self.good_reply(audience="group-9"))
        self.assertEqual((response.status_code, response.json()["code"]), (401, "invalid_token"))
        self.assertNotIn(TOKEN_COOKIE, response.cookies)

    def test_an_incomplete_identity_is_refused_here_not_later(self) -> None:
        response = self.finish(self.start(), self.good_reply(omit=["email"]))
        self.assertEqual(
            (response.status_code, response.json()["code"]), (403, "incomplete_identity")
        )

    def test_without_a_client_secret_the_service_says_what_is_missing(self) -> None:
        login = self.start()
        with (
            override_settings(KEYCLOAK_CLIENT_SECRET=""),
            self.assertRaisesMessage(ImproperlyConfigured, "KEYCLOAK_CLIENT_SECRET"),
        ):
            self.finish(login, self.good_reply())

    def test_the_state_cannot_be_used_twice(self) -> None:
        login = self.start()
        self.finish(login, self.good_reply())
        again = self.client.get(
            f"/auth/callback?code=x&state={parse_qs(urlsplit(login['Location']).query)['state'][0]}"
        )
        self.assertEqual(again.status_code, 400)


@covers("SYS-AUTH-03", "SYS-ACC-02")
class PageAccessTests(OidcTestCase):
    def with_cookie(self, **token: Any) -> None:
        self.client.cookies[TOKEN_COOKIE] = make_token(**token)

    def test_a_visitor_who_is_not_signed_in_is_sent_to_sign_in_and_back(self) -> None:
        response = self.client.get("/page?tab=2")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/auth/login?next=%2Fpage%3Ftab%3D2")

    def test_a_signed_in_student_sees_the_page(self) -> None:
        self.with_cookie(roles=("student",))
        self.assertEqual(self.client.get("/page").status_code, 200)

    def test_another_role_is_refused_not_sent_around_in_circles(self) -> None:
        self.with_cookie(roles=("professor",))
        response = self.client.get("/page")
        self.assertEqual(
            (response.status_code, response.json()["code"]), (403, "permission_denied")
        )

    def test_a_stale_or_invalid_cookie_means_not_signed_in(self) -> None:
        for token in (make_token(issued_at=1_700_000_000), "garbage", make_token(audience="x")):
            with self.subTest(token=token[:12]):
                self.client.cookies[TOKEN_COOKIE] = token
                self.assertEqual(self.client.get("/page").status_code, 302)

    def test_a_request_that_changes_things_gets_a_401_not_a_redirect(self) -> None:
        response = self.client.post("/page")
        self.assertEqual(
            (response.status_code, response.json()["code"]), (401, "not_authenticated")
        )

    def test_an_authorization_header_still_works_and_wins_over_the_cookie(self) -> None:
        self.with_cookie(roles=("professor",))
        response = self.client.get("/page", **self.bearer(make_token(roles=("student",))))
        self.assertEqual(response.status_code, 200)

    def test_a_bad_bearer_header_is_not_rescued_by_a_good_cookie(self) -> None:
        self.with_cookie(roles=("student",))
        response = self.client.get("/page", HTTP_AUTHORIZATION="Bearer garbage")
        self.assertEqual(response.status_code, 401)

    @override_settings(GRADIAN_COOKIE_AUTH=False)
    def test_the_cookie_is_ignored_unless_the_service_turns_it_on(self) -> None:
        self.with_cookie(roles=("student",))
        self.assertEqual(self.client.get("/page").status_code, 302)

    def test_the_decorator_needs_its_parentheses(self) -> None:
        with self.assertRaises(TypeError):
            require_page_user(lambda request: None)  # type: ignore[arg-type]  # the mistake


@covers("SYS-AUTH-06", "SYS-AUTH-03")
class LogoutAndPanelTests(OidcTestCase):
    def test_logout_ends_the_session_here_and_at_keycloak_and_returns_to_the_landing_page(
        self,
    ) -> None:
        self.client.cookies[TOKEN_COOKIE] = make_token()
        response = self.client.get("/auth/logout")
        target = urlsplit(response["Location"])
        self.assertEqual(target.path, "/realms/gradian/protocol/openid-connect/logout")
        query = parse_qs(target.query)
        self.assertEqual(query["client_id"], ["gradian-core"])
        self.assertEqual(query["post_logout_redirect_uri"], ["http://frontend.test/"])
        self.assertEqual(response.cookies[TOKEN_COOKIE]["max-age"], 0)

    def test_the_link_back_goes_to_the_persons_own_panel(self) -> None:
        for role in ("student", "professor", "admin"):
            with self.subTest(role=role):
                self.client.cookies[TOKEN_COOKIE] = make_token(roles=(role,))
                request = self.client.get("/open").wsgi_request
                self.assertEqual(
                    oidc.panel_url(request.principal),
                    f"http://frontend.test/{role}",
                )

    def test_anyone_else_goes_to_the_start_of_the_panel(self) -> None:
        self.assertEqual(oidc.panel_url(None), "http://frontend.test/")
        self.assertEqual(oidc.panel_url(ServicePrincipal("s", "c")), "http://frontend.test/")

    def test_a_missing_service_url_is_named(self) -> None:
        with (
            override_settings(GRADIAN_SERVICE_URL=""),
            self.assertRaisesMessage(ImproperlyConfigured, "GRADIAN_SERVICE_URL"),
        ):
            oidc.redirect_uri()

    def test_a_missing_frontend_url_is_named(self) -> None:
        with (
            override_settings(GRADIAN_FRONTEND_URL=""),
            self.assertRaisesMessage(ImproperlyConfigured, "GRADIAN_FRONTEND_URL"),
        ):
            oidc.panel_url(None)


@covers("SYS-AUTH-03")
class StateCookieTests(OidcTestCase):
    def test_the_state_cookie_holds_nothing_a_client_could_mangle(self) -> None:
        value = self.start("/a?b=1&c=2").cookies[oidc.STATE_COOKIE].value
        self.assertRegex(value, r"^[A-Za-z0-9_=\-:]+$")

    def test_a_state_cookie_that_is_not_what_we_wrote_is_refused(self) -> None:
        from django.core import signing

        self.start()
        forged = signing.get_cookie_signer().sign("not-base64-json")
        self.client.cookies[oidc.STATE_COOKIE] = forged
        self.assertEqual(self.client.get("/auth/callback?code=x&state=y").status_code, 400)
        array = signing.get_cookie_signer().sign(oidc._pack({}).replace("e30=", "W10="))
        self.client.cookies[oidc.STATE_COOKIE] = array
        self.assertEqual(self.client.get("/auth/callback?code=x&state=y").status_code, 400)
