"""Release-metadata regression guards; no publication or ownership claim.

The machine-readable SPDX metadata is built by setuptools (PEP 639).
CI separately validates distribution archives, the CFF schema and twine.
"""

from __future__ import annotations

import re
from importlib.metadata import metadata, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CITATION = ROOT / "CITATION.cff"
PROJECT = ROOT / "pyproject.toml"
LICENSE = ROOT / "LICENSE"
SDIST_MANIFEST = ROOT / "MANIFEST.in"

CORRECT_ORCID = "https://orcid.org/0009-0009-8429-1266"
OLD_UNRELATED_ORCID = "https://orcid.org/0000-0003-0299-5745"


def test_package_and_cff_use_same_explicit_alpha_version():
    packaging = PROJECT.read_text(encoding="utf-8")
    citation = CITATION.read_text(encoding="utf-8")
    declared = re.search(r'^version = "([^"]+)"$', packaging, re.MULTILINE)
    assert declared is not None
    assert declared.group(1) == version("enerlint") == "0.1.0a0"
    assert re.search(r"^version: 0\.1\.0a0$", citation, re.MULTILINE)


def test_correct_author_orcid_never_aliases_another_researcher():
    citation = CITATION.read_text(encoding="utf-8")
    assert CORRECT_ORCID in citation
    assert OLD_UNRELATED_ORCID not in citation
    assert re.search(r'^    given-names: "Abhijith"$', citation, re.MULTILINE)
    assert re.search(r'^  - family-names: "Sivaprasadan"$', citation, re.MULTILINE)


def test_no_unassigned_doi_or_misleading_release_date():
    citation = CITATION.read_text(encoding="utf-8")
    assert not re.search(r"^doi:", citation, re.MULTILINE)
    assert not re.search(r"^date-released:", citation, re.MULTILINE)
    assert "no tagged release or DOI yet" in citation


def test_pep639_mit_license_metadata_and_file_are_consistent():
    project = PROJECT.read_text(encoding="utf-8")
    assert 'license = "MIT"' in project
    assert 'license-files = ["LICENSE"]' in project
    installed = metadata("enerlint")
    assert installed["License-Expression"] == "MIT"
    assert "LICENSE" in installed.get_all("License-File", [])
    text = LICENSE.read_text(encoding="utf-8")
    assert text.startswith("MIT License\n")
    assert "Copyright (c) 2026 Abhijith Sivaprasadan" in text
    assert "THE SOFTWARE IS PROVIDED \"AS IS\"" in text


def test_published_source_archive_explicitly_includes_reproduction_inputs():
    manifest = SDIST_MANIFEST.read_text(encoding="utf-8")
    for line in (
        "include LICENSE",
        "include CITATION.cff",
        "include README.md",
        "recursive-include docs *.md *.json",
        "recursive-include examples *.json",
        "recursive-include scripts *.py",
        "recursive-include tests *.py",
        "exclude docs/KTH_CONCEPT_NOTE.md",
        "exclude docs/BRANDING.md",
    ):
        assert line in manifest


def test_public_alpha_readme_remains_scope_limited():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "v0.1.0a0" in readme
    assert "Not" in readme and "validated" in readme.lower()
    assert "No PyPI or Zenodo release is claimed" in readme
    assert "compensating" in readme.lower()
