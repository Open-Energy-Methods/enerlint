# Development roadmap

## Foundation alpha (local package: implementation and offline tests)

- [x] Strict JSON contract with explicit SI units and provenance declaration
- [x] Independent steady mass and energy residuals for non-reactive CVs
- [x] Worked boundary/sign review, nonadiabatic counterexample and optional author-attested preflight ([review guide](CONTROL_VOLUME_BOUNDARY_REVIEW.md))
- [x] Energy interval accounting and optional storage capacity
- [x] Numeric tolerances visible alongside each residual
- [x] Publish a [strict v0.1.0 JSON report schema](REPORT_SCHEMA.md) with stable check IDs and status constraints
- [x] Publish an [explicit V0–V5 OEM scientific claim and evidence policy](SCIENTIFIC_CLAIM_POLICY.md) with audited positive/negative statement examples and counterexample tests
- [x] Emit deterministic report JSON and optional machine-readable `INVALID_INPUT` artifacts
- [x] Validate schema invariants and packaged schema resources across supported CI environments
- [x] CLI, Python API, example cases and machine-readable reports
- [x] Fault injection and metamorphic invariance tests
- [x] Synthetic benchmark run with hashed JSON evidence ledger
- [x] CI configuration and successful GitHub Actions execution (27 Oct 2026; not independent scientific validation)
- [ ] Fresh independent technical review
- [x] Publish GitHub repository and verify that configured CI runs successfully

## v0.1.0 pre-release gate

- [x] Regression coverage of zero-flow, reference-datum, cancellation, strict-threshold and arithmetic-overflow cases (maintainer-authored tests)
- [ ] Independent scientific critique of numeric tolerances, conditioning and residual formulation
- [ ] Source review of analytical cases and tolerance choice
- [x] Publish [property-data acceptance protocol](PROPERTY_DATA_ACCEPTANCE.md), author-attested reference sidecars and mismatch regression cases (not physical-property validation)
- [ ] Replace/generalize demonstration fixtures with real exported model
      results from at least one consented publicly shareable source
- [ ] Compare fault detection with incumbent modeling tools
- [x] Build wheel/sdist on GitHub CI across the supported OS/Python matrix and smoke-test each in a fresh virtual environment ([reproducibility protocol](REPRODUCIBILITY.md))
- [x] Add bounded [CI artifact hygiene and per-run SHA-256 manifest](CI_SECURITY_AND_REPRODUCIBILITY.md), pinned Actions, least privilege and targeted static lint (internal controls)
- [x] Record versioned [alpha release-readiness assessment](RELEASE_READINESS_2026-10-27.md), [rights inventory](RELEASE_RIGHTS_REGISTER.md) and [draft release notes](RELEASE_NOTES_CANDIDATE.md); **NO-GO for publication** until open gates close
- [ ] Complete founder-approved asset/source rights clearance and independent distribution/source review; publication remains blocked
- [ ] Add contribution, documentation and security procedures
- [ ] Verify package and project naming/ownership on PyPI and GitHub

## Research notes / comparisons

- [x] Publish **ten** analytical [benchmark case cards](BENCHMARK_CASE_CARDS.md), independently hand-checkable with a [versioned SI oracle](analytical_reference_v0.1.json) and ten developer-selected failing mutations (maintainer-authored, **not externally reviewed**).
- [x] Record separately implemented [Decimal-based reference arithmetic](../scripts/run_analytical_catalog.py) and an automated ten-case/twenty-run self-test ledger; preserve the earlier four-case result.
- [x] Develop [13 manufactured/limiting test problems](MANUFACTURED_LIMITS.md) (11 evaluated, 2 rejected), record 13 selected perturbations including two known tolerated errors and a flow/power convergence sequence. Developer self-test only, external review still open.
- [x] Freeze and replay [39 synthetic negative controls](NEGATIVE_CONTROL_STUDY.md): 18 failed balances, 11 invalid-input rejections, six expected blind spots, one metadata-only timing description and three invariant controls. Developer-authored, not an empirical fault-detection study.
- [x] Draft a prespecified [native thermal-tool comparison](EXPERIMENT_D1_THERMAL_COMPARISON.md) with equal-information controls; **experiment not yet run**.
- [ ] Obtain independent critique and compare with one real external implementation; retain null/negative findings.

## v0.2 (candidate)

- [ ] Explicit time-series interval contracts with timestamp/timezone checks
- [ ] Uncertainty propagation and normalized residuals
- [ ] Generic SI unit conversion using a controlled Pint interface
- [ ] Nontrivial uncertainty-aware energy/heat measurement data checks
- [ ] Validated adapter for one existing independent solver

## Separate future research directions, not release promises

- AC power-flow and optimization result feasibility (PyPSA/pandapower)
- Thermal-property consistency with CoolProp/IAPWS
- Thermal-field/FEA reference problems
- Coupled-energy and building thermal/electrical data contracts
- Reactor balance-of-plant only before any nuclear-domain specialist review

## Publication

No GitHub tag, PyPI version or DOI is claimed. When ready, use GitHub tagged
release and Zenodo to create a software DOI for the exact archived version.
A DOI is an identifier, not independent scientific validation.
