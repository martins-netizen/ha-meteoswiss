"""Reuse publication guard regressions for the version-only beta2 package."""

from __future__ import annotations

import base64
import json
import types

import test_prerelease_publisher as original

SCRIPT = original.SCRIPT.with_name("veroeffentliche_meteoswiss_beta_v1.1.sh")
PAYLOAD = SCRIPT.read_text().split("<<'PY_PUBLISH'\n", 1)[1].split("\nPY_PUBLISH", 1)[0]
publisher = types.ModuleType("beta2_publisher_under_test")
exec(compile(PAYLOAD, str(SCRIPT), "exec"), publisher.__dict__)


class Beta2GitHub(original.FakeGitHub):
    def __init__(self, module):
        super().__init__(module)
        self.legacy_tag = module.LEGACY_BETA_COMMIT
        self.source_manifest = {"domain": "meteoswiss", "version": "8.2.0b1"}
        self.source_version = '__version__ = "8.2.0b1"\n'
        self.source_hacs = {"name": "MeteoSwiss", "homeassistant": "2026.8.3"}
        self.hacs = {**self.source_hacs, "hide_default_branch": True}

    def __call__(self, path, *, method="GET", body=None, missing_ok=False):
        suffix = path.removeprefix(self.publisher.API_PREFIX)
        if method == "GET" and suffix == "/git/ref/tags/8.2.0b1":
            self.calls.append((method, path, body))
            return {"object": {"type": "commit", "sha": self.legacy_tag}}
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
                return {
                    "encoding": "base64",
                    "size": len(text),
                    "content": base64.b64encode(text.encode()).decode(),
                }
        return super().__call__(path, method=method, body=body, missing_ok=missing_ok)


class Beta2PublisherTests(original.PrereleasePublisherTests):
    publisher = publisher
    identical_components = 31

    def fake(self):
        return Beta2GitHub(self.publisher)

    def test_legacy_immutable_tag_must_remain_unchanged(self):
        fake = self.fake()
        fake.legacy_tag = original.OTHER
        self.assert_stops_without_write(fake)

    def test_manifest_change_beyond_version_stops(self):
        fake = self.fake()
        fake.manifest["requirements"] = ["unreviewed-package"]
        self.assert_stops_without_write(fake)

    def test_version_module_change_beyond_version_stops(self):
        fake = self.fake()
        fake.version += "unreviewed_code = True\n"
        self.assert_stops_without_write(fake)

    def test_branch_hiding_must_be_enabled(self):
        fake = self.fake()
        fake.hacs["hide_default_branch"] = False
        self.assert_stops_without_write(fake)

    def test_unreviewed_hacs_change_stops(self):
        fake = self.fake()
        fake.hacs["homeassistant"] = "2027.1.0"
        self.assert_stops_without_write(fake)

    def test_receipt_separates_version_files(self):
        result = self.run_publish(self.fake())
        self.assertEqual(result["component_files_identical"], 31)
        self.assertEqual(result["version_files_checked"], 2)
        self.assertTrue(result["hide_default_branch"])
