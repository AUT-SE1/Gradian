import io
import urllib.error
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.test import SimpleTestCase

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class FakeJWKS:
    def get_signing_key_from_jwt(self, token):
        return type("K", (), {"key": KEY.public_key()})


def token(phone="+989212157879", roles=("candidate",), iss=None):
    claims = {"preferred_username": phone, "realm_access": {"roles": list(roles)},
              "iss": iss or settings.KEYCLOAK_ISSUER}
    return {"HTTP_AUTHORIZATION": "Bearer " + jwt.encode(claims, KEY, algorithm="RS256")}


@patch("core.auth._jwks", lambda: FakeJWKS())
class RoutingTests(SimpleTestCase):
    def test_redirect_per_role(self):
        for role, home in [("admin", "/api/admin-panel/"), ("candidate", "/api/candidate/"),
                           ("advisor", "/api/advisor/"), ("instructor", "/api/instructor/")]:
            r = self.client.get("/api/auth/me/", **token(roles=[role]))
            self.assertEqual(r.json()["redirect"], home)
        # admin wins over candidate
        r = self.client.get("/api/auth/me/", **token(roles=["candidate", "admin"]))
        self.assertEqual(r.json()["role"], "admin")

    def test_rejects_bad_auth(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)
        self.assertEqual(self.client.get("/api/auth/me/", **token(phone="ali")).status_code, 401)
        self.assertEqual(self.client.get("/api/auth/me/", **token(roles=[])).status_code, 401)
        self.assertEqual(self.client.get("/api/auth/me/", **token(iss="http://evil")).status_code, 401)

    def test_role_gates(self):
        self.assertEqual(self.client.get("/api/admin-panel/shop-items/", **token()).status_code, 403)
        self.assertEqual(self.client.get("/api/admin-panel/shop-items/", **token(roles=["admin"])).status_code, 200)
        self.assertEqual(self.client.post("/api/advisor/profile/", **token(roles=["advisor"])).status_code, 405)

    def test_candidate_landing_has_ten_team_ports(self):
        services = self.client.get("/api/candidate/", **token()).json()["services"]
        self.assertEqual([s["port"] for s in services], list(range(8001, 8011)))
        self.assertEqual(services[2]["url"], "/api/teams/3/")

    def test_gateway_forwards_to_team_with_user_headers(self):
        sent = {}

        def fake_urlopen(req, timeout):
            sent["url"], sent["headers"] = req.full_url, dict(req.header_items())
            r = io.BytesIO(b'{"ok": 1}')
            r.status, r.headers = 200, {"Content-Type": "application/json"}
            return r

        with patch("core.views.urllib.request.urlopen", fake_urlopen):
            r = self.client.get("/api/teams/3/books/?page=2", HTTP_X_USER_ROLE="admin", **token())
        self.assertEqual(r.json(), {"ok": 1})
        self.assertEqual(sent["url"], "http://localhost:8003/books/?page=2")
        self.assertEqual(sent["headers"]["X-user-phone"], "+989212157879")
        self.assertEqual(sent["headers"]["X-user-role"], "candidate")  # client's forged header ignored

    def test_gateway_errors(self):
        self.assertEqual(self.client.get("/api/teams/3/").status_code, 401)
        self.assertEqual(self.client.get("/api/teams/11/", **token()).status_code, 404)
        with patch("core.views.urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
            self.assertEqual(self.client.get("/api/teams/3/", **token()).status_code, 502)
