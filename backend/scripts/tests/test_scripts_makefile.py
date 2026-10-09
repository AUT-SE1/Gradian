"""The Makefile is the interface of local operation; these checks keep its promises."""

import re
import unittest
from pathlib import Path

from covers import covers

ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = (ROOT / "Makefile").read_text(encoding="utf-8")
TARGET = re.compile(r"^([a-z][a-z-]*):(.*)$", re.MULTILINE)


def recipe(target: str) -> str:
    """The lines under `target:` up to the next blank line."""
    match = re.search(rf"^{re.escape(target)}:.*\n((?:\t.*\n)*)", MAKEFILE, re.MULTILINE)
    assert match, f"no target {target}"
    return match.group(1)


def prerequisites(target: str) -> list[str]:
    match = re.search(rf"^{re.escape(target)}:([^#\n]*)", MAKEFILE, re.MULTILINE)
    assert match, f"no target {target}"
    return match.group(1).split()


def variable(name: str) -> str:
    match = re.search(rf"^{name}\s*\??=\s*(.*)$", MAKEFILE, re.MULTILINE)
    assert match, f"no variable {name}"
    return match.group(1)


@covers("SYS-OPS-04")
class DiscoverabilityTests(unittest.TestCase):
    def test_every_target_has_help_text_so_make_help_lists_it(self) -> None:
        without = [name for name, rest in TARGET.findall(MAKEFILE) if "## " not in rest]
        self.assertEqual(without, [])

    def test_a_target_is_either_a_main_target_or_a_step_never_ambiguous(self) -> None:
        for name, rest in TARGET.findall(MAKEFILE):
            text = rest.split("## ", 1)[1]
            self.assertTrue(text.strip(), name)

    def test_the_variables_the_help_text_mentions_exist(self) -> None:
        for name in ("TEAMS", "CMD", "COMPOSE", "EXEC_FLAGS"):
            self.assertRegex(MAKEFILE, rf"(?m)^{name}\s*\??=", name)

    def test_no_target_is_declared_phony_without_being_defined(self) -> None:
        declared = re.search(r"^\.PHONY:(.*?)(?:\n\n|\Z)", MAKEFILE, re.MULTILINE | re.DOTALL)
        assert declared
        defined = {name for name, _ in TARGET.findall(MAKEFILE)}
        phony = set(declared.group(1).replace("\\", " ").split())
        self.assertEqual(sorted(phony - defined), [])


@covers("SYS-OPS-03")
class TestCommandsTests(unittest.TestCase):
    def test_the_fast_tests_leave_out_the_ones_that_need_the_system(self) -> None:
        self.assertIn("--exclude-tag=integration", recipe("test"))

    def test_the_integration_command_runs_only_the_tagged_tests(self) -> None:
        self.assertIn("--tag=integration", variable("INTEGRATION_CMD"))
        self.assertIn("$(INTEGRATION_CMD)", recipe("itest"))

    def test_the_fast_tests_do_not_start_anything(self) -> None:
        self.assertNotIn("up", prerequisites("test"))
        self.assertNotIn("start", prerequisites("test"))
        self.assertNotIn("start", prerequisites("check"))

    def test_the_integration_tests_start_the_system_first(self) -> None:
        self.assertIn("start", prerequisites("itest"))


@covers("SYS-OPS-02")
class ResetTests(unittest.TestCase):
    def test_reset_removes_the_volumes_and_then_starts_again(self) -> None:
        lines = recipe("reset").splitlines()
        wipe = next(i for i, line in enumerate(lines) if "down -v" in line)
        start = next(i for i, line in enumerate(lines) if "$(MAKE) start" in line)
        self.assertLess(wipe, start)

    def test_start_loads_the_demo_data(self) -> None:
        self.assertEqual(prerequisites("start"), ["up", "bootstrap"])
        self.assertEqual(prerequisites("bootstrap"), ["seed"])
        self.assertIn("loaddata $(FIXTURES)", recipe("bootstrap"))

    def test_every_fixture_the_seed_writes_is_loaded(self) -> None:
        loaded = variable("FIXTURES").split()
        self.assertEqual(sorted(loaded), ["landing", "profiles", "services", "widgets"])
