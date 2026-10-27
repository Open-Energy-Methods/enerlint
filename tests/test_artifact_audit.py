"""Focused positive/negative controls for the CI publishing hygiene gate.

These tests check archive shape and selected credential patterns, not the
absence of every possible secret or third-party provenance.
"""

from __future__ import annotations

import io
import json
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts.audit_release_artifacts import (
    AuditError,
    _check_path,
    _scan_bytes,
    audit_package,
)

METADATA = b"Name: enerlint\nVersion: 0.1.0a0\nLicense-Expression: MIT\nLicense-File: LICENSE\n\n"


def make_wheel(tmp_path: Path, extra: dict[str, bytes] | None = None) -> Path:
    path = tmp_path / "enerlint-0.1.0a0-py3-none-any.whl"
    members = {
        "enerlint/verify.py": b"def check_case(x): return x\n",
        "enerlint/schemas/report-v0.1.0.schema.json": b'{"type":"object"}\n',
        "enerlint-0.1.0a0.dist-info/METADATA": METADATA,
        "enerlint-0.1.0a0.dist-info/licenses/LICENSE": b"MIT License\n",
    }
    members.update(extra or {})
    with zipfile.ZipFile(path, "w") as archive:
        for name, contents in members.items():
            archive.writestr(name, contents)
    return path


def make_sdist(tmp_path: Path, extra: dict[str, bytes] | None = None) -> Path:
    path = tmp_path / "enerlint-0.1.0a0.tar.gz"
    root = "enerlint-0.1.0a0/"
    members = {
        root + "src/enerlint/verify.py": b"def check_case(x): return x\n",
        root + "src/enerlint/schemas/report-v0.1.0.schema.json": b'{"type":"object"}\n',
        root + "pyproject.toml": b'[project]\nname = "enerlint"\n',
        root + "PKG-INFO": METADATA,
        root + "LICENSE": b"MIT License\n",
        root + "CITATION.cff": b"cff-version: 1.2.0\n",
        root + "examples/steady_compressor.json": b"{}\n",
        root + "docs/VERIFICATION_CONTRACT.md": b"# Contract\n",
        root + "scripts/run_foundation_benchmark.py": b"pass\n",
        root + "tests/test_steady.py": b"pass\n",
    }
    members.update(extra or {})
    with tarfile.open(path, "w:gz") as archive:
        for name, contents in members.items():
            member = tarfile.TarInfo(name)
            member.size = len(contents)
            archive.addfile(member, io.BytesIO(contents))
    return path


def test_both_minimal_archive_shapes_and_metadata_are_accepted(tmp_path):
    for path in (make_wheel(tmp_path), make_sdist(tmp_path)):
        report = audit_package(path)
        assert report["filename"] == path.name
        assert report["contains_report_schema"]
        assert report["contains_license"]
        assert report["runtime_dependencies"] == []
        assert len(report["sha256"]) == 64


@pytest.mark.parametrize(
    "filename",
    [
        "../outside.txt",
        "/etc/passwd",
        "src/../secret.txt",
        "my/credentials.json",
        "file.pem",
        "private/notebook.txt",
        "src/.env",
        "oem_enerlint_founders_research_bible.md",
    ],
)
def test_prohibited_distribution_paths_rejected(filename):
    with pytest.raises(AuditError):
        _check_path(filename)


@pytest.mark.parametrize(
    "kind,prefix",
    [
        ("GitHub token", b"ghp_"),
        ("GitHub fine-grained token", b"github_pat_"),
        ("AWS access key ID", b"AKIA"),
    ],
)
def test_high_confidence_credential_patterns_are_detected(kind, prefix):
    token = prefix + b"A" * 48
    with pytest.raises(AuditError, match=kind):
        _scan_bytes(b"secret = '" + token + b"'\n", "case.txt")


def test_sensitive_value_is_not_reproduced_in_exception():
    token = b"ghp_" + b"Z" * 40
    with pytest.raises(AuditError) as found:
        _scan_bytes(token, "danger.txt")
    assert token.decode("ascii") not in str(found.value)


def test_private_key_boundary_rejected():
    start = b"-----BEGIN " + b"RSA PRIVATE KEY-----"
    with pytest.raises(AuditError, match="PEM private key"):
        _scan_bytes(start + b"\nAAAAAAAAAA\n", "key.txt")


def test_benign_scientific_synthetic_values_are_not_secrets():
    data = json.dumps({
        "schema_version": "0.1.0",
        "case_id": "synthetic_adiabatic_compressor",
        "mass_flow_kg_s": 2.0,
        "specific_enthalpy_j_kg": 300000.0,
    }).encode()
    _scan_bytes(data, "example.json")


def test_wheel_with_private_file_is_rejected(tmp_path):
    archive = make_wheel(tmp_path, {"enerlint/credentials.json": b"hidden"})
    with pytest.raises(AuditError, match="Sensitive filename"):
        audit_package(archive)


def test_sdist_with_credential_like_value_is_rejected(tmp_path):
    secret = b"AKIA" + b"0" * 16
    archive = make_sdist(tmp_path, {"enerlint-0.1.0a0/docs/notes.txt": secret})
    with pytest.raises(AuditError, match="AWS access"):
        audit_package(archive)


def test_dependency_metadata_requires_no_runtime_dependencies(tmp_path):
    wheel = make_wheel(tmp_path, {
        "enerlint-0.1.0a0.dist-info/METADATA":
            METADATA.replace(b"\n\n", b"\nRequires-Dist: unsafe-package>=1\n\n"),
    })
    with pytest.raises(AuditError, match="Unexpected runtime dependencies"):
        audit_package(wheel)


def test_dev_only_optional_dependency_remains_allowed(tmp_path):
    wheel = make_wheel(tmp_path, {
        "enerlint-0.1.0a0.dist-info/METADATA":
            METADATA.replace(b"\n\n", b"\nRequires-Dist: pytest>=8; extra == 'dev'\n\n"),
    })
    assert audit_package(wheel)["runtime_dependencies"] == []


def test_missing_report_schema_is_rejected(tmp_path):
    wheel = make_wheel(tmp_path)
    with zipfile.ZipFile(wheel, "r") as archive:
        items = {i.filename: archive.read(i) for i in archive.infolist()}
    items.pop("enerlint/schemas/report-v0.1.0.schema.json")
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, value in items.items():
            archive.writestr(name, value)
    with pytest.raises(AuditError, match="lacks expected module/schema"):
        audit_package(wheel)



def test_sdist_with_setuptools_egg_info_duplicate_metadata_is_accepted(tmp_path):
    """Setuptools may ship both root and egg-info PKG-INFO in a source archive."""
    archive = make_sdist(tmp_path, {
        "enerlint-0.1.0a0/src/enerlint.egg-info/PKG-INFO": METADATA,
    })
    result = audit_package(archive)
    assert result["contains_report_schema"]
    assert result["runtime_dependencies"] == []


def test_non_spdx_license_metadata_rejected(tmp_path):
    metadata = METADATA.replace(b"License-Expression: MIT", b"License: MIT")
    archive = make_wheel(tmp_path, {
        "enerlint-0.1.0a0.dist-info/METADATA": metadata,
    })
    with pytest.raises(AuditError, match="SPDX License-Expression"):
        audit_package(archive)


def test_missing_license_file_metadata_rejected(tmp_path):
    metadata = METADATA.replace(b"License-File: LICENSE\n", b"")
    archive = make_sdist(tmp_path, {
        "enerlint-0.1.0a0/PKG-INFO": metadata,
    })
    with pytest.raises(AuditError, match="License-File"):
        audit_package(archive)
