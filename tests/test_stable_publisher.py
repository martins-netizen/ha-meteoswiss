"""Exercise stable publication/refusal/retry without any real GitHub writes."""

from __future__ import annotations

import base64
import copy
import json
import subprocess
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

import test_prerelease_publisher as original

SCRIPT = original.SCRIPT.with_name("veroeffentliche_meteoswiss_stable_v1.2.sh")
PAYLOAD = SCRIPT.read_text().split("<<'PY_PUBLISH'\n", 1)[1].split("\nPY_PUBLISH", 1)[0]
publisher = types.ModuleType("stable_publisher_under_test")
exec(compile(PAYLOAD, str(SCRIPT), "exec"), publisher.__dict__)


class StableGitHub(original.FakeGitHub):
    def __init__(self, module):
        super().__init__(module)
        self.beta_tags = dict(module.BETA_COMMITS)
        self.source_manifest = {"domain": "meteoswiss", "version": "8.2.0b2"}
        self.source_version = '__version__ = "8.2.0b2"\n'
        self.source_hacs = {"name": "MeteoSwiss", "hide_default_branch": True}
        self.hacs = dict(self.source_hacs)
        for row in self.rows:
            row.update(app={"id": 15368}, head_sha=original.COMMIT)

    def __call__(self, path, *, method="GET", body=None, missing_ok=False):
        suffix = path.removeprefix(self.publisher.API_PREFIX)
        if method == "POST":
            self.calls.append((method, path, body))
            assert suffix == "/releases"
            assert body["tag_name"] == "8.2.0"
            assert body["target_commitish"] == original.COMMIT
            assert body["prerelease"] is False and body["draft"] is False
            assert body["make_latest"] == "true"
            self.tag = original.COMMIT
            self.release = dict(
                id=2, tag_name="8.2.0", draft=False, prerelease=False,
                html_url=self.publisher.RELEASE_URL, body=body["body"],
                published_at="2026-10-22T08:00:00Z",
            )
            if self.fail_after_post:
                raise subprocess.TimeoutExpired("gh", 90)
            return copy.deepcopy(self.release)
        if method == "GET" and suffix.startswith("/git/ref/tags/8.2.0b"):
            self.calls.append((method, path, body))
            return {"object": {"type": "commit", "sha": self.beta_tags[suffix.rsplit("/", 1)[1]]}}
        if method == "GET" and suffix.startswith("/contents/"):
            source = suffix.endswith("?ref=" + self.publisher.ACCEPTED_RUNTIME)
            text = None
            if "hacs.json?" in suffix:
                text = json.dumps(self.source_hacs if source else self.hacs)
            elif source and "manifest.json?" in suffix:
                text = json.dumps(self.source_manifest)
            elif source and "version.py?" in suffix:
                text = self.source_version
            if text is not None:
                self.calls.append((method, path, body))
                return {"encoding": "base64", "size": len(text),
                        "content": base64.b64encode(text.encode()).decode()}
        return super().__call__(path, method=method, body=body, missing_ok=missing_ok)


class StablePublisherTests(original.PrereleasePublisherTests):
    publisher = publisher
    identical_components = 31

    def fake(self):
        return StableGitHub(self.publisher)

    def test_version_mismatch_stops(self):
        fake = self.fake()
        fake.manifest["version"] = "8.2.0b2"
        self.assert_stops_without_write(fake)

    def test_existing_stable_release_is_not_modified(self):
        fake = self.fake()
        self.run_publish(fake)
        fake.calls.clear()
        fake.release["prerelease"] = True
        self.assert_stops_without_write(fake)

    def test_read_only_check_never_creates_a_release_or_tag(self):
        fake = self.fake()
        with patch.object(self.publisher, "api", fake):
            result = self.publisher.publish(original.COMMIT, {}, allow_write=False)
        self.assertEqual(result["status"], "ready_to_publish")
        self.assertFalse(result["prerelease"])
        self.assertEqual(fake.writes(), [])
        self.assertIsNone(fake.tag)

    def test_check_mode_records_a_read_only_receipt(self):
        fake = self.fake()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "receipt.json"
            with patch.object(self.publisher, "api", fake):
                self.assertEqual(self.publisher.main(original.COMMIT, output, "--check"), 0)
            receipt = json.loads(output.read_text())
        self.assertEqual(receipt["status"], "ready_to_publish")
        self.assertFalse(receipt["release_write_attempted"])
        self.assertFalse(receipt["ha_writes_performed"])
        self.assertEqual(fake.writes(), [])

    def test_both_immutable_beta_tags_are_preserved(self):
        for beta in self.publisher.BETA_COMMITS:
            with self.subTest(beta=beta):
                fake = self.fake()
                fake.beta_tags[beta] = original.OTHER
                self.assert_stops_without_write(fake)

    def test_additional_manifest_or_module_code_stops(self):
        for field in ("manifest", "module"):
            with self.subTest(field=field):
                fake = self.fake()
                if field == "manifest":
                    fake.manifest["requirements"] = ["unreviewed-package"]
                else:
                    fake.version += "unreviewed_code = True\n"
                self.assert_stops_without_write(fake)

    def test_hacs_manifest_must_remain_identical_with_branch_hiding(self):
        for field, value in (("hide_default_branch", False), ("homeassistant", "2027.1.0")):
            with self.subTest(field=field):
                fake = self.fake()
                fake.hacs[field] = value
                self.assert_stops_without_write(fake)

    def test_checks_from_another_app_or_commit_do_not_authorise_publication(self):
        for field, value in (("app", {"id": 1}), ("head_sha", original.OTHER)):
            with self.subTest(field=field):
                fake = self.fake()
                fake.rows[0][field] = value
                self.assert_stops_without_write(fake)

    def test_receipt_distinguishes_source_files_and_stable_publication(self):
        result = self.run_publish(self.fake())
        self.assertEqual(result["component_files_identical"], 31)
        self.assertEqual(result["version_files_checked"], 2)
        self.assertTrue(result["beta_tags_unchanged"])
        self.assertFalse(result["prerelease"])
