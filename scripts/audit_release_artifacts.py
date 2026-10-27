"""Inspect committed source and built distributions; write a CI build manifest.

Usage after `python -m build --sdist --wheel`:
    python scripts/audit_release_artifacts.py

This is a *bounded* supply-chain hygiene check, not comprehensive secret
detection, independent provenance attestation, SLSA compliance, or a claim of
reproducible byte-identical builds. Python 3.10+, standard library only.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tarfile
import zipfile
from datetime import datetime, timezone
from email.parser import Parser
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
MANIFEST = ROOT / "artifacts" / "ci" / "build-manifest.json"
MAX_MEMBER_BYTES = 8 * 1024 * 1024
BAD_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".jks", ".kdbx", ".sqlite", ".db")
BAD_NAMES = {".env", ".netrc", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"}
BAD_PATH_PARTS = {"__pycache__", ".git", ".venv", ".tox", "private", "secrets"}
KEY_PATTERNS = {
    "PEM private key": re.compile(rb"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    "GitHub token": re.compile(rb"gh[pousr]_[A-Za-z0-9_]{30,}"),
    "GitHub fine-grained token": re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    "AWS access key ID": re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    "Slack token": re.compile(rb"xox[baprs]-[0-9A-Za-z-]{20,}"),
}


class AuditError(ValueError):
    """Source or distribution failed a conservative publishing hygiene gate."""


def sha256(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def _check_path(name: str, *, is_directory: bool = False) -> None:
    path = PurePosixPath(name)
    if not name or name.startswith("/") or "\\" in name or ".." in path.parts:
        raise AuditError(f"Unsafe archive path: {name!r}")
    if path.name in BAD_NAMES or path.name.lower().endswith(BAD_SUFFIXES):
        raise AuditError(f"Sensitive filename present in archive: {name!r}")
    if any(x.lower() in BAD_PATH_PARTS for x in path.parts):
        raise AuditError(f"Private/build directory included in archive: {name!r}")
    if "founders_research_bible" in name.lower() or "oem_enerlint_founders" in name.lower():
        raise AuditError(f"Private strategy file included: {name!r}")
    if not is_directory and len(name) > 500:
        raise AuditError("Unexpectedly long archive member path")


def _scan_bytes(contents: bytes, filename: str) -> None:
    if len(contents) > MAX_MEMBER_BYTES:
        raise AuditError(f"File too large for bounded security review: {filename!r}")
    for description, pattern in KEY_PATTERNS.items():
        if pattern.search(contents):
            raise AuditError(f"Possible {description} in {filename!r} (do not print the value)")


def tracked_source_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True, check=True,
    )
    tracked = [
        ROOT / os.fsdecode(piece)
        for piece in result.stdout.split(b"\0") if piece
    ]
    if not tracked:
        raise AuditError("No tracked files to inspect")
    return sorted(tracked)


def audit_sources() -> int:
    """Check exact git-tracked source, not environment/config untracked files."""
    files = tracked_source_paths()
    for file in files:
        relative = file.relative_to(ROOT).as_posix()
        _check_path(relative)
        if file.is_symlink():
            raise AuditError(f"Tracked symbolic link needs explicit audit: {relative}")
        if not file.is_file():
            raise AuditError(f"Tracked file unavailable: {relative}")
        _scan_bytes(file.read_bytes(), relative)
    return len(files)


def archive_members(path: Path) -> dict[str, bytes]:
    members: dict[str, bytes] = {}
    if path.name.endswith(".whl"):
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                _check_path(info.filename, is_directory=info.is_dir())
                mode = info.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise AuditError(f"Wheel contains symlink: {info.filename}")
                if info.is_dir():
                    continue
                if info.filename in members:
                    raise AuditError(f"Duplicate wheel member: {info.filename}")
                if info.file_size > MAX_MEMBER_BYTES:
                    raise AuditError(f"Oversized wheel member: {info.filename}")
                contents = archive.read(info)
                _scan_bytes(contents, info.filename)
                members[info.filename] = contents
    elif path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            for info in archive.getmembers():
                _check_path(info.name, is_directory=info.isdir())
                if info.isdir():
                    continue
                if not info.isfile():
                    raise AuditError(f"Sdist contains link/device/special member: {info.name}")
                if info.name in members:
                    raise AuditError(f"Duplicate sdist member: {info.name}")
                if info.size > MAX_MEMBER_BYTES:
                    raise AuditError(f"Oversized sdist member: {info.name}")
                extracted = archive.extractfile(info)
                if extracted is None:
                    raise AuditError(f"Cannot read source file: {info.name}")
                contents = extracted.read(MAX_MEMBER_BYTES + 1)
                _scan_bytes(contents, info.name)
                members[info.name] = contents
    else:
        raise AuditError(f"Unknown distribution type: {path.name}")
    return members


def audit_package(path: Path) -> dict:
    members = archive_members(path)
    filenames = list(members)
    if path.name.endswith(".whl"):
        required = {"enerlint/verify.py", "enerlint/schemas/report-v0.1.0.schema.json"}
        if not required.issubset(members):
            raise AuditError("Wheel lacks expected module/schema")
        if not all(
            name.startswith("enerlint/") or ".dist-info/" in name
            for name in filenames
        ):
            raise AuditError("Unexpected top-level payload in wheel")
        metadata_paths = [x for x in filenames if x.endswith(".dist-info/METADATA")]
    else:
        roots = {PurePosixPath(name).parts[0] for name in filenames}
        if len(roots) != 1 or not next(iter(roots)).startswith("enerlint-"):
            raise AuditError("Unexpected sdist root structure")
        root = next(iter(roots))
        required = {
            f"{root}/src/enerlint/verify.py",
            f"{root}/src/enerlint/schemas/report-v0.1.0.schema.json",
            f"{root}/pyproject.toml",
        }
        if not required.issubset(members):
            raise AuditError("Sdist lacks expected source/schema/build configuration")
        # Setuptools sdists may contain both top-level PKG-INFO and
        # src/enerlint.egg-info/PKG-INFO. The top-level file is authoritative.
        metadata_paths = [f"{root}/PKG-INFO"] if f"{root}/PKG-INFO" in members else []
    if len(metadata_paths) != 1:
        raise AuditError(f"Expected one package metadata file, got {metadata_paths!r}")
    metadata = Parser().parsestr(members[metadata_paths[0]].decode("utf-8"))
    if metadata["Name"].lower() != "enerlint" or metadata["Version"] != "0.1.0a0":
        raise AuditError("Unexpected package name/version in built metadata")
    runtime_dependencies = [
        spec for spec in metadata.get_all("Requires-Dist", [])
        if "extra ==" not in spec.lower()
    ]
    if runtime_dependencies:
        raise AuditError(f"Unexpected runtime dependencies: {runtime_dependencies!r}")
    if metadata.get("License-Expression") != "MIT":
        raise AuditError("Missing or incorrect SPDX License-Expression: expected MIT")
    declared_licenses = metadata.get_all("License-File", [])
    if "LICENSE" not in declared_licenses:
        raise AuditError("Distribution metadata missing License-File: LICENSE")
    license_paths = [x for x in filenames if PurePosixPath(x).name == "LICENSE"]
    if len(license_paths) != 1:
        raise AuditError("Expected exactly one distributed LICENSE file")
    if not members[license_paths[0]].startswith(b"MIT License"):
        raise AuditError("Distributed license content does not begin with MIT License")
    return {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path.read_bytes()),
        "member_count": len(members),
        "runtime_dependencies": runtime_dependencies,
        "contains_license": True,
        "license_expression": "MIT",
        "contains_report_schema": True,
    }


def build_tool_versions() -> dict[str, str | None]:
    """Record installed build/test package versions without assuming they are pinned."""
    packages = ("build", "setuptools", "wheel", "pytest", "jsonschema", "ruff")
    result: dict[str, str | None] = {}
    for package in packages:
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = None
    return result


def main() -> int:
    try:
        wheels = sorted(DIST.glob("enerlint-*.whl"))
        sdists = sorted(DIST.glob("enerlint-*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            raise AuditError(
                "Expected one wheel and one sdist: clear dist/ and rebuild before running the audit"
            )
        tracked_count = audit_sources()
        products = [audit_package(path) for path in wheels + sdists]
        manifest = {
            "manifest_version": "0.1.0",
            "purpose": "CI software build inventory and bounded secret/path scan, not physical validation",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit_sha": os.environ.get("GITHUB_SHA") or None,
            "github_run_id": os.environ.get("GITHUB_RUN_ID") or None,
            "runner_os": os.environ.get("RUNNER_OS") or sys.platform,
            "python_version": sys.version.split()[0],
            "build_tool_versions": build_tool_versions(),
            "source_tracked_file_count": tracked_count,
            "security_checks": [
                "git tracked files: bounded token/private-key pattern and prohibited names",
                "wheel and sdist: path traversal, symlinks, oversized files and payload scan",
                "distribution: exact version/name, license, report schema, runtime dependencies",
            ],
            "artifact_checksums_are_build_specific": True,
            "limitations": [
                "Pattern scanning misses many credential formats and cannot prove absence of secrets.",
                "A git-tracked source scan does not inspect untracked files or external provenance.",
                "Artifact SHA-256 hashes identify this build; byte-for-byte reproducibility was NOT tested.",
                "Dependency/build-backend provenance is not independently attested or pinned here.",
                "CI success is neither scientific validation nor OpenSSF/SLSA certification.",
            ],
            "distributions": products,
        }
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(
            json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    except (AuditError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ARTIFACT_AUDIT_FAILED: {exc}", file=sys.stderr)
        return 1
    print(
        f"PASS limited artifact/security audit: {tracked_count} tracked files, "
        f"{len(products)} build archives; manifest: {MANIFEST.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
