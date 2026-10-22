#!/bin/bash
# Publish exactly the approved first MeteoSwiss fork prerelease from the Mac.
# GitHub only: no Home Assistant connection, installation, restart or device call.
set -Eeuo pipefail
umask 077
if [[ "${1:-}" = '--help' ]] || [[ "${1:-}" = '-h' ]]; then
  printf '%s\n' 'bash veroeffentliche_meteoswiss_beta_v1.0.sh --publish FREIGEGEBENER_MERGE_COMMIT' 'Prueft den exakten Commit und veroeffentlicht 8.2.0b1 als GitHub-Vorabversion.' 'Voraussetzungen: python3, gh und vorhandene GitHub-Anmeldung. Keine HA-Aenderung.'
  exit 0
fi
if [[ "$#" -ne 2 ]] || [[ "$1" != '--publish' ]] || ! [[ "$2" =~ ^[0-9a-f]{40}$ ]]; then
  printf '%s\n' 'Verwendung: bash veroeffentliche_meteoswiss_beta_v1.0.sh --publish FREIGEGEBENER_MERGE_COMMIT' >&2
  exit 2
fi
for program in gh python3; do
  command -v "${program}" >/dev/null || { printf 'Fehlt: %s\n' "${program}" >&2; exit 1; }
done
RUN_ID="$(date +%Y%m%d-%H%M%S)-$$"
DIAG_DIR="${HOME}/Downloads/HA/05_Diagnose"
REPORT="${DIAG_DIR}/meteoswiss_beta_release_v1.0_${RUN_ID}.json"
LOG="${DIAG_DIR}/meteoswiss_beta_release_v1.0_${RUN_ID}.log"
mkdir -p "${DIAG_DIR}"
exec > >(tee -a "${LOG}") 2>&1
printf '%s\n' '=== MeteoSwiss · erste Beta veroeffentlichen V1.0 ===' "Freigegebener Merge: $2" 'GitHub-Vorabversion 8.2.0b1; keine HA-Aenderung.'
python3 - "$2" "${REPORT}" <<'PY_PUBLISH'
"""Publish one approved prerelease; fail closed on changed code or checks."""
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
ACCEPTED_RUNTIME = '0086b956d44b7144b242c5d5c1881d0b0650e524'
TAG = '8.2.0b1'
TITLE = '8.2.0b1 — first maintained-fork prerelease'
RELEASE_URL = 'https://github.com/' + REPOSITORY + '/releases/tag/' + TAG
REQUIRED_CHECKS = {'tests', 'HA 2026.8.3', 'HA 2026.10.1', 'hassfest', 'Analyze Python', 'HACS validation'}


class PublicationError(RuntimeError):
    """A bounded public diagnostic, without subprocess stderr or credentials."""


def api(path, *, method='GET', body=None, missing_ok=False):
    """Use the user's existing gh authentication, with fixed host and repository."""
    if not path.startswith(API_PREFIX + '/') and path != API_PREFIX:
        raise PublicationError('Nicht zugelassener Repository-Pfad.')
    if method != 'GET' and not (method == 'POST' and path == API_PREFIX + '/releases'):
        raise PublicationError('Nicht zugelassene GitHub-Aenderung.')
    args = ['gh', 'api', '--hostname', 'github.com', '--method', method,
            '-H', 'Accept: application/vnd.github+json', path]
    if body is not None:
        args += ['--input', '-']
    result = subprocess.run(args, input=json.dumps(body) if body is not None else None,
                            text=True, capture_output=True, timeout=90, check=False)
    if result.returncode:
        if missing_ok and re.search(r'HTTP\s+404\b', result.stderr):
            return None
        raise PublicationError('GitHub-Abfrage fehlgeschlagen: ' + method + ' ' + path)
    try:
        return json.loads(result.stdout)
    except (ValueError, TypeError) as exc:
        raise PublicationError('GitHub-Antwort ist kein gueltiges JSON.') from exc


def read_file(commit, path):
    data = api(API_PREFIX + '/contents/' + path + '?ref=' + commit)
    if data.get('encoding') != 'base64' or data.get('size', 0) > 1024 * 1024:
        raise PublicationError('Unerwartetes Quellformat: ' + path)
    try:
        return base64.b64decode(data['content'], validate=False).decode('utf-8')
    except (ValueError, KeyError, UnicodeError) as exc:
        raise PublicationError('Quelldatei nicht lesbar: ' + path) from exc


def tree_files(commit):
    data = api(API_PREFIX + '/git/trees/' + commit + '?recursive=1')
    if data.get('truncated') is not False or not isinstance(data.get('tree'), list):
        raise PublicationError('Repository-Tree nicht vollstaendig gelesen.')
    return {row['path']: (row['mode'], row['sha']) for row in data['tree'] if row.get('type') == 'blob'}


def check_statuses(commit):
    data = api(API_PREFIX + '/commits/' + commit + '/check-runs?per_page=100')
    if data.get('total_count', 0) > 100:
        raise PublicationError('Pruefliste groesser als die begrenzte Abfrage.')
    latest = {}
    for row in data.get('check_runs', []):
        if row.get('id', -1) > latest.get(row['name'], {}).get('id', -2):
            latest[row['name']] = row
    if not REQUIRED_CHECKS <= latest.keys():
        raise PublicationError('Pflichtpruefungen fehlen noch fuer den Merge-Commit.')
    if any(row.get('status') != 'completed' or row.get('conclusion') != 'success' for row in latest.values()):
        raise PublicationError('Merge-Pruefungen sind noch nicht vollstaendig erfolgreich.')
    combined = api(API_PREFIX + '/commits/' + commit + '/status?per_page=100')
    if combined.get('total_count', 0) > 100:
        raise PublicationError('Statusliste groesser als die begrenzte Abfrage.')
    if any(row.get('state') != 'success' for row in combined.get('statuses', [])):
        raise PublicationError('Ein weiterer Commit-Status ist nicht erfolgreich.')
    return sorted(latest)


def tag_commit():
    data = api(API_PREFIX + '/git/ref/tags/' + TAG, missing_ok=True)
    if data is None:
        return None
    obj = data.get('object', {})
    for _ in range(5):
        if obj.get('type') == 'commit':
            return obj.get('sha')
        if obj.get('type') != 'tag' or not re.fullmatch(r'[0-9a-f]{40}', obj.get('sha', '')):
            break
        obj = api(API_PREFIX + '/git/tags/' + obj['sha']).get('object', {})
    raise PublicationError('Vorhandenen Tag nicht eindeutig auf Commit aufgeloest.')


def release_notes(commit):
    text = read_file(commit, 'docs/RELEASE_8.2.0b1.md')
    marker = '\nThis community fork builds on '
    if marker not in text or not text.startswith('# 8.2.0b1 — first maintained-fork prerelease\n'):
        raise PublicationError('Freigegebene Release-Hinweise nicht erkannt.')
    body = 'This community fork builds on ' + text.split(marker, 1)[1].lstrip()
    def absolute_link(match):
        target = match[1]
        if target.startswith(('https://', 'http://', '#')):
            return match[0]
        path, separator, anchor = target.partition('#')
        path = posixpath.normpath(posixpath.join('docs', path))
        if path.startswith('../') or path.startswith('/') or ':' in path:
            raise PublicationError('Unerwarteter relativer Release-Link.')
        return '](https://github.com/' + REPOSITORY + '/blob/' + commit + '/' + path + (separator + anchor if separator else '') + ')'
    return re.sub(r'\]\(([^)]+)\)', absolute_link, body)


def verify_release(release, commit):
    if (release.get('tag_name') != TAG or release.get('draft') is not False
            or release.get('prerelease') is not True or release.get('html_url') != RELEASE_URL):
        raise PublicationError('Release ist nicht die erwartete veroeffentlichte Vorabversion.')
    if tag_commit() != commit:
        raise PublicationError('Release-Tag zeigt nicht auf den freigegebenen Merge-Commit.')


def publish(commit, receipt):
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise PublicationError('Vollstaendiger freigegebener Commit fehlt.')
    repo = api(API_PREFIX)
    if (repo.get('full_name') != REPOSITORY or repo.get('default_branch') != 'development'
            or repo.get('private') is not False or repo.get('archived') is not False
            or repo.get('permissions', {}).get('push') is not True):
        raise PublicationError('Repository, Default-Branch oder vorhandene Schreibberechtigung weicht ab.')
    branch = api(API_PREFIX + '/branches/development')
    if branch.get('commit', {}).get('sha') != commit or branch.get('protected') is not True:
        raise PublicationError('Geschuetzter Development-Stand ist nicht der freigegebene Merge.')
    accepted = tree_files(ACCEPTED_RUNTIME)
    candidate = tree_files(commit)
    prefix = 'custom_components/meteoswiss/'
    before = {k: v for k, v in accepted.items() if k.startswith(prefix)}
    after = {k: v for k, v in candidate.items() if k.startswith(prefix)}
    if len(before) != 33 or before != after:
        raise PublicationError('Integrationsdateien weichen vom abgenommenen Laufzeitcode ab.')
    workflows_before = {k: v for k, v in accepted.items() if k.startswith('.github/workflows/')}
    workflows_after = {k: v for k, v in candidate.items() if k.startswith('.github/workflows/')}
    if workflows_before != workflows_after:
        raise PublicationError('Workflow-Dateien wurden seit der Abnahme veraendert.')
    manifest = json.loads(read_file(commit, prefix + 'manifest.json'))
    version = read_file(commit, prefix + 'version.py')
    if manifest.get('domain') != 'meteoswiss' or manifest.get('version') != TAG or '__version__ = "' + TAG + '"' not in version:
        raise PublicationError('Manifest, Modulversion oder Domain stimmen nicht ueberein.')
    checks = check_statuses(commit)
    body = release_notes(commit)
    receipt.update({'component_files_identical': 33, 'workflow_files_unchanged': True,
                    'checks_successful': checks, 'prerelease': True})
    existing_tag = tag_commit()
    if existing_tag is not None and existing_tag != commit:
        raise PublicationError('Bestehender Beta-Tag zeigt auf einen anderen Commit; nichts veraendert.')
    existing = api(API_PREFIX + '/releases/tags/' + TAG, missing_ok=True)
    if existing is not None:
        verify_release(existing, commit)
        if existing.get('body') != body:
            raise PublicationError('Vorhandene Release-Hinweise weichen ab; Release nicht ueberschrieben.')
        receipt.update({'status': 'already_published_and_verified', 'release_created': False,
                        'release_url': RELEASE_URL, 'published_at': existing.get('published_at')})
        return receipt
    # Recheck the mutable branch immediately before the only remote write.
    if api(API_PREFIX + '/branches/development').get('commit', {}).get('sha') != commit:
        raise PublicationError('Development wurde waehrend der Vorpruefung veraendert.')
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
        raise PublicationError('Veroeffentlichte Release-Hinweise nicht eindeutig bestaetigt.')
    receipt.update({'status': 'published_and_verified', 'release_created': True,
                    'release_url': RELEASE_URL, 'published_at': confirmed.get('published_at')})
    return receipt


def main(commit, report_path):
    report = Path(report_path)
    if report.exists():
        raise PublicationError('Lokaler Berichtsname existiert bereits.')
    receipt = {'tool_version': 'MeteoSwiss Beta Publisher V1.0',
               'repository': REPOSITORY, 'tag_name': TAG,
               'approved_publication_commit': commit, 'accepted_runtime_commit': ACCEPTED_RUNTIME,
               'status': 'not_published', 'release_write_attempted': False,
               'ha_writes_performed': False, 'core_restarted': False,
               'device_service_calls_sent': False}
    code = 0
    try:
        publish(commit, receipt)
    except Exception as exc:
        code = 1
        receipt['status'] = 'publication_result_unconfirmed' if receipt['release_write_attempted'] else 'stopped_before_publication'
        receipt['error_type'] = type(exc).__name__
        if isinstance(exc, PublicationError):
            receipt['reason'] = str(exc)
        print('ABBRUCH: ' + receipt.get('reason', 'Veroeffentlichung nicht vollstaendig bestaetigt (' + type(exc).__name__ + ').'))
        if receipt['release_write_attempted']:
            print('GitHub-Release kann bereits bestehen. Dieses Skript prueft bei Wiederholung zuerst den bestehenden Release; nichts loeschen oder umtaggen.')
    receipt['checked_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    with report.open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
    if code == 0:
        print('=== BETA VEROEFFENTLICHT UND BESTAETIGT ===')
        print('Vorabversion:', TAG)
        print('Release:', RELEASE_URL)
        print('33 Integrationsdateien identisch zum abgenommenen HA-Code.')
        print('Home Assistant wurde nicht veraendert oder neu gestartet.')
    print('Pruefbericht:', report)
    return code


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
PY_PUBLISH
printf '%s\n' "Protokoll: ${LOG}" 'Bitte JSON und Log senden; danach wird der tatsaechliche Veroeffentlichungsstand nachgefuehrt.'
