"""Publish the reviewed 8.3.6b1 package from its signed development squash."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import posixpath
import re
import subprocess
import tempfile

REPOSITORY = "martins-netizen/ha-meteoswiss"
OWNER = "martins-netizen"
OWNER_ID = 299523863
REPO_ID = 1333898084
REVIEWED_SOURCE = "f9abaa12018fb89fd6c31633eadf6a975019d596"
SOURCE_TREE = "e958573cbae9bd8b5685a627645f9ff1477c73f8"
TAG = "8.3.6b1"
TITLE = "MeteoSwiss 8.3.6b1"
PACKAGE_BRANCH = "release/" + TAG
PACKAGE_TITLE = "Prepare the 8.3.6b1 prerelease"
URL = "https://github.com/" + REPOSITORY
NOTES = "docs/RELEASE_8.3.6b1.md"
COMPONENT = "custom_components/meteoswiss/"
VERSIONS = {
    COMPONENT + "manifest.json": '"version": "8.3.5"',
    COMPONENT + "version.py": '__version__ = "8.3.5"',
}
PACKAGE_PATHS = set(VERSIONS) | {
    "CHANGELOG.md", "README.md", "ROADMAP.md", NOTES, "docs/ACCEPTANCE_8.3.6b1.md",
    "docs/RELEASE_EVIDENCE_8.3.6b1.md", "docs/NEXT_RELEASE_PLAN.md", "docs/RELEASE_READINESS.md",
    "docs/PUBLISHING.md", "scripts/release_meteoswiss_836_beta_v1.15.sh",
    "scripts/publish_meteoswiss_836_beta.py", "tests/test_release_836b1.py",
}
REQUIRED_CHECKS = {
    "tests": 15368, "HA 2026.11.0": 15368, "HA 2026.11.2": 15368,
    "hassfest": 15368, "Analyze Python": 15368, "HACS validation": 15368,
    "Universal test locks": 15368, "Test dependency advisories": 15368,
    "SonarCloud Code Analysis": 12526,
}
# Immutable tag target and GitHub release ID for each published version through 8.3.5.
PRIOR = {
    "8.2.0": ("5a0bf684eb44fd54c4e91d7cbce9e90798b72fa5", 420392277),
    "8.2.0b1": ("abbb6b7701134ac2573f35b425ab3f0697a80540", 418588999),
    "8.2.0b2": ("80bf9195ecc3d42d9e4d1beb4ce8143e2c2df2c8", 420331076),
    "8.3.0": ("3ca9a1c166920fbdda88d15238affafe520f4b68", 422817883),
    "8.3.0b1": ("a6b9df9f57dec3e93c8f698133cdb0e7e4c3e937", 422558946),
    "8.3.0b2": ("50b5711213bd8a1706871718a283b9fcb4db257d", 422656379),
    "8.3.0b3": ("9d75aa8673c417f24caaa1f83181b5ef811d56fc", 422744751),
    "8.3.0b4": ("a8728e35837cc93ccc0ef0780e8f3dc2c0b65ce5", 422790421),
    "8.3.1": ("fa298ca72bf62da727797f9bfcacf95c83ffeaf1", 424249153),
    "8.3.1b1": ("c7b20c78d4273a33ba8c6f06c1834fc2f22c8665", 423899845),
    "8.3.2": ("aea4c5eab0534a6e675a4f564bde7521df193c58", 426633496),
    "8.3.2b1": ("5a39c3cdbf31f0807f52bcb4acb26190cc1e8423", 425962004),
    "8.3.3": ("3d4fad2330c89f134eba208e8b2db55705177e7d", 429354633),
    "8.3.3b1": ("d9fbc3fd49220b0ecc019d2babe0c173c46986f5", 429321251),
    "8.3.4": ("f4479897023fa35d7c2fcb4c4859c4de8861fdda", 437853341),
    "8.3.4b1": ("1e5c5d1a7fc1c18d520e99189ae4dd5894621706", 437718127),
    "8.3.5": ("cc158cbdce07f015952275fba72e3c0160c63c80", 450993306),
    "8.3.5b1": ("af1220249e672bd8a6742c73022a7c42aca2f20a", 444798178),
    "8.3.5b2": ("f8ea38babdfd44354059927888fb54fd662e5696", 445608354),
    "8.3.5b3": ("b6c4502e5cdeb48121be628fdb7eda579df4f7c3", 446112927),
    "8.3.5b4": ("a6a233513ac8e7c5937f9c41eee085e76108e801", 446375287),
    "8.3.5b5": ("ba8a15aa282aa7b67d16c83cca6f99e38ee2bf4b", 447678651),
    "8.3.5b6": ("cc4f494694609af28fd27c46c475a8270d3858ab", 449276745),
    "8.3.5b7": ("9ea96fc5a5306342eef0aa73ae50cc95bb844fb4", 450428545),
}


class PublicationError(RuntimeError):
    """The exact package or publication could not be confirmed."""


def require(condition, reason):
    if not condition:
        raise PublicationError(reason)


def is_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def api(path, *, method="GET", body=None, missing_ok=False):
    """Use the signed-in GitHub CLI. The only write is creation of this prerelease."""
    if method == "GET":
        require(body is None, "A read must not include a body.")
    else:
        require(method == "POST" and path == "/releases" and isinstance(body, dict)
                and body.get("tag_name") == TAG and body.get("prerelease") is True
                and body.get("draft") is False and body.get("make_latest") == "false"
                and is_sha(body.get("target_commitish")), "Release write is outside the approved scope.")
    require(path == "user" or path == "" or (path.startswith("/") and ".." not in path),
            "Unexpected repository endpoint.")
    endpoint = "user" if path == "user" else "repos/" + REPOSITORY + path
    args = ["gh", "api", "--hostname", "github.com", "--include", "--method", method,
            "-H", "Accept: application/vnd.github+json", endpoint]
    if body is not None:
        args.extend(["--input", "-"])
    result = subprocess.run(args, input=json.dumps(body) if body is not None else None,
                            text=True, capture_output=True, timeout=90, check=False)
    headers, separator, payload = result.stdout.partition("\n\n")
    status = re.match(r"^HTTP/\S+ (\d{3})\b", headers)
    require(separator and status, "Unconfirmed HTTP response from GitHub.")
    if missing_ok and status[1] == "404":
        return None
    require(not result.returncode and status[1] == ("201" if method == "POST" else "200"),
            "GitHub did not confirm " + method + " " + path + ".")
    require(not re.search(r'^link:.*rel="next"', headers, re.I | re.M),
            "GitHub returned an incomplete paginated inventory.")
    return json.loads(payload)


def check_branch(commit):
    branch = api("/branches/development")
    require(branch.get("name") == "development" and branch.get("protected") is True
            and branch.get("commit", {}).get("sha") == commit,
            "Protected development does not point to the approved package squash.")


def package_tree(commit):
    rows = api("/pulls?state=all&base=development&head=martins-netizen%3Arelease%2F8.3.6b1&per_page=100")
    require(isinstance(rows, list) and len(rows) == 1, "Expected exactly one package pull request.")
    number = rows[0].get("number")
    require(type(number) is int and number > 0, "Invalid package pull request number.")
    pr = api("/pulls/" + str(number))
    require(pr.get("number") == number and pr.get("html_url") == URL + "/pull/" + str(number)
            and pr.get("state") == "closed" and pr.get("merged") is True and pr.get("merged_at")
            and pr.get("title") == PACKAGE_TITLE and pr.get("merge_commit_sha") == commit
            and pr.get("user", {}).get("login") == OWNER and pr["user"].get("id") == OWNER_ID
            and all(pr.get(side, {}).get("repo", {}).get("full_name") == REPOSITORY
                    and pr[side]["repo"].get("id") == REPO_ID for side in ("base", "head"))
            and pr["base"].get("ref") == "development" and pr["base"].get("sha") == REVIEWED_SOURCE
            and pr["head"].get("ref") == PACKAGE_BRANCH, "The signed squash does not belong to the reviewed package PR.")
    head = pr["head"].get("sha")
    require(is_sha(head) and head != commit, "Invalid package PR head.")
    merged = api("/git/commits/" + commit)
    original = api("/git/commits/" + head)
    tree = merged.get("tree", {}).get("sha")
    require(is_sha(tree) and tree != SOURCE_TREE and all(
        obj.get("sha") == sha and obj.get("tree", {}).get("sha") == tree
        and [p.get("sha") for p in obj.get("parents", [])] == [REVIEWED_SOURCE]
        for obj, sha in ((merged, commit), (original, head))
    ), "The PR head and package squash must have the same tree and source parent.")
    require(merged.get("verification", {}).get("verified") is True
            and merged["verification"].get("reason") == "valid"
            and merged.get("author", {}).get("name") == OWNER
            and merged["author"].get("email") == "299523863+martins-netizen@users.noreply.github.com"
            and merged.get("committer", {}).get("name") == "GitHub"
            and merged["committer"].get("email") == "noreply@github.com",
            "Package squash is not signed by GitHub with the expected public identities.")
    return tree


def tree_files(tree):
    data = api("/git/trees/" + tree + "?recursive=1")
    require(data.get("sha") == tree and data.get("truncated") is False and isinstance(data.get("tree"), list),
            "Missing or incomplete Git tree.")
    paths = set()
    blobs = {}
    for row in data["tree"]:
        path, kind, mode, sha = (row.get(k) for k in ("path", "type", "mode", "sha"))
        require(isinstance(path, str) and path and path not in paths and is_sha(sha),
                "Unexpected or duplicate Git tree entry.")
        paths.add(path)
        if kind == "tree" and mode == "040000":
            continue
        require(kind == "blob" and mode in {"100644", "100755"}, "Unexpected Git file type.")
        blobs[path] = (mode, sha)
    return blobs


def blob_text(sha):
    obj = api("/git/blobs/" + sha)
    require(obj.get("sha") == sha and obj.get("encoding") == "base64"
            and type(obj.get("size")) is int and 0 <= obj["size"] <= 1024 * 1024,
            "Unexpected release blob format or size.")
    data = base64.b64decode("".join(obj["content"].split()), validate=True)
    git_hash = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    require(len(data) == obj["size"] and git_hash == sha, "Release blob content or length differs.")
    return data.decode("utf-8")


def package_notes(commit, tree):
    source, package = tree_files(SOURCE_TREE), tree_files(tree)
    changed = {path for path in source.keys() | package.keys() if source.get(path) != package.get(path)}
    require(changed == PACKAGE_PATHS and all(package.get(path, (None,))[0] == "100644" for path in changed),
            "The repository differs outside the exact regular package files, or an expected change is missing.")
    components = {path for path in source if path.startswith(COMPONENT)}
    require(len(components) == 52 and all(source[path][0] == "100644" for path in components),
            "The reviewed component inventory differs.")
    for path, old in VERSIONS.items():
        before = blob_text(source[path][1])
        after = blob_text(package[path][1])
        require(before.count(old) == 1 and after == before.replace(old, old.replace("8.3.5", TAG)),
                "A component file differs beyond the exact version bump.")
    notes = blob_text(package[NOTES][1])
    marker = "This community fork builds on "
    require(notes.startswith("# MeteoSwiss 8.3.6b1\n") and notes.count("\n" + marker) == 1,
            "The package release notes do not match the reviewed format.")
    body = notes[notes.index("\n" + marker) + 1:]

    def absolute_link(match):
        target = match[1]
        if target.startswith(("https://", "http://", "#")):
            return match[0]
        path, anchor, fragment = target.partition("#")
        path = posixpath.normpath(posixpath.join("docs", path))
        require(not path.startswith(("../", "/")) and ":" not in path and path in package,
                "Relative release link is outside the package.")
        return "](" + URL + "/blob/" + commit + "/" + path + anchor + fragment + ")"

    return re.sub(r"\]\(([^)]+)\)", absolute_link, body)


def check_statuses(commit):
    checks = api("/commits/" + commit + "/check-runs?per_page=100")
    runs = checks.get("check_runs")
    require(isinstance(runs, list) and type(checks.get("total_count")) is int
            and len(runs) == checks["total_count"] <= 100, "Incomplete merge checks.")
    latest = {}
    for row in runs:
        name = row.get("name")
        require(isinstance(name, str) and name and row.get("head_sha") == commit and type(row.get("id")) is int,
                "Merge check belongs to another commit or has no identity.")
        if name not in latest or latest[name]["id"] < row["id"]:
            latest[name] = row
    require(REQUIRED_CHECKS.keys() <= latest.keys(), "Required merge checks are missing.")
    trusted = {**REQUIRED_CHECKS, "CodeQL": 57789, "update-pip-graph": 15368}
    for name, row in latest.items():
        require(row.get("status") == "completed" and row.get("conclusion") == "success"
                and (name not in trusted or row.get("app", {}).get("id") == trusted[name]),
                "Merge check failed, is pending, or has unexpected provenance.")
    combined = api("/commits/" + commit + "/status?per_page=100")
    statuses = combined.get("statuses")
    require(isinstance(statuses, list) and type(combined.get("total_count")) is int
            and len(statuses) == combined["total_count"] <= 100 and combined.get("sha") == commit
            and (combined.get("state") == "success" or (not statuses and combined.get("state") == "pending"))
            and all(row.get("state") == "success" for row in statuses), "Incomplete or failing commit status.")
    return sorted(latest)


def release_contents(row):
    """Compare publication settings, text and artifact identity across GitHub reads."""
    if row is None:
        return None
    public_fields = ("id", "tag_name", "target_commitish", "name", "body", "draft", "prerelease",
                     "immutable", "html_url", "created_at", "published_at")
    content = {field: row.get(field) for field in public_fields}
    content["author_id"] = row.get("author", {}).get("id")
    asset_fields = ("id", "name", "label", "state", "content_type", "size", "digest", "created_at")
    # Download and reaction counters may change between consecutive GETs.
    assets = [{field: asset.get(field) for field in asset_fields} for asset in row.get("assets", [])]
    content["assets"] = sorted(assets, key=lambda asset: asset["id"])
    return content


def inventory(commit):
    refs = api("/git/matching-refs/tags/")
    rows = api("/releases?per_page=100")
    require(isinstance(refs, list) and isinstance(rows, list), "Release or tag inventory is missing.")
    tags = {}
    for ref in refs:
        name = ref.get("ref", "")
        obj = ref.get("object", {})
        require(name.startswith("refs/tags/") and obj.get("type") == "commit" and is_sha(obj.get("sha")),
                "Expected a lightweight version tag.")
        tag = name[len("refs/tags/"):]
        require(tag not in tags, "Duplicate tag.")
        tags[tag] = obj["sha"]
    records = {row["tag_name"]: row for row in rows}
    require(len(records) == len(rows) and records.keys() - {TAG} == PRIOR.keys()
            and tags.keys() - {TAG} == PRIOR.keys(), "Historical release or tag inventory differs.")
    for tag, (target, release_id) in PRIOR.items():
        row = records[tag]
        require(tags[tag] == target and row.get("id") == release_id
                and row.get("draft") is False and row.get("prerelease") is ("b" in tag),
                "Historical tag or release identity differs: " + tag)
    stable = api("/releases/latest")
    require(stable.get("id") == PRIOR["8.3.5"][1] and stable.get("tag_name") == "8.3.5"
            and stable.get("draft") is False and stable.get("prerelease") is False,
            "Latest stable release is no longer 8.3.5.")
    require(tags.get(TAG, commit) == commit, "Existing beta tag points to another commit.")
    release = api("/releases/tags/" + TAG, missing_ok=True)
    require(release_contents(release) == release_contents(records.get(TAG))
            and (release is None or tags.get(TAG) == commit),
            "The beta release or tag is inconsistent with the complete inventory.")
    return {tag: release_contents(records[tag]) for tag in PRIOR}, release


def verify_release(release, commit, body):
    require(isinstance(release, dict) and type(release.get("id")) is int and release["id"] > 0
            and release.get("tag_name") == TAG and release.get("target_commitish") == commit
            and release.get("name") == TITLE and release.get("body") == body
            and release.get("prerelease") is True and release.get("draft") is False
            and release.get("author", {}).get("id") == OWNER_ID and release["author"].get("login") == OWNER
            and release.get("assets") == []
            and release.get("html_url") == URL + "/releases/tag/" + TAG,
            "The beta release differs from the approved publication.")


def publish(commit, *, allow_write=False):
    require(is_sha(commit), "Supply the full approved package merge SHA.")
    identity, repo = api("user"), api("")
    require(identity.get("id") == OWNER_ID and identity.get("login") == OWNER
            and repo.get("id") == REPO_ID and repo.get("full_name") == REPOSITORY
            and repo.get("owner", {}).get("id") == OWNER_ID and repo["owner"].get("login") == OWNER
            and repo.get("default_branch") == "development" and repo.get("archived") is False
            and repo.get("private") is False and repo.get("permissions", {}).get("push") is True,
            "Unexpected account, repository, default branch or permissions.")
    tree = package_tree(commit)
    body = package_notes(commit, tree)
    checks = check_statuses(commit)
    previous, existing = inventory(commit)
    receipt = {"tag_name": TAG, "approved_publication_commit": commit, "reviewed_source": REVIEWED_SOURCE,
               "package_tree": tree, "checks_successful": checks, "stable_release_id": PRIOR["8.3.5"][1],
               "preserved_release_records_verified": len(previous), "release_created": False}
    if existing is not None:
        verify_release(existing, commit, body)
        return dict(receipt, status="already_published_and_verified", release_id=existing["id"])
    check_branch(commit)
    if not allow_write:
        return dict(receipt, status="ready_to_publish")
    # Repeat mutable publication state immediately before the single allowed write.
    current, existing = inventory(commit)
    require(current == previous and existing is None, "Release state changed during preflight; check again.")
    check_branch(commit)
    payload = {"tag_name": TAG, "target_commitish": commit, "name": TITLE, "body": body,
               "draft": False, "prerelease": True, "make_latest": "false", "generate_release_notes": False}
    try:
        created = api("/releases", method="POST", body=payload)
        verify_release(created, commit, body)
        current, confirmed = inventory(commit)
        verify_release(confirmed, commit, body)
        require(current == previous and confirmed["id"] == created["id"], "Publication readback differs.")
    except Exception as exc:
        raise PublicationError("Publication result unconfirmed. Run --check with the same SHA before retrying.") from exc
    return dict(receipt, status="published_and_verified", release_created=True, release_id=confirmed["id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="verify the package without publishing")
    mode.add_argument("--publish", action="store_true", help="create the separately approved prerelease")
    parser.add_argument("commit", metavar="APPROVED_MERGE_COMMIT")
    args = parser.parse_args()
    if not is_sha(args.commit):
        parser.error("expected a full lowercase Git commit SHA")
    report_dir = Path.home() / "Downloads/HA/05_Diagnose"
    report_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Reserve a private receipt before making any GitHub request.
    with tempfile.NamedTemporaryFile(mode="w", prefix="meteoswiss_836_beta_", suffix=".json",
                                     dir=report_dir, delete=False, encoding="utf-8") as report:
        try:
            result = publish(args.commit, allow_write=args.publish)
            code = 0
        except Exception as exc:
            result = {"status": "unconfirmed", "tag_name": TAG, "approved_publication_commit": args.commit,
                      "reason": str(exc) if isinstance(exc, PublicationError) else type(exc).__name__}
            code = 1
        result["checked_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        result["mode"] = "--publish" if args.publish else "--check"
        json.dump(result, report, ensure_ascii=False, indent=2)
        report.write("\n")
    print(result["status"], result.get("reason", ""))
    print("Report:", report.name)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
