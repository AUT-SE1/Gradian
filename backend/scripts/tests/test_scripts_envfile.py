import tempfile
import unittest
from pathlib import Path

import envfile
from covers import covers


class DotenvTests(unittest.TestCase):
    def test_parsing_ignores_comments_and_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("# note\n\nA=1\nB = two\nbroken\n", encoding="utf-8")
            self.assertEqual(envfile.parse_dotenv(path), {"A": "1", "B": "two"})
        self.assertEqual(envfile.parse_dotenv(Path(tmp) / "missing"), {})


@covers("SYS-DATA-07")
class ProductionDetectionTests(unittest.TestCase):
    def detect(self, dotenv: str | None, environ: dict[str, str]) -> bool:
        with tempfile.TemporaryDirectory() as tmp:
            if dotenv is not None:
                (Path(tmp) / ".env").write_text(dotenv, encoding="utf-8")
            return envfile.is_production(Path(tmp), environ)

    def test_production_in_the_dotenv_file_is_seen(self) -> None:
        self.assertTrue(self.detect("ENVIRONMENT=production\n", {}))

    def test_production_in_the_process_environment_is_seen(self) -> None:
        self.assertTrue(self.detect(None, {"ENVIRONMENT": "production"}))

    def test_the_process_environment_wins_over_the_file(self) -> None:
        self.assertFalse(self.detect("ENVIRONMENT=production\n", {"ENVIRONMENT": "development"}))

    def test_default_is_not_production(self) -> None:
        self.assertFalse(self.detect(None, {}))
        self.assertFalse(self.detect("ENVIRONMENT=test\n", {}))
