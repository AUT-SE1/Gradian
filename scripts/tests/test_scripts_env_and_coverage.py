import subprocess
import tempfile
import unittest
from pathlib import Path

import check_env_example
import req_coverage
from covers import covers

ROOT = Path(__file__).resolve().parents[2]


@covers("SYS-OPS-05")
class EnvExampleTests(unittest.TestCase):
    def test_repository_env_example_matches_the_settings(self) -> None:
        read = check_env_example.variables_read(ROOT / "core")
        documented = check_env_example.variables_documented(ROOT / ".env.example")
        self.assertEqual(sorted(read - documented), [])
        self.assertEqual(sorted(documented - read - check_env_example.EXTERNAL), [])

    def test_script_finds_literal_reads_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "settings.py").write_text(
                'A = env.require("ALPHA")\nB = env.get("BETA", "x")\nC = env.flag("GAMMA", False)\n'
                'D = other.get("DELTA")\n',
                encoding="utf-8",
            )
            self.assertEqual(
                check_env_example.variables_read(Path(tmp)), {"ALPHA", "BETA", "GAMMA"}
            )


@covers("SYS-NFR-08")
class RequirementCoverageTests(unittest.TestCase):
    def test_requirement_ids_are_read_from_the_document(self) -> None:
        ids = req_coverage.required_ids(ROOT / "docs" / "backend" / "01-requirements.md")
        self.assertIn("SYS-AUTH-01", ids)
        self.assertIn("SYS-NFR-08", ids)
        self.assertEqual(len(ids), len(set(ids)))

    def test_tests_only_name_requirements_that_exist(self) -> None:
        required = set(req_coverage.required_ids(ROOT / "docs" / "backend" / "01-requirements.md"))
        self.assertEqual(sorted(req_coverage.covered_ids(ROOT) - required), [])

    def test_a_gap_is_reported_and_strict_fails(self) -> None:
        script = ROOT / "scripts" / "req_coverage.py"
        loose = subprocess.run([str(script)], capture_output=True, text=True, check=False)
        strict = subprocess.run(
            [str(script), "--strict"], capture_output=True, text=True, check=False
        )
        self.assertEqual(loose.returncode, 0, loose.stdout)
        self.assertIn("without a test", loose.stdout)  # not every requirement is built yet
        self.assertEqual(strict.returncode, 1)
