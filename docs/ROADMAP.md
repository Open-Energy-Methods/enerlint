# Development roadmap

## Foundation alpha (local package: implementation and offline tests)

- [x] Strict JSON contract with explicit SI units and provenance declaration
- [x] Independent steady mass and energy residuals for non-reactive CVs
- [x] Energy interval accounting and optional storage capacity
- [x] Numeric tolerances visible alongside each residual
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
- [ ] Add documented property-data acceptance protocol
- [ ] Replace/generalize demonstration fixtures with real exported model
      results from at least one consented publicly shareable source
- [ ] Compare fault detection with incumbent modeling tools
- [x] Build wheel/sdist on GitHub CI across the supported OS/Python matrix and smoke-test each in a fresh virtual environment ([reproducibility protocol](REPRODUCIBILITY.md))
- [ ] Complete release-manifest/license/provenance audit of built distributions
- [ ] Add contribution, documentation and security procedures
- [ ] Verify package and project naming/ownership on PyPI and GitHub

## Research notes / comparisons

- [x] Publish two complete, human-checkable analytical [benchmark case cards](BENCHMARK_CASE_CARDS.md) (maintainer-derived, **not externally reviewed**).
- [x] Record explicit independent-arithmetic regression checks for those cards.
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
