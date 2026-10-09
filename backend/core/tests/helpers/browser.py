"""A browser stand-in for integration tests: keeps cookies, follows redirects, fills forms.

Keycloak is reached at its internal address whatever address it advertises (inside Compose the
public one, `localhost:8080`, is not reachable from a container); the cookies it sets are
accepted although they are marked Secure, as a browser does for localhost.
"""

import html
import re
from dataclasses import dataclass, field

import requests

from gradian_keycloak.config import get_config

MAX_REDIRECTS = 20
LOGIN_FORM = "kc-form-login"


@dataclass
class Page:
    url: str
    status: int
    text: str
    hops: list[str] = field(default_factory=list)

    @property
    def is_keycloak_login(self) -> bool:
        return LOGIN_FORM in self.text


class Browser:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.visited: list[Page] = []

    def _reachable(self, url: str) -> str:
        config = get_config()
        return (
            config.internal_url + url.removeprefix(config.public_url)
            if url.startswith(config.public_url)
            else url
        )

    def _relax_cookies(self) -> None:
        for cookie in self.session.cookies:
            cookie.secure = False

    def get(self, url: str, stop_at: str | None = None) -> Page:
        """Open `url` and follow redirects. Stops, without fetching, at an address that starts
        with `stop_at` (the frontend, which these tests do not run)."""
        hops: list[str] = []
        for _ in range(MAX_REDIRECTS):
            if stop_at and url.startswith(stop_at):
                page = Page(url, 302, "", hops)
                self.visited.append(page)
                return page
            reply = self.session.get(self._reachable(url), allow_redirects=False, timeout=15)
            self._relax_cookies()
            hops.append(f"{reply.status_code} {url}")
            if reply.status_code in (301, 302, 303, 307):
                url = requests.compat.urljoin(url, reply.headers["Location"])
                continue
            page = Page(url, reply.status_code, reply.text, hops)
            self.visited.append(page)
            return page
        raise AssertionError(f"too many redirects: {hops}")

    def submit_login(
        self, page: Page, mobile: str, password: str, stop_at: str | None = None
    ) -> Page:
        """Fill in Keycloak's login form and follow where it leads."""
        match = re.search(r'<form[^>]+action="([^"]+)"', page.text)
        assert match, "no login form on the page"
        action = html.unescape(match.group(1))
        reply = self.session.post(
            self._reachable(action),
            data={"username": mobile, "password": password},
            allow_redirects=False,
            timeout=15,
        )
        self._relax_cookies()
        assert reply.status_code == 302, "Keycloak did not accept the sign-in"
        return self.get(requests.compat.urljoin(action, reply.headers["Location"]), stop_at)

    def sign_in_at_keycloak(self, mobile: str, password: str, frontend_url: str) -> None:
        """What the panel does: sign in through the frontend's client, leaving a session behind."""
        config = get_config()
        authorize = (
            f"{config.issuer}/protocol/openid-connect/auth?client_id=gradian-web"
            "&response_type=code&scope=openid&state=s"
            "&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
            f"&code_challenge_method=S256&redirect_uri={frontend_url}/auth/callback"
        )
        page = self.get(authorize, stop_at=frontend_url)
        self.submit_login(page, mobile, password, stop_at=frontend_url)
        self.visited.clear()  # what follows is what the person sees on the group's pages

    def cookie(self, name: str) -> str | None:
        return self.session.cookies.get(name)
