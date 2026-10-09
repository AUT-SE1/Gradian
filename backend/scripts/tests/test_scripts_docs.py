import re
import unittest
from pathlib import Path

import yaml
from covers import covers

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)\)")
GUIDE = ROOT / "docs" / "06-integration-guide.md"


def documents() -> list[Path]:
    found = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "dev-frontend" / "README.md"]
    found += sorted((ROOT / "docs").glob("*.md"))
    found += sorted((ROOT / "packages").glob("**/README.md"))
    return [path for path in found if path.is_file()]


@covers("SYS-NFR-07")
class DocumentationTests(unittest.TestCase):
    def test_every_relative_link_in_the_documents_reaches_a_file(self) -> None:
        broken: list[str] = []
        for document in documents():
            for target in LINK.findall(document.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path = (document.parent / target.split("#", 1)[0]).resolve()
                if not path.exists():
                    broken.append(f"{document.relative_to(ROOT)} -> {target}")
        self.assertEqual(broken, [])

    def test_the_readme_gets_a_newcomer_to_a_running_system(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for needed in ("make start", "make check", "make reset", "make users"):
            self.assertIn(needed, readme)

    def test_the_readme_points_to_the_integration_guide(self) -> None:
        self.assertIn("docs/06-integration-guide.md", (ROOT / "README.md").read_text("utf-8"))

    def test_the_integration_guide_covers_what_a_group_needs(self) -> None:
        text = GUIDE.read_text(encoding="utf-8")
        for topic in (
            "make users",
            "audience",
            "GET /health",
            "internal/users",
            "embed",
            "redirect",
            "frame-ancestors",
            "CORS",
            "make check-service",
            "target_url",
        ):
            with self.subTest(topic=topic):
                self.assertIn(topic, text)

    def test_every_service_entry_is_listed_with_its_owner_in_the_guide(self) -> None:
        text = GUIDE.read_text(encoding="utf-8")
        services = yaml.safe_load((ROOT / "seed/content/services.yaml").read_text("utf-8"))
        for entry in services["services"]:
            with self.subTest(key=entry["key"]):
                row = next((line for line in text.splitlines() if f"`{entry['key']}`" in line), "")
                self.assertTrue(row.startswith(f"| {entry['owner_group']} |"), row)
