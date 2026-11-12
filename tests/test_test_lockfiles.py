"""Guard against platform-specific regeneration and unsafe dependency locks."""

from importlib import util
from pathlib import Path
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_test_lockfiles.py"
SPEC = util.spec_from_file_location("meteoswiss_test_locks", SCRIPT)
locks = util.module_from_spec(SPEC)
sys.modules[SPEC.name] = locks
SPEC.loader.exec_module(locks)

HASH_A = "a" * 64
HASH_B = "b" * 64


def pin(name="sample", version="1.0", marker="", hashes=(HASH_A,)):
    condition = "; " + marker if marker else ""
    return f"{name}=={version}{condition} " + " ".join(
        "--hash=sha256:" + value for value in hashes
    ) + "\n"


def test_real_universal_locks_and_compiler_requirements():
    """The committed baseline contains packages for all three host platforms."""
    root = SCRIPT.parents[1]
    for name in locks.LOCKS:
        content = (root / name).read_text(encoding="utf-8")
        parsed = locks.parse_lock(content)
        assert locks.compare_locks(content, content) > 100
        for platform in ("win32", "darwin", "linux"):
            assert any(platform in key for key in parsed)
        compiler = locks.compiler_requirements(content)
        assert len(locks.parse_lock(compiler)) == 2


def test_formatting_and_new_upstream_wheels_do_not_require_a_lock_update():
    committed = "# generated\n" + pin(hashes=(HASH_A,))
    regenerated = pin(name="Sample", hashes=(HASH_B, HASH_A))
    assert locks.compare_locks(committed, regenerated) == 1


@pytest.mark.parametrize("marker", ["sys_platform == 'win32'", "sys_platform == 'darwin'"])
def test_linux_only_recompilation_cannot_silently_remove_foreign_platforms(marker):
    universal = pin() + pin(name="platform-package", marker=marker)
    with pytest.raises(locks.LockfileError, match="Universal package"):
        locks.compare_locks(pin(), universal)


def test_removed_marker_cannot_make_a_platform_dependency_unconditional():
    with pytest.raises(locks.LockfileError, match="environment markers"):
        locks.compare_locks(pin(), pin(marker="sys_platform == 'linux'"))


def test_fixture_version_disagreement_is_rejected():
    with pytest.raises(locks.LockfileError, match="fixture inputs"):
        locks.compare_locks(pin(version="1.0"), pin(version="2.0"))


def test_hash_not_reported_by_the_native_resolver_is_rejected():
    with pytest.raises(locks.LockfileError, match="SHA-256 hash"):
        locks.compare_locks(pin(hashes=(HASH_A,)), pin(hashes=(HASH_B,)))


@pytest.mark.parametrize("content", [
    "", "sample==1.0\n", "sample==1.0 \\\n", pin() + pin(),
    "sample>=1.0 --hash=sha256:" + HASH_A,
    "sample==1.* --hash=sha256:" + HASH_A,
    "sample @ https://example.invalid/package.whl --hash=sha256:" + HASH_A,
    "--index-url https://example.invalid --hash=sha256:" + HASH_A,
    "sample==1.0 --hash=md5:" + HASH_A,
])
def test_unpinned_or_unsupported_lock_content_is_rejected(content):
    with pytest.raises(locks.LockfileError):
        locks.parse_lock(content)


@pytest.mark.parametrize("compiler", [
    pin(name="uv", version="0.13.3") + pin(name="packaging"),
    pin(name="uv", version="0.13.6"),
    pin(name="uv", version="0.13.6") * 2 + pin(name="packaging"),
    pin(name="uv", version="0.13.6", marker="sys_platform == 'linux'") + pin(name="packaging"),
    pin(name="uv", version="0.13.6") + "packaging==1.0\n",
    pin(name="uv", version="0.13.6") + pin(name="packaging") + " \\\n",
])
def test_bootstrap_cannot_install_an_outdated_or_unhashed_compiler(compiler):
    with pytest.raises(locks.LockfileError):
        locks.compiler_requirements(compiler)
