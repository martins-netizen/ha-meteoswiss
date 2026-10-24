"""Verify the candidate-only publication boundary without live GitHub writes."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(
    params=[
        ("v1.0", "8.2.0", "8.3.0b1", "4c8169206fdcb8688a438c16a93f867a633a344f"),
        ("v1.1", "8.3.0b1", "8.3.0b2", "781ba3a41fafc2e8dd5bc5f867f55c646c4a2412"),
        ("v1.2", "8.3.0b2", "8.3.0b3", "97338f68038eab80c75c2028c9deb5e24ad552e6"),
    ],
    ids=["beta1", "beta2", "beta3"],
)
def publisher(request):
    """Exercise each historical/follow-up boundary independently."""
    revision, source_version, tag, reviewed = request.param
    script = ROOT / f"scripts/publish_meteoswiss_830_beta_{revision}.sh"
    payload = (
        script.read_text().split("<<'PY_PUBLISH'\n", 1)[1].split("\nPY_PUBLISH", 1)[0]
    )
    module = types.ModuleType("release_830_publisher_under_test")
    exec(compile(payload, str(script), "exec"), module.__dict__)
    assert module.TAG == tag and module.REVIEWED_SOURCE == reviewed
    module._script = script
    module._source_version = source_version
    return module


COMMIT = "a" * 40
OTHER = "b" * 40
PREFIX = "custom_components/meteoswiss/"


def blob(text):
    content = text.encode() if isinstance(text, str) else text
    return hashlib.sha1(
        b"blob " + str(len(content)).encode() + b"\0" + content
    ).hexdigest()


class GitHub:
    """Public response fixtures; the only simulated write creates this beta."""

    def __init__(self, publisher):
        self.publisher = publisher
        files = [
            p
            for p in (ROOT / PREFIX).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        ]
        self.candidate = {
            str(p.relative_to(ROOT)): ("100644", blob(p.read_bytes())) for p in files
        }
        self.source = copy.deepcopy(self.candidate)
        self.manifest = {
            **json.loads((ROOT / PREFIX / "manifest.json").read_text()),
            "version": self.publisher.TAG,
        }
        self.source_manifest = {
            **self.manifest,
            "version": self.publisher._source_version,
        }
        root_version = json.loads((ROOT / PREFIX / "manifest.json").read_text())[
            "version"
        ]
        self.version = (
            (ROOT / PREFIX / "version.py")
            .read_text()
            .replace(f'"{root_version}"', f'"{self.publisher.TAG}"')
        )
        self.source_version = self.version.replace(
            f'"{self.publisher.TAG}"', f'"{self.publisher._source_version}"'
        )
        self.hacs = json.loads((ROOT / "hacs.json").read_text())
        self.source_hacs = dict(self.hacs)
        self.notes = (ROOT / f"docs/RELEASE_{self.publisher.TAG}.md").read_text()
        self.rows = [
            dict(
                id=i + 1,
                name=name,
                status="completed",
                conclusion="success",
                head_sha=COMMIT,
                app={"id": 12526 if name.startswith("Sonar") else 15368},
            )
            for i, name in enumerate(sorted(self.publisher.REQUIRED_CHECKS))
        ]
        self.calls = []
        self.branch = COMMIT
        self.protected = True
        self.branch_reads = 0
        self.move = False
        self.tag = None
        self.tags = dict(self.publisher.PRESERVED_TAGS)
        self.release = None
        self.stable = dict(
            id=self.publisher.STABLE_RELEASE_ID,
            tag_name="8.2.0",
            draft=False,
            prerelease=False,
        )
        self.fail_after_post = False
        self.change_stable_after_post = False
        self.truncated = False
        self.extra_entry = None
        self.repo = dict(
            full_name=self.publisher.REPOSITORY,
            default_branch="development",
            private=False,
            archived=False,
            permissions={"push": True},
        )
        self.source[".github/workflows/ci.yml"] = ("100644", "c" * 40)
        self.candidate[".github/workflows/ci.yml"] = ("100644", "c" * 40)

    def __call__(self, path, *, method="GET", body=None, missing_ok=False):
        self.calls.append((method, path, copy.deepcopy(body)))
        suffix = path.removeprefix(self.publisher.API_PREFIX)
        if method == "POST":
            assert suffix == "/releases"
            assert body["tag_name"] == self.publisher.TAG
            assert body["target_commitish"] == COMMIT
            assert body["prerelease"] is True and body["draft"] is False
            assert body["make_latest"] == "false"
            self.tag = COMMIT
            self.release = dict(
                id=7,
                tag_name=self.publisher.TAG,
                draft=False,
                prerelease=True,
                html_url=self.publisher.RELEASE_URL,
                body=body["body"],
                published_at="2026-10-24T08:00:00Z",
            )
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
            sha = OTHER if self.move and self.branch_reads > 1 else self.branch
            return {"commit": {"sha": sha}, "protected": self.protected}
        if suffix.startswith("/git/trees/"):
            files = (
                self.source
                if suffix.endswith(self.publisher.REVIEWED_SOURCE + "?recursive=1")
                else self.candidate
            )
            rows = [
                dict(path=k, mode=v[0], sha=v[1], type="blob") for k, v in files.items()
            ]
            if self.extra_entry:
                rows.append(self.extra_entry)
            return {"truncated": self.truncated, "tree": rows}
        if "/check-runs?" in suffix:
            return {
                "total_count": len(self.rows),
                "check_runs": copy.deepcopy(self.rows),
            }
        if suffix.endswith("/status?per_page=100"):
            return {"total_count": 0, "statuses": []}
        if suffix.startswith("/git/ref/tags/"):
            tag = suffix.rsplit("/", 1)[1]
            sha = self.tag if tag == self.publisher.TAG else self.tags.get(tag)
            return {"object": {"type": "commit", "sha": sha}} if sha else None
        if suffix == "/releases/latest":
            return copy.deepcopy(self.stable)
        if suffix == "/releases/tags/" + self.publisher.TAG:
            return copy.deepcopy(self.release)
        if suffix.startswith("/contents/"):
            source = suffix.endswith("?ref=" + self.publisher.REVIEWED_SOURCE)
            if "manifest.json?" in suffix:
                text = json.dumps(self.source_manifest if source else self.manifest)
            elif "version.py?" in suffix:
                text = self.source_version if source else self.version
            elif "hacs.json?" in suffix:
                text = json.dumps(self.source_hacs if source else self.hacs)
            else:
                text = self.notes
            return {
                "encoding": "base64",
                "size": len(text),
                "content": base64.b64encode(text.encode()).decode(),
            }
        raise AssertionError(path)

    def writes(self):
        return [call for call in self.calls if call[0] != "GET"]


def run(fake, *, write=False):
    with patch.object(fake.publisher, "api", fake):
        return fake.publisher.publish(
            COMMIT, {"release_write_attempted": False}, allow_write=write
        )


def test_default_preflight_is_read_only_and_preserves_stable(publisher):
    fake = GitHub(publisher)
    result = run(fake)
    assert result["status"] == "ready_to_publish"
    assert result["component_files_identical"] == 36
    assert result["version_files_checked"] == 2
    assert result["country"] == "CH" and result["existing_tags_unchanged"]
    assert result["stable_release_id"] == publisher.STABLE_RELEASE_ID
    assert not fake.writes() and fake.tag is None


def test_publish_creates_exact_beta_once_and_resolves_note_links(publisher):
    fake = GitHub(publisher)
    result = run(fake, write=True)
    assert result["status"] == "published_and_verified"
    assert result["release_id"] == 7
    assert len(fake.writes()) == 1
    body = fake.writes()[0][2]["body"]
    assert "Prepared candidate" not in body
    assert f"/blob/{COMMIT}/docs/ACCEPTANCE_{publisher.TAG}.md" in body
    fake.calls.clear()
    assert run(fake, write=True)["status"] == "already_published_and_verified"
    assert fake.writes() == []


@pytest.mark.parametrize(
    "path,value",
    [
        (PREFIX + "weather.py", ("100644", OTHER)),
        (PREFIX + "extra.py", ("100644", OTHER)),
        (PREFIX + "weather.py", None),
        (".github/workflows/ci.yml", ("100644", OTHER)),
        (PREFIX + "version.py", ("120000", OTHER)),
    ],
)
def test_unreviewed_file_changes_stop_before_write(publisher, path, value):
    fake = GitHub(publisher)
    if value is None:
        fake.candidate.pop(path)
    else:
        fake.candidate[path] = value
    with pytest.raises(publisher.PublicationError):
        run(fake, write=True)
    assert not fake.writes()


@pytest.mark.parametrize(
    "area,key,value",
    [
        ("manifest", "requirements", ["unreviewed"]),
        ("source_manifest", "version", "8.2.0b2"),
        ("hacs", "hide_default_branch", False),
        ("source_hacs", "country", None),
        ("repo", "private", True),
        ("stable", "id", 1),
    ],
)
def test_unreviewed_metadata_stops_before_write(publisher, area, key, value):
    fake = GitHub(publisher)
    getattr(fake, area)[key] = value
    with pytest.raises(publisher.PublicationError):
        run(fake, write=True)
    assert not fake.writes()


@pytest.mark.parametrize(
    "attribute,value",
    [
        ("truncated", True),
        (
            "extra_entry",
            dict(path=PREFIX + "external", type="commit", mode="160000", sha=OTHER),
        ),
        ("branch", OTHER),
        ("protected", False),
        ("move", True),
        ("tag", OTHER),
    ],
)
def test_invalid_provenance_stops_before_write(publisher, attribute, value):
    fake = GitHub(publisher)
    setattr(fake, attribute, value)
    with pytest.raises(publisher.PublicationError):
        run(fake, write=True)
    assert not fake.writes()


def test_added_code_in_version_module_stops_before_write(publisher):
    fake = GitHub(publisher)
    fake.version += "unreviewed = True\n"
    with pytest.raises(publisher.PublicationError):
        run(fake, write=True)
    assert not fake.writes()


def test_all_immutable_old_tags_are_checked(publisher):
    for tag in publisher.PRESERVED_TAGS:
        fake = GitHub(publisher)
        fake.tags[tag] = OTHER
        with pytest.raises(publisher.PublicationError):
            run(fake, write=True)
        assert not fake.writes(), tag


@pytest.mark.parametrize(
    "change", ["missing", "pending", "failure", "wrong_app", "wrong_head", "sonar_app"]
)
def test_checks_require_successful_exact_head_and_expected_apps(publisher, change):
    fake = GitHub(publisher)
    if change == "missing":
        fake.rows.pop()
    elif change == "pending":
        fake.rows[0].update(status="in_progress", conclusion=None)
    elif change == "failure":
        fake.rows[0]["conclusion"] = "failure"
    elif change == "wrong_app":
        fake.rows[0]["app"] = {"id": 1}
    elif change == "wrong_head":
        fake.rows[0]["head_sha"] = OTHER
    elif change == "sonar_app":
        next(row for row in fake.rows if row["name"].startswith("Sonar"))["app"] = {
            "id": 15368
        }
    with pytest.raises(publisher.PublicationError):
        run(fake, write=True)
    assert not fake.writes()


@pytest.mark.parametrize(
    "field,value",
    [("draft", True), ("prerelease", False), ("body", "different"), ("id", None)],
)
def test_conflicting_existing_release_is_never_rewritten(publisher, field, value):
    fake = GitHub(publisher)
    run(fake, write=True)
    fake.calls.clear()
    fake.release[field] = value
    with pytest.raises(publisher.PublicationError):
        run(fake, write=True)
    assert not fake.writes()


def test_uncertain_write_records_receipt_and_retry_does_not_post_again(
    publisher, tmp_path
):
    fake = GitHub(publisher)
    fake.fail_after_post = True
    path = tmp_path / "receipt.json"
    with patch.object(publisher, "api", fake):
        assert publisher.main(COMMIT, path, "--publish") == 1
    receipt = json.loads(path.read_text())
    assert receipt["status"] == "publication_result_unconfirmed"
    assert receipt["release_write_attempted"] is True
    assert receipt["ha_writes_performed"] is False
    assert receipt["focused_ha_ui_acceptance"] == f"pending_{publisher.TAG}"
    fake.fail_after_post = False
    fake.calls.clear()
    assert run(fake, write=True)["status"] == "already_published_and_verified"
    assert not fake.writes()


def test_changed_latest_stable_after_post_is_not_reported_as_success(
    publisher, tmp_path
):
    fake = GitHub(publisher)
    fake.change_stable_after_post = True
    path = tmp_path / "receipt.json"
    with patch.object(publisher, "api", fake):
        assert publisher.main(COMMIT, path, "--publish") == 1
    assert json.loads(path.read_text())["status"] == "publication_result_unconfirmed"


def test_unusable_receipt_path_stops_before_any_api_access(publisher, tmp_path):
    with patch.object(publisher, "api") as api:
        with pytest.raises(OSError):
            publisher.main(COMMIT, tmp_path / "missing" / "receipt.json", "--publish")
    api.assert_not_called()


def test_check_receipt_is_explicitly_read_only(publisher, tmp_path):
    fake = GitHub(publisher)
    path = tmp_path / "receipt.json"
    with patch.object(publisher, "api", fake):
        assert publisher.main(COMMIT, path) == 0
    receipt = json.loads(path.read_text())
    assert receipt["status"] == "ready_to_publish"
    assert receipt["release_write_attempted"] is False
    assert not fake.writes()


def test_api_boundary_rejects_other_writes_and_hides_gh_stderr(publisher):
    for path, method in [
        (publisher.API_PREFIX + "/git/refs", "POST"),
        ("repos/other/repo", "GET"),
    ]:
        with patch.object(publisher.subprocess, "run") as process:
            with pytest.raises(publisher.PublicationError):
                publisher.api(path, method=method)
            process.assert_not_called()
    with patch.object(
        publisher.subprocess,
        "run",
        return_value=types.SimpleNamespace(
            returncode=1, stderr="private_marker token=secret", stdout=""
        ),
    ) as process:
        with pytest.raises(publisher.PublicationError) as caught:
            publisher.api(publisher.API_PREFIX)
    assert "private_marker" not in str(caught.value)
    assert process.call_args.args[0][2:4] == ["--hostname", "github.com"]


def test_standalone_read_only_shell_works_without_a_checkout(publisher, tmp_path):
    """Run the whole shell/Python/log chain with an executable fake gh."""
    fake = GitHub(publisher)
    run(fake)
    responses = {
        path: fake(path) for method, path, _ in list(fake.calls) if method == "GET"
    }
    fixtures = tmp_path / "responses.json"
    fixtures.write_text(json.dumps(responses))
    calls = tmp_path / "calls.log"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python3").symlink_to(sys.executable)
    gh = bin_dir / "gh"
    gh.write_text(
        f"#!{sys.executable}\n"
        "import json,sys\nfrom pathlib import Path\n"
        f"responses=json.loads(Path({str(fixtures)!r}).read_text())\n"
        "assert sys.argv[1:4] == ['api','--hostname','github.com']\n"
        "assert sys.argv[sys.argv.index('--method')+1] == 'GET'\n"
        f"with Path({str(calls)!r}).open('a') as log: log.write(sys.argv[-1]+'\\n')\n"
        "value=responses[sys.argv[-1]]\n"
        "if value is None:\n print('HTTP 404',file=sys.stderr)\n sys.exit(1)\n"
        "print(json.dumps(value))\n"
    )
    gh.chmod(0o700)
    diagnostics = tmp_path / "diagnostics"
    script = tmp_path / publisher._script.name
    # Redirect only the diagnostic directory; do not repurpose HOME.
    source = publisher._script.read_text()
    line = 'DIAG_DIR="${HOME}/Downloads/HA/05_Diagnose"'
    assert source.count(line) == 1
    script.write_text(source.replace(line, f'DIAG_DIR="{diagnostics}"'))
    result = subprocess.run(
        ["/bin/bash", str(script), "--check", COMMIT],
        cwd=tmp_path,
        env={**os.environ, "PATH": f"{bin_dir}:/usr/bin:/bin"},
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    receipts = list(diagnostics.glob("*.json"))
    assert len(receipts) == 1
    receipt = json.loads(receipts[0].read_text())
    assert receipt["status"] == "ready_to_publish"
    assert receipt["release_write_attempted"] is False
    assert receipt["component_files_identical"] == 36
    assert len(list(diagnostics.glob("*.log"))) == 1
    assert calls.read_text().splitlines()


@pytest.mark.parametrize(
    "args,status",
    [
        (["--help"], 0),
        ([], 2),
        (["--publish"], 2),
        (["--check", "a" * 40], 1),
        (["--publish", "a" * 40], 1),
        (["--unknown", "a" * 40], 2),
    ],
)
def test_shell_guard_runs_before_any_external_command(publisher, args, status):
    result = subprocess.run(
        ["/bin/bash", str(publisher._script), *args],
        env={"PATH": "/nonexistent"},
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == status
    assert "unbound variable" not in result.stderr


def test_profiles_preserve_the_preceding_published_betas(publisher):
    if publisher.TAG in {"8.3.0b2", "8.3.0b3"}:
        assert (
            publisher.PRESERVED_TAGS["8.3.0b1"]
            == "a6b9df9f57dec3e93c8f698133cdb0e7e4c3e937"
        )
    else:
        assert "8.3.0b1" not in publisher.PRESERVED_TAGS
    if publisher.TAG == "8.3.0b3":
        assert publisher.PRESERVED_TAGS["8.3.0b2"] == "50b5711213bd8a1706871718a283b9fcb4db257d"
    else:
        assert "8.3.0b2" not in publisher.PRESERVED_TAGS
    assert publisher.STABLE_RELEASE_ID == 420392277
