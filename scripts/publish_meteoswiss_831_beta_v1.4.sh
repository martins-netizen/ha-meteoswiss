#!/bin/bash
# Publish only the approved 8.3.1b1 test package from the Mac.
# GitHub only: no Home Assistant connection, installation, restart or device call.
set -Eeuo pipefail
umask 077
if [[ "${1:-}" = '--help' ]] || [[ "${1:-}" = '-h' ]]; then
  printf '%s\n' 'bash publish_meteoswiss_831_beta_v1.4.sh --check|--publish APPROVED_MERGE_COMMIT' 'Checks the exact commit read-only with --check; --publish creates prerelease 8.3.1b1.' 'Requires python3, gh and existing GitHub authentication. No HA changes.'
  exit 0
fi
if [[ "$#" -ne 2 ]] || { [[ "$1" != '--check' ]] && [[ "$1" != '--publish' ]]; } || ! [[ "$2" =~ ^[0-9a-f]{40}$ ]]; then
  printf '%s\n' 'Usage: bash publish_meteoswiss_831_beta_v1.4.sh --check|--publish APPROVED_MERGE_COMMIT' >&2
  exit 2
fi
for program in gh python3; do
  command -v "${program}" >/dev/null || { printf 'Missing: %s\n' "${program}" >&2; exit 1; }
done
RUN_ID="$(date +%Y%m%d-%H%M%S)-$$"
DIAG_DIR="${HOME}/Downloads/HA/05_Diagnose"
REPORT="${DIAG_DIR}/meteoswiss_831_beta_release_v1.4_${RUN_ID}.json"
LOG="${DIAG_DIR}/meteoswiss_831_beta_release_v1.4_${RUN_ID}.log"
mkdir -p "${DIAG_DIR}"
exec > >(tee -a "${LOG}") 2>&1
printf '%s\n' '=== MeteoSwiss · 8.3.1b1 prerelease publication V1.4 ===' "Approved merge: $2" 'GitHub prerelease 8.3.1b1; no Home Assistant changes.'
python3 - "$2" "${REPORT}" "$1" <<'PY_PUBLISH'
"""Check/publish the exact 8.3.1b1 package based on reviewed PR #70."""
from __future__ import annotations

import base64
import datetime as dt
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path

REPOSITORY = 'martins-netizen/ha-meteoswiss'
API_PREFIX = 'repos/' + REPOSITORY
# Reviewed PR #70, not a claim of candidate-specific live HA acceptance.
REVIEWED_SOURCE = '22004177b96adb4452fdbd116174915de4dc18cf'
PRESERVED_TAGS = {
    '8.2.0b1': 'abbb6b7701134ac2573f35b425ab3f0697a80540',
    '8.2.0b2': '80bf9195ecc3d42d9e4d1beb4ce8143e2c2df2c8',
    '8.2.0': '5a0bf684eb44fd54c4e91d7cbce9e90798b72fa5',
    '8.3.0b1': 'a6b9df9f57dec3e93c8f698133cdb0e7e4c3e937',
    '8.3.0b2': '50b5711213bd8a1706871718a283b9fcb4db257d',
    '8.3.0b3': '9d75aa8673c417f24caaa1f83181b5ef811d56fc',
    '8.3.0b4': 'a8728e35837cc93ccc0ef0780e8f3dc2c0b65ce5',
    '8.3.0': '3ca9a1c166920fbdda88d15238affafe520f4b68',
}
STABLE_RELEASE_ID = 422817883
TAG = '8.3.1b1'
TITLE = '8.3.1b1 — repair notices and station-map help test prerelease'
RELEASE_URL = 'https://github.com/' + REPOSITORY + '/releases/tag/' + TAG
REQUIRED_CHECKS = {'tests', 'HA 2026.8.3', 'HA 2026.10.1', 'hassfest', 'Analyze Python', 'HACS validation', 'SonarCloud Code Analysis'}


class PublicationError(RuntimeError):
    """A bounded public diagnostic, without subprocess stderr or credentials."""


def api(path, *, method='GET', body=None, missing_ok=False):
    """Use the user's existing gh authentication, with fixed host and repository."""
    if not path.startswith(API_PREFIX + '/') and path != API_PREFIX:
        raise PublicationError('Repository path is not allowed.')
    if method != 'GET' and not (method == 'POST' and path == API_PREFIX + '/releases'):
        raise PublicationError('GitHub write is not allowed.')
    args = ['gh', 'api', '--hostname', 'github.com', '--method', method,
            '-H', 'Accept: application/vnd.github+json', path]
    if body is not None:
        args += ['--input', '-']
    result = subprocess.run(args, input=json.dumps(body) if body is not None else None,
                            text=True, capture_output=True, timeout=90, check=False)
    if result.returncode:
        if missing_ok and re.search(r'HTTP\s+404\b', result.stderr):
            return None
        raise PublicationError('GitHub request failed: ' + method + ' ' + path)
    try:
        return json.loads(result.stdout)
    except (ValueError, TypeError) as exc:
        raise PublicationError('GitHub response is not valid JSON.') from exc


def read_file(commit, path):
    data = api(API_PREFIX + '/contents/' + path + '?ref=' + commit)
    if data.get('encoding') != 'base64' or data.get('size', 0) > 1024 * 1024:
        raise PublicationError('Unexpected source format: ' + path)
    try:
        return base64.b64decode(data['content'], validate=False).decode('utf-8')
    except (ValueError, KeyError, UnicodeError) as exc:
        raise PublicationError('Source file is unreadable: ' + path) from exc


def tree_files(commit):
    data = api(API_PREFIX + '/git/trees/' + commit + '?recursive=1')
    if data.get('truncated') is not False or not isinstance(data.get('tree'), list):
        raise PublicationError('Repository tree is incomplete.')
    if any(row.get('type') not in {'tree', 'blob'}
           and row.get('path', '').startswith('custom_components/meteoswiss/')
           for row in data['tree']):
        raise PublicationError('Component tree contains an unsupported Git entry.')
    return {row['path']: (row['mode'], row['sha']) for row in data['tree'] if row.get('type') == 'blob'}


def check_statuses(commit):
    data = api(API_PREFIX + '/commits/' + commit + '/check-runs?per_page=100')
    if data.get('total_count', 0) > 100:
        raise PublicationError('Check list exceeds the bounded request.')
    latest = {}
    for row in data.get('check_runs', []):
        if row.get('id', -1) > latest.get(row['name'], {}).get('id', -2):
            latest[row['name']] = row
    if not REQUIRED_CHECKS <= latest.keys():
        raise PublicationError('Required checks are missing for the merge commit.')
    if any(latest[name].get('app', {}).get('id') != (12526 if name == 'SonarCloud Code Analysis' else 15368) or latest[name].get('head_sha') != commit
           for name in REQUIRED_CHECKS):
        raise PublicationError('Required check provenance or commit differs.')
    if any(row.get('status') != 'completed' or row.get('conclusion') != 'success' for row in latest.values()):
        raise PublicationError('Merge checks have not all succeeded.')
    combined = api(API_PREFIX + '/commits/' + commit + '/status?per_page=100')
    if combined.get('total_count', 0) > 100:
        raise PublicationError('Status list exceeds the bounded request.')
    if any(row.get('state') != 'success' for row in combined.get('statuses', [])):
        raise PublicationError('Another commit status is not successful.')
    return sorted(latest)


def tag_commit(tag=TAG):
    data = api(API_PREFIX + '/git/ref/tags/' + tag, missing_ok=True)
    if data is None:
        return None
    obj = data.get('object', {})
    for _ in range(5):
        if obj.get('type') == 'commit':
            return obj.get('sha')
        if obj.get('type') != 'tag' or not re.fullmatch(r'[0-9a-f]{40}', obj.get('sha', '')):
            break
        obj = api(API_PREFIX + '/git/tags/' + obj['sha']).get('object', {})
    raise PublicationError('Existing tag could not be resolved to a unique commit.')


def release_notes(commit):
    text = read_file(commit, 'docs/RELEASE_8.3.1b1.md')
    marker = '\nThis community fork builds on '
    if marker not in text or not text.startswith('# 8.3.1b1 — repair notices and station-map help test prerelease\n'):
        raise PublicationError('Approved release notes were not recognised.')
    body = 'This community fork builds on ' + text.split(marker, 1)[1].lstrip()
    def absolute_link(match):
        target = match[1]
        if target.startswith(('https://', 'http://', '#')):
            return match[0]
        path, separator, anchor = target.partition('#')
        path = posixpath.normpath(posixpath.join('docs', path))
        if path.startswith('../') or path.startswith('/') or ':' in path:
            raise PublicationError('Unexpected relative release link.')
        return '](https://github.com/' + REPOSITORY + '/blob/' + commit + '/' + path + (separator + anchor if separator else '') + ')'
    return re.sub(r'\]\(([^)]+)\)', absolute_link, body)


def verify_release(release, commit):
    if (type(release.get('id')) is not int or release['id'] <= 0
            or release.get('tag_name') != TAG or release.get('draft') is not False
            or release.get('prerelease') is not True or release.get('html_url') != RELEASE_URL):
        raise PublicationError('Release is not the expected published prerelease.')
    if tag_commit() != commit:
        raise PublicationError('Release tag does not point to the approved merge commit.')


def verify_latest_stable():
    """A test prerelease must preserve the existing stable release selection."""
    stable = api(API_PREFIX + '/releases/latest')
    if (stable.get('id') != STABLE_RELEASE_ID or stable.get('tag_name') != '8.3.0'
            or stable.get('draft') is not False or stable.get('prerelease') is not False):
        raise PublicationError('Latest stable release differs from the reviewed 8.3.0 baseline.')
    return stable


def publish(commit, receipt, *, allow_write=False):
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise PublicationError('The full approved commit is missing.')
    repo = api(API_PREFIX)
    if (repo.get('full_name') != REPOSITORY or repo.get('default_branch') != 'development'
            or repo.get('private') is not False or repo.get('archived') is not False
            or repo.get('permissions', {}).get('push') is not True):
        raise PublicationError('Repository, default branch or existing write permission differs.')
    branch = api(API_PREFIX + '/branches/development')
    if branch.get('commit', {}).get('sha') != commit or branch.get('protected') is not True:
        raise PublicationError('Protected development head is not the approved merge.')
    accepted = tree_files(REVIEWED_SOURCE)
    candidate = tree_files(commit)
    prefix = 'custom_components/meteoswiss/'
    before = {k: v for k, v in accepted.items() if k.startswith(prefix)}
    after = {k: v for k, v in candidate.items() if k.startswith(prefix)}
    if any(mode != '100644' for mode, _ in after.values()):
        raise PublicationError('All component files must be regular non-executable files.')
    version_paths = {prefix + 'manifest.json', prefix + 'version.py'}
    identical_before = {k: v for k, v in before.items() if k not in version_paths}
    identical_after = {k: v for k, v in after.items() if k not in version_paths}
    if len(before) != 40 or before.keys() != after.keys() or identical_before != identical_after:
        raise PublicationError('Component code differs from the reviewed PR #70 source.')
    source_manifest = json.loads(read_file(REVIEWED_SOURCE, prefix + 'manifest.json'))
    expected_manifest = {**source_manifest, 'version': TAG}
    expected_version = read_file(REVIEWED_SOURCE, prefix + 'version.py').replace(
        '__version__ = "8.3.0"', '__version__ = "' + TAG + '"'
    )
    if (source_manifest.get('version') != '8.3.0'
            or json.loads(read_file(commit, prefix + 'manifest.json')) != expected_manifest
            or read_file(commit, prefix + 'version.py') != expected_version):
        raise PublicationError('Only the reviewed 8.3.1b1 version bump is allowed in component files.')
    source_hacs = json.loads(read_file(REVIEWED_SOURCE, 'hacs.json'))
    if (source_hacs.get('hide_default_branch') is not True
            or source_hacs.get('country') != 'CH'
            or json.loads(read_file(commit, 'hacs.json')) != source_hacs):
        raise PublicationError('HACS manifest differs from the reviewed branch-hiding change.')
    for tag, expected in PRESERVED_TAGS.items():
        if tag_commit(tag) != expected:
            raise PublicationError('An existing immutable tag differs: ' + tag)
    stable = verify_latest_stable()
    workflows_before = {k: v for k, v in accepted.items() if k.startswith('.github/workflows/')}
    workflows_after = {k: v for k, v in candidate.items() if k.startswith('.github/workflows/')}
    if workflows_before != workflows_after:
        raise PublicationError('Workflow files differ from the checked source.')
    manifest = json.loads(read_file(commit, prefix + 'manifest.json'))
    version = read_file(commit, prefix + 'version.py')
    if manifest.get('domain') != 'meteoswiss' or manifest.get('version') != TAG or '__version__ = "' + TAG + '"' not in version:
        raise PublicationError('Manifest, module version or domain does not match.')
    checks = check_statuses(commit)
    body = release_notes(commit)
    receipt.update({'component_files_identical': 38, 'version_files_checked': 2, 'hide_default_branch': True, 'workflow_files_unchanged': True,
                    'checks_successful': checks, 'prerelease': True, 'existing_tags_unchanged': True, 'country': 'CH',
                    'reviewed_source': REVIEWED_SOURCE, 'stable_release_id': stable['id']})
    existing_tag = tag_commit()
    if existing_tag is not None and existing_tag != commit:
        raise PublicationError('Existing prerelease tag points to another commit; nothing was changed.')
    existing = api(API_PREFIX + '/releases/tags/' + TAG, missing_ok=True)
    if existing is not None:
        verify_release(existing, commit)
        if existing.get('body') != body:
            raise PublicationError('Existing release notes differ; the release was not overwritten.')
        verify_latest_stable()
        receipt.update({'status': 'already_published_and_verified', 'release_created': False,
                        'release_url': RELEASE_URL, 'release_id': existing['id'], 'published_at': existing.get('published_at')})
        return receipt
    # Recheck the mutable branch immediately before the only remote write.
    if api(API_PREFIX + '/branches/development').get('commit', {}).get('sha') != commit:
        raise PublicationError('Development moved during preflight.')
    verify_latest_stable()
    if not allow_write:
        receipt.update({'status': 'ready_to_publish', 'release_created': False})
        return receipt
    receipt['release_write_attempted'] = True
    created = api(API_PREFIX + '/releases', method='POST', body={
        'tag_name': TAG, 'target_commitish': commit, 'name': TITLE, 'body': body,
        'draft': False, 'prerelease': True, 'make_latest': 'false',
        'generate_release_notes': False,
    })
    verify_release(created, commit)
    confirmed = api(API_PREFIX + '/releases/tags/' + TAG)
    verify_release(confirmed, commit)
    if confirmed.get('body') != body or confirmed.get('id') != created.get('id'):
        raise PublicationError('Published release notes could not be verified.')
    for tag, expected in PRESERVED_TAGS.items():
        if tag_commit(tag) != expected:
            raise PublicationError('An existing tag changed during publication.')
    verify_latest_stable()
    receipt.update({'status': 'published_and_verified', 'release_created': True,
                    'release_url': RELEASE_URL, 'release_id': confirmed['id'], 'published_at': confirmed.get('published_at')})
    return receipt


def main(commit, report_path, mode="--check"):
    report = Path(report_path)
    if report.exists():
        raise PublicationError('The local report path already exists.')
    receipt = {'tool_version': 'MeteoSwiss 8.3.1b1 Publisher V1.4',
               'repository': REPOSITORY, 'tag_name': TAG,
               'approved_publication_commit': commit, 'reviewed_source_commit': REVIEWED_SOURCE, 'focused_ha_ui_acceptance': 'pending_8.3.1b1', 'mode': mode,
               'status': 'not_published', 'release_write_attempted': False,
               'ha_writes_performed': False, 'core_restarted': False,
               'device_service_calls_sent': False}
    with report.open('x', encoding='utf-8') as handle:
        code = 0
        try:
            if mode not in {"--check", "--publish"}:
                raise PublicationError("Use --check or --publish.")
            publish(commit, receipt, allow_write=mode == "--publish")
        except Exception as exc:
            code = 1
            receipt['status'] = 'publication_result_unconfirmed' if receipt['release_write_attempted'] else 'stopped_before_publication'
            receipt['error_type'] = type(exc).__name__
            if isinstance(exc, PublicationError):
                receipt['reason'] = str(exc)
            print('STOP: ' + receipt.get('reason', 'Publication not fully verified (' + type(exc).__name__ + ').'))
            if receipt['release_write_attempted']:
                print('A GitHub release may already exist. Rerun this script to verify it first; do not delete or retag it.')
        receipt['checked_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        json.dump(receipt, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
    if code == 0:
        print('=== READY TO PUBLISH (READ ONLY) ===' if receipt['status'] == 'ready_to_publish' else '=== PRERELEASE VERIFIED ===')
        print('Version:', TAG)
        print('Release:', RELEASE_URL)
        print('38 component files match the reviewed source; two version files were checked separately.')
        print('Home Assistant was not changed or restarted.')
    print('Report:', report)
    return code


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
PY_PUBLISH
printf '%s\n' "Log: ${LOG}" 'Send the JSON and log to record the confirmed publication status.'
