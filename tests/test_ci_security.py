"""Regression tests for CI installer and offline compatibility boundaries."""

from importlib import metadata, util
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from pathlib import Path
import subprocess
import sys
from threading import Thread

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_ci_security.py"
SPEC = util.spec_from_file_location("check_ci_security", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
security = util.module_from_spec(SPEC)
SPEC.loader.exec_module(security)


@pytest.fixture
def secure_environment(monkeypatch):
    """Represent the current-HA fixture with patched installer and CA bundle."""
    versions = {
        "pip": "26.2.2",
        "certifi": "2026.10.19",
        "homeassistant": "2026.10.1",
        "uv": "0.12.23",
    }

    def installed_version(name):
        if name not in versions:
            raise metadata.PackageNotFoundError(name)
        return versions[name]

    monkeypatch.setattr(security.metadata, "version", installed_version)
    monkeypatch.setattr(security.sys, "version_info", (3, 14, 10, "final", 0))
    monkeypatch.setenv("UV_OFFLINE", "true")
    return versions


@pytest.mark.parametrize("pip", ["26.2.1", "26.1", "26.2.2rc1"])
def test_bootstrap_rejects_stale_or_prerelease_pip(secure_environment, pip):
    secure_environment["pip"] = pip
    with pytest.raises(security.SecurityBaselineError):
        security.check_security("bootstrap")


@pytest.mark.parametrize("name", ["certifi", "homeassistant", "uv"])
def test_bootstrap_does_not_require_uninstalled_test_dependencies(secure_environment, name):
    del secure_environment[name]
    assert security.check_security("bootstrap")["pip"] == "26.2.2"


@pytest.mark.parametrize(
    "python",
    [(3, 14, 9, "final", 0), (3, 15, 2, "final", 0), (3, 14, 11, "candidate", 1)],
)
def test_rejects_stale_wrong_minor_or_prerelease_python(secure_environment, monkeypatch, python):
    monkeypatch.setattr(security.sys, "version_info", python)
    with pytest.raises(security.SecurityBaselineError, match="Python"):
        security.check_security("bootstrap")


@pytest.mark.parametrize("certifi", ["2026.10.18", "2026.7.22", "2026.10.19.dev1"])
def test_installed_rejects_stale_or_prerelease_ca_bundle(secure_environment, certifi):
    secure_environment["certifi"] = certifi
    with pytest.raises(security.SecurityBaselineError):
        security.check_security("installed", "2026.10.1")


@pytest.mark.parametrize("value", [None, "", "false", "0"])
@pytest.mark.parametrize("uv", ["0.12.23", "0.13.4"])
def test_uv_requires_offline_mode_even_when_patched(secure_environment, monkeypatch, value, uv):
    secure_environment["uv"] = uv
    if value is None:
        monkeypatch.delenv("UV_OFFLINE")
    else:
        monkeypatch.setenv("UV_OFFLINE", value)
    with pytest.raises(security.SecurityBaselineError, match="UV_OFFLINE"):
        security.check_security("installed", "2026.10.1")


@pytest.mark.parametrize("ha,uv", [("2026.8.3", "0.11.31"), ("2026.10.1", "0.12.23")])
def test_exact_legacy_ha_dependency_is_explicitly_offline_only(secure_environment, ha, uv):
    secure_environment.update(homeassistant=ha, uv=uv)
    report = security.check_security("installed", ha)
    assert report["UV_OFFLINE"] == "true"
    assert "not security-patched" in report["uv"]


@pytest.mark.parametrize(
    "ha,uv",
    [("2026.8.3", "0.12.23"), ("2026.10.1", "0.11.31"), ("2026.9.3", "0.12.23")],
)
def test_offline_exception_cannot_cover_other_legacy_dependencies(secure_environment, ha, uv):
    secure_environment.update(homeassistant=ha, uv=uv)
    with pytest.raises(security.SecurityBaselineError, match="approved offline"):
        security.check_security("installed", ha)


def test_installed_ha_must_match_the_matrix(secure_environment):
    with pytest.raises(security.SecurityBaselineError, match="does not match"):
        security.check_security("installed", "2026.8.3")


@pytest.mark.parametrize("name", ["pip", "certifi", "homeassistant", "uv"])
def test_missing_required_distribution_fails_closed(secure_environment, name):
    del secure_environment[name]
    with pytest.raises(security.SecurityBaselineError, match="missing"):
        security.check_security("installed", "2026.10.1")


def test_newer_final_releases_are_accepted(secure_environment, monkeypatch):
    secure_environment.update(pip="27.0", certifi="2026.10.23", uv="0.13.5")
    monkeypatch.setattr(security.sys, "version_info", (3, 14, 11, "final", 0))
    assert security.check_security("installed", "2026.10.1")["uv"] == "0.13.5"


def test_cli_failure_is_nonzero_and_does_not_expose_paths(secure_environment, monkeypatch, capsys):
    secure_environment["pip"] = "26.2.1"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "bootstrap"])
    assert security.main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == "CI security check failed: CI requires pip>=26.2.2."


def test_installed_uv_honours_offline_environment(socket_enabled, tmp_path):
    """Probe the real pinned binary; the control can reach only a local index."""
    requests = []

    class IndexHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(404)
            self.end_headers()

        def log_message(self, *_args):
            """Do not put request URLs in the test log."""

    server = HTTPServer(("127.0.0.1", 0), IndexHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    command = [
        sys.executable, "-m", "uv", "--no-config", "--no-cache", "pip", "compile",
        "--python", sys.executable,
        "--index-url", f"http://127.0.0.1:{server.server_port}/simple/", "-",
    ]
    # Do not inherit extra package indexes, proxies, credentials, or uv overrides.
    env = {
        "PATH": os.environ["PATH"],
        "UV_OFFLINE": "true",
        "UV_PYTHON_DOWNLOADS": "never",
    }
    try:
        offline = subprocess.run(
            command, input="meteoswiss-ci-offline-probe-nonexistent==0.0.0\n",
            env=env, cwd=tmp_path, text=True, capture_output=True, timeout=15, check=False,
        )
        assert offline.returncode != 0
        assert requests == []

        control = subprocess.run(
            command, input="meteoswiss-ci-offline-probe-nonexistent==0.0.0\n",
            env={**env, "UV_OFFLINE": "false"}, cwd=tmp_path,
            text=True, capture_output=True, timeout=15, check=False,
        )
        assert control.returncode != 0
        assert requests  # Proves the same binary/command can reach the local detector.
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
