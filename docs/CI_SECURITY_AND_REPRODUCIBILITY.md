# CI, artifact hygiene, and reproducibility — control record

**27 October 2026 · EnerLint #16 · maintainer-authored · alpha**

This is a practical engineering workbench security checklist, not a corporate compliance program. CI exists to catch code, packaging, contract, and accidental-publication mistakes in *EnerLint*; it cannot establish that a physical model is valid or that a software supply chain is independently certified.

## 1. Gates on every pushed commit and pull request

[Scientific core workflow](../.github/workflows/ci.yml) runs on:

| Runner | Interpreters | Tests |
|---|---|---|
| Ubuntu | Python 3.10 / 3.13 | Full test suite plus negative controls |
| Windows | Python 3.10 / 3.13 | Identical checks |
| macOS | Python 3.10 / 3.13 | Identical checks |

The job performs, in order:

1. Checkout using a **commit-pinned** GitHub Action with `persist-credentials: false` and workflow-level `permissions: contents: read`.
2. Install the editable developer package and bounded-version Ruff. Run `compileall` plus deliberately narrow Ruff `E4,E7,E9,F63,F7,F82` rules (import/syntax/undefined-name correctness rather than enforcing every formatting opinion).
3. Run the full pytest suite, including strict JSON Schema checks, compensation/false-pass examples, invalid-input behavior, boundary and property-reference review tests, and archive-audit negative controls.
4. Recreate the foundation synthetic benchmark ledger; rebuild exactly one wheel and one source distribution.
5. Install each built distribution into a new Python virtual environment *outside the checkout* and test successful/failed/invalid CLI paths, including packaged JSON Schema.
6. Inspect git-tracked source and both distributable archives for selected high-confidence secret forms, prohibited files, unsafe archive paths/links, unexpected package metadata, missing license/schema, and unexpected runtime dependencies.
7. Write a [build-specific JSON manifest](../scripts/audit_release_artifacts.py) with source commit, run ID, runner OS, Python and build-tool versions, wheel/sdist SHA-256, archive member counts and limitations.
8. Upload the **audited** wheel, sdist and manifest as a GitHub Actions artifact retained for **14 days**. This is a downloadable *CI build*, **not** a tagged software release or a PyPI distribution.
9. Exercise two opt-in, **author-attested** review sidecars and the specified standalone synthetic example checks.

A failure in any required gate fails that matrix job. This is intentionally stricter than merely seeing the test suite pass.

## 2. Secret and packaging audit coverage (bounded)

The [artifact audit](../scripts/audit_release_artifacts.py) examines **git-tracked** files and the *actual bytes* in both wheel/sdist. It rejects:

- Common high-confidence patterns for private-key headers, GitHub personal tokens, AWS access-key IDs and Slack tokens.
- Named credential/configuration files such as `.env`, `.netrc`, `credentials.json`, `secrets.json`, private-key keystores and suspicious secret-containing paths.
- Founder-only planning materials or private folders accidentally included in either distributable archive.
- Archive path traversal, symbolic links/special entries, duplicated files or oversized members.
- Archives missing core EnerLint code, the JSON report schema or the MIT LICENSE.
- Unexpected package name/version or **nonoptional runtime dependencies** (runtime remains Python standard library).

The test suite includes **intentionally constructed mock credentials and unsafe archives** to show the gate fails as expected. It never prints a detected credential value; a failing audit reports the file and pattern type only.

**Limits:** this is not a full-depth credential scanner; weak patterns, novel token formats, encrypted secrets, untracked files, externally fetched dependencies, and credentials in external runtime environments may escape. Git-tracked file scanning does not inspect previous commits/history or pull-request discussions. A pass means *none of the configured red flags triggered*—never that a security expert has audited the repository or that no secrets exist. If a real secret is found, revoke/rotate it immediately and review commit history; deleting a file is not enough.

## 3. GitHub Actions supply-chain choices

- **Least privilege:** workflow declares `contents: read`; no release publishing, OIDC identity token, package registry write, or deployment credentials.
- **Pinned action versions:** checkout, setup-python and upload-artifact are referenced by their commit SHA rather than a mutable major-version alias. Those revisions were verified against their GitHub release/ref records on 27 October 2026. Periodically review for security updates; a pin does **not** prove an action is safe.
- **Untrusted PR code:** do not execute pull-request scripts with elevated/organization secrets. No `pull_request_target` is used.
- **Matrix cancellation:** only newer runs on the same workflow/ref supersede older in-progress runs, limiting duplicated work. Avoid interpreting a cancelled superseded run as a scientific regression.
- **Dependency reality:** the runtime intentionally has **zero third-party dependencies**. Developer/build tools are downloaded from package repositories at build time; their resolved versions are recorded in the manifest but **not yet hash-locked**, so full build reproducibility and dependency-chain provenance are **not** claimed.
- **Releases:** artifacts are not auto-published. Any tag/DOI/PyPI release is subject to a separate explicit go/no-go review and the project's scientific limitations.

These are *OpenSSF-informed hygiene choices*, not an OpenSSF Scorecard rating, SLSA provenance level, package attestation, SBOM audit, reproducible-build certification or supply-chain guarantee. Future measures should respond to real risks, not to an imagined corporate compliance requirement.

## 4. Reproduce the CI checks

From a clean clone with Python 3.10+:

```bash
python -m pip install -e ".[dev]" "ruff>=0.12,<1"
python -m compileall -q src scripts tests
python -m ruff check --select E4,E7,E9,F63,F7,F82 src scripts tests
python -m pytest -q
python scripts/run_foundation_benchmark.py
python -m pip install build
python -m build --sdist --wheel
python scripts/verify_distributions.py
python scripts/audit_release_artifacts.py
```

The manifest is written to `artifacts/ci/build-manifest.json` (gitignored) and the wheel/sdist to `dist/` (also gitignored). You may inspect their `sha256` fields or download those files from the exact successful CI run's **Artifacts** section. The manifest includes `generated_at_utc` and archive hashes, so its own byte sequence—and potentially the wheel/sdist bytes—can differ on a different machine/run. **Builds are not currently proven byte-for-byte reproducible.**

Report unexpected security-tool detections with filenames and reproducible steps but **never paste tokens, passwords, or private model files into issues**. Use a private security report for genuine vulnerabilities.

## 5. Acceptance and what remains outside scope

- A passing workflow demonstrates the selected code paths, formatting-independent correctness lint, distribution installation, strict schema/report cases, and selected publishing-hygiene rules on the documented platforms.
- It does **not** establish scientific independent review, real plant/model validity, measured fault-detection sensitivity, calibrated property data or production safety.
- This issue does not settle the final release manifest and software citation gate ([#5](https://github.com/Open-Energy-Methods/enerlint/issues/5)), code-signing, upstream dependency pinning, independent audit, a comprehensive threat model, or external provenance attestation.
- Review new file types, dependencies, workflow permissions and release destinations **before** expanding publication.

See also [reproducibility instructions](REPRODUCIBILITY.md), [report schema](REPORT_SCHEMA.md), [scientific claims policy](SCIENTIFIC_CLAIM_POLICY.md), and the [S0 sprint](https://github.com/Open-Energy-Methods/.github/issues/34).
