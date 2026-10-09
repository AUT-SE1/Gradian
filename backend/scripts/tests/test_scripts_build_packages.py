import tempfile
import unittest
from pathlib import Path

import build_packages

ROOT = Path(__file__).resolve().parents[2]


class BuildPackagesTests(unittest.TestCase):
    def test_every_package_of_the_repository_is_found(self) -> None:
        names = [path.name for path in build_packages.package_dirs(ROOT / "packages")]
        self.assertEqual(names, ["gradian-auth", "gradian-keycloak", "gradian-testing"])

    def test_directories_without_a_pyproject_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a").mkdir()
            (Path(tmp) / "b").mkdir()
            (Path(tmp) / "b" / "pyproject.toml").write_text("", encoding="utf-8")
            self.assertEqual([p.name for p in build_packages.package_dirs(Path(tmp))], ["b"])
