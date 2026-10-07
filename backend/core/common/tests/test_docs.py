from django.conf import settings
from django.test import SimpleTestCase


class ApiDocsTests(SimpleTestCase):
    def test_the_docs_page_and_the_schema_are_public(self) -> None:
        page = self.client.get("/api/docs/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("text/html", page["Content-Type"])
        self.assertEqual(self.client.get("/api/schema/?format=json").status_code, 200)

    def test_the_docs_sign_in_through_the_address_browsers_use(self) -> None:
        schemes = self.client.get("/api/schema/?format=json").json()["components"][
            "securitySchemes"
        ]
        token_url = schemes["keycloakPassword"]["flows"]["password"]["tokenUrl"]
        self.assertTrue(token_url.startswith(settings.KEYCLOAK_PUBLIC_URL))
        self.assertNotIn(settings.KEYCLOAK_URL, token_url)
        self.assertEqual(schemes["keycloakBearer"]["scheme"], "bearer")
