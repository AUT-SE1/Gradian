import threading
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import check_service
from covers import covers

AUTH = "http://kc.test/realms/gradian/protocol/openid-connect/auth"
PEOPLE = {"person:student", "person:professor", "person:admin", "person:consultant"}


class Tokens:
    def person(self, role: str) -> str:
        return f"person:{role}"

    def other_group_service(self, group: int) -> str:
        return "foreign"


def service(**flaws: bool) -> type[BaseHTTPRequestHandler]:
    """A service that is correct unless a flaw is switched on."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def reply(self, status: int, location: str | None = None) -> None:
            self.send_response(status)
            if location:
                self.send_header("Location", location)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self) -> None:
            token = (self.headers.get("Authorization") or "").removeprefix("Bearer ")
            if self.path == "/health":
                self.reply(404 if flaws.get("no_health") else 200)
            elif self.path == "/app":
                client = "gradian-web" if flaws.get("wrong_client") else "group-3"
                if flaws.get("page_open"):
                    self.reply(200)
                elif flaws.get("no_keycloak"):
                    self.reply(302, "/somewhere-else")
                else:
                    self.reply(302, f"{AUTH}?client_id={client}&state=s")
            elif flaws.get("open"):
                self.reply(200)
            elif self.path == "/":
                valid = token in PEOPLE or (token == "foreign" and flaws.get("any_audience"))
                valid = valid or (token == "not.a.token" and flaws.get("accepts_garbage"))
                self.reply(200 if valid else 401)
            elif self.path == "/staff":
                if token not in PEOPLE:
                    self.reply(401)
                elif token in {"person:professor", "person:admin"} or flaws.get("any_role"):
                    self.reply(200)
                else:
                    self.reply(403)
            else:
                self.reply(404)

    return Handler


@contextmanager
def running(handler: type[BaseHTTPRequestHandler]) -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def check(handler: type[BaseHTTPRequestHandler], **options: object) -> list[check_service.Result]:
    with running(handler) as url:
        return check_service.run_checks(
            url,
            Tokens(),
            group=3,
            restricted_path="/staff",
            allowed_roles=("professor", "admin"),
            page_path="/app",
            auth_endpoint=AUTH,
            **options,  # type: ignore[arg-type]
        )


def failures(results: list[check_service.Result]) -> list[str]:
    return [result.name for result in results if result.failed]


@covers("SYS-INT-04")
class CheckServiceTests(unittest.TestCase):
    def test_a_service_that_follows_the_rules_passes_every_check(self) -> None:
        results = check(service())
        self.assertEqual(failures(results), [])
        self.assertEqual({result.status for result in results}, {"PASS"})
        self.assertEqual(len(results), 8)

    def test_each_rule_that_is_broken_is_reported(self) -> None:
        flaws: dict[str, str] = {
            "open": "without a token is refused",
            "accepts_garbage": "invalid token is refused",
            "any_audience": "meant for another service is refused",
            "any_role": "refuses a student with 403",
            "no_health": "health:",
            "page_open": "sent to Keycloak",
            "wrong_client": "sent to Keycloak",
            "no_keycloak": "sent to Keycloak",
        }
        for flaw, expected in flaws.items():
            with self.subTest(flaw=flaw):
                broken = failures(check(service(**{flaw: True})))
                self.assertTrue(broken, f"{flaw} was not detected")
                self.assertTrue(any(expected in name for name in broken), broken)

    def test_a_check_that_cannot_run_is_skipped_never_passed(self) -> None:
        with running(service()) as url:
            results = check_service.run_checks(url, Tokens())
        skipped = [result.name for result in results if result.status == "SKIP"]
        self.assertEqual(len(skipped), 3)
        self.assertEqual(failures(results), [])

    def test_a_service_that_is_not_running_is_a_setup_error(self) -> None:
        with self.assertRaises(check_service.SetupError):
            check_service.run_checks("http://127.0.0.1:9", Tokens())

    def test_the_http_helper_gives_the_status_of_an_error_response(self) -> None:
        with running(service()) as url:
            self.assertEqual(check_service.http_get(url + "/missing"), 404)
