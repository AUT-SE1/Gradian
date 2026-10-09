"""Needs the running stack: `make itest` starts it and runs these.

The reference group service is the skeleton in `teams/team1`, started for the duration of the
class and given its own client, `group-1`.
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, ClassVar

import requests
from django.conf import settings

from accounts.models import Profile
from gradian import env
from gradian_testing.covers import covers
from tests.helpers.base import IntegrationTestCase
from tests.helpers.browser import Browser
from tests.helpers.keycloak import password_token, service_token
from tests.helpers.repo import REPO_ROOT, group_service_secret

GROUP = 1
CHECKER = REPO_ROOT / "scripts" / "check_service.py"
CHECK_ARGS = [
    "--group",
    str(GROUP),
    "--restricted-path",
    "/staff",
    "--allowed-roles",
    "professor,admin",
    "--page-path",
    "/app",
]


PORT = 8000 + GROUP


def port_is_free(port: int) -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


def status_of(url: str, token: str | None = None) -> int:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.get(url, headers=headers, timeout=10).status_code


class AcceptsEverything(BaseHTTPRequestHandler):
    """A service that checks nothing: the deliberately broken one."""

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()


class ReferenceServiceTests(IntegrationTestCase):
    fixtures = ["profiles"]  # noqa: RUF012
    process: ClassVar[subprocess.Popen[bytes]]
    url: ClassVar[str]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        port = PORT
        assert port_is_free(port), (
            f"port {port} is in use: Keycloak only accepts group {GROUP} there"
        )
        cls.url = f"http://localhost:{port}"
        service_env = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_SECRET_KEY": "reference-service-for-tests-only",
            "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost",
            "KEYCLOAK_PUBLIC_URL": settings.KEYCLOAK_PUBLIC_URL,
            "KEYCLOAK_URL": settings.KEYCLOAK_URL,
            "KEYCLOAK_CLIENT_ID": f"group-{GROUP}",
            "KEYCLOAK_CLIENT_SECRET": group_service_secret(
                GROUP, env.require("SEED_DEFAULT_PASSWORD")
            ),
            "GRADIAN_SERVICE_URL": cls.url,
            "GRADIAN_FRONTEND_URL": settings.FRONTEND_URL,
        }
        workdir = Path(tempfile.mkdtemp(prefix="reference-service-"))
        cls.addClassCleanup(shutil.rmtree, workdir, ignore_errors=True)
        source = REPO_ROOT / "teams" / f"team{GROUP}"
        # A copy: the repository is mounted read-only, and runserver opens its SQLite file.
        shutil.copytree(
            source,
            workdir / source.name,
            ignore=shutil.ignore_patterns(".env", "*.sqlite3", "__pycache__"),
        )
        cls.process = subprocess.Popen(  # noqa: S603  # fixed arguments
            [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
            cwd=workdir / source.name,
            env=service_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls.addClassCleanup(cls.stop_service)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                if status_of(f"{cls.url}/health") == 200:
                    return
            except OSError:
                pass
            time.sleep(0.3)
        raise AssertionError("the reference service did not start")

    @classmethod
    def stop_service(cls) -> None:
        cls.process.terminate()
        cls.process.wait(timeout=10)

    def person(self, role: str, consultant_type: str = "") -> str:
        profile = (
            Profile.objects.filter(role=role, consultant_type=consultant_type)
            .order_by("mobile")
            .first()
        )
        assert profile is not None
        return password_token(profile.mobile, env.require("SEED_DEFAULT_PASSWORD"))

    def check(self, url: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603  # fixed arguments
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "check_service.py"),
                "--url",
                url,
                *CHECK_ARGS,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
            env=os.environ,
        )

    @covers("SYS-AUTH-03")
    def test_one_sign_in_is_recognised_by_core_and_by_the_group_service(self) -> None:
        token = self.person("student")
        core = self.client.get("/api/v1/me", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(core.status_code, 200, core.content)
        self.assertEqual(status_of(f"{self.url}/", token), 200)

    @covers("SYS-INT-02", "SYS-AUTH-03")
    def test_the_group_service_knows_who_called_and_what_their_role_is(self) -> None:
        token = self.person("professor")
        response = requests.get(
            f"{self.url}/", headers={"Authorization": f"Bearer {token}"}, timeout=10
        )
        body = response.text
        self.assertIn('"role": "professor"', body)
        self.assertIn(f'"team": {GROUP}', body)

    @covers("SYS-INT-02")
    def test_the_group_service_refuses_what_it_should(self) -> None:
        password = env.require("SEED_DEFAULT_PASSWORD")
        another_service = service_token("group-2", group_service_secret(2, password))
        cases: dict[str, tuple[str, str | None, int]] = {
            "no token": ("/", None, 401),
            "garbage": ("/", "not.a.token", 401),
            "a token meant for another service": ("/", another_service, 401),
            "a student on a staff-only endpoint": ("/staff", self.person("student"), 403),
            "a professor on a staff-only endpoint": ("/staff", self.person("professor"), 200),
        }
        for name, (path, token, expected) in cases.items():
            with self.subTest(name):
                self.assertEqual(status_of(self.url + path, token), expected)

    @covers("SYS-INT-04")
    def test_the_check_passes_the_reference_service(self) -> None:
        result = self.check(self.url)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("FAIL", result.stdout)
        self.assertIn("follows the integration rules", result.stdout)

    @covers("SYS-INT-04")
    def test_the_check_fails_a_service_that_checks_nothing(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), AcceptsEverything)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = self.check(f"http://127.0.0.1:{server.server_address[1]}")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL", result.stdout)

    def seeded(self, role: str) -> Profile:
        profile = Profile.objects.filter(role=role).order_by("mobile").first()
        assert profile is not None
        return profile

    @covers("SYS-AUTH-03", "SYS-INT-05")
    def test_a_person_signed_in_at_the_panel_reaches_the_group_page_without_a_second_login(
        self,
    ) -> None:
        student = self.seeded("student")
        browser = Browser()
        browser.sign_in_at_keycloak(
            student.mobile, env.require("SEED_DEFAULT_PASSWORD"), settings.FRONTEND_URL
        )
        page = browser.get(f"{self.url}/app")
        self.assertEqual(page.status, 200, page.hops)
        self.assertIn(student.first_name, page.text)
        self.assertIn(f"{settings.FRONTEND_URL}/student", page.text)
        self.assertFalse(
            any(seen.is_keycloak_login for seen in browser.visited), "asked to sign in"
        )
        self.assertTrue(browser.cookie("gradian_token"))
        again = browser.get(f"{self.url}/app")
        self.assertEqual((again.status, len(again.hops)), (200, 1))

    @covers("SYS-AUTH-03", "SYS-INT-05")
    def test_without_a_session_the_person_signs_in_once_and_lands_on_the_group_page(self) -> None:
        professor = self.seeded("professor")
        browser = Browser()
        login = browser.get(f"{self.url}/app")
        self.assertTrue(login.is_keycloak_login, login.hops)
        page = browser.submit_login(login, professor.mobile, env.require("SEED_DEFAULT_PASSWORD"))
        self.assertEqual(page.status, 200, page.hops)
        self.assertIn(f"{settings.FRONTEND_URL}/professor", page.text)
        self.assertIn("professor", page.text)

    @covers("SYS-AUTH-03")
    def test_a_wrong_password_never_reaches_the_group_page(self) -> None:
        browser = Browser()
        login = browser.get(f"{self.url}/app")
        with self.assertRaises(AssertionError):
            browser.submit_login(login, self.seeded("student").mobile, "not-the-password")
        self.assertIsNone(browser.cookie("gradian_token"))

    @covers("SYS-AUTH-06")
    def test_logging_out_of_the_group_page_clears_its_cookie_and_leaves_through_keycloak(
        self,
    ) -> None:
        student = self.seeded("student")
        browser = Browser()
        browser.sign_in_at_keycloak(
            student.mobile, env.require("SEED_DEFAULT_PASSWORD"), settings.FRONTEND_URL
        )
        browser.get(f"{self.url}/app")
        reply = browser.session.get(f"{self.url}/auth/logout", allow_redirects=False, timeout=15)
        self.assertEqual(reply.status_code, 302)
        self.assertIn("/protocol/openid-connect/logout", reply.headers["Location"])
        self.assertIn(f"client_id=group-{GROUP}", reply.headers["Location"])
        self.assertIsNone(reply.cookies.get("gradian_token") or None)
