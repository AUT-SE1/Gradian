import tempfile
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from gradian import env
from gradian_testing.covers import covers


@covers("SYS-OPS-06")
class RequireTests(SimpleTestCase):
    def test_a_missing_variable_is_named_in_the_error(self) -> None:
        with self.assertRaisesMessage(ImproperlyConfigured, "SOME_REQUIRED_NAME"):
            env.require("SOME_REQUIRED_NAME", environ={})

    def test_an_empty_value_counts_as_missing(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            env.require("A", environ={"A": ""})

    def test_a_present_value_is_returned(self) -> None:
        self.assertEqual(env.require("A", environ={"A": "x"}), "x")


class ReadTests(SimpleTestCase):
    def test_flag_and_csv_parsing(self) -> None:
        self.assertTrue(env.flag("A", False, environ={"A": " Yes "}))
        self.assertFalse(env.flag("A", True, environ={"A": "0"}))
        self.assertTrue(env.flag("MISSING", True, environ={}))
        self.assertEqual(env.csv("A", "", environ={"A": "a, b,,c"}), ["a", "b", "c"])

    def test_the_real_environment_wins_over_the_dotenv_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(
                "# comment\nA=from-file\nB=from-file\n\nbroken line\n", encoding="utf-8"
            )
            environ = {"A": "from-env"}
            env.load_dotenv(path, environ)
        self.assertEqual(environ, {"A": "from-env", "B": "from-file"})
