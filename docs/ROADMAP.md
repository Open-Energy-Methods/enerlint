# Development roadmap

## Foundation alpha (local package: implementation and offline tests)

- [x] Strict JSON contract with explicit SI units and provenance declaration
- [x] Independent steady mass and energy residuals for non-reactive CVs
- [x] Energy interval accounting and optional storage capacity
- [x] Numeric tolerances visible alongside each residual
- [x] CLI, Python API, example cases and machine-readable reports
- [x] Fault injection and metamorphic invariance tests
- [x] Synthetic benchmark run with hashed JSON evidence ledger
- [x] Cross-platform CI configuration (not remotely run yet)
- [ ] Fresh independent technical review
- [ ] Publish a GitHub repository and verify CI results there

## v0.1.0 pre-release gate

- [ ] Source review of analytical cases and tolerance choice
- [ ] Add documented property-data acceptance protocol
- [ ] Replace/generalize demonstration fixtures with real exported model
      results from at least one consented publicly shareable source
- [ ] Compare fault detection with incumbent modeling tools
- [ ] Build wheel/sdist in GitHub CI and audit included files
- [ ] Add contribution, documentation and security procedures
- [ ] Verify package and project naming/ownership on PyPI and GitHub

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
