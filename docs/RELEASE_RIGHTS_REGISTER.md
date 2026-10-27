# Release rights and provenance register — EnerLint alpha

**Snapshot date:** 27 October 2026 · **Baseline Git tree:** `c42b42f71eea5301990769919916f74470f91ec1` · **Release publication status: NO-GO.**

This is an **inventory of the actual public repository**, not an assertion that every file was independently cleared. The creator/maintainer must confirm the rights to publish and redistribute each bundled file, including any code generated with AI support, contributions adapted from other repositories, screenshots, figures, outputs, and any simulated or measured data.

The [MIT license](../LICENSE) declares the intended license for EnerLint's original material. It **does not** establish ownership of third-party source code, data or other rights. A Git commit author field, a DOI, GitHub organization membership, or an AI-generated file is not proof of rights. Do not import Siemens Energy, KTH, employer or private archive data without explicit permission and provenance.

## Decisions recorded now

- **Runtime requirements:** no declared third-party runtime packages; development and build dependencies are consumed from external repositories and not redistributed inside the enerlint wheel. Version pins for build tools are *bounded but not hash locked*. Confirm dependency licences separately before substantially bundling/vendorizing.
- **Source code and developer tests:** represented as maintainer-led/AI-assisted original project work; **individual contribution/licence pedigree is not externally confirmed**. The maintainer must attest no unauthorized copied code or employer-derived confidential input.
- **Synthetic fixtures:** self-labelled `hand_constructed`; their model data rights and scientific validity are not independently reviewed. A synthetic source label is not permission to publish actual measurements.
- **Remote branding:** root README hotlinks an OEM-owned SVG stored in the .github repository. The logo is **not bundled** in the EnerLint distribution; third-party logo/trademark rights must still be separately considered.
- **Public institutional references:** `docs/KTH_CONCEPT_NOTE.md` explicitly denies affiliation/endorsement and is **excluded from the source distribution** by `MANIFEST.in`. The author must review it before outreach; no use of institution-specific protected work is authorized.
- **Package distribution:** the source archive intentionally includes code, citation, documentation, runnable examples and tests. The wheel includes runtime package modules, metadata and MIT license, not private planning files. The bounded CI audit checks distributions, but cannot detect all problematic assets.
- **External review status:** rights attribution and research independence **not signed off** as of this snapshot. Preserve a distinct release gate before publishing.

## File-level register

Columns: **Shipment** is intended contents under the current `MANIFEST.in` / Python package configuration, not a manually downloaded independently reviewed archive. **Finding** is a triage note rather than a statement of cleared rights.

| Repository path | Category | Intended shipment | Finding / remaining review |
|---|---|---|---|
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | Repository automation | Repository only | Review source, quotations, attribution and source license |
| [`.github/workflows/issue-workflow.yml`](../.github/workflows/issue-workflow.yml) | Repository automation | Repository only | Review source, quotations, attribution and source license |
| [`.github/workflows/normalize-issue-metadata.yml`](../.github/workflows/normalize-issue-metadata.yml) | Repository automation | Repository only | Review source, quotations, attribution and source license |
| [`.github/workflows/sync-issue-labels.yml`](../.github/workflows/sync-issue-labels.yml) | Repository automation | Repository only | Review source, quotations, attribution and source license |
| [`.github/workflows/sync-native-issue-types.yml`](../.github/workflows/sync-native-issue-types.yml) | Repository automation | Repository only | Review source, quotations, attribution and source license |
| [`.github/workflows/sync-stage-milestones.yml`](../.github/workflows/sync-stage-milestones.yml) | Repository automation | Repository only | Review source, quotations, attribution and source license |
| [`.gitignore`](../.gitignore) | Repository root / metadata | Repository only | Review source, quotations, attribution and source license |
| [`CITATION.cff`](../CITATION.cff) | Repository root / metadata | Sdist / metadata | ORCID corrected; attribution to maintainer |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Repository root / metadata | Repository only | Review source, quotations, attribution and source license |
| [`LICENSE`](../LICENSE) | Repository root / metadata | Sdist / metadata | Declared MIT text; verify copyright authority |
| [`MANIFEST.in`](../MANIFEST.in) | Repository root / metadata | Sdist / metadata | Review source, quotations, attribution and source license |
| [`README.md`](../README.md) | Repository root / metadata | Sdist / metadata | Review source, quotations, attribution and source license |
| [`artifacts/foundation_benchmark.json`](../artifacts/foundation_benchmark.json) | Generated reference baseline | Repository only | Review source, quotations, attribution and source license |
| [`docs/ADAPTER_SPEC.md`](../docs/ADAPTER_SPEC.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/BENCHMARK_CASE_CARDS.md`](../docs/BENCHMARK_CASE_CARDS.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/BENCHMARK_PROTOCOL.md`](../docs/BENCHMARK_PROTOCOL.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/BRANDING.md`](../docs/BRANDING.md) | Research documentation | Excluded from sdist | References external OEM logo; assets are not bundled |
| [`docs/CI_SECURITY_AND_REPRODUCIBILITY.md`](../docs/CI_SECURITY_AND_REPRODUCIBILITY.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/CONTROL_VOLUME_BOUNDARY_REVIEW.md`](../docs/CONTROL_VOLUME_BOUNDARY_REVIEW.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/EXPERIMENT_D1_THERMAL_COMPARISON.md`](../docs/EXPERIMENT_D1_THERMAL_COMPARISON.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/KTH_CONCEPT_NOTE.md`](../docs/KTH_CONCEPT_NOTE.md) | Research documentation | Excluded from sdist | Draft is not institutional endorsement; excluded from sdist |
| [`docs/NUMERICAL_TOLERANCE_POLICY.md`](../docs/NUMERICAL_TOLERANCE_POLICY.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/PRIOR_ART.md`](../docs/PRIOR_ART.md) | Research documentation | Sdist | Third-party tools linked, not copied; recheck quotes/citations |
| [`docs/PROPERTY_DATA_ACCEPTANCE.md`](../docs/PROPERTY_DATA_ACCEPTANCE.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/RELEASE_RIGHTS_REGISTER.md`](../docs/RELEASE_RIGHTS_REGISTER.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/REPORT_SCHEMA.md`](../docs/REPORT_SCHEMA.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/RESULTS.md`](../docs/RESULTS.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/ROADMAP.md`](../docs/ROADMAP.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/SCIENTIFIC_CLAIM_POLICY.md`](../docs/SCIENTIFIC_CLAIM_POLICY.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/SCIENTIFIC_SCOPE.md`](../docs/SCIENTIFIC_SCOPE.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/VERIFICATION_CONTRACT.md`](../docs/VERIFICATION_CONTRACT.md) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`docs/claim_examples_v0.1.json`](../docs/claim_examples_v0.1.json) | Research documentation | Sdist | Review source, quotations, attribution and source license |
| [`examples/steady_compressor.boundary-review.json`](../examples/steady_compressor.boundary-review.json) | Synthetic reference inputs | Sdist | Synthetic by declared provenance; check dataset rights |
| [`examples/steady_compressor.json`](../examples/steady_compressor.json) | Synthetic reference inputs | Sdist | Synthetic by declared provenance; check dataset rights |
| [`examples/steady_compressor.property-review.json`](../examples/steady_compressor.property-review.json) | Synthetic reference inputs | Sdist | Synthetic by declared provenance; check dataset rights |
| [`examples/steady_heat_exchanger.json`](../examples/steady_heat_exchanger.json) | Synthetic reference inputs | Sdist | Synthetic by declared provenance; check dataset rights |
| [`examples/steady_heat_exchanger.property-review.json`](../examples/steady_heat_exchanger.property-review.json) | Synthetic reference inputs | Sdist | Synthetic by declared provenance; check dataset rights |
| [`examples/steady_mismatched_reference_compensated.json`](../examples/steady_mismatched_reference_compensated.json) | Synthetic reference inputs | Sdist | Synthetic by declared provenance; check dataset rights |
| [`examples/steady_mismatched_reference_compensated.property-review.json`](../examples/steady_mismatched_reference_compensated.property-review.json) | Synthetic reference inputs | Sdist | Synthetic by declared provenance; check dataset rights |
| [`examples/steady_nonadiabatic_compressor.json`](../examples/steady_nonadiabatic_compressor.json) | Synthetic reference inputs | Sdist | Synthetic by declared provenance; check dataset rights |
| [`examples/steady_turbine.json`](../examples/steady_turbine.json) | Synthetic reference inputs | Sdist | Synthetic by declared provenance; check dataset rights |
| [`examples/storage_interval.json`](../examples/storage_interval.json) | Synthetic reference inputs | Sdist | Synthetic by declared provenance; check dataset rights |
| [`pyproject.toml`](../pyproject.toml) | Repository root / metadata | Sdist / metadata | Review source, quotations, attribution and source license |
| [`scripts/audit_release_artifacts.py`](../scripts/audit_release_artifacts.py) | Scripts/experiments | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`scripts/normalize_issue_metadata.py`](../scripts/normalize_issue_metadata.py) | Scripts/experiments | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`scripts/review_control_volume.py`](../scripts/review_control_volume.py) | Scripts/experiments | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`scripts/review_property_references.py`](../scripts/review_property_references.py) | Scripts/experiments | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`scripts/run_foundation_benchmark.py`](../scripts/run_foundation_benchmark.py) | Scripts/experiments | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`scripts/verify_distributions.py`](../scripts/verify_distributions.py) | Scripts/experiments | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`src/enerlint/__init__.py`](../src/enerlint/__init__.py) | Source/runtime | Wheel and sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`src/enerlint/__main__.py`](../src/enerlint/__main__.py) | Source/runtime | Wheel and sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`src/enerlint/cli.py`](../src/enerlint/cli.py) | Source/runtime | Wheel and sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`src/enerlint/faults.py`](../src/enerlint/faults.py) | Source/runtime | Wheel and sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`src/enerlint/models.py`](../src/enerlint/models.py) | Source/runtime | Wheel and sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`src/enerlint/schemas/report-v0.1.0.schema.json`](../src/enerlint/schemas/report-v0.1.0.schema.json) | Source/runtime | Wheel and sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`src/enerlint/verify.py`](../src/enerlint/verify.py) | Source/runtime | Wheel and sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/conftest.py`](../tests/conftest.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_artifact_audit.py`](../tests/test_artifact_audit.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_boundary_review.py`](../tests/test_boundary_review.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_case_card_oracles.py`](../tests/test_case_card_oracles.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_cli.py`](../tests/test_cli.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_control_volume_contract_examples.py`](../tests/test_control_volume_contract_examples.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_faults.py`](../tests/test_faults.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_numerical_bounds.py`](../tests/test_numerical_bounds.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_property_references.py`](../tests/test_property_references.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_report_schema.py`](../tests/test_report_schema.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_scientific_claims.py`](../tests/test_scientific_claims.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_steady.py`](../tests/test_steady.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |
| [`tests/test_storage.py`](../tests/test_storage.py) | Regression tests | Sdist | Developer-created or AI-assisted; source rights require author confirmation |

## File-level release clearance method

For **each file shipped in the chosen candidate distribution**, the maintainer must complete a dated review specifying: (1) original author and rights holder; (2) source URL/repository commit or independently produced formula/data origin; (3) inbound licence and attribution obligations; (4) whether changes are derivative; (5) whether institutional or third-party confidentiality applies; (6) approval or removal action. Prefer a signed-off checklist linked from the actual tag/commit, rather than assuming a green scanner means legal clearance.

A post-snapshot file **must be added** to this register before a published version. The register is not self-updating, and any future pull request can change contents. A real external data adapter or measured reference must have separately documented data use permissions.

## Release blocker

**Not cleared:** individual origin, code/data authorship and redistribution rights have not been independently or maintainer-signed reviewed in this register. Do not claim the register itself is a legal audit. This is a STOP gate for publication pending an explicit founder review and release approval.

Related: [release decision](RELEASE_READINESS_2026-10-27.md), [CI artifact scan](CI_SECURITY_AND_REPRODUCIBILITY.md), [scientific claims policy](SCIENTIFIC_CLAIM_POLICY.md).
