"""Exercise local tool input boundaries without GitHub or Home Assistant."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CoverageInputTests(unittest.TestCase):
    """Only the repository's standard report can enter the coverage gate."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "repository with spaces"
        self.outside = Path(self.directory.name) / "outside"
        (self.root / "scripts").mkdir(parents=True)
        self.outside.mkdir()
        self.script = self.root / "scripts/check_quality_coverage.py"
        shutil.copyfile(ROOT / "scripts/check_quality_coverage.py", self.script)
        self.report = {
            "meta": {"branch_coverage": True},
            "totals": {"percent_covered": 100.0},
            "files": {
                f"custom_components/meteoswiss/{path.name}": {
                    "summary": {
                        "covered_lines": 1,
                        "num_statements": 1,
                        "covered_branches": 2,
                        "num_branches": 2,
                        "percent_covered": 100.0,
                    },
                    "missing_lines": [],
                    "missing_branches": [],
                }
                for path in (ROOT / "custom_components/meteoswiss").glob("*.py")
            },
        }

    def run_checker(self, *args):
        return subprocess.run(
            [sys.executable, str(self.script), *args],
            cwd=self.outside,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    def write_report(self, report=None):
        (self.root / "coverage.json").write_text(
            json.dumps(self.report if report is None else report), encoding="utf-8"
        )

    def test_uses_repository_report_independently_of_working_directory(self):
        self.write_report()
        (self.outside / "coverage.json").write_text("not the report", encoding="utf-8")
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("All modules exceed 95%", result.stdout)

    def test_rejects_all_path_arguments_before_reading_a_report(self):
        for argument in (
            "../outside/private.json",
            str(self.outside / "private.json"),
            "coverage.json",
            "--report=../../private.json",
        ):
            with self.subTest(argument=argument):
                result = self.run_checker(argument)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("no arguments", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_rejects_a_symbolic_link_report(self):
        private = self.outside / "private.json"
        private.write_text("private marker", encoding="utf-8")
        (self.root / "coverage.json").symlink_to(private)
        result = self.run_checker()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not be a symbolic link", result.stderr)
        self.assertNotIn("private marker", result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_existing_coverage_failures_still_stop_the_gate(self):
        cases = (
            ("branch", "Branch coverage must be enabled"),
            ("module", "must exceed 95% per-module coverage"),
            ("flow", "Config flow must have 100% line and branch coverage"),
            ("source", "coordinator.py must retain full line and branch coverage"),
            ("aggregate", "below the current 99.0% floor"),
        )
        for case, message in cases:
            with self.subTest(case=case):
                report = copy.deepcopy(self.report)
                files = report["files"]
                if case == "branch":
                    report["meta"]["branch_coverage"] = False
                elif case == "module":
                    files["custom_components/meteoswiss/const.py"]["summary"]["percent_covered"] = 95.0
                elif case == "flow":
                    files["custom_components/meteoswiss/config_flow.py"]["missing_lines"] = [1]
                elif case == "source":
                    files["custom_components/meteoswiss/coordinator.py"]["missing_branches"] = [[1, 2]]
                else:
                    report["totals"]["percent_covered"] = 98.99
                self.write_report(report)
                result = self.run_checker()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)


class PublisherShellTests(unittest.TestCase):
    """Bad arguments must stop before dependency lookup or publication."""

    def test_help_and_invalid_arguments_stop_before_external_commands(self):
        cases = (
            (["--help"], 0),
            (["-h"], 0),
            ([], 2),
            (["--publish"], 2),
            (["--publish", "-" + "a" * 39], 2),
            (["--publish", "*"], 2),
            (["--unknown", "a" * 40], 2),
            (["--publish", "a" * 40, "extra"], 2),
        )
        for script in sorted((ROOT / "scripts").glob("veroeffentliche_*.sh")):
            accepted_modes = (
                (["--publish", "a" * 40], 1),
                (["--check", "a" * 40], 1 if "stable" in script.name else 2),
            )
            for args, expected in cases + accepted_modes:
                with self.subTest(script=script.name, args=args):
                    result = subprocess.run(
                        ["/bin/bash", str(script), *args],
                        env={"PATH": "/nonexistent"},
                        text=True,
                        capture_output=True,
                        timeout=10,
                        check=False,
                    )
                    self.assertEqual(result.returncode, expected, result.stderr)
                    self.assertNotIn("unbound variable", result.stderr)
                    if expected == 1:
                        self.assertIn("gh", result.stderr)
                    else:
                        self.assertNotIn("Missing:", result.stderr)
                        self.assertNotIn("Fehlt:", result.stderr)


if __name__ == "__main__":
    unittest.main()
