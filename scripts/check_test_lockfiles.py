"""Verify test locks with the original universal compiler in an isolated directory."""

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LOCKS = ("requirements_test.txt", "requirements_test_min.txt")
HASH = re.compile(r"--hash=sha256:([0-9a-f]{64})(?=\s|$)")


class LockfileError(ValueError):
    """A dependency lock has lost its reproducible, universal contract."""


@dataclass(frozen=True)
class LockedRequirement:
    """One exact package selection, including its environment condition."""

    requirement: str
    hashes: frozenset[str]


def logical_lines(content: str) -> list[str]:
    """Join pip continuations without interpreting comments as requirements."""
    result = []
    pending = ""
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        continued = line.endswith("\\")
        pending += " " + (line[:-1] if continued else line)
        if not continued:
            result.append(pending.strip())
            pending = ""
    if pending:
        raise LockfileError("Unterminated requirement continuation.")
    return result


def compiler_requirements(content: str) -> str:
    """Extract only the hash-pinned compiler/parser without bootstrap imports."""
    selected = {}
    for line in logical_lines(content):
        match = re.match(r"(uv|packaging)==([0-9]+(?:\.[0-9]+){1,2})\s+", line)
        if match is None:
            continue
        name = match[1]
        hashes = HASH.findall(line)
        remaining = HASH.sub("", line).strip()
        if name in selected or not hashes or remaining != match[0].strip():
            raise LockfileError("Invalid compiler requirement.")
        version = tuple(int(part) for part in match[2].split("."))
        if name == "uv" and version < (0, 13, 4):
            raise LockfileError("The universal compiler must be uv>=0.13.4.")
        selected[name] = line
    if set(selected) != {"uv", "packaging"}:
        raise LockfileError("Hash-pinned uv and packaging are required.")
    return "\n".join(selected[name] for name in sorted(selected)) + "\n"


def parse_lock(content: str) -> dict[str, LockedRequirement]:
    """Compare package versions, extras, markers and hashes; ignore formatting."""
    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.utils import canonicalize_name

    result = {}
    for line in logical_lines(content):
        hashes = frozenset(HASH.findall(line))
        requirement_text = HASH.sub("", line).strip()
        if not hashes:
            raise LockfileError("Every locked requirement needs SHA-256 hashes.")
        try:
            requirement = Requirement(requirement_text)
        except InvalidRequirement as err:
            raise LockfileError("Unsupported locked requirement.") from err
        specs = list(requirement.specifier)
        if (
            requirement.url is not None
            or len(specs) != 1
            or specs[0].operator != "=="
            or "*" in specs[0].version
        ):
            raise LockfileError("Only exact package pins are allowed in test locks.")
        name = canonicalize_name(requirement.name)
        extras = "[" + ",".join(sorted(requirement.extras)) + "]" if requirement.extras else ""
        marker = "; " + str(requirement.marker) if requirement.marker is not None else ""
        key = name + extras + marker
        if key in result:
            raise LockfileError("Duplicate locked requirement.")
        result[key] = LockedRequirement(name + extras + str(requirement.specifier) + marker, hashes)
    if not result:
        raise LockfileError("The dependency lock is empty.")
    return result


def compare_locks(committed: str, regenerated: str) -> int:
    """Reject missing foreign-platform packages, changed pins or invalid hashes."""
    actual = parse_lock(committed)
    expected = parse_lock(regenerated)
    if set(actual) != set(expected):
        raise LockfileError("Universal package selections or environment markers differ.")
    for key, locked in actual.items():
        canonical = expected[key]
        if locked.requirement != canonical.requirement:
            raise LockfileError("A locked version disagrees with its fixture inputs.")
        # New wheels for an existing release can add hashes upstream. The
        # committed hashes must all remain valid, but need not include new wheels.
        if not locked.hashes <= canonical.hashes:
            raise LockfileError("A committed SHA-256 hash is absent from the regenerated lock.")
    return len(actual)


def verify(root: Path) -> dict[str, int]:
    """Resolve copies, preserving selected versions and leaving the checkout intact."""
    report = {}
    with tempfile.TemporaryDirectory(prefix="meteoswiss-locks-") as directory:
        work = Path(directory)
        for name in (*LOCKS, *(Path(name).with_suffix(".in").name for name in LOCKS),
                     "requirements_ci_security.txt"):
            shutil.copyfile(root / name, work / name)
        env = os.environ.copy()
        env["UV_OFFLINE"] = "false"
        env["UV_PYTHON_DOWNLOADS"] = "never"
        env["UV_NO_CONFIG"] = "true"
        for name in LOCKS:
            completed = subprocess.run(
                ["uv", "pip", "compile", "--universal", "--python-version", "3.14.10",
                 "--generate-hashes", "--output-file", name,
                 Path(name).with_suffix(".in").name],
                cwd=work, env=env, capture_output=True, text=True, timeout=300,
                check=False,
            )
            if completed.returncode != 0:
                raise LockfileError("Universal dependency regeneration failed; no checkout files changed.")
            report[name] = compare_locks(
                (root / name).read_text(encoding="utf-8"),
                (work / name).read_text(encoding="utf-8"),
            )
    return report


def main() -> int:
    """Provide hash-pinned bootstrap requirements or verify both fixture locks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("compiler", "verify"))
    args = parser.parse_args()
    try:
        if args.command == "compiler":
            print(compiler_requirements((ROOT / LOCKS[0]).read_text(encoding="utf-8")), end="")
        else:
            for name, count in verify(ROOT).items():
                print(f"{name}: {count} universal package selections verified")
    except (LockfileError, OSError, subprocess.TimeoutExpired) as err:
        # Registry errors can contain credentials or environment-specific paths.
        message = str(err) if isinstance(err, LockfileError) else "Lock verification could not complete."
        print(f"Test lock verification failed: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
