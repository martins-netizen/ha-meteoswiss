"""Exercise the 8.3.6b1 publisher against an isolated GitHub API."""

import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import publish_meteoswiss_836_beta as publisher
from test_release_835_stable_publisher import load_publisher as load_previous_publisher

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "f9abaa12018fb89fd6c31633eadf6a975019d596"
FIRST = "fbd46b71dd2009e98d295b263ca19e101855332d"
FIRST_TREE = "5574bb14feae7c56411c4f57c54ae9c49ae06c31"
HEAD, MERGE, PACKAGE_TREE = ("1" * 40, "2" * 40, "3" * 40)
SOURCE_TREE = "e958573cbae9bd8b5685a627645f9ff1477c73f8"
STABLE_COMMIT = "cc158cbdce07f015952275fba72e3c0160c63c80"
TAG = "8.3.6b1"
BRANCH = "release/" + TAG
REPO = "martins-netizen/ha-meteoswiss"
WEB = "https://github.com/" + REPO
PREFIX = "custom_components/meteoswiss/"
NOTES = "docs/RELEASE_" + TAG + ".md"
# Keep historical component bytes independent of future changes to the integration.
STABLE_MANIFEST = b'''{
  "domain": "meteoswiss",
  "name": "MeteoSwiss",
  "after_dependencies": [
    "recorder"
  ],
  "codeowners": [
    "@martins-netizen"
  ],
  "config_flow": true,
  "documentation": "https://github.com/martins-netizen/ha-meteoswiss",
  "integration_type": "service",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/martins-netizen/ha-meteoswiss/issues",
  "requirements": [],
  "version": "8.3.5"
}
'''
STABLE_VERSION = (
    b'"""Version information for MeteoSwiss integration."""\n'
    b'from __future__ import annotations\n'
    b'\n'
    b'__version__ = "8.3.5"\n'
)
NOTES_LINKS = {
    "WIND_STATISTICS_MIGRATION.md": "docs/WIND_STATISTICS_MIGRATION.md",
    "UPGRADING_8.3.5.md": "docs/UPGRADING_8.3.5.md",
    "../DEVELOPMENT.md": "DEVELOPMENT.md",
    "ACCEPTANCE_8.3.6b1.md": "docs/ACCEPTANCE_8.3.6b1.md",
    "RELEASE_EVIDENCE_8.3.6b1.md": "docs/RELEASE_EVIDENCE_8.3.6b1.md",
}
LABEL = "MeteoSwiss 8.3.6b1"
PR_QUERY = "/pulls?state=all&base=development&head=martins-netizen%3Arelease%2F8.3.6b1&per_page=100"
HISTORY = "/releases?per_page=100"
REFS = "/git/matching-refs/tags/"
RUNS = "/commits/" + MERGE + "/check-runs?per_page=100"
MERGE_INFO = "/git/commits/" + MERGE
LATEST = "/releases/latest"
TARGET = "/releases/tags/" + TAG
PACKAGE_PATHS = {
    "CHANGELOG.md", "README.md", "ROADMAP.md", "docs/NEXT_RELEASE_PLAN.md",
    "docs/RELEASE_READINESS.md", "docs/PUBLISHING.md", NOTES,
    "docs/ACCEPTANCE_8.3.6b1.md", "docs/RELEASE_EVIDENCE_8.3.6b1.md",
    "scripts/publish_meteoswiss_836_beta.py", "scripts/release_meteoswiss_836_beta_v1.15.sh",
    "tests/test_release_836b1.py",
}


class GitHub:
    """Read-only by default. The single release POST updates the in-memory refs."""

    def __init__(self):
        self.posts = []
        self.after_post = lambda: None
        self.data = {}
        account = {"login": "martins-netizen", "id": 299523863}
        repo = {"id": 1333898084, "full_name": REPO, "owner": account,
                "archived": False, "private": False, "permissions": {"push": True},
                "default_branch": "development"}
        pull = {"number": 148, "html_url": WEB + "/pull/148", "user": account,
                "title": "Prepare the 8.3.6b1 prerelease", "state": "closed",
                "draft": False, "merged": True, "merged_at": "2026-11-20T12:00:00Z",
                "merge_commit_sha": MERGE, "commits": 2,
                "base": {"ref": "development", "repo": repo, "sha": SOURCE},
                "head": {"ref": BRANCH, "repo": repo, "sha": HEAD}}
        commit = {"tree": {"sha": PACKAGE_TREE}, "parents": [{"sha": SOURCE}],
                  "author": {"name": "martins-netizen",
                             "email": "299523863+martins-netizen@users.noreply.github.com"},
                  "committer": {"name": "GitHub", "email": "noreply@github.com"},
                  "verification": {"verified": True, "reason": "valid"}}
        self.data.update({
            "user": account, "": repo, PR_QUERY: [deepcopy(pull)], "/pulls/148": pull,
            "/branches/development": {"name": "development", "protected": True, "commit": {"sha": MERGE}},
            MERGE_INFO: {**deepcopy(commit), "sha": MERGE},
            "/git/commits/" + FIRST: {"sha": FIRST, "tree": {"sha": FIRST_TREE}, "parents": [{"sha": SOURCE}]},
            "/git/commits/" + HEAD: {**deepcopy(commit), "sha": HEAD, "parents": [{"sha": FIRST}],
                                     "committer": dict(commit["author"])},
            "/commits/" + MERGE + "/status?per_page=100": {
                "sha": MERGE, "state": "pending", "total_count": 0, "statuses": []},
        })
        checks = {"tests": 15368, "HA 2026.11.0": 15368, "HA 2026.11.2": 15368,
                  "HACS validation": 15368, "Analyze Python": 15368, "hassfest": 15368,
                  "Universal test locks": 15368, "Test dependency advisories": 15368,
                  "SonarCloud Code Analysis": 12526}
        self.data[RUNS] = {
            "total_count": len(checks), "check_runs": [
                {"id": i, "name": name, "app": {"id": app}, "status": "completed",
                 "conclusion": "success", "head_sha": MERGE} for i, (name, app) in enumerate(checks.items(), 1)
            ],
        }
        old = load_previous_publisher()
        tags = {**old.PRESERVED_TAGS, "8.3.5": STABLE_COMMIT}
        ids = {**old.PRESERVED_RELEASE_IDS, "8.3.5": 450993306}
        self.data[REFS] = [self.ref(name, sha) for name, sha in tags.items()]
        self.data[HISTORY] = [
            {"tag_name": tag, "id": rid, "name": tag, "body": "Published " + tag,
             "draft": False, "prerelease": "b" in tag, "html_url": WEB + "/releases/tag/" + tag,
             "assets": [{"id": rid + 100, "name": "archived", "size": 9,
                         "digest": "sha256:" + "a" * 64, "download_count": 7}],
             "reactions": {"total_count": 2, "+1": 2}}
            for tag, rid in ids.items()
        ]
        self.data[LATEST] = deepcopy(self.data[HISTORY][-1])

        shared = [self.file(PREFIX + name, b"unchanged") for name in
                  ["stations_map.py", *(f"module_{i}.py" for i in range(49))]]
        shared.append(self.file("requirements_test.txt", b"locked"))
        shared.extend(self.file(path, b"unchanged") for path in NOTES_LINKS.values() if path not in PACKAGE_PATHS)
        source = shared.copy()
        package = shared.copy()
        for name, original in [("manifest.json", STABLE_MANIFEST), ("version.py", STABLE_VERSION)]:
            source.append(self.file(PREFIX + name, original))
            package.append(self.file(PREFIX + name, original.replace(b"8.3.5", TAG.encode())))
        for path in sorted(PACKAGE_PATHS):
            payload = b"packaged"
            if path == NOTES:
                payload = (ROOT / NOTES).read_bytes()
            if path in {"CHANGELOG.md", "README.md", "ROADMAP.md", "docs/PUBLISHING.md",
                        "docs/NEXT_RELEASE_PLAN.md", "docs/RELEASE_READINESS.md"}:
                source.append(self.file(path, b"previous release guidance"))
            package.append(self.file(path, payload))
        self.package = package
        for sha, tree in [(SOURCE_TREE, source), (PACKAGE_TREE, package)]:
            self.data["/git/trees/" + sha + "?recursive=1"] = {
                "sha": sha, "tree": tree, "truncated": False,
            }

    def file(self, path, payload):
        sha = hashlib.sha256(payload).hexdigest()[:40]  # Opaque IDs for the fake GitHub tree.
        self.data["/git/blobs/" + sha] = {
            "sha": sha, "size": len(payload), "encoding": "base64",
            "content": base64.b64encode(payload).decode(),
        }
        return {"path": path, "sha": sha, "mode": "100644", "type": "blob"}

    @staticmethod
    def ref(tag, sha):
        return {"ref": "refs/tags/" + tag, "object": {"sha": sha, "type": "commit"}}

    def api(self, path, *, method="GET", body=None, missing_ok=False):
        if method == "GET":
            if missing_ok and path == TARGET and TARGET not in self.data:
                return None
            return deepcopy(self.data[path])
        assert (method, path) == ("POST", "/releases")
        self.posts.append(deepcopy(body))
        self.data[REFS].append(self.ref(TAG, body["target_commitish"]))
        self.data[TARGET] = {
            **body, "id": 500000001, "html_url": WEB + "/releases/tag/" + TAG,
            "author": deepcopy(self.data["user"]), "assets": [],
            "published_at": "2026-11-20T12:01:00Z",
        }
        self.data[HISTORY].append(self.data[TARGET])
        self.after_post()
        return deepcopy(self.data[TARGET])


@pytest.fixture
def github(monkeypatch):
    fixture = GitHub()
    monkeypatch.setattr(publisher, "api", fixture.api)
    return fixture


def test_check_publish_and_rerun_use_only_one_explicit_prerelease_post(github):
    before = deepcopy(github.data[HISTORY])
    refs = deepcopy(github.data[REFS])
    assert publisher.publish(MERGE)["status"] == "ready_to_publish"
    assert not github.posts
    assert publisher.publish(MERGE, allow_write=True)["status"] == "published_and_verified"
    assert publisher.publish(MERGE, allow_write=True)["status"] == "already_published_and_verified"
    body = (ROOT / NOTES).read_text(encoding="utf-8").split("\n\n", 1)[1]
    for relative, path in NOTES_LINKS.items():
        body = body.replace(f"]({relative})", f"]({WEB}/blob/{MERGE}/{path})")
    assert github.posts == [{
        "tag_name": TAG, "target_commitish": MERGE, "name": LABEL, "draft": False,
        "body": body,
        "prerelease": True, "make_latest": "false", "generate_release_notes": False,
    }]
    assert len(before) == len(refs) == 24
    assert github.data[HISTORY][:-1] == before and github.data[REFS][:-1] == refs
    assert github.data[LATEST]["id"] == 450993306


@pytest.mark.parametrize(("endpoint", "path", "value"), [
    (PR_QUERY, [], []),
    (PR_QUERY, [0, "number"], 149),
    ("/pulls/148", ["state"], "open"),
    ("/pulls/148", ["commits"], 1),
    ("/pulls/148", ["merge_commit_sha"], HEAD),
    ("/pulls/148", ["title"], "An unrelated package"),
    ("/pulls/148", ["head", "ref"], "release/unreviewed"),
    ("/pulls/148", ["head", "repo", "id"], 123),
    ("/pulls/148", ["user", "id"], 123),
    ("/pulls/148", ["base", "sha"], HEAD),
    (MERGE_INFO, ["parents"], [{"sha": SOURCE}, {"sha": HEAD}]),
    (MERGE_INFO, ["parents"], [{"sha": FIRST}]),
    (MERGE_INFO, ["verification", "verified"], False),
    ("/git/commits/" + FIRST, ["parents"], [{"sha": HEAD}]),
    ("/git/commits/" + HEAD, ["parents"], [{"sha": SOURCE}]),
    ("/git/commits/" + HEAD, ["author", "email"], "other@users.noreply.github.com"),
    ("/git/commits/" + HEAD, ["committer", "name"], "GitHub"),
    ("/git/commits/" + HEAD, ["tree", "sha"], SOURCE_TREE),
    ("/branches/development", ["protected"], False),
    ("/git/trees/" + PACKAGE_TREE + "?recursive=1", ["truncated"], True),
    (RUNS, ["check_runs", 0, "conclusion"], "failure"),
    (RUNS, ["check_runs", 0, "app", "id"], 1),
    (HISTORY, [0, "id"], 1),
    (REFS, [0, "object", "sha"], HEAD),
    (REFS, [0, "object", "type"], "tag"),
    (LATEST, ["id"], 1),
])
def test_mismatched_provenance_or_inventory_stops_before_post(github, endpoint, path, value):
    record = github.data
    *parents, field = [endpoint, *path]
    for key in parents:
        record = record[key]
    record[field] = value
    with pytest.raises(publisher.PublicationError):
        publisher.publish(MERGE, allow_write=True)
    assert not github.posts


@pytest.mark.parametrize(("path", "payload"), [
    (PREFIX + "stations_map.py", b"unreviewed implementation"),
    (PREFIX + "version.py", b'__version__ = "8.3.6b1"\nunrelated_change = True\n'),
    (PREFIX + "manifest.json", b'{"domain":"meteoswiss","version":"8.3.6b1","requirements":["x"]}'),
    ("requirements_test.txt", b"unreviewed dependencies"),
    (NOTES, b"# Different release\n\nThis community fork builds on upstream.\n"),
])
def test_unreviewed_blob_is_never_published(github, path, payload):
    index = next(i for i, entry in enumerate(github.package) if entry["path"] == path)
    github.package[index] = github.file(path, payload)
    with pytest.raises(publisher.PublicationError):
        publisher.publish(MERGE, allow_write=True)
    assert not github.posts


@pytest.mark.parametrize(("tree_sha", "path"), [
    (SOURCE_TREE, PREFIX + "manifest.json"), (PACKAGE_TREE, PREFIX + "manifest.json"),
    (SOURCE_TREE, PREFIX + "version.py"), (PACKAGE_TREE, PREFIX + "version.py"),
    (PACKAGE_TREE, NOTES),
])
def test_same_length_tampering_with_unchanged_blob_id_cannot_publish(github, tree_sha, path):
    tree = github.data["/git/trees/" + tree_sha + "?recursive=1"]["tree"]
    sha = next(row["sha"] for row in tree if row["path"] == path)
    blob = github.data["/git/blobs/" + sha]
    data = base64.b64decode(blob["content"])
    blob["content"] = base64.b64encode(data.replace(b"MeteoSwiss", b"MeteoSwizz", 1)).decode()
    with pytest.raises(publisher.PublicationError, match="reviewed bytes"):
        publisher.publish(MERGE, allow_write=True)
    assert not github.posts


def test_ambiguous_post_can_be_verified_without_recreating_release(github):
    def lost_response():
        raise TimeoutError("Connection closed after GitHub accepted the request")

    github.after_post = lost_response
    with pytest.raises((publisher.PublicationError, TimeoutError)):
        publisher.publish(MERGE, allow_write=True)
    assert publisher.publish(MERGE)["status"] == "already_published_and_verified"
    assert len(github.posts) == 1


@pytest.mark.parametrize(("field", "value"), [
    ("id", 321), ("size", 44), ("digest", "sha256:" + "b" * 64), ("body", "Edited notes"),
])
def test_changed_historical_asset_or_notes_during_publish_is_detected(github, field, value):
    def edit():
        release = github.data[HISTORY][0]
        target = release if field == "body" else release["assets"][0]
        target[field] = value

    github.after_post = edit
    with pytest.raises(publisher.PublicationError):
        publisher.publish(MERGE, allow_write=True)
    assert len(github.posts) == 1


def test_downloads_and_reactions_can_change_between_release_reads(github):
    old = github.data[HISTORY][0]

    def record_activity(release):
        release["assets"][0]["download_count"] += 1
        release["reactions"]["+1"] += 1
        release["reactions"]["total_count"] += 1

    github.after_post = lambda: record_activity(old)
    assert publisher.publish(MERGE, allow_write=True)["status"] == "published_and_verified"
    listed = github.data[HISTORY][-1]
    listed["reactions"] = deepcopy(old["reactions"])
    by_tag = github.data[TARGET] = deepcopy(listed)
    by_tag["reactions"]["+1"] += 1
    by_tag["reactions"]["total_count"] += 1
    assert publisher.publish(MERGE)["status"] == "already_published_and_verified"
    assert len(github.posts) == 1


def test_only_existing_publication_can_be_verified_after_development_advances(github):
    branch = github.data["/branches/development"]["commit"]
    branch["sha"] = "4" * 40
    for write in (False, True):
        with pytest.raises(publisher.PublicationError):
            publisher.publish(MERGE, allow_write=write)
    assert not github.posts
    branch["sha"] = MERGE
    publisher.publish(MERGE, allow_write=True)
    branch["sha"] = "4" * 40
    for write in (False, True):
        assert publisher.publish(MERGE, allow_write=write)["status"] == "already_published_and_verified"
    assert len(github.posts) == 1


@pytest.mark.parametrize(("key", "value"), [
    ("body", "Unexpected release notes."),
    ("assets", [{"id": 421, "name": "other.zip", "size": 20, "digest": "sha256:" + "b" * 64}]),
    ("author", {"login": "martins-netizen", "id": 123}),
    ("author", {"login": "another-owner", "id": 299523863}),
])
def test_mismatched_existing_prerelease_is_never_accepted_or_updated(github, key, value):
    publisher.publish(MERGE, allow_write=True)
    github.data[TARGET][key] = value
    for write in (False, True):
        with pytest.raises(publisher.PublicationError):
            publisher.publish(MERGE, allow_write=write)
    assert len(github.posts) == 1


def test_shell_check_reads_fake_github_and_rejects_short_commit_before_requests(github, tmp_path):
    script = ROOT / "scripts/release_meteoswiss_836_beta_v1.15.sh"
    home = tmp_path / "home"
    home.mkdir()
    (tmp_path / "python3").symlink_to(sys.executable)
    (tmp_path / "api.json").write_text(json.dumps(github.data))
    calls = tmp_path / "reads"
    gh = tmp_path / "gh"
    gh.write_text(f"""#!{sys.executable}
import json, sys
from pathlib import Path
root = Path(__file__).parent
args = sys.argv[1:]
assert args[0] == "api" and args[args.index("--method") + 1] == "GET"
resource = next(arg for arg in args if arg == "user" or arg.startswith("repos/"))
path = resource.removeprefix("repos/{REPO}")
data = json.loads((root / "api.json").read_text())
with (root / "reads").open("a") as log:
    print(path, file=log)
if "--include" in args or "-i" in args:
    print("HTTP/2", 200 if path in data else 404, "\\r\\n")
if path not in data:
    assert path == "{TARGET}"
    print("gh: Not Found (HTTP 404)", file=sys.stderr)
    sys.exit(1)
print(json.dumps(data[path]))
""")
    gh.chmod(0o700)
    env = {"HOME": str(home), "PATH": str(tmp_path) + ":/usr/bin:/bin"}

    def invoke(*args):
        return subprocess.run(["/bin/bash", str(script), *args], cwd=tmp_path, env=env,
                              capture_output=True, text=True, check=False, timeout=30)

    assert invoke("--publish", "0123456").returncode != 0
    assert invoke("--p", MERGE).returncode != 0
    assert not calls.exists()
    result = invoke("--check", MERGE)
    assert result.returncode == 0, result.stdout + result.stderr
    assert {PR_QUERY, RUNS, LATEST, TARGET} <= set(calls.read_text().splitlines())
    receipt, = (home / "Downloads/HA/05_Diagnose").glob("*.json")
    saved = json.loads(receipt.read_text())
    assert saved["status"] == "ready_to_publish" and saved["mode"] == "--check"
