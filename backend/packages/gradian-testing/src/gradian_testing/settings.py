"""Keycloak settings for tests, so a test does not depend on anyone's `.env`."""

KEYCLOAK_TEST_SETTINGS: dict[str, str] = {
    "KEYCLOAK_PUBLIC_URL": "http://keycloak.test",
    "KEYCLOAK_URL": "http://keycloak.internal.test",
    "KEYCLOAK_REALM": "gradian",
    "KEYCLOAK_CLIENT_ID": "gradian-core",
    "KEYCLOAK_CLIENT_SECRET": "test-client-secret",
}
