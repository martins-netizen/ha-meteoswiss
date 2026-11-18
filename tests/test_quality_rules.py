"""Fail closed on absent, stale or misleading rule evidence from real pytest XML."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from importlib import util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_quality_rules.py"
SPEC = util.spec_from_file_location("quality_rules", SCRIPT)
quality = util.module_from_spec(SPEC)
SPEC.loader.exec_module(quality)


def isolated_cli_environment(**overrides):
    """The disposable package owns its coverage, separate from the outer suite."""
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("COVERAGE_", "COV_CORE_"))}
    return {**env, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", **overrides}


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / "project"
    for folder in ("docs", "tests", "custom_components/meteoswiss"):
        (root / folder).mkdir(parents=True)
    (root / "docs/evidence.md").write_text("# Evidence\n\n# Evidence\n")
    (root / "tests/test_behavior.py").write_text("def test_behavior():\n    assert True\n")
    (root / "custom_components/meteoswiss/__init__.py").write_text("value = 1\n")
    rows = [{"id": rule, "tier": tier, "applicability": "applicable",
             "assessment": "reviewed", "source": ["custom_components/meteoswiss/__init__.py"],
             "documentation": ["docs/evidence.md#evidence-1"], "tests": [],
             "rationale": "The engineering behavior has explicit bounded review evidence."}
            for rule, tier in quality.RULE_TIERS.items()]
    rows[0].update(assessment="automated", tests=["tests/test_behavior.py::test_behavior"])
    index = {"schema_version": 1, "assessment": "custom-integration-engineering", "rules": rows}
    (root / quality.INDEX).write_text(json.dumps(index))
    monkeypatch.setattr(quality.tempfile, "gettempdir", lambda: str(tmp_path))
    return root


def alter_index(root, change):
    path = root / quality.INDEX
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))


def reports(root, *, cases=None):
    nonce = quality.prepare(root)
    directory, state = quality.read_state(root)
    suite = ET.SubElement(ET.Element("testsuites"), "testsuite", {
        "tests": "1", "errors": "0", "failures": "0", "skipped": "0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    for name, result in cases or [("test_behavior", None)]:
        case = ET.SubElement(suite, "testcase", classname=nonce + ".tests.test_behavior", name=name)
        if result:
            ET.SubElement(case, result)
    suite.set("tests", str(len(suite)))
    root_xml = ET.Element("testsuites")
    root_xml.append(suite)
    path = quality.fixed_file(directory, "pytest-results.xml")
    path.write_bytes(ET.tostring(root_xml))
    coverage = {"meta": {"branch_coverage": True}, "files": {
        "custom_components/meteoswiss/__init__.py": {"summary": {
            "covered_lines": 1, "num_statements": 1, "num_branches": 0, "covered_branches": 0}}},
        "totals": {"num_statements": 1}}
    (root / "coverage.json").write_text(json.dumps(coverage))
    return directory, state, root_xml


def save_xml(directory, xml):
    quality.fixed_file(directory, "pytest-results.xml").write_bytes(ET.tostring(xml))


def test_complete_index_preserves_manual_review_and_custom_tier_boundary(project):
    reports(project)
    result = quality.verify(project)
    assert result["rule_count"] == 51 and result["official_tier_awarded"] is False
    assert result["rules"][0]["evidence"] == "automated_verified"
    assert result["rules"][1]["evidence"] == "human_review_recorded"
    assert result["rules"][1]["passing_test_variants"] == 0


@pytest.mark.parametrize("change", [
    lambda d: d["rules"].pop(),
    lambda d: d["rules"].__setitem__(1, deepcopy(d["rules"][0])),
    lambda d: d["rules"][0].update(id="invented-rule"),
    lambda d: d["rules"][0].update(id=[]),
    lambda d: d["rules"][0].update(applicability={}),
    lambda d: d["rules"][0].update(assessment=[]),
    lambda d: d["rules"][0].update(tier="platinum"),
    lambda d: d["rules"][0].update(tests=[]),
    lambda d: d["rules"][0].update(rationale="yes"),
    lambda d: d["rules"][0].update(source=["../outside"]),
    lambda d: d["rules"][0].update(documentation=["/etc/passwd"]),
    lambda d: d["rules"][0].update(documentation=["https://example.test/evidence.md"]),
    lambda d: d["rules"][0].update(documentation=["docs/evidence.md#missing"]),
    lambda d: d["rules"][0].update(documentation=["docs/%2e%2e/%2e%2e/outside.md"]),
    lambda d: d["rules"][0].update(source=["docs/evidence.md", "docs/evidence.md"]),
    lambda d: d["rules"][0].update(tests=["tests/test_behavior.py::test_behavior[passing-only]"]),
    lambda d: d["rules"][0].update(tests=["tests//test_behavior.py::test_behavior"]),
    lambda d: d["rules"][0].update(applicability="exempt", assessment="automated"),
    lambda d: d["rules"][0].update(applicability="exempt", assessment="exempt", tests=[], official_rule="wrong"),
    lambda d: d["rules"][0].update(assessment="pending", source=["../outside"]),
])
def test_invalid_missing_or_escaping_rule_evidence_is_rejected(project, change):
    alter_index(project, change)
    with pytest.raises(quality.EvidenceError):
        quality.load_index(project)


def test_reasoned_exemption_is_recorded_without_inventing_test_evidence(project):
    alter_index(project, lambda d: d["rules"][0].update(
        applicability="exempt", assessment="exempt", tests=[],
        official_rule="https://contributors.home-assistant.io/core/quality-scale/action-setup/"))
    reports(project)
    assert quality.verify(project)["rules"][0]["evidence"] == "exemption_recorded"


def test_pending_cross_pr_rule_cannot_pass(project):
    alter_index(project, lambda d: d["rules"][0].update(assessment="pending"))
    reports(project)
    with pytest.raises(quality.EvidenceError, match="pending"):
        quality.verify(project)


def test_prepare_removes_old_reports_and_uses_private_new_nonce(project):
    directory, previous, _xml = reports(project)
    nonce = quality.prepare(project)
    assert nonce != previous["nonce"] and not (project / "coverage.json").exists()
    assert (directory / "pytest-results.xml").read_bytes() == b""
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    for path in directory.iterdir():
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.parametrize("target", ["coverage", "junit", "marker", "source", "directory"])
def test_symlinks_are_rejected_without_reading_or_removing_target(project, target, tmp_path):
    directory, _state, _xml = reports(project)
    outside = tmp_path / "outside"
    outside.write_text("private sentinel")
    path = {"coverage": project / "coverage.json", "junit": directory / "pytest-results.xml",
            "marker": directory / "run.json", "source": project / "docs/evidence.md",
            "directory": directory}[target]
    if path.is_dir():
        for child in path.iterdir():
            child.unlink()
        path.rmdir()
    else:
        path.unlink()
    path.symlink_to(outside)
    with pytest.raises(quality.EvidenceError):
        quality.prepare(project)
    assert outside.read_text() == "private sentinel"


@pytest.mark.parametrize("target", ["junit", "coverage", "suite", "session"])
@pytest.mark.parametrize("offset", [-7200, 7200])
def test_stale_and_future_evidence_is_rejected(project, target, offset):
    directory, _state, xml = reports(project)
    when = time.time() + offset
    if target in {"junit", "coverage"}:
        path = directory / "pytest-results.xml" if target == "junit" else project / "coverage.json"
        os.utime(path, (when, when))
    elif target == "suite":
        xml[0].set("timestamp", datetime.fromtimestamp(when, timezone.utc).isoformat())
        save_xml(directory, xml)
    else:
        path = directory / "run.json"
        state = json.loads(path.read_text())
        state["started_ns"] = int(when * 1e9)
        path.write_text(json.dumps(state))
    with pytest.raises(quality.EvidenceError):
        quality.verify(project)


def test_source_changed_during_run_invalidates_evidence(project):
    reports(project)
    (project / "tests/test_behavior.py").write_text("def test_behavior():\n    assert False\n")
    with pytest.raises(quality.EvidenceError, match="changed_source"):
        quality.verify(project)


@pytest.mark.parametrize("mutate", [
    lambda xml: xml[0].remove(xml[0][0]),
    lambda xml: xml[0].append(deepcopy(xml[0][0])),
    lambda xml: xml[0][0].set("classname", "old_nonce.tests.test_behavior"),
    lambda xml: xml[0][0].set("name", "test_unused_selector"),
    lambda xml: ET.SubElement(xml[0][0], "skipped"),
    lambda xml: ET.SubElement(xml[0][0], "failure"),
    lambda xml: ET.SubElement(xml[0][0], "error"),
    lambda xml: xml[0].set("tests", "0"),
    lambda xml: xml[0].set("errors", "1"),
    lambda xml: xml[0].set("timestamp", "2026-11-17T12:00:00"),
])
def test_xml_empty_duplicate_skipped_failed_unmatched_and_unbound_cases_fail(project, mutate):
    directory, _state, xml = reports(project)
    mutate(xml)
    save_xml(directory, xml)
    with pytest.raises(quality.EvidenceError):
        quality.verify(project)


def test_all_parameter_variants_must_pass(project):
    reports(project, cases=[("test_behavior[first]", None), ("test_behavior[second]", "skipped")])
    with pytest.raises(quality.EvidenceError, match="nonpassing_selector"):
        quality.verify(project)


@pytest.mark.parametrize("data", [b"", b"broken", b"<!DOCTYPE x><testsuites />", b"<testcase />"])
def test_malformed_xml_is_rejected(project, data):
    directory, _state, _xml = reports(project)
    (directory / "pytest-results.xml").write_bytes(data)
    with pytest.raises(quality.EvidenceError):
        quality.verify(project)


@pytest.mark.parametrize("change", [
    lambda d: d.update(files={}),
    lambda d: d.update(files={"invented.py": next(iter(d["files"].values()))}),
    lambda d: d["meta"].update(branch_coverage=False),
    lambda d: d["totals"].update(num_statements=0),
    lambda d: next(iter(d["files"].values()))["summary"].update(covered_lines=2),
])
def test_empty_fabricated_or_inconsistent_coverage_is_rejected(project, change):
    reports(project)
    path = project / "coverage.json"
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))
    with pytest.raises(quality.EvidenceError):
        quality.verify(project)


def test_duplicate_json_keys_are_not_silently_overwritten(project):
    (project / quality.INDEX).write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(quality.EvidenceError, match="duplicate_json"):
        quality.load_index(project)


def test_actual_pytest_cli_parameter_and_subtest_xml_contract(project):
    """Observe pinned pytest itself: subtests increase counters without testcase rows."""
    test = project / "tests/test_behavior.py"
    test.write_text("import pytest\n@pytest.mark.parametrize('value', [1, 2])\ndef test_behavior(value, subtests):\n"
                    "    for part in (1, 2):\n        with subtests.test(part=part):\n            assert value > 0\n")
    nonce = quality.prepare(project)
    directory, _state = quality.read_state(project)
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "--confcutdir", str(project),
                             "--junitxml", str(directory / "pytest-results.xml"), "--junit-prefix", nonce, str(test)],
                            cwd=project, env=isolated_cli_environment(),
                            capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout
    # Coverage is independently shape-tested; this small CLI probe never runs the integration suite.
    (project / "coverage.json").write_text(json.dumps({"meta": {"branch_coverage": True}, "files": {
        "custom_components/meteoswiss/__init__.py": {"summary": {
            "covered_lines": 1, "num_statements": 1, "num_branches": 0, "covered_branches": 0}}},
        "totals": {"num_statements": 1}}))
    xml = ET.parse(directory / "pytest-results.xml").getroot()
    assert int(xml[0].get("tests")) > len(xml[0].findall("testcase")) == 2
    assert quality.verify(project)["rules"][0]["passing_test_variants"] == 2


def test_cli_does_not_accept_arbitrary_report_or_output_paths(tmp_path):
    target = tmp_path / "forbidden"
    result = subprocess.run([sys.executable, str(SCRIPT), "verify", "--report-path", str(target)],
                            env=isolated_cli_environment(), capture_output=True, text=True, timeout=10, check=False)
    assert result.returncode == 2 and not target.exists()


def test_actual_prepare_pytest_coverage_verify_cli_sequence(project, monkeypatch):
    """A disposable source proves the actual CLI/pytest/coverage API contract."""
    script = project / "scripts/check_quality_rules.py"
    script.parent.mkdir()
    shutil.copyfile(SCRIPT, script)
    (project / "tests/test_behavior.py").write_text(
        "import pathlib, sys\n"
        "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))\n"
        "from custom_components.meteoswiss import value\n"
        "def test_behavior():\n    assert value == 1\n"
        "def test_unmapped():\n    assert value > 0\n")
    # Real pytest-cov/coverage.py instrumentation can auto-start in subprocesses.
    # The nested probe must neither append its fake package to the outer report
    # nor inherit the outer data filename. Keep an independent write sentinel.
    outer_data = project.parent / "outer-coverage-sentinel"
    outer_data.write_bytes(b"owned by the outer coverage session")
    monkeypatch.setenv("COVERAGE_FILE", str(outer_data))
    env = isolated_cli_environment(TMPDIR=str(project.parent))

    def command(*args):
        result = subprocess.run([sys.executable, *args], cwd=project, env=env,
                                capture_output=True, text=True, timeout=30, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout.strip()

    nonce = command(str(script), "prepare")
    junit_path = Path(command(str(script), "junit-path"))
    assert junit_path.name == "pytest-results.xml" and junit_path.parent.parent == project.parent
    command("-m", "pytest", "-q", "-p", "pytest_cov", "-o", "addopts=", "--confcutdir", str(project),
            "--cov=custom_components.meteoswiss", "--cov-branch", "--cov-report=json:coverage.json",
            "--junitxml", str(junit_path), "--junit-prefix", nonce, "tests")
    assert stat.S_IMODE(junit_path.stat().st_mode) == 0o600
    result = json.loads(command(str(script), "verify"))
    assert result["rules"][0]["evidence"] == "automated_verified"
    assert result["rule_count"] == 51 and result["official_tier_awarded"] is False
    # A real successful filtered run is insufficient when the mapped function
    # was deselected. XML makes no assertion about unreported parameter variants.
    nonce = command(str(script), "prepare")
    command("-m", "pytest", "-q", "-p", "pytest_cov", "-o", "addopts=", "--confcutdir", str(project),
            "--cov=custom_components.meteoswiss", "--cov-branch", "--cov-report=json:coverage.json",
            "--junitxml", str(junit_path), "--junit-prefix", nonce, "-k", "test_unmapped", "tests")
    rejected = subprocess.run([sys.executable, str(script), "verify"], cwd=project, env=env,
                              capture_output=True, text=True, timeout=10, check=False)
    assert rejected.returncode == 1 and "missing_or_nonpassing_selector" in rejected.stderr
    assert outer_data.read_bytes() == b"owned by the outer coverage session"
    assert (project / ".coverage").is_file()
