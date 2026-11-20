"""Exercise promotion of the accepted 8.3.6b1 release through the GitHub API."""
from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from scripts import publish_meteoswiss_836_stable as stable
from test_release_836b1 import GitHub as BetaGitHub
from test_release_836b1 import NOTES_LINKS as BETA_LINKS
from test_release_836b1 import STABLE_MANIFEST, STABLE_VERSION

ROOT = Path(__file__).resolve().parents[1]
WEB = "https://github.com/martins-netizen/ha-meteoswiss"
BASE = "ea278684dfccb6770e32cad1cdf51e7e08fb7614"
BASE_TREE = "6430dd70c4b8c98655640021ecac980a7f127a46"
BETA = "8.3.6b1"
BETA_COMMIT = "ceec7a8b23a5669f20677ef67a87b31b2b523d5f"
BETA_TREE = "618ca49970a5d900d00922bf3428bd0e22852fe3"
BETA_ID = 452371818
TAG = "8.3.6"
HEAD, MERGE, TREE = "1" * 40, "2" * 40, "3" * 40
HISTORY, REFS, LATEST = "/releases?per_page=100", "/git/matching-refs/tags/", "/releases/latest"
TARGET = "/releases/tags/" + TAG
BETA_TARGET = "/releases/tags/" + BETA
PR_NUMBER = 271  # Hypothetical GitHub-assigned number.
PR = f"/pulls/{PR_NUMBER}"
PR_QUERY = "/pulls?state=all&base=development&head=martins-netizen%3Arelease%2F8.3.6&per_page=100"
MERGE_INFO = "/git/commits/" + MERGE
NOTES = "docs/RELEASE_8.3.6.md"
PREFIX = "custom_components/meteoswiss/"
NOTES_LINKS = {name: "docs/" + name for name in (
    "WIND_STATISTICS_MIGRATION.md", "UPGRADING_8.3.5.md", "ACCEPTANCE_8.3.6.md")}


def release_notes(path, commit, links):
    text = (ROOT / path).read_text(encoding="utf-8").split("\n\n", 1)[1]
    for relative, target in links.items():
        text = text.replace(f"]({relative})", f"]({WEB}/blob/{commit}/{target})")
    return text


class StableGitHub(BetaGitHub):
    """A release POST creates one tag and one release; promotion is observable independently."""

    def __init__(self):
        super().__init__()
        self.calls = []
        self.promote = True
        beta = {
            "id": BETA_ID, "tag_name": BETA, "name": "MeteoSwiss " + BETA,
            "target_commitish": BETA_COMMIT, "body": release_notes("docs/RELEASE_8.3.6b1.md", BETA_COMMIT, BETA_LINKS),
            "draft": False, "prerelease": True, "immutable": True, "assets": [], "author": deepcopy(self.data["user"]),
            "html_url": WEB + "/releases/tag/" + BETA, "published_at": "2026-11-20T07:08:05Z",
        }
        self.data[HISTORY].append(beta)
        self.data[REFS].append(self.ref(BETA, BETA_COMMIT))
        self.data[BETA_TARGET] = beta
        self.data["/releases/" + str(BETA_ID)] = beta
        self.data["/git/ref/tags/" + BETA] = self.ref(BETA, BETA_COMMIT)
        pull = deepcopy(self.data["/pulls/148"])
        pull.update(number=PR_NUMBER, html_url=f"{WEB}/pull/{PR_NUMBER}", commits=1,
                    title="Prepare the 8.3.6 stable release")
        pull["base"]["sha"] = BASE
        pull["head"]["ref"] = "release/" + TAG
        self.data[PR_QUERY] = [deepcopy(pull)]
        self.data[PR] = pull
        for sha in (HEAD, MERGE):
            self.data["/git/commits/" + sha]["parents"] = [{"sha": BASE}]

    def api(self, path, *, method="GET", body=None, missing_ok=False):
        self.calls.append((method, path))
        if method == "GET":
            if path == TARGET and missing_ok and path not in self.data:
                return None
            return deepcopy(self.data[path])
        assert (method, path) == ("POST", "/releases")
        assert TARGET not in self.data
        self.posts.append(deepcopy(body))
        release = {
            **deepcopy(body), "id": 500000002, "html_url": WEB + "/releases/tag/" + TAG,
            "author": deepcopy(self.data["user"]), "assets": [], "published_at": "2026-11-21T12:00:00Z",
        }
        self.data[TARGET] = release
        self.data[HISTORY].append(release)
        self.data[REFS].append(self.ref(TAG, body["target_commitish"]))
        self.data["/git/ref/tags/" + TAG] = self.ref(TAG, body["target_commitish"])
        self.data["/releases/" + str(release["id"])] = release
        if self.promote:
            self.data[LATEST] = deepcopy(release)
        self.after_post()
        return deepcopy(release)

    def file(self, path, payload):
        sha = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
        self.data["/git/blobs/" + sha] = {"sha": sha, "size": len(payload), "encoding": "base64",
                                         "content": base64.b64encode(payload).decode()}
        return {"path": path, "sha": sha, "mode": "100644", "type": "blob"}


@pytest.fixture
def api(monkeypatch):
    fixture = StableGitHub()
    monkeypatch.setattr(stable, "api", fixture.api)
    monkeypatch.setattr(stable.beta, "api", fixture.api)
    return fixture


@pytest.fixture
def expected_post():
    return {"tag_name": TAG, "target_commitish": MERGE, "name": "MeteoSwiss " + TAG,
            "body": release_notes(NOTES, MERGE, NOTES_LINKS),
            "prerelease": False, "draft": False, "make_latest": "true", "generate_release_notes": False}


@pytest.fixture
def github(api):
    beta = {row["path"]: row for row in api.package}
    source = dict(beta)
    package = dict(source)
    texts = {
        PREFIX + "manifest.json": STABLE_MANIFEST.replace(b"8.3.5", b"8.3.6"),
        PREFIX + "version.py": STABLE_VERSION.replace(b"8.3.5", b"8.3.6"),
        NOTES: (ROOT / NOTES).read_bytes(),
    }
    for path in stable.PACKAGE_PATHS:
        package[path] = api.file(path, texts.get(path, b"stable package"))
    for sha, files in ((BETA_TREE, beta), (BASE_TREE, source), (TREE, package)):
        api.data["/git/trees/" + sha + "?recursive=1"] = {
            "sha": sha, "truncated": False, "tree": deepcopy(list(files.values())),
        }
    return api


def test_stable_notes_and_version_only_runtime_changes(github):
    assert stable.package_notes(MERGE, TREE) == release_notes(NOTES, MERGE, NOTES_LINKS)


@pytest.mark.parametrize("tree_sha,path", [
    (TREE, PREFIX + "stations_map.py"), (BASE_TREE, PREFIX + "stations_map.py"),
    (TREE, PREFIX + "manifest.json"), (TREE, PREFIX + "version.py"), (TREE, NOTES),
])
def test_content_outside_reviewed_promotion_cannot_be_published(github, tree_sha, path):
    rows = github.data["/git/trees/" + tree_sha + "?recursive=1"]["tree"]
    row = next(item for item in rows if item["path"] == path)
    row.update(github.file(path, b"unexpected change"))
    with pytest.raises(stable.beta.PublicationError):
        stable.publish(MERGE, allow_write=True)
    assert github.posts == []


def test_check_publish_and_resume(github, expected_post):
    old_releases = deepcopy(github.data[HISTORY])
    old_tags = deepcopy(github.data[REFS])
    accepted = deepcopy(github.data[BETA_TARGET])
    assert len(old_releases) == len(old_tags) == 25
    assert (github.data[LATEST]["tag_name"], github.data[LATEST]["id"]) == ("8.3.5", 450993306)

    assert stable.publish(MERGE)["status"] == "ready_to_publish"
    assert github.posts == []
    assert stable.publish(MERGE, allow_write=True)["status"] == "published_and_verified"
    assert github.posts == [expected_post]

    assert len(github.data[HISTORY]) == len(github.data[REFS]) == 26
    assert github.data[HISTORY][:-1] == old_releases
    assert github.data[REFS][:-1] == old_tags
    assert github.data[BETA_TARGET] == accepted
    assert github.data[LATEST]["id"] == github.data[TARGET]["id"]
    assert stable.publish(MERGE, allow_write=True)["status"] == "already_published_and_verified"
    assert stable.publish(MERGE)["status"] == "already_published_and_verified"
    assert github.posts == [expected_post]


@pytest.mark.parametrize("endpoint,path,value", [
    (PR_QUERY, [], []), (PR, ["title"], "Other package"),
    (PR, ["merged"], False), (PR, ["head", "ref"], "release/other"),
    (PR, ["merge_commit_sha"], HEAD), (PR, ["base", "sha"], "f" * 40),
    (MERGE_INFO, ["verification", "verified"], False),
    (MERGE_INFO, ["parents"], [{"sha": BETA_COMMIT}]),
    ("/git/commits/" + HEAD, ["tree", "sha"], "4" * 40),
    ("/branches/development", ["protected"], False),
    ("/branches/development", ["commit", "sha"], "f" * 40),
])
def test_unreviewed_package_cannot_be_promoted(github, endpoint, path, value):
    if path:
        node = github.data[endpoint]
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
    else:
        github.data[endpoint] = value
    with pytest.raises(stable.beta.PublicationError):
        stable.publish(MERGE, allow_write=True)
    assert github.posts == []


@pytest.mark.parametrize("field,value", [
    ("body", "edited"), ("immutable", False), ("id", 7), ("draft", True), ("prerelease", False),
    ("target_commitish", "f" * 40), ("assets", [{"id": 1, "name": "extra"}]),
])
def test_changed_accepted_prerelease_blocks_promotion(github, field, value):
    github.data[BETA_TARGET][field] = value
    with pytest.raises(stable.beta.PublicationError):
        stable.publish(MERGE, allow_write=True)
    assert github.posts == []


def test_wrong_latest_before_publish(github):
    github.data[LATEST] = deepcopy(github.data[BETA_TARGET])
    with pytest.raises(stable.beta.PublicationError):
        stable.publish(MERGE, allow_write=True)
    assert github.posts == []


def test_retained_historical_release_and_beta_tag_targets_are_checked(github):
    tag = next(ref for ref in github.data[REFS] if ref["ref"] == "refs/tags/" + BETA)
    tag["object"]["sha"] = "f" * 40
    with pytest.raises(stable.beta.PublicationError):
        stable.publish(MERGE, allow_write=True)
    tag["object"]["sha"] = BETA_COMMIT
    github.data[HISTORY][0]["id"] = 8
    with pytest.raises(stable.beta.PublicationError):
        stable.publish(MERGE, allow_write=True)
    assert github.posts == []


def test_unpromoted_release_never_gets_patched_or_recreated(github, expected_post):
    github.promote = False
    with pytest.raises(stable.beta.PublicationError):
        stable.publish(MERGE, allow_write=True)
    assert github.posts == [expected_post]
    with pytest.raises(stable.beta.PublicationError):
        stable.publish(MERGE, allow_write=True)
    assert github.posts == [expected_post]
    assert github.data[LATEST]["tag_name"] == "8.3.5"


@pytest.mark.parametrize("field,value", [
    ("body", "unrelated release"), ("target_commitish", "f" * 40), ("prerelease", True), ("draft", True),
])
def test_existing_release_is_never_overwritten(github, expected_post, field, value):
    stable.publish(MERGE, allow_write=True)
    github.data[TARGET][field] = value
    github.data[LATEST] = deepcopy(github.data[TARGET])
    with pytest.raises(stable.beta.PublicationError):
        stable.publish(MERGE, allow_write=True)
    assert github.posts == [expected_post]
    assert github.data[TARGET][field] == value


def test_historical_asset_changed_during_creation_is_detected(github, expected_post):
    def change_history():
        github.data[HISTORY][0]["assets"][0]["size"] += 1

    github.after_post = change_history
    with pytest.raises(stable.beta.PublicationError):
        stable.publish(MERGE, allow_write=True)
    assert github.posts == [expected_post]


def test_lost_response_recovers_from_confirmed_stable_without_another_post(github, expected_post):
    def lose_response():
        raise TimeoutError("Connection dropped after creation")

    github.after_post = lose_response
    with pytest.raises(stable.beta.PublicationError):
        stable.publish(MERGE, allow_write=True)
    assert github.posts == [expected_post]
    assert stable.publish(MERGE)["status"] == "already_published_and_verified"
    assert stable.publish(MERGE, allow_write=True)["status"] == "already_published_and_verified"
    assert github.posts == [expected_post]
