# Foundation synthetic benchmark results (27 October 2026)

**Scope:** developer-built software smoke/negative-control checks. This is **not**
empirical verification, peer review, or evidence of deployment suitability.

Reproduce offline using:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/run_foundation_benchmark.py
```

At development time, **42 Python tests passed locally on Python 3.13.5**.
GitHub Actions CI has run successfully as of 27 October 2026 ([example successful run](https://github.com/Open-Energy-Methods/enerlint/actions/runs/40452499654)). This establishes that the configured workflow executed, **not** that the benchmarks were independently reviewed or the software externally validated.

| Demonstration | Expected | Observed |
|---|---|---|
| 4 hand-constructed cases | Pass declared checks | 4 passed in scope |
| 6 deliberately broken cases | At least one declared balance fails | 6 failed as expected |
| 1 compensating operating-point error | Conservation cannot detect it | Passed in scope as an **intentional escape** |

The report is saved in [`artifacts/foundation_benchmark.json`](../artifacts/foundation_benchmark.json),
with a canonical SHA-256 digest stored inside the record. The archive records
all case and fault names, check residuals, input fingerprints and thresholds.
The ledger is deterministic for the declared Python implementation.

## Baselines

- Compressor: 0 kg/s mass residual and 0 W first-law residual.
- Turbine: 0 kg/s mass residual and 0 W first-law residual.
- Two-stream heat exchanger: 0 kg/s mass residual and 0 W first-law residual.
- One-hour storage: 0 J accumulation residual; within declared capacity.

## Named detected errors (deliberately inserted)

| Error | Example failed residual |
|---|---:|
| Outlet flow increased 20% | -0.4 kg/s mass; -168,000 W energy |
| Outlet enthalpy increased 20% | -168,000 W energy |
| Compressor shaft work sign inverted | -480,000 W energy |
| Turbine heat sign inverted | -10,000 W energy |
| Stored energy state raised 20% | +443,200,000 J |
| Interval duration increased 20% | -43,200,000 J |

**Do not report '100% detection accuracy'.** These specific mutations were
selected in advance by the software developer, do not constitute a held-out
independent fault distribution, and do not quantify false positives on real
engineering data. Strongly correlated or compensated errors can escape.

## Expanded analytical reference catalogue — separate evidence set

A newer [ten-case analytical catalogue](BENCHMARK_CASE_CARDS.md) adds worked
compressor, turbine, mixer, splitter, exchanger and storage cases, with a
versioned [manifest of author-derived oracle values](analytical_reference_v0.1.json)
and a [standalone Decimal reference calculator](../scripts/run_analytical_catalog.py).

```bash
python scripts/run_analytical_catalog.py
```

The catalogue has **ten selected positive cases and ten deliberately failing
mutations**, selected by the same project maintainer. The runner writes a new,
hashed-input, per-run evidence ledger to
`artifacts/ci/analytical_catalog_v0.1.json` which is uploaded as a
GitHub Actions artifact. The foundation's four-baseline/six-mutation ledger
remains unchanged, and overlapping cases must **not** be counted as
independent new datasets. The new tests do **not** establish validation,
blind fault-detection rates, external reproducibility or a peer-reviewed
benchmark. See [open review issue #25](https://github.com/Open-Energy-Methods/enerlint/issues/25).

## External review required before a scientific release

Obtain an independent review of boundary equations, unit conventions,
uncertainty/tolerance policies, reference-case selection, and effect of
shared model assumptions. Then compare against the diagnostics provided
by at least one established energy-modeling framework.
