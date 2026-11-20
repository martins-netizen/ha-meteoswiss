"""Verify or publish the reviewed MeteoSwiss 8.3.6 stable package using GitHub CLI."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import posixpath
import re
import subprocess
import tempfile
from urllib.parse import urlencode


def load_beta_helpers():
    """Reuse the reviewed read-only tree, blob, branch, CI and inventory comparators."""
    path = Path(__file__).with_name("publish_meteoswiss_836_beta.py")
    if hashlib.sha256(path.read_bytes()).hexdigest() != "73220692eb07e7087c2e577218345cb919eeddeaa20d747dae9ae663bb82e570":
        raise RuntimeError("The 8.3.6b1 verification module has changed.")
    spec = importlib.util.spec_from_file_location("meteoswiss_836_beta", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("The 8.3.6b1 verification module could not be loaded.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


beta = load_beta_helpers()
require = beta.require
TAG = "8.3.6"
TITLE = "MeteoSwiss " + TAG
BRANCH = "release/" + TAG
PR_TITLE = "Prepare the 8.3.6 stable release"
SOURCE = "ea278684dfccb6770e32cad1cdf51e7e08fb7614"
SOURCE_TREE = "6430dd70c4b8c98655640021ecac980a7f127a46"
BETA_COMMIT = "ceec7a8b23a5669f20677ef67a87b31b2b523d5f"
BETA_TREE = "618ca49970a5d900d00922bf3428bd0e22852fe3"
BETA_ID = 452371818
BETA_BODY_SHA256 = "f7ec2012ab017fb6e1111b3ada24f9e8af1cd6424153863fbe57e2d7b82688f2"
PRIOR = {**beta.PRIOR, beta.TAG: (BETA_COMMIT, BETA_ID)}
NOTES = "docs/RELEASE_8.3.6.md"
NOTES_SHA256 = "a63a9f85e0c3cb43d7bb003e334c433358809bc5c4466b0422f55c6cce631b54"
VERSIONS = {
    beta.COMPONENT + "manifest.json": (beta.VERSIONS[beta.COMPONENT + "manifest.json"][2],
                                      "0ada6483b08358ddc1fa2f74edda0d8217ecb57dca89de2fdcc3e8cff7dbd152"),
    beta.COMPONENT + "version.py": (beta.VERSIONS[beta.COMPONENT + "version.py"][2],
                                   "a422c7255c1157a03194dc3588155e4c2572be07db53ed1018c2761bb10c60c8"),
}
PACKAGE_PATHS = set(VERSIONS) | {
    "CHANGELOG.md", "README.md", "ROADMAP.md", NOTES, "docs/ACCEPTANCE_8.3.6.md",
    "docs/RELEASE_EVIDENCE_8.3.6.md", "docs/NEXT_RELEASE_PLAN.md", "docs/PUBLISHING.md",
    "docs/RELEASE_READINESS.md", "scripts/publish_meteoswiss_836_stable.py", "tests/test_publish_836_stable.py",
}
PUBLIC_AUTHOR = (beta.OWNER, beta.OWNER_EMAIL)


def api(path, *, method="GET", body=None, missing_ok=False):
    if method == "GET":
        return beta.api(path, body=body, missing_ok=missing_ok)
    require(method == "POST" and path == "/releases" and not missing_ok and isinstance(body, dict)
            and set(body) == {"tag_name", "target_commitish", "name", "body", "draft", "prerelease",
                              "make_latest", "generate_release_notes"}
            and body["tag_name"] == TAG and body["name"] == TITLE and beta.is_sha(body["target_commitish"])
            and isinstance(body["body"], str) and body["body"] and body["draft"] is False
            and body["prerelease"] is False and body["make_latest"] == "true" and body["generate_release_notes"] is False,
            "Unexpected stable publication request.")
    result = subprocess.run(["gh", "api", "--hostname", "github.com", "--include", "--method", "POST",
                             "-H", "Accept: application/vnd.github+json", "repos/" + beta.REPOSITORY + path,
                             "--input", "-"], text=True, input=json.dumps(body), capture_output=True,
                            timeout=90, check=False)
    headers, separator, payload = result.stdout.partition("\n\n")
    require(result.returncode == 0 and separator and re.match(r"^HTTP/\S+ 201\b", headers),
            "GitHub did not confirm creation. Run --check for the same SHA.")
    return json.loads(payload)


def check_account():
    user, repo = api("user"), api("")
    require((user.get("id"), user.get("login")) == (beta.OWNER_ID, beta.OWNER)
            and (repo.get("id"), repo.get("full_name")) == (beta.REPO_ID, beta.REPOSITORY)
            and (repo["owner"].get("id"), repo["owner"].get("login")) == (beta.OWNER_ID, beta.OWNER)
            and repo.get("default_branch") == "development" and repo.get("archived") is False
            and repo.get("private") is False and repo["permissions"].get("push") is True,
            "Unexpected GitHub account, repository or permissions.")


def package_tree(commit):
    query = urlencode({"state": "all", "base": "development", "head": beta.OWNER + ":" + BRANCH, "per_page": 100})
    rows = api("/pulls?" + query)
    require(isinstance(rows, list) and len(rows) == 1 and type(rows[0].get("number")) is int,
            "Expected exactly one package PR.")
    number = rows[0]["number"]
    pr = api("/pulls/" + str(number))
    head = pr.get("head", {}).get("sha")
    require(pr.get("number") == number and pr.get("html_url") == beta.URL + "/pull/" + str(number)
            and pr.get("state") == "closed" and pr.get("merged") is True and pr.get("merged_at")
            and pr.get("title") == PR_TITLE and pr.get("merge_commit_sha") == commit
            and (pr["user"].get("login"), pr["user"].get("id")) == (beta.OWNER, beta.OWNER_ID)
            and all((pr[s]["repo"].get("full_name"), pr[s]["repo"].get("id")) == (beta.REPOSITORY, beta.REPO_ID)
                    for s in ("head", "base"))
            and pr["base"].get("ref") == "development" and pr["base"].get("sha") == SOURCE
            and pr["head"].get("ref") == BRANCH and beta.is_sha(head) and head != commit,
            "The approved SHA is not the merged package PR.")
    merged = api("/git/commits/" + commit)
    original = api("/git/commits/" + head)
    tree = merged.get("tree", {}).get("sha")
    require(merged.get("sha") == commit and [p.get("sha") for p in merged["parents"]] == [SOURCE]
            and merged["verification"].get("verified") is True and merged["verification"].get("reason") == "valid"
            and (merged["author"].get("name"), merged["author"].get("email")) == PUBLIC_AUTHOR
            and (merged["committer"].get("name"), merged["committer"].get("email")) == ("GitHub", "noreply@github.com")
            and beta.is_sha(tree) and tree != SOURCE_TREE and original.get("sha") == head and original["tree"].get("sha") == tree
            and all((original[role].get("name"), original[role].get("email")) == PUBLIC_AUTHOR
                    for role in ("author", "committer")), "Unexpected signed squash, PR head or public identity.")
    return tree


def package_notes(commit, tree):
    source, accepted, package = (beta.tree_files(t) for t in (SOURCE_TREE, BETA_TREE, tree))
    component = {path: row for path, row in accepted.items() if path.startswith(beta.COMPONENT)}
    require(len(component) == 52 and all(mode == "100644" for mode, _ in component.values())
            and component == {p: v for p, v in source.items() if p.startswith(beta.COMPONENT)},
            "The source runtime differs from the accepted 8.3.6b1 runtime.")
    changed = {p for p in source.keys() | package.keys() if source.get(p) != package.get(p)}
    require(changed == PACKAGE_PATHS and all(package.get(p, (None,))[0] == "100644" for p in changed),
            "Unexpected package files or Git modes.")
    for path, (before_hash, after_hash) in VERSIONS.items():
        before = beta.blob_text(source[path][1], before_hash)
        after = beta.blob_text(package[path][1], after_hash)
        require(before.count(beta.TAG) == 1 and after == before.replace(beta.TAG, TAG), "Unexpected version bytes.")
    notes = beta.blob_text(package[NOTES][1], NOTES_SHA256)
    marker = "\nThis community fork builds on "
    require(notes.startswith("# " + TITLE + "\n") and notes.count(marker) == 1, "Unexpected release notes.")
    body = notes[notes.index(marker) + 1:]

    def absolute_link(match):
        target = match[1]
        if target.startswith(("https://", "http://", "#")):
            return match[0]
        name, anchor, fragment = target.partition("#")
        path = posixpath.normpath(posixpath.join("docs", name))
        require(path in package and not path.startswith(("/", "../")) and ":" not in path, "Unknown release link.")
        return "](" + beta.URL + "/blob/" + commit + "/" + path + anchor + fragment + ")"

    return re.sub(r"\]\(([^)]+)\)", absolute_link, body)


def inventory(commit):
    refs = api("/git/matching-refs/tags/")
    rows = api("/releases?per_page=100")
    require(isinstance(refs, list) and isinstance(rows, list), "Tag or release inventory is missing.")
    tags = {}
    for row in refs:
        ref, obj = row.get("ref", ""), row.get("object", {})
        require(ref.startswith("refs/tags/") and obj.get("type") == "commit" and beta.is_sha(obj.get("sha"))
                and ref[10:] not in tags, "Unexpected tag.")
        tags[ref[10:]] = obj["sha"]
    releases = {r["tag_name"]: r for r in rows}
    require(len(releases) == len(rows) and releases.keys() - {TAG} == PRIOR.keys()
            and tags.keys() - {TAG} == PRIOR.keys(), "Unexpected historical release or tag inventory.")
    for name, (sha, release_id) in PRIOR.items():
        row = releases[name]
        require(tags[name] == sha and row.get("id") == release_id and row.get("draft") is False
                and row.get("prerelease") is ("b" in name), "Historical release changed: " + name)
    accepted = releases[beta.TAG]
    require(accepted.get("target_commitish") == BETA_COMMIT and accepted.get("immutable") is True
            and accepted.get("assets") == [] and accepted["author"].get("id") == beta.OWNER_ID
            and accepted.get("name") == beta.TITLE
            and hashlib.sha256(accepted["body"].encode()).hexdigest() == BETA_BODY_SHA256,
            "The accepted 8.3.6b1 prerelease differs.")
    require(tags.get(TAG, commit) == commit, "The stable tag points to a different commit.")
    release = api("/releases/tags/" + TAG, missing_ok=True)
    require(beta.release_contents(release) == beta.release_contents(releases.get(TAG))
            and (release is None or tags.get(TAG) == commit), "The stable release inventory disagrees.")
    latest = api("/releases/latest")
    expected_latest = releases["8.3.5"] if release is None else release
    require(beta.release_contents(latest) == beta.release_contents(expected_latest), "Unexpected Latest stable release.")
    return {k: beta.release_contents(releases[k]) for k in PRIOR}, release


def verify_release(row, commit, body):
    require(isinstance(row, dict) and type(row.get("id")) is int and row["id"] > 0
            and row.get("target_commitish") == commit and row.get("name") == TITLE and row.get("tag_name") == TAG
            and row.get("body") == body and row.get("prerelease") is False and row.get("draft") is False
            and row.get("html_url") == beta.URL + "/releases/tag/" + TAG and row.get("assets") == []
            and (row["author"].get("login"), row["author"].get("id")) == (beta.OWNER, beta.OWNER_ID),
            "Published release differs from the approved stable release.")


def publish(commit, *, allow_write=False):
    require(beta.is_sha(commit), "Supply the approved full stable squash SHA.")
    check_account()
    tree = package_tree(commit)
    body = package_notes(commit, tree)
    checks = beta.check_statuses(commit)
    previous, existing = inventory(commit)
    receipt = {"tag_name": TAG, "approved_publication_commit": commit, "package_tree": tree,
               "accepted_beta_release_id": BETA_ID, "checks_successful": checks,
               "preserved_release_records_verified": len(previous), "release_created": False}
    if existing is not None:
        verify_release(existing, commit, body)
        return dict(receipt, status="already_published_and_verified", release_id=existing["id"])
    beta.check_branch(commit)
    if not allow_write:
        return dict(receipt, status="ready_to_publish")
    check_account()
    current, existing = inventory(commit)
    require(current == previous and existing is None, "Release state changed during the preflight.")
    beta.check_branch(commit)
    payload = {"tag_name": TAG, "target_commitish": commit, "name": TITLE, "body": body,
               "prerelease": False, "draft": False, "make_latest": "true", "generate_release_notes": False}
    try:
        created = api("/releases", method="POST", body=payload)
    except Exception as exc:
        raise beta.PublicationError("Creation response unconfirmed. Run --check with the same SHA.") from exc
    try:
        verify_release(created, commit, body)
        current, confirmed = inventory(commit)
        verify_release(confirmed, commit, body)
        require(current == previous and confirmed["id"] == created["id"], "Historical or new release record differs.")
    except Exception as exc:
        raise beta.PublicationError("GitHub accepted the POST; readback is unconfirmed. Run --check with the same SHA.") from exc
    return dict(receipt, status="published_and_verified", release_created=True, release_id=confirmed["id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--publish", action="store_true")
    parser.add_argument("commit", metavar="APPROVED_MERGE_COMMIT")
    args = parser.parse_args()
    if not beta.is_sha(args.commit):
        parser.error("expected the full lowercase merge SHA")
    directory = Path.home() / "Downloads/HA/05_Diagnose"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", prefix="meteoswiss_836_stable_", suffix=".json",
                                     dir=directory, delete=False, encoding="utf-8") as fh:
        try:
            result = publish(args.commit, allow_write=args.publish)
            code = 0
        except Exception as exc:
            result = {"status": "unconfirmed", "tag_name": TAG, "approved_publication_commit": args.commit,
                      "reason": str(exc) if isinstance(exc, beta.PublicationError) else type(exc).__name__}
            code = 1
        result.update(mode="--publish" if args.publish else "--check",
                      checked_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
        json.dump(result, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(result["status"], result.get("reason", ""))
    print("Report:", fh.name)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
