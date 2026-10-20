"""Check publication guards with mocked GitHub replies; never contact GitHub."""
from __future__ import annotations

import base64
import copy
import json
import subprocess
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'veroeffentliche_meteoswiss_beta_v1.0.sh'
PAYLOAD = SCRIPT.read_text().split("<<'PY_PUBLISH'\n", 1)[1].split('\nPY_PUBLISH', 1)[0]
publisher = types.ModuleType('publisher_under_test')
exec(compile(PAYLOAD, str(SCRIPT), 'exec'), publisher.__dict__)
COMMIT = 'a' * 40
OTHER = 'b' * 40


class FakeGitHub:
    def __init__(self):
        self.calls = []
        self.branch = COMMIT
        self.tag = None
        self.release = None
        self.fail_after_post = False
        self.move_before_post = False
        self.branch_reads = 0
        self.rows = [dict(id=index + 1, name=name, status='completed', conclusion='success')
                     for index, name in enumerate(sorted(publisher.REQUIRED_CHECKS))]
        prefix = 'custom_components/meteoswiss/'
        self.accepted = {prefix + 'manifest.json': ('100644', '1' * 40),
                         prefix + 'version.py': ('100644', '2' * 40)}
        self.accepted.update({prefix + 'module_' + str(index) + '.py': ('100644', '3' * 40)
                              for index in range(31)})
        self.accepted['.github/workflows/ci.yml'] = ('100644', '4' * 40)
        self.candidate = copy.deepcopy(self.accepted)
        self.manifest = {'domain': 'meteoswiss', 'version': publisher.TAG}
        self.version = '__version__ = "8.2.0b1"\n'
        self.notes = '# 8.2.0b1 — first maintained-fork prerelease\n\nRelease notes.\n\nThis community fork builds on LNKtwo.\n[Migration](WECHSEL_DE.md)\n'

    def tree(self, files):
        return {'truncated': False, 'tree': [dict(path=k, mode=v[0], sha=v[1], type='blob') for k, v in files.items()]}

    def body(self):
        return 'This community fork builds on LNKtwo.\n[Migration](https://github.com/' + publisher.REPOSITORY + '/blob/' + COMMIT + '/docs/WECHSEL_DE.md)\n'

    def __call__(self, path, *, method='GET', body=None, missing_ok=False):
        self.calls.append((method, path, body))
        suffix = path.removeprefix(publisher.API_PREFIX)
        if method == 'POST':
            assert suffix == '/releases'
            assert body['target_commitish'] == COMMIT
            assert body['prerelease'] is True and body['draft'] is False
            assert body['make_latest'] == 'false'
            self.tag = COMMIT
            self.release = dict(id=1, tag_name=publisher.TAG, draft=False, prerelease=True,
                                html_url=publisher.RELEASE_URL, body=body['body'], published_at='2026-10-20T16:00:00Z')
            if self.fail_after_post:
                raise subprocess.TimeoutExpired('gh', 90)
            return copy.deepcopy(self.release)
        if suffix == '':
            return dict(full_name=publisher.REPOSITORY, default_branch='development',
                        private=False, archived=False, permissions={'push': True})
        if suffix == '/branches/development':
            self.branch_reads += 1
            head = OTHER if self.move_before_post and self.branch_reads > 1 else self.branch
            return {'commit': {'sha': head}, 'protected': True}
        if suffix.startswith('/git/trees/'):
            files = self.accepted if publisher.ACCEPTED_RUNTIME in suffix else self.candidate
            return self.tree(files)
        if '/check-runs?' in suffix:
            return {'total_count': len(self.rows), 'check_runs': self.rows}
        if suffix.endswith('/status?per_page=100'):
            return {'total_count': 0, 'statuses': []}
        if suffix == '/git/ref/tags/' + publisher.TAG:
            return {'object': {'type': 'commit', 'sha': self.tag}} if self.tag else None
        if suffix == '/releases/tags/' + publisher.TAG:
            return copy.deepcopy(self.release)
        if suffix.startswith('/contents/'):
            if 'manifest.json?' in suffix:
                text = json.dumps(self.manifest)
            elif 'version.py?' in suffix:
                text = self.version
            else:
                text = self.notes
            return {'encoding': 'base64', 'size': len(text), 'content': base64.b64encode(text.encode()).decode()}
        raise AssertionError(path)

    def writes(self):
        return [row for row in self.calls if row[0] != 'GET']


class PrereleasePublisherTests(unittest.TestCase):
    def run_publish(self, fake, receipt=None):
        receipt = receipt if receipt is not None else {'release_write_attempted': False}
        with patch.object(publisher, 'api', fake):
            return publisher.publish(COMMIT, receipt)

    def test_only_exact_approved_prerelease_is_created_and_verified(self):
        fake = FakeGitHub()
        result = self.run_publish(fake)
        self.assertEqual(result['status'], 'published_and_verified')
        self.assertEqual(result['component_files_identical'], 33)
        self.assertEqual(len(fake.writes()), 1)
        self.assertEqual(fake.writes()[0][2]['body'], fake.body())

    def test_existing_identical_release_is_read_only(self):
        fake = FakeGitHub()
        self.run_publish(fake)
        fake.calls.clear()
        result = self.run_publish(fake)
        self.assertEqual(result['status'], 'already_published_and_verified')
        self.assertEqual(fake.writes(), [])

    def test_relative_links_use_exact_publication_commit(self):
        fake = FakeGitHub()
        with patch.object(publisher, 'api', fake):
            body = publisher.release_notes(COMMIT)
        self.assertEqual(body, fake.body())

    def assert_stops_without_write(self, fake):
        with self.assertRaises(publisher.PublicationError):
            self.run_publish(fake)
        self.assertEqual(fake.writes(), [])

    def test_changed_branch_stops(self):
        fake = FakeGitHub()
        fake.branch = OTHER
        self.assert_stops_without_write(fake)

    def test_branch_changed_during_checks_stops(self):
        fake = FakeGitHub()
        fake.move_before_post = True
        self.assert_stops_without_write(fake)

    def test_runtime_change_stops(self):
        fake = FakeGitHub()
        fake.candidate['custom_components/meteoswiss/module_0.py'] = ('100644', OTHER)
        self.assert_stops_without_write(fake)

    def test_new_component_file_stops(self):
        fake = FakeGitHub()
        fake.candidate['custom_components/meteoswiss/extra.py'] = ('100644', OTHER)
        self.assert_stops_without_write(fake)

    def test_workflow_change_stops(self):
        fake = FakeGitHub()
        fake.candidate['.github/workflows/ci.yml'] = ('100644', OTHER)
        self.assert_stops_without_write(fake)

    def test_pending_or_failed_required_check_stops(self):
        for status, conclusion in [('in_progress', None), ('completed', 'failure')]:
            with self.subTest(status=status):
                fake = FakeGitHub()
                fake.rows[0].update(status=status, conclusion=conclusion)
                self.assert_stops_without_write(fake)

    def test_missing_required_check_stops(self):
        fake = FakeGitHub()
        fake.rows.pop()
        self.assert_stops_without_write(fake)

    def test_existing_foreign_tag_stops_without_retagging(self):
        fake = FakeGitHub()
        fake.tag = OTHER
        self.assert_stops_without_write(fake)

    def test_version_mismatch_stops(self):
        fake = FakeGitHub()
        fake.manifest['version'] = '8.2.0'
        self.assert_stops_without_write(fake)

    def test_existing_stable_release_is_not_modified(self):
        fake = FakeGitHub()
        self.run_publish(fake)
        fake.calls.clear()
        fake.release['prerelease'] = False
        self.assert_stops_without_write(fake)

    def test_existing_different_release_notes_are_not_overwritten(self):
        fake = FakeGitHub()
        self.run_publish(fake)
        fake.calls.clear()
        fake.release['body'] = 'Different reviewed notes'
        self.assert_stops_without_write(fake)

    def test_uncertain_post_is_recorded_and_safe_to_recheck(self):
        fake = FakeGitHub()
        fake.fail_after_post = True
        receipt = {'release_write_attempted': False}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'receipt.json'
            with patch.object(publisher, 'api', fake):
                self.assertEqual(publisher.main(COMMIT, output), 1)
            data = json.loads(output.read_text())
        self.assertTrue(data['release_write_attempted'])
        self.assertEqual(data['status'], 'publication_result_unconfirmed')
        self.assertFalse(data['ha_writes_performed'])
        fake.fail_after_post = False
        fake.calls.clear()
        self.assertEqual(self.run_publish(fake)['status'], 'already_published_and_verified')
        self.assertEqual(fake.writes(), [])

    def test_api_rejects_unapproved_write_and_foreign_repository(self):
        for path, method in [(publisher.API_PREFIX + '/git/refs/tags/test', 'POST'),
                             ('repos/other/project/releases', 'POST')]:
            with self.assertRaises(publisher.PublicationError):
                publisher.api(path, method=method)


if __name__ == '__main__':
    unittest.main()
