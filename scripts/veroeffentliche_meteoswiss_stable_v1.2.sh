#!/bin/bash
# Publish exactly the approved first stable MeteoSwiss fork release from the Mac.
# GitHub only: no Home Assistant connection, installation, restart or device call.
set -Eeuo pipefail
umask 077
if [[ "${1:-}" = '--help' ]] || [[ "${1:-}" = '-h' ]]; then
  printf '%s\n' 'bash veroeffentliche_meteoswiss_stable_v1.2.sh --check|--publish APPROVED_MERGE_COMMIT' 'Checks the exact commit read-only with --check; --publish creates stable 8.2.0.' 'Requires python3, gh and existing GitHub authentication. No HA changes.'
  exit 0
fi
if [[ "$#" -ne 2 ]] || { [[ "$1" != '--check' ]] && [[ "$1" != '--publish' ]]; } || ! [[ "$2" =~ ^[0-9a-f]{40}$ ]]; then
  printf '%s\n' 'Usage: bash veroeffentliche_meteoswiss_stable_v1.2.sh --check|--publish APPROVED_MERGE_COMMIT' >&2
  exit 2
fi
for program in gh python3; do
  command -v "${program}" >/dev/null || { printf 'Missing: %s\n' "${program}" >&2; exit 1; }
done
RUN_ID="$(date +%Y%m%d-%H%M%S)-$$"
DIAG_DIR="${HOME}/Downloads/HA/05_Diagnose"
REPORT="${DIAG_DIR}/meteoswiss_stable_release_v1.2_${RUN_ID}.json"
LOG="${DIAG_DIR}/meteoswiss_stable_release_v1.2_${RUN_ID}.log"
mkdir -p "${DIAG_DIR}"
exec > >(tee -a "${LOG}") 2>&1
printf '%s\n' '=== MeteoSwiss · stable publication V1.2 ===' "Approved merge: $2" 'GitHub stable release 8.2.0; no Home Assistant changes.'
python3 - "$2" "${REPORT}" "$1" <<'PY_PUBLISH'
"""Derive from Beta Publisher V1.1; check/publish one exact stable package."""
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
# Published Beta2; focused setup/data display operator-confirmed on 22 October.
ACCEPTED_RUNTIME = '80bf9195ecc3d42d9e4d1beb4ce8143e2c2df2c8'
BETA_COMMITS = {
    '8.2.0b1': 'abbb6b7701134ac2573f35b425ab3f0697a80540',
    '8.2.0b2': ACCEPTED_RUNTIME,
}
TAG = '8.2.0'
TITLE = '8.2.0 — first stable maintained-fork release'
RELEASE_URL = 'https://github.com/' + REPOSITORY + '/releases/tag/' + TAG
REQUIRED_CHECKS = {'tests', 'HA 2026.8.3', 'HA 2026.10.1', 'hassfest', 'Analyze Python', 'HACS validation'}


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
    if any(latest[name].get('app', {}).get('id') != 15368 or latest[name].get('head_sha') != commit
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
    text = read_file(commit, 'docs/RELEASE_8.2.0.md')
    marker = '\nThis community fork builds on '
    if marker not in text or not text.startswith('# 8.2.0 — first stable maintained-fork release\n'):
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
    if (release.get('tag_name') != TAG or release.get('draft') is not False
            or release.get('prerelease') is not False or release.get('html_url') != RELEASE_URL):
        raise PublicationError('Release is not the expected published stable release.')
    if tag_commit() != commit:
        raise PublicationError('Release tag does not point to the approved merge commit.')


def publish(commit, receipt, *, allow_write=True):
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
    accepted = tree_files(ACCEPTED_RUNTIME)
    candidate = tree_files(commit)
    prefix = 'custom_components/meteoswiss/'
    before = {k: v for k, v in accepted.items() if k.startswith(prefix)}
    after = {k: v for k, v in candidate.items() if k.startswith(prefix)}
    version_paths = {prefix + 'manifest.json', prefix + 'version.py'}
    identical_before = {k: v for k, v in before.items() if k not in version_paths}
    identical_after = {k: v for k, v in after.items() if k not in version_paths}
    if len(before) != 33 or before.keys() != after.keys() or identical_before != identical_after:
        raise PublicationError('Component code differs from the accepted Beta2 source.')
    source_manifest = json.loads(read_file(ACCEPTED_RUNTIME, prefix + 'manifest.json'))
    expected_manifest = {**source_manifest, 'version': TAG}
    expected_version = read_file(ACCEPTED_RUNTIME, prefix + 'version.py').replace(
        '__version__ = "8.2.0b2"', '__version__ = "' + TAG + '"'
    )
    if (source_manifest.get('version') != '8.2.0b2'
            or json.loads(read_file(commit, prefix + 'manifest.json')) != expected_manifest
            or read_file(commit, prefix + 'version.py') != expected_version):
        raise PublicationError('Only the reviewed stable version bump is allowed in component files.')
    source_hacs = json.loads(read_file(ACCEPTED_RUNTIME, 'hacs.json'))
    if (source_hacs.get('hide_default_branch') is not True
            or json.loads(read_file(commit, 'hacs.json')) != source_hacs):
        raise PublicationError('HACS manifest differs from the reviewed branch-hiding change.')
    for beta, expected in BETA_COMMITS.items():
        if tag_commit(beta) != expected:
            raise PublicationError('An immutable beta tag differs: ' + beta)
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
    receipt.update({'component_files_identical': 31, 'version_files_checked': 2, 'hide_default_branch': True, 'workflow_files_unchanged': True,
                    'checks_successful': checks, 'prerelease': False, 'beta_tags_unchanged': True})
    existing_tag = tag_commit()
    if existing_tag is not None and existing_tag != commit:
        raise PublicationError('Existing stable tag points to another commit; nothing was changed.')
    existing = api(API_PREFIX + '/releases/tags/' + TAG, missing_ok=True)
    if existing is not None:
        verify_release(existing, commit)
        if existing.get('body') != body:
            raise PublicationError('Existing release notes differ; the release was not overwritten.')
        receipt.update({'status': 'already_published_and_verified', 'release_created': False,
                        'release_url': RELEASE_URL, 'published_at': existing.get('published_at')})
        return receipt
    # Recheck the mutable branch immediately before the only remote write.
    if api(API_PREFIX + '/branches/development').get('commit', {}).get('sha') != commit:
        raise PublicationError('Development moved during preflight.')
    if not allow_write:
        receipt.update({'status': 'ready_to_publish', 'release_created': False})
        return receipt
    receipt['release_write_attempted'] = True
    created = api(API_PREFIX + '/releases', method='POST', body={
        'tag_name': TAG, 'target_commitish': commit, 'name': TITLE, 'body': body,
        'draft': False, 'prerelease': False, 'make_latest': 'true',
        'generate_release_notes': False,
    })
    verify_release(created, commit)
    confirmed = api(API_PREFIX + '/releases/tags/' + TAG)
    verify_release(confirmed, commit)
    if confirmed.get('body') != body or confirmed.get('id') != created.get('id'):
        raise PublicationError('Published release notes could not be verified.')
    receipt.update({'status': 'published_and_verified', 'release_created': True,
                    'release_url': RELEASE_URL, 'published_at': confirmed.get('published_at')})
    return receipt


def main(commit, report_path, mode="--publish"):
    report = Path(report_path)
    if report.exists():
        raise PublicationError('The local report path already exists.')
    receipt = {'tool_version': 'MeteoSwiss Stable Publisher V1.2',
               'repository': REPOSITORY, 'tag_name': TAG,
               'approved_publication_commit': commit, 'accepted_beta_commit': ACCEPTED_RUNTIME, 'focused_ha_ui_acceptance': 'operator_confirmed_2026-10-22', 'mode': mode,
               'status': 'not_published', 'release_write_attempted': False,
               'ha_writes_performed': False, 'core_restarted': False,
               'device_service_calls_sent': False}
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
    with report.open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
    if code == 0:
        print('=== READY TO PUBLISH (READ ONLY) ===' if receipt['status'] == 'ready_to_publish' else '=== STABLE RELEASE VERIFIED ===')
        print('Version:', TAG)
        print('Release:', RELEASE_URL)
        print('31 component files match the CI-tested source; two version files were checked separately.')
        print('Home Assistant was not changed or restarted.')
    print('Report:', report)
    return code


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
PY_PUBLISH
printf '%s\n' "Log: ${LOG}" 'Send the JSON and log to record the confirmed publication status.'
