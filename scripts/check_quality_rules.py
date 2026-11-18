"""Verify the project's 51-rule evidence index against one fresh native pytest run.

This verifies evidence, not an official tier or the outcome of human review.
All input/output locations are fixed; no caller-supplied file path is accepted.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import tempfile
import time
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
INDEX = "docs/quality_rules.json"
TIERS = {
    "bronze": "action-setup appropriate-polling brands common-modules config-flow config-flow-test-coverage dependency-transparency docs-actions docs-conditions docs-high-level-description docs-installation-instructions docs-removal-instructions docs-triggers entity-event-setup entity-unique-id has-entity-name runtime-data test-before-configure test-before-setup unique-config-entry".split(),
    "silver": "action-exceptions config-entry-unloading docs-configuration-parameters docs-installation-parameters entity-unavailable integration-owner log-when-unavailable parallel-updates reauthentication-flow test-coverage".split(),
    "gold": "devices diagnostics discovery discovery-update-info docs-data-update docs-examples docs-known-limitations docs-supported-devices docs-supported-functions docs-troubleshooting docs-use-cases dynamic-devices entity-category entity-device-class entity-disabled-by-default entity-translations exception-translations icon-translations reconfiguration-flow repair-issues stale-devices".split(),
}
RULE_TIERS = {rule: tier for tier, rules in TIERS.items() for rule in rules}
MAX_INDEX_BYTES = 256 * 1024
MAX_XML_BYTES = 32 * 1024 * 1024
MAX_COVERAGE_BYTES = 16 * 1024 * 1024
MAX_SESSION_SECONDS = 3600
CLOCK_SKEW_NS = 2_000_000_000
SELECTOR = re.compile(r"tests/[A-Za-z0-9_/]+\.py(?:::[A-Za-z_][A-Za-z0-9_]*)+")


class EvidenceError(ValueError):
    """A fixed diagnostic code; never raw source/report content."""


def require(ok: bool, code: str) -> None:
    if not ok:
        raise EvidenceError(code)


def project_path(root: Path, name: str) -> Path:
    require(isinstance(name, str) and name and "\\" not in name and "\x00" not in name,
            "invalid_reference")
    path = Path(name)
    require(not path.is_absolute() and ".." not in path.parts and str(path) == name,
            "reference_escape")
    candidate = root / path
    require(not any((root / Path(*path.parts[:index])).is_symlink()
                    for index in range(1, len(path.parts) + 1)), "reference_symlink")
    require(candidate.resolve().is_relative_to(root.resolve()), "reference_escape")
    return candidate


def read_bytes(path: Path, limit: int) -> bytes:
    require(not path.is_symlink(), "report_symlink")
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as source:
            require(stat.S_ISREG(os.fstat(source.fileno()).st_mode), "not_regular_file")
            result = source.read(limit + 1)
    except OSError as error:
        raise EvidenceError("file_unavailable") from error
    require(len(result) <= limit, "oversized_input")
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def read_json(path: Path, limit: int):
    try:
        return json.loads(read_bytes(path, limit).decode("utf-8"), object_pairs_hook=unique_object,
                          parse_constant=lambda _value: (_ for _ in ()).throw(EvidenceError("invalid_json_number")))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise EvidenceError("invalid_json") from error


def anchors(path: Path) -> set[str]:
    """GitHub heading anchors, including duplicate-heading suffixes."""
    result, counts = set(), {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^#{1,6}\s+", line):
            continue
        title = re.sub(r"^#{1,6}\s+", "", line).strip().rstrip("#").strip().lower()
        slug = re.sub(r"[^\w\- ]", "", title).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(slug + ("-" + str(count) if count else ""))
    return result


def validate_reference(root: Path, reference: str, *, documentation: bool, pending: bool = False) -> None:
    require(isinstance(reference, str), "invalid_reference")
    split = urlsplit(reference)
    require(not split.scheme and not split.netloc and not split.query, "reference_escape")
    path = project_path(root, unquote(split.path))
    if documentation:
        require(path.suffix == ".md", "documentation_reference_type")
    if pending:
        return
    require(path.is_file(), "missing_reference")
    if split.fragment:
        require(documentation and unquote(split.fragment) in anchors(path), "missing_anchor")


def load_index(root: Path = ROOT) -> list[dict]:
    index = read_json(project_path(root, INDEX), MAX_INDEX_BYTES)
    require(isinstance(index, dict) and type(index.get("schema_version")) is int and index["schema_version"] == 1 and
            index.get("assessment") == "custom-integration-engineering", "invalid_index")
    rows = index.get("rules")
    require(isinstance(rows, list) and len(rows) == 51, "rule_count")
    seen = set()
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("id"), str) and row["id"] in RULE_TIERS and row["id"] not in seen,
                "unknown_or_duplicate_rule")
        seen.add(row["id"])
        require(row.get("tier") == RULE_TIERS[row["id"]], "wrong_tier")
        require(isinstance(row.get("applicability"), str) and row["applicability"] in {"applicable", "exempt", "custom-route"} and
                isinstance(row.get("assessment"), str) and row["assessment"] in {"automated", "reviewed", "exempt", "pending"}, "invalid_assessment")
        require(isinstance(row.get("rationale"), str) and len(row["rationale"].strip()) >= 20,
                "missing_rationale")
        for name in ("source", "documentation", "tests"):
            values = row.get(name)
            require(isinstance(values, list) and all(isinstance(value, str) and value for value in values) and
                    len(values) == len(set(values)), "duplicate_or_invalid_reference")
        require(row["source"] and row["documentation"], "missing_evidence_reference")
        if row["assessment"] == "automated":
            require(row["tests"] and row["applicability"] != "exempt", "missing_behavioral_evidence")
        if row["applicability"] == "exempt" or row["assessment"] == "exempt":
            require(row["applicability"] == row["assessment"] == "exempt" and not row["tests"] and
                    row.get("official_rule") == "https://contributors.home-assistant.io/core/quality-scale/" + row["id"] + "/",
                    "invalid_exemption")
        for selector in row["tests"]:
            require(SELECTOR.fullmatch(selector) is not None and ".." not in selector and
                    "[" not in selector, "invalid_selector")
        # Pending cross-PR references still obey confinement; verify cannot pass them.
        for reference in row["source"]:
            validate_reference(root, reference, documentation=False, pending=row["assessment"] == "pending")
        for reference in row["documentation"]:
            validate_reference(root, reference, documentation=True, pending=row["assessment"] == "pending")
        for selector in row["tests"]:
            validate_reference(root, selector.split("::", 1)[0], documentation=False, pending=row["assessment"] == "pending")
    require(seen == set(RULE_TIERS), "missing_rule")
    return rows


def source_fingerprint(root: Path) -> str:
    """Bind the run to runtime, tests, policies and documentation bytes."""
    paths = set()
    for name in ("custom_components/meteoswiss", "tests", "scripts", ".github", "docs"):
        folder = project_path(root, name)
        if folder.is_dir():
            for path in folder.rglob("*"):
                if "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
                    if path.is_symlink():
                        raise EvidenceError("source_symlink")
                    if path.is_file():
                        paths.add(path)
    for pattern in ("*.md", "requirements*", "pytest.ini", "hacs.json", "pyproject.toml", ".coveragerc"):
        for path in root.glob(pattern):
            require(not path.is_symlink(), "source_symlink")
            if path.is_file():
                paths.add(path)
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        with path.open("rb") as source:
            file_digest = hashlib.file_digest(source, "sha256").digest()
        digest.update(file_digest)
    return digest.hexdigest()


def evidence_directory(root: Path = ROOT) -> Path:
    key = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:20]
    path = Path(tempfile.gettempdir()).resolve() / ("meteoswiss-quality-" + key)
    require(not path.is_symlink(), "evidence_directory_symlink")
    if path.exists():
        info = path.stat()
        require(path.is_dir() and info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700,
                "evidence_directory_permissions")
    return path


def fixed_file(directory: Path, name: str) -> Path:
    require(name in {"run.json", "pytest-results.xml"}, "invalid_evidence_name")
    path = directory / name
    require(not path.is_symlink() and path.resolve().parent == directory.resolve(), "report_symlink")
    return path


def write_private(path: Path, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)


def prepare(root: Path = ROOT) -> str:
    load_index(root)
    directory = evidence_directory(root)
    directory.mkdir(mode=0o700, exist_ok=True)
    for path in (fixed_file(directory, "run.json"), fixed_file(directory, "pytest-results.xml"),
                 project_path(root, "coverage.json")):
        if path.exists():
            require(path.is_file() and not path.is_symlink(), "not_regular_file")
            path.unlink()
    started = time.time_ns()
    nonce = "msq_" + secrets.token_hex(16)
    state = {"schema_version": 1, "nonce": nonce, "started_ns": started,
             "source_sha256": source_fingerprint(root)}
    write_private(fixed_file(directory, "run.json"), json.dumps(state).encode())
    # Pre-create privately; pytest's normal write preserves 0600.
    write_private(fixed_file(directory, "pytest-results.xml"), b"")
    return nonce


def read_state(root: Path) -> tuple[Path, dict]:
    directory = evidence_directory(root)
    state = read_json(fixed_file(directory, "run.json"), 4096)
    now = time.time_ns()
    require(isinstance(state, dict) and type(state.get("schema_version")) is int and state["schema_version"] == 1 and
            isinstance(state.get("nonce"), str) and re.fullmatch(r"msq_[0-9a-f]{32}", state["nonce"]) is not None and
            type(state.get("started_ns")) is int and
            now - MAX_SESSION_SECONDS * 1_000_000_000 <= state["started_ns"] <= now + CLOCK_SKEW_NS and
            state.get("source_sha256") == source_fingerprint(root), "stale_or_changed_source")
    return directory, state


def report_time(value: str, started_ns: int) -> None:
    try:
        timestamp = datetime.fromisoformat(value)
        require(timestamp.tzinfo is not None, "timestamp_timezone")
        epoch = int(timestamp.timestamp() * 1_000_000_000)
    except (ValueError, TypeError, OverflowError) as error:
        raise EvidenceError("invalid_timestamp") from error
    require(started_ns - CLOCK_SKEW_NS <= epoch <= time.time_ns() + CLOCK_SKEW_NS,
            "stale_or_future_report")


def junit_cases(path: Path, state: dict) -> dict[tuple[str, str], list[dict]]:
    raw = read_bytes(path, MAX_XML_BYTES)
    require(raw and b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "invalid_xml")
    try:
        xml = ET.fromstring(raw)
    except (ET.ParseError, ValueError) as error:
        raise EvidenceError("invalid_xml") from error
    require(xml.tag == "testsuites", "invalid_xml_root")
    suites = list(xml.findall("testsuite"))
    require(len(suites) == 1, "invalid_suite_count")
    suite = suites[0]
    report_time(suite.get("timestamp"), state["started_ns"])
    try:
        counts = {name: int(suite.get(name, "")) for name in ("tests", "errors", "failures", "skipped")}
    except (TypeError, ValueError) as error:
        raise EvidenceError("invalid_suite_counts") from error
    cases = list(suite.findall("testcase"))
    # pytest 9 subtests legitimately increase tests without extra testcase nodes.
    require(cases and counts["tests"] >= len(cases) and all(value >= 0 for value in counts.values()) and
            counts["errors"] == counts["failures"] == 0, "empty_or_failed_suite")
    seen, grouped = set(), {}
    prefix = state["nonce"] + "."
    for case in cases:
        classname, name = case.get("classname"), case.get("name")
        require(isinstance(classname, str) and classname.startswith(prefix) and isinstance(name, str) and name,
                "report_nonce_or_identity")
        key = (classname[len(prefix):], name)
        require(key not in seen, "duplicate_testcase")
        require(case.find("failure") is None and case.find("error") is None, "failed_testcase")
        seen.add(key)
        base_name = name.partition("[")[0]
        grouped.setdefault((key[0], base_name), []).append({
            "passed": not any(case.find(tag) is not None for tag in ("failure", "error", "skipped")),
        })
    return grouped


def validate_coverage(root: Path, path: Path) -> None:
    """Bind coverage to every component module; thresholds stay in the existing gate."""
    report = read_json(path, MAX_COVERAGE_BYTES)
    require(isinstance(report, dict) and isinstance(report.get("meta"), dict) and
            report["meta"].get("branch_coverage") is True and isinstance(report.get("files"), dict),
            "coverage_not_generated")
    expected = {path.relative_to(root).as_posix()
                for path in project_path(root, "custom_components/meteoswiss").rglob("*.py")}
    require(expected and set(report["files"]) == expected, "coverage_source_inventory")
    statements = 0
    for data in report["files"].values():
        require(isinstance(data, dict) and isinstance(data.get("summary"), dict), "invalid_coverage_summary")
        summary = data["summary"]
        for field in ("covered_lines", "num_statements", "num_branches", "covered_branches"):
            require(type(summary.get(field)) is int and summary[field] >= 0, "invalid_coverage_summary")
        require(summary["covered_lines"] <= summary["num_statements"] and
                summary["covered_branches"] <= summary["num_branches"], "invalid_coverage_summary")
        statements += summary["num_statements"]
    require(statements > 0 and isinstance(report.get("totals"), dict) and
            type(report["totals"].get("num_statements")) is int and
            report["totals"].get("num_statements") == statements, "empty_or_inconsistent_coverage")


def selector_key(selector: str) -> tuple[str, str]:
    parts = selector.split("::")
    module = parts[0][:-3].replace("/", ".")
    return ".".join([module, *parts[1:-1]]), parts[-1]


def verify(root: Path = ROOT) -> dict:
    rows = load_index(root)
    require(not any(row["assessment"] == "pending" for row in rows), "pending_rule_evidence")
    directory, state = read_state(root)
    junit = fixed_file(directory, "pytest-results.xml")
    coverage_path = project_path(root, "coverage.json")
    now = time.time_ns()
    for path in (junit, coverage_path):
        require(path.is_file() and state["started_ns"] - CLOCK_SKEW_NS <= path.stat().st_mtime_ns <= now + CLOCK_SKEW_NS,
                "stale_or_future_report")
    validate_coverage(root, coverage_path)
    cases = junit_cases(junit, state)
    result = []
    for row in rows:
        count = 0
        for selector in row["tests"]:
            matches = cases.get(selector_key(selector), [])
            require(matches and all(case["passed"] for case in matches), "missing_or_nonpassing_selector")
            count += len(matches)
        result.append({"id": row["id"], "tier": row["tier"], "applicability": row["applicability"],
                       "evidence": "automated_verified" if row["assessment"] == "automated" else
                       "exemption_recorded" if row["assessment"] == "exempt" else "human_review_recorded",
                       "passing_test_variants": count})
    return {"schema_version": 1, "assessment": "custom-integration-engineering",
            "rule_count": len(result), "source_sha256": state["source_sha256"],
            "official_tier_awarded": False, "rules": result}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "junit-path", "verify"))
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "prepare":
            print(prepare())
        elif arguments.command == "junit-path":
            directory, _state = read_state(ROOT)
            print(fixed_file(directory, "pytest-results.xml"))
        else:
            print(json.dumps(verify(), indent=2, allow_nan=False))
    except (EvidenceError, OSError, UnicodeError) as error:
        code = str(error) if isinstance(error, EvidenceError) else "evidence_io_error"
        print("Quality evidence verification failed: " + code, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
