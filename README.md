<p align="center">
  <a href="https://github.com/Open-Energy-Methods">
    <img src="https://raw.githubusercontent.com/Open-Energy-Methods/.github/main/assets/brand/oem-logo-full-primary.svg" alt="Open Energy Methods — full-color navy and teal logo" width="480">
  </a>
</p>

# EnerLint

**Independent, scope-limited physical consistency checks for energy-engineering outputs.**

> **Scientific status: initial foundation / alpha (v0.1.0a0).** Four hand-constructed
> analytical demonstrations and a negative-control suite. **Not** externally
> validated or qualified for operational control, engineering certification,
> procurement decisions, or nuclear safety assessments. No PyPI or Zenodo release is claimed; the public GitHub repository is a review-stage alpha.

## Why this exists

I like working with energy models, but a successful simulation run does not settle every engineering question. A model can produce neat-looking outputs while a sign convention, boundary, or assumption is wrong.

I started EnerLint to ask one small question independently of the originating solver: **do these exported quantities satisfy the physical relationships we said they should?**

Even that question has a catch. In the first benchmark, six deliberately introduced inconsistencies are flagged, but a compensating compressor error **still passes**. The check is not broken; the underlying equations cannot distinguish two internally balanced operating points without extra evidence. I think that limitation belongs on the front page, not in the fine print.

[Read the worked example and the numbers behind it](https://open-energy-methods.github.io/notes/001-a-pass-isnt-proof.html).

The goal is to detect numerical and physical *inconsistencies in exported model
results* without trusting the originating solver's convergence flag or residuals.
A passing conservation check does **not** prove that the model is realistic, that
measurements were correct, or that its scientific conclusions are justified.
The [scientific claims policy](docs/SCIENTIFIC_CLAIM_POLICY.md) distinguishes bounded
output-consistency evidence from model validation, calibration, UQ and certification.
Its V0–V5 terms are **OEM-only descriptions**, not ASME ratings or automatic grades.

## What works now

- **Steady control volumes:** mass-flow closure and energy/enthalpy closure with
  explicit heat and shaft-work crossing conventions. An optional, author-attested
  [boundary preflight](docs/CONTROL_VOLUME_BOUNDARY_REVIEW.md) records physical port,
  omitted-term and reference assumptions before interpreting results.
- **Thermal storage (one interval):** stored-energy change versus charge,
  discharge and loss; optional storage capacity check.
- **Strict JSON/SI input contracts:** explicit assumptions, numeric finite checks,
  rejection of unknown fields and omitted quantities. Does not silently infer
  missing input as zero.
- **Numerical tolerances:** displayed absolute/relative thresholds and measured
  residuals per check.
- **Machine-readable reports:** input SHA-256 of canonical JSON, evidence origin,
  exact assertions/assumptions/limitations, and `PASS_IN_SCOPE` / `FAIL`.
- **Fault injection and metamorphic tests:** deliberately altered mass/enthalpy,
  work sign, heat sign, storage state and timestep, plus valid transformations.

No external dependencies are required for the runtime. The initial target is
Python >=3.10.

## Install and try (after unpacking source)

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/run_foundation_benchmark.py
enerlint check examples/steady_compressor.json --output reports/compressor.json
enerlint check examples/steady_heat_exchanger.json
enerlint check examples/steady_turbine.json
enerlint check examples/storage_interval.json
```

Run it without installing using `PYTHONPATH=src python -m enerlint check ...` on
Unix-like systems, or `$env:PYTHONPATH = "src"` in PowerShell.

### Python API

```python
import json
from enerlint import check_case

with open("examples/steady_compressor.json", encoding="utf-8") as f:
    case = json.load(f)
report = check_case(case)
print(report.status, report.as_dict()["checks"])
report.assert_passed()
```

### Core first-law sign convention

For the declared steady-state boundary, neglecting kinetic/potential flow energy:

```
    sum(m_dot * h)_in - sum(m_dot * h)_out + Q_into - W_out = 0
```

Positive `heat_into_volume_w` enters the control volume; positive
`shaft_work_out_w` leaves it. A compressor receiving shaft work uses **negative**
`shaft_work_out_w`. Inlet and outlet mass flow rates are both nonnegative
magnitudes relative to their explicitly named boundaries.

For storage (rates constant over the interval):

```
    E_final - E_initial = (Q_charge - Q_discharge - Q_loss) * duration_s
```

Storage energies use a zero-based nonnegative energy convention.

## Interpret results carefully

- `PASS_IN_SCOPE`: every applicable **implemented** numerical check passes,
  within tolerances. The report always names what was **not** evaluated.
- `FAIL`: at least one evaluated physical check is inconsistent with supplied data.
- `NOT_CHECKED` (per-check only): optional calculation lacked required input,
  such as storage capacity; **never** reinterpreted as a successful check.
- Input errors raise `ContractError`; CLI exits with status **2**, not "PASS".
  When `--output` is supplied, rejected inputs also produce a structured
  `INVALID_INPUT` JSON report; the CLI still prints the diagnostic to stderr.
- Failed conservation checks exit with status **1**; scoped passes exit **0**.

This package does not inspect the physical solver, prove its governing equations
are appropriate, independently certify property calculations, or authenticate
model-data provenance. It can miss correlated or compensating errors: a model
with wrong inputs may still satisfy conservation.

## Docs

- [Numeric tolerance, cancellation and representability policy](docs/NUMERICAL_TOLERANCE_POLICY.md)
- [Verification contract, equations, tolerances](docs/VERIFICATION_CONTRACT.md)
- [Versioned report schema, stable check IDs and rejected-input JSON](docs/REPORT_SCHEMA.md)
- [Scientific limits and independence](docs/SCIENTIFIC_SCOPE.md)
- [Evidence descriptors (V0–V5), scientific claims and prohibited inferences](docs/SCIENTIFIC_CLAIM_POLICY.md)
- [Predeclared benchmark and fault-injection protocol](docs/BENCHMARK_PROTOCOL.md)
- [Worked analytical benchmark case cards (compressor and thermal store)](docs/BENCHMARK_CASE_CARDS.md)
- [Initial synthetic benchmark results](docs/RESULTS.md)
- [Prespecified native thermal diagnostic comparison (D1; not yet run)](docs/EXPERIMENT_D1_THERMAL_COMPARISON.md)
- [Future adapter contract](docs/ADAPTER_SPEC.md)
- [Competitive overlap and differentiation](docs/PRIOR_ART.md)
- [KTH research concept note](docs/KTH_CONCEPT_NOTE.md)
- [Roadmap](docs/ROADMAP.md)

### Reproduce the package, not just a source checkout

The CI matrix now builds both a wheel and a source distribution and tests each
through a fresh virtual environment **outside the source checkout**, covering
the CLI's pass, fail, and invalid-input exit paths. To run that gate locally:

```bash
python -m pip install build
python -m build --wheel --sdist
python scripts/verify_distributions.py
```

This verifies packaging and declared program behavior. It does **not** supply
independent scientific review or operational validation. See
[packaging and reproducibility notes](docs/REPRODUCIBILITY.md).

## Development and release policy

This is a **candidate foundation**, not a published software release. Scientific
benchmark cases are currently hand-constructed, not independently reviewed.
No DOI is assigned, and a green local test run is not evidence of external
validation. A public GitHub release, PyPI distribution, and Zenodo deposit will
require separate publication steps and a fresh review of benchmarks and scope.

Contributions welcome after repository publication. MIT licensed.


## About the workbench

EnerLint is the first project under [Open Energy Methods](https://github.com/Open-Energy-Methods), my independent open-source workbench for computational energy engineering. It is not currently a product of an incorporated company, a certification tool, or an externally validated diagnostic service.

The [OEM website](https://open-energy-methods.github.io/) has the longer story and technical field notes. The approved [brand assets](https://github.com/Open-Energy-Methods/.github/tree/main/assets/brand/) are maintained centrally.

If you find an error in the derivations, a false alarm, a case that slips through, or a native tool that already does the job better, please [open an issue](https://github.com/Open-Energy-Methods/enerlint/issues). The work is organized through the [scientific roadmap](https://github.com/Open-Energy-Methods/enerlint/issues/36) and [OEM Agile playbook](https://github.com/Open-Energy-Methods/.github/blob/main/docs/AGILE_PLAYBOOK.md). These are planning aids, not measures of scientific maturity.

[OEM on LinkedIn](https://www.linkedin.com/company/open-energy-methods)
