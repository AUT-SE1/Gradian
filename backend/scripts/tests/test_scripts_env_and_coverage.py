import subprocess
import sys
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
        ids = req_coverage.required_ids(ROOT / "docs" / "01-requirements.md")
        self.assertIn("SYS-AUTH-01", ids)
        self.assertIn("SYS-NFR-08", ids)
        self.assertEqual(len(ids), len(set(ids)))

    def test_tests_only_name_requirements_that_exist(self) -> None:
        required = set(req_coverage.required_ids(ROOT / "docs" / "01-requirements.md"))
        self.assertEqual(sorted(req_coverage.covered_ids(ROOT) - required), [])

    def test_external_marks_are_read_from_the_test_plan(self) -> None:
        external = req_coverage.external_ids(ROOT / "docs" / "04-test-plan.md")
        self.assertIn("SYS-AUTH-01", external)
        self.assertNotIn("SYS-AUTH-02", external)

    def test_external_marks_only_name_requirements_that_exist(self) -> None:
        required = set(req_coverage.required_ids(ROOT / "docs" / "01-requirements.md"))
        external = req_coverage.external_ids(ROOT / "docs" / "04-test-plan.md")
        self.assertEqual(sorted(external - required), [])

    def test_only_the_level_column_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "plan.md"
            plan.write_text(
                "| SYS-AUTH-01 | EXT, MANUAL | text |\n"
                "| SYS-AUTH-02 | UNIT | the word EXT here does not count |\n",
                encoding="utf-8",
            )
            self.assertEqual(req_coverage.external_ids(plan), {"SYS-AUTH-01"})

    def run_in(self, root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        script = ROOT / "scripts" / "req_coverage.py"
        return subprocess.run(
            [sys.executable, str(script), "--root", str(root), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def small_tree(self, tmp: str, *, test_body: str = "") -> Path:
        root = Path(tmp)
        (root / "docs").mkdir()
        (root / "docs" / "01-requirements.md").write_text(
            "| SYS-AUTH-02 | text |\n| SYS-AUTH-03 | text |\n", encoding="utf-8"
        )
        (root / "docs" / "04-test-plan.md").write_text(
            "| SYS-AUTH-03 | EXT | x |\n", encoding="utf-8"
        )
        (root / "core").mkdir()
        (root / "core" / "test_x.py").write_text(test_body, encoding="utf-8")
        return root

    def test_a_gap_is_reported_and_strict_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.small_tree(tmp)
            loose = self.run_in(root)
            strict = self.run_in(root, "--strict")
        self.assertEqual(loose.returncode, 0, loose.stdout)
        self.assertIn("neither a test nor an EXT mark: SYS-AUTH-02", loose.stdout)
        self.assertEqual(strict.returncode, 1)

    def test_when_every_requirement_has_a_test_or_a_mark_strict_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.small_tree(tmp, test_body='@covers("SYS-AUTH-02")\nclass T: ...\n')
            strict = self.run_in(root, "--strict")
        self.assertEqual(strict.returncode, 0, strict.stdout)

    def test_the_repository_has_no_gap(self) -> None:
        result = self.run_in(ROOT, "--strict")
        self.assertEqual(result.returncode, 0, result.stdout)
