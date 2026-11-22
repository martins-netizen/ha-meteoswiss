"""Independent b7 publication profile; old publishers and profiles stay frozen."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import types
from unittest.mock import patch

import pytest

from release_835_fixture import component_tree

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/publish_meteoswiss_835_beta_v1.14.sh"
COMMIT = "a" * 40
OTHER = "b" * 40
SOURCE = "c" * 40
PREFIX = "custom_components/meteoswiss/"


def load_publisher():
    payload = SCRIPT.read_text().split("<<'PY_PUBLISH'\n", 1)[1].split("\nPY_PUBLISH", 1)[0]
    module = types.ModuleType("release_835b7_publisher_under_test")
    exec(compile(payload, str(SCRIPT), "exec"), module.__dict__)
    return module


@pytest.fixture
def publisher():
    module = load_publisher()
    # This isolated GitHub fixture is not an approved live source merge.
    module.REVIEWED_SOURCE = SOURCE
    return module


def blob(value):
    data = value.encode() if isinstance(value, str) else value
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


class GitHub:
    """Public native API-shaped fixtures; only one release POST is simulated."""

    def __init__(self, publisher):
        self.publisher = publisher
        self.calls = []
        self.account = {"login": "martins-netizen", "id": 299523863}
        self.repo = {
            "id": 1333898084, "full_name": publisher.REPOSITORY,
            "default_branch": "development", "private": False, "archived": False,
            "permissions": {"push": True},
            "owner": {"login": "martins-netizen", "id": 299523863},
        }
        self.approved_merge = {
            "sha": COMMIT, "parents": [{"sha": SOURCE}],
            "verification": {"verified": True, "reason": "valid"},
            "author": {"name": "martins-netizen", "email": "299523863+martins-netizen@users.noreply.github.com"},
            "committer": {"name": "GitHub", "email": "noreply@github.com"},
        }
        self.branch = COMMIT
        self.protected = True
        self.move = False
        self.branch_reads = 0
        self.source = component_tree(blob)
        assert len(self.source) == 52
        for path in [
            *ROOT.glob("requirements*"),
            ROOT / "docs/quality_rules.json",
            *(ROOT / name for name in ("pyproject.toml", "pytest.ini", ".coveragerc") if (ROOT / name).is_file()),
            *ROOT.glob("scripts/check_*.py"),
            *(path for path in (ROOT / ".github").rglob("*") if path.is_file()),
        ]:
            self.source[str(path.relative_to(ROOT))] = ("100644", blob(path.read_bytes()))
        frozen = [
            *ROOT.glob("scripts/publish_*.sh"),
            *ROOT.glob("scripts/veroeffentliche_*.sh"),
            *ROOT.glob("tests/test_*publisher*.py"),
            *(path for path in (ROOT / "tests/fixtures").glob("*") if "release" in path.name),
        ]
        for path in frozen:
            if path in {SCRIPT, Path(__file__)}:
                continue
            self.source[str(path.relative_to(ROOT))] = ("100644", blob(path.read_bytes()))
        self.candidate = copy.deepcopy(self.source)
        for path in (SCRIPT, Path(__file__)):
            self.candidate[str(path.relative_to(ROOT))] = ("100644", blob(path.read_bytes()))
        self.source_manifest = {"domain": "meteoswiss", "version": "8.3.5b6"}
        self.manifest = {**self.source_manifest, "version": publisher.TAG}
        self.source_version = '__version__ = "8.3.5b6"\n'
        self.version = '__version__ = "' + publisher.TAG + '"\n'
        self.source_hacs = {"name": "MeteoSwiss", "homeassistant": "2026.11.0", "country": "CH", "hide_default_branch": True}
        self.hacs = copy.deepcopy(self.source_hacs)
        self.notes = (
            publisher.NOTES_HEADING + "\nPrepared candidate.\n\n"
            "This community fork builds on upstream.\n"
            "[Acceptance](ACCEPTANCE_8.3.5b7.md)\n"
        )
        self.rows = [
            {"id": index + 1, "name": name, "status": "completed", "conclusion": "success",
             "head_sha": COMMIT, "app": {"id": 12526 if name.startswith("Sonar") else 57789 if name == "CodeQL" else 15368}}
            for index, name in enumerate(sorted(publisher.REQUIRED_CHECKS))
        ]
        self.statuses = []
        self.check_total = None
        self.status_total = None
        self.check_response = None
        self.status_response = None
        self.tags = dict(publisher.PRESERVED_TAGS)
        self.tag = None
        self.release = None
        self.stable = {"id": 437853341, "tag_name": "8.3.4", "draft": False, "prerelease": False}
        self.prior_records = [
            {"id": release_id, "tag_name": name, "name": name, "body": "Frozen " + name + " notes.",
             "draft": False, "prerelease": "b" in name,
             "assets": [{"id": release_id + 100, "name": "historical-asset", "size": 7}],
             "author": {"login": "martins-netizen"}, "published_at": "2026-11-01T00:00:00Z"}
            for name, release_id in publisher.PRESERVED_RELEASE_IDS.items()
        ]
        self.fail_after_post = False
        self.change_prior_after_post = False
        self.change_stable_after_post = False
        self.truncated = False
        self.extra_entry = None

    def tree(self, files):
        rows = [{"path": path, "mode": value[0], "sha": value[1], "type": "blob"} for path, value in files.items()]
        if self.extra_entry:
            rows.append(self.extra_entry)
        return {"truncated": self.truncated, "tree": rows}

    def __call__(self, path, *, method="GET", body=None, missing_ok=False):
        self.calls.append((method, path, copy.deepcopy(body)))
        if path == "user":
            assert method == "GET"
            return copy.deepcopy(self.account)
        suffix = path.removeprefix(self.publisher.API_PREFIX)
        if method == "POST":
            assert suffix == "/releases"
            assert body == {
                "tag_name": self.publisher.TAG, "target_commitish": COMMIT,
                "name": self.publisher.TITLE, "body": self.body(), "draft": False,
                "prerelease": True, "make_latest": "false", "generate_release_notes": False,
            }
            self.tag = COMMIT
            self.release = {
                "id": 7, "tag_name": self.publisher.TAG, "name": self.publisher.TITLE,
                "draft": False, "prerelease": True, "html_url": self.publisher.RELEASE_URL,
                "body": body["body"], "published_at": "2026-11-18T18:00:00Z",
            }
            if self.change_stable_after_post:
                self.stable["id"] = 1
            if self.fail_after_post:
                raise subprocess.TimeoutExpired("gh", 90)
            return copy.deepcopy(self.release)
        assert method == "GET"
        if suffix == "":
            return copy.deepcopy(self.repo)
        if suffix == "/branches/development":
            self.branch_reads += 1
            return {"commit": {"sha": OTHER if self.move and self.branch_reads > 1 else self.branch}, "protected": self.protected}
        if suffix == "/git/commits/" + COMMIT:
            return copy.deepcopy(self.approved_merge)
        if suffix.startswith("/git/trees/"):
            return self.tree(self.source if suffix.endswith(SOURCE + "?recursive=1") else self.candidate)
        if "/check-runs?" in suffix:
            if self.check_response is not None:
                return copy.deepcopy(self.check_response)
            return {"total_count": len(self.rows) if self.check_total is None else self.check_total, "check_runs": copy.deepcopy(self.rows)}
        if suffix.endswith("/status?per_page=100"):
            if self.status_response is not None:
                return copy.deepcopy(self.status_response)
            return {"sha": COMMIT, "state": "success", "total_count": len(self.statuses) if self.status_total is None else self.status_total, "statuses": copy.deepcopy(self.statuses)}
        if suffix.startswith("/git/ref/tags/"):
            name = suffix.rsplit("/", 1)[1]
            commit = self.tag if name == self.publisher.TAG else self.tags.get(name)
            return {"object": {"type": "commit", "sha": commit}} if commit else None
        if suffix == "/releases/latest":
            return copy.deepcopy(self.stable)
        if suffix == "/releases?per_page=100":
            rows = copy.deepcopy(self.prior_records)
            if self.release is not None:
                rows.append(copy.deepcopy(self.release))
                if self.change_prior_after_post:
                    rows[0]["body"] = "Changed old body"
            return rows
        if suffix == "/releases/tags/" + self.publisher.TAG:
            return copy.deepcopy(self.release)
        if suffix.startswith("/contents/"):
            source = suffix.endswith("?ref=" + SOURCE)
            if "manifest.json?" in suffix:
                text = json.dumps(self.source_manifest if source else self.manifest)
            elif "version.py?" in suffix:
                text = self.source_version if source else self.version
            elif "hacs.json?" in suffix:
                text = json.dumps(self.source_hacs if source else self.hacs)
            else:
                text = self.notes
            return {"encoding": "base64", "size": len(text), "content": base64.b64encode(text.encode()).decode()}
        raise AssertionError(path)

    def body(self):
        return ("This community fork builds on upstream.\n"
                "[Acceptance](https://github.com/" + self.publisher.REPOSITORY + "/blob/" + COMMIT + "/docs/ACCEPTANCE_8.3.5b7.md)\n")

    def writes(self):
        return [call for call in self.calls if call[0] != "GET"]


def run(fake, *, write=False):
    with patch.object(fake.publisher, "api", fake):
        return fake.publisher.publish(COMMIT, {"release_write_attempted": False}, allow_write=write)


def assert_stops(fake):
    with pytest.raises(fake.publisher.PublicationError):
        run(fake, write=True)
    assert not fake.writes()


def test_b7_profile_has_exact_new_boundary_and_preserves_twenty_two_old_records(publisher):
    assert publisher.TAG == "8.3.5b7"
    assert publisher.STABLE_RELEASE_ID == 437853341
    assert publisher.PRESERVED_TAGS["8.3.5b6"] == "cc4f494694609af28fd27c46c475a8270d3858ab"
    assert publisher.PRESERVED_TAGS["8.3.5b5"] == "ba8a15aa282aa7b67d16c83cca6f99e38ee2bf4b"
    assert publisher.PRESERVED_RELEASE_IDS["8.3.5b6"] == 449276745
    assert publisher.PRESERVED_RELEASE_IDS["8.3.5b5"] == 447678651
    assert len(publisher.PRESERVED_TAGS) == len(publisher.PRESERVED_RELEASE_IDS) == 22
    assert "HA 2026.11.0" in publisher.REQUIRED_CHECKS
    assert "HA 2026.11.2" in publisher.REQUIRED_CHECKS
    assert "HA 2026.11.1" not in publisher.REQUIRED_CHECKS
    assert len(publisher.REQUIRED_CHECKS) == 9
    assert publisher.REQUIRED_CHECKS == {
        "tests", "HA 2026.11.0", "HA 2026.11.2", "hassfest",
        "Analyze Python", "HACS validation", "SonarCloud Code Analysis",
        "Universal test locks", "Test dependency advisories",
    }


def test_profile_is_frozen_to_the_actual_verified_gold_source():
    publisher = load_publisher()
    assert publisher.REVIEWED_SOURCE == "8887597ebf8567b5969ee70b8f9dd6f261603aec"


def test_shell_and_python_source_freeze_state_agree():
    publisher = load_publisher()
    flag = re.search(r"^PUBLISHER_SOURCE_FROZEN=([01])$", SCRIPT.read_text(), re.MULTILINE)
    assert flag is not None
    frozen = isinstance(publisher.REVIEWED_SOURCE, str) and re.fullmatch(r"[0-9a-f]{40}", publisher.REVIEWED_SOURCE)
    assert flag[1] == ("1" if frozen else "0")


def test_read_only_preview_retains_exact_runtime_policy_history_and_stable(publisher):
    fake = GitHub(publisher)
    result = run(fake)
    assert result["status"] == "ready_to_publish"
    assert result["component_files_identical"] == 50 and result["version_files_checked"] == 2
    assert result["preserved_release_records_verified"] == 22
    assert result["stable_release_id"] == 437853341
    assert not fake.writes() and fake.tag is None


def test_explicit_publish_is_one_exact_post_and_matching_rerun_is_read_only(publisher):
    fake = GitHub(publisher)
    before = copy.deepcopy(fake.prior_records)
    assert run(fake, write=True)["status"] == "published_and_verified"
    assert len(fake.writes()) == 1 and fake.writes()[0][1] == publisher.API_PREFIX + "/releases"
    assert fake.prior_records == before
    fake.calls.clear()
    assert run(fake, write=True)["status"] == "already_published_and_verified"
    assert not fake.writes()


@pytest.mark.parametrize("area,key,value", [
    ("account", "login", "other"), ("account", "id", 1),
    ("repo", "id", 1), ("repo", "full_name", "other/repo"),
    ("repo", "owner", {"login": "other", "id": 299523863}),
    ("repo", "owner", {"login": "martins-netizen", "id": 1}),
    ("repo", "default_branch", "main"),
    ("repo", "private", True), ("repo", "archived", True), ("repo", "permissions", {"push": False}),
    ("approved_merge", "sha", OTHER), ("approved_merge", "parents", []),
    ("approved_merge", "parents", [{"sha": OTHER}]),
    ("approved_merge", "parents", [{"sha": SOURCE}, {"sha": OTHER}]),
    ("approved_merge", "verification", {"verified": False, "reason": "unsigned"}),
    ("approved_merge", "verification", {"verified": True, "reason": "unknown_key"}),
    ("approved_merge", "author", {"name": "Private Person", "email": "private@example.invalid"}),
    ("approved_merge", "committer", {"name": "martins-netizen", "email": "private@example.invalid"}),
])
def test_identity_signature_and_exact_direct_parent_must_match(publisher, area, key, value):
    fake = GitHub(publisher)
    getattr(fake, area)[key] = value
    assert_stops(fake)


@pytest.mark.parametrize("attribute,value", [("branch", OTHER), ("protected", False), ("move", True), ("tag", OTHER), ("truncated", True)])
def test_changed_branch_tag_or_incomplete_tree_is_never_written(publisher, attribute, value):
    fake = GitHub(publisher)
    setattr(fake, attribute, value)
    assert_stops(fake)


@pytest.mark.parametrize("path,value", [
    (PREFIX + "precipitation.py", ("100644", OTHER)),
    (PREFIX + "hgt_ogd_manager.py", ("100644", OTHER)),
    (PREFIX + "extra.py", ("100644", OTHER)),
    (PREFIX + "weather.py", None),
    (PREFIX + "version.py", ("120000", OTHER)),
    (".github/workflows/ci.yml", ("100644", OTHER)),
    ("requirements_test.txt", ("100644", OTHER)),
    ("scripts/check_quality_coverage.py", ("100644", OTHER)),
    ("scripts/check_quality_rules.py", ("100644", OTHER)),
    ("docs/quality_rules.json", ("100644", OTHER)),
    ("docs/quality_rules.json", None),
    ("docs/quality_rules.json", ("120000", OTHER)),
])
def test_unreviewed_runtime_or_policy_changes_stop_before_write(publisher, path, value):
    fake = GitHub(publisher)
    if value is None:
        fake.candidate.pop(path)
    else:
        fake.candidate[path] = value
    assert_stops(fake)


@pytest.mark.parametrize("change", ["added", "missing-both", "source-symlink"])
def test_known_gold_source_requires_its_regular_evidence_policy(publisher, change):
    fake = GitHub(publisher)
    path = "docs/quality_rules.json"
    if change == "source-symlink":
        fake.source[path] = ("120000", fake.source[path][1])
    else:
        fake.source.pop(path)
        if change == "missing-both":
            fake.candidate.pop(path)
    assert_stops(fake)


@pytest.mark.parametrize("change", ["manifest", "source-version", "version-code", "hacs", "source-hacs"])
def test_only_the_two_exact_version_fields_may_change(publisher, change):
    fake = GitHub(publisher)
    if change == "manifest": fake.manifest["requirements"] = ["unreviewed"]
    elif change == "source-version": fake.source_manifest["version"] = "8.3.5b4"
    elif change == "version-code": fake.version += "extra_code = True\n"
    elif change == "hacs": fake.hacs["hide_default_branch"] = False
    else: fake.source_hacs["homeassistant"] = fake.hacs["homeassistant"] = "2026.8.3"
    assert_stops(fake)


@pytest.mark.parametrize("change", ["missing", "old-ha", "pending", "failed", "skipped", "wrong-app", "wrong-head", "sonar-app", "extra-failed"])
def test_checks_require_new_ha_fixture_success_and_exact_app_head(publisher, change):
    fake = GitHub(publisher)
    if change == "missing": fake.rows.pop()
    elif change == "old-ha": next(row for row in fake.rows if row["name"] == "HA 2026.11.2")["name"] = "HA 2026.11.1"
    elif change == "pending": fake.rows[0].update(status="in_progress", conclusion=None)
    elif change == "failed": fake.rows[0]["conclusion"] = "failure"
    elif change == "skipped": fake.rows[0]["conclusion"] = "skipped"
    elif change == "wrong-app": fake.rows[0]["app"] = {"id": 1}
    elif change == "wrong-head": fake.rows[0]["head_sha"] = OTHER
    elif change == "sonar-app": next(row for row in fake.rows if row["name"].startswith("Sonar"))["app"] = {"id": 15368}
    else: fake.rows.append({"id": 1000, "name": "extra", "status": "completed", "conclusion": "failure", "head_sha": COMMIT, "app": {"id": 15368}})
    assert_stops(fake)


@pytest.mark.parametrize("change", ["wrong-app", "wrong-head", "pending", "failed"])
def test_codeql_aggregate_is_verified_when_emitted(publisher, change):
    fake = GitHub(publisher)
    row = {"id": 1000, "name": "CodeQL", "status": "completed", "conclusion": "success", "head_sha": COMMIT, "app": {"id": 57789}}
    if change == "wrong-app": row["app"]["id"] = 15368
    elif change == "wrong-head": row["head_sha"] = OTHER
    elif change == "pending": row.update(status="in_progress", conclusion=None)
    else: row["conclusion"] = "failure"
    fake.rows.append(row)
    assert_stops(fake)


def test_successful_codeql_aggregate_is_accepted_and_other_statuses_must_succeed(publisher):
    fake = GitHub(publisher)
    fake.rows.append({"id": 1000, "name": "CodeQL", "status": "completed", "conclusion": "success", "head_sha": COMMIT, "app": {"id": 57789}})
    assert "CodeQL" in run(fake)["checks_successful"]
    fake.calls.clear()
    fake.statuses = [{"state": "pending"}]
    assert_stops(fake)


@pytest.mark.parametrize("change", ["wrong-app", "wrong-head", "pending", "failed"])
def test_optional_dependency_graph_is_app_bound_and_must_succeed(publisher, change):
    fake = GitHub(publisher)
    row = {"id": 1000, "name": "update-pip-graph", "status": "completed", "conclusion": "success", "head_sha": COMMIT, "app": {"id": 15368}}
    if change == "wrong-app": row["app"]["id"] = 57789
    elif change == "wrong-head": row["head_sha"] = OTHER
    elif change == "pending": row.update(status="in_progress", conclusion=None)
    else: row["conclusion"] = "failure"
    fake.rows.append(row)
    assert_stops(fake)


def test_green_optional_graph_and_codeql_are_accepted_together(publisher):
    fake = GitHub(publisher)
    for index, (name, app) in enumerate([("CodeQL", 57789), ("update-pip-graph", 15368)], 1000):
        fake.rows.append({"id": index, "name": name, "status": "completed", "conclusion": "success", "head_sha": COMMIT, "app": {"id": app}})
    result = run(fake)
    assert set(result["checks_successful"]) == publisher.REQUIRED_CHECKS | {"CodeQL", "update-pip-graph"}
    assert not fake.writes()


@pytest.mark.parametrize("response", [
    [], {}, {"total_count": 0, "check_runs": {}},
    {"total_count": True, "check_runs": []},
    {"total_count": 1, "check_runs": []},
    {"total_count": 101, "check_runs": []},
])
def test_incomplete_or_malformed_check_inventory_stops(publisher, response):
    fake = GitHub(publisher)
    fake.check_response = response
    assert_stops(fake)


@pytest.mark.parametrize("change", ["shape", "missing", "count", "bool-count", "wrong-head", "failed-state", "unknown-state"])
def test_combined_status_inventory_is_complete_and_belongs_to_exact_head(publisher, change):
    fake = GitHub(publisher)
    response = {"sha": COMMIT, "state": "success", "total_count": 0, "statuses": []}
    if change == "shape": response = []
    elif change == "missing": response = {}
    elif change == "count": response["total_count"] = 1
    elif change == "bool-count": response["total_count"] = True
    elif change == "wrong-head": response["sha"] = OTHER
    elif change == "failed-state": response["state"] = "failure"
    else: response["state"] = "unknown"
    fake.status_response = response
    assert_stops(fake)


def test_even_a_green_unexpected_check_must_belong_to_the_package_head(publisher):
    fake = GitHub(publisher)
    fake.rows.append({"id": 1000, "name": "other", "status": "completed", "conclusion": "success", "head_sha": OTHER, "app": {"id": 15368}})
    assert_stops(fake)


def test_all_frozen_publishers_and_profile_blobs_are_preserved(publisher):
    baseline = GitHub(publisher)
    paths = [path for path in baseline.source if (
        path.startswith(("scripts/publish_", "scripts/veroeffentliche_")) and path.endswith(".sh")
        or path.startswith("tests/test_") and "publisher" in path
        or path.startswith("tests/fixtures/") and "release" in Path(path).name
    )]
    assert len(paths) >= 25
    for path in paths:
        fake = GitHub(publisher)
        fake.candidate[path] = ("100644", OTHER)
        assert_stops(fake)


def test_every_old_tag_is_immutable_including_b6(publisher):
    for name in publisher.PRESERVED_TAGS:
        fake = GitHub(publisher)
        fake.tags[name] = OTHER
        assert_stops(fake)


@pytest.mark.parametrize("change", ["missing", "duplicate", "wrong-id", "unexpected"])
def test_prior_inventory_requires_all_twenty_two_unique_release_identities(publisher, change):
    fake = GitHub(publisher)
    if change == "missing": fake.prior_records.pop()
    elif change == "duplicate": fake.prior_records.append(copy.deepcopy(fake.prior_records[0]))
    elif change == "wrong-id": fake.prior_records[0]["id"] = 1
    else: fake.prior_records.append({"tag_name": "unexpected", "id": 1})
    assert_stops(fake)


@pytest.mark.parametrize("field,value", [("draft", True), ("prerelease", False), ("body", "changed"), ("id", None)])
def test_conflicting_existing_b7_release_is_not_overwritten(publisher, field, value):
    fake = GitHub(publisher)
    run(fake, write=True)
    fake.calls.clear()
    fake.release[field] = value
    assert_stops(fake)


def test_prior_record_body_change_after_post_is_unconfirmed_without_overwrite(publisher):
    fake = GitHub(publisher)
    fake.change_prior_after_post = True
    with pytest.raises(publisher.PublicationError, match="release record changed"):
        run(fake, write=True)
    assert len(fake.writes()) == 1
    assert fake.writes()[0][1] == publisher.API_PREFIX + "/releases"


def test_uncertain_post_is_receipted_and_next_run_only_verifies(publisher, tmp_path):
    fake = GitHub(publisher)
    fake.fail_after_post = True
    receipt = tmp_path / "receipt.json"
    with patch.object(publisher, "api", fake):
        assert publisher.main(COMMIT, receipt, "--publish") == 1
    saved = json.loads(receipt.read_text())
    assert saved["status"] == "publication_result_unconfirmed"
    assert saved["release_write_attempted"] is True
    assert saved["ha_writes_performed"] is False
    assert saved["focused_ha_ui_acceptance"] == "pending_8.3.5b7"
    fake.fail_after_post = False
    fake.calls.clear()
    assert run(fake, write=True)["status"] == "already_published_and_verified"
    assert not fake.writes()


def test_latest_stable_change_after_post_remains_unconfirmed(publisher, tmp_path):
    fake = GitHub(publisher)
    fake.change_stable_after_post = True
    receipt = tmp_path / "receipt.json"
    with patch.object(publisher, "api", fake):
        assert publisher.main(COMMIT, receipt, "--publish") == 1
    assert json.loads(receipt.read_text())["status"] == "publication_result_unconfirmed"


def test_unfrozen_python_source_stops_before_api_access():
    publisher = load_publisher()
    publisher.REVIEWED_SOURCE = None
    with patch.object(publisher, "api") as api, pytest.raises(publisher.PublicationError):
        publisher.publish(COMMIT, {}, allow_write=True)
    api.assert_not_called()


def test_unfrozen_main_stops_before_report_path_access(tmp_path):
    publisher = load_publisher()
    publisher.REVIEWED_SOURCE = None
    report = tmp_path / "not-created" / "receipt.json"
    with patch.object(publisher, "api") as api, pytest.raises(publisher.PublicationError):
        publisher.main(COMMIT, report, "--publish")
    api.assert_not_called()
    assert not report.parent.exists()


def test_unfrozen_shell_stops_before_external_commands_or_receipt_io(tmp_path):
    source = SCRIPT.read_text()
    assert re.search(r"PUBLISHER_SOURCE_FROZEN=[01]", source)
    source = re.sub(r"PUBLISHER_SOURCE_FROZEN=[01]", "PUBLISHER_SOURCE_FROZEN=0", source, count=1)
    script = tmp_path / SCRIPT.name
    script.write_text(source)
    home = tmp_path / "home"
    home.mkdir()
    result = subprocess.run(["/bin/bash", str(script), "--publish", COMMIT],
                            env={"HOME": str(home), "PATH": "/nonexistent"}, text=True,
                            capture_output=True, timeout=5, check=False)
    assert result.returncode != 0
    assert not list(home.iterdir())
    assert "not frozen" in (result.stdout + result.stderr).lower()


def test_standalone_frozen_read_only_shell_uses_only_fake_gets(publisher, tmp_path):
    fake = GitHub(publisher)
    run(fake)
    responses = {path: fake(path) for method, path, _ in list(fake.calls) if method == "GET"}
    fixtures = tmp_path / "responses.json"
    fixtures.write_text(json.dumps(responses))
    calls = tmp_path / "calls.log"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python3").symlink_to(sys.executable)
    gh = bin_dir / "gh"
    gh.write_text(
        f"#!{sys.executable}\nimport json,sys\nfrom pathlib import Path\n"
        f"responses=json.loads(Path({str(fixtures)!r}).read_text())\n"
        "assert sys.argv[1:4]==['api','--hostname','github.com']\n"
        "assert sys.argv[sys.argv.index('--method')+1]=='GET'\n"
        f"with Path({str(calls)!r}).open('a') as log: log.write(sys.argv[-1]+'\\n')\n"
        "value=responses[sys.argv[-1]]\n"
        "if value is None:\n print('HTTP 404',file=sys.stderr)\n sys.exit(1)\n"
        "print(json.dumps(value))\n"
    )
    gh.chmod(0o700)
    diagnostics = tmp_path / "diagnostics"
    source = SCRIPT.read_text()
    source = re.sub(r"PUBLISHER_SOURCE_FROZEN=[01]", "PUBLISHER_SOURCE_FROZEN=1", source, count=1)
    source = re.sub(r"^REVIEWED_SOURCE = .*$", "REVIEWED_SOURCE = " + repr(SOURCE), source, count=1, flags=re.MULTILINE)
    line = 'DIAG_DIR="${HOME}/Downloads/HA/05_Diagnose"'
    assert source.count(line) == 1
    source = source.replace(line, f'DIAG_DIR="{diagnostics}"')
    script = tmp_path / SCRIPT.name
    script.write_text(source)
    result = subprocess.run(["/bin/bash", str(script), "--check", COMMIT], cwd=tmp_path,
                            env={**os.environ, "PATH": f"{bin_dir}:/usr/bin:/bin"},
                            text=True, capture_output=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    receipts = list(diagnostics.glob("*.json"))
    assert len(receipts) == 1
    saved = json.loads(receipts[0].read_text())
    assert saved["status"] == "ready_to_publish" and saved["release_write_attempted"] is False
    assert saved["component_files_identical"] == 50
    assert saved["preserved_release_records_verified"] == 22
    assert calls.read_text().splitlines()


def test_api_boundary_has_no_tag_force_or_overwrite_endpoint(publisher):
    for endpoint, method in [(publisher.API_PREFIX + "/git/refs", "POST"),
                             (publisher.API_PREFIX + "/releases/7", "PATCH"),
                             ("repos/other/repository", "GET")]:
        with patch.object(publisher.subprocess, "run") as process, pytest.raises(publisher.PublicationError):
            publisher.api(endpoint, method=method)
        process.assert_not_called()

