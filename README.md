<p align="center">
  <a href="https://github.com/Open-Energy-Methods"><img src="https://raw.githubusercontent.com/Open-Energy-Methods/.github/main/assets/brand/oem-logo-symbol-primary.svg" alt="Open Energy Methods logo" width="92"></a>
</p>

# EnerLint

**Independent, scope-limited physical consistency checks for energy-engineering outputs.**

> **Scientific status: initial foundation / alpha (v0.1.0a0).** Four hand-constructed
> analytical demonstrations and a negative-control suite. **Not** externally
> validated or qualified for operational control, engineering certification,
> procurement decisions, or nuclear safety assessments. No PyPI or Zenodo release is claimed; the public GitHub repository is a review-stage alpha.

The goal is to detect numerical and physical *inconsistencies in exported model
results* without trusting the originating solver's convergence flag or residuals.
A passing conservation check does **not** prove that the model is realistic, that
measurements were correct, or that its scientific conclusions are justified.

## What works now

- **Steady control volumes:** mass-flow closure and energy/enthalpy closure with
  explicit heat and shaft-work crossing conventions.
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
- Failed conservation checks exit with status **1**; scoped passes exit **0**.

This package does not inspect the physical solver, prove its governing equations
are appropriate, independently certify property calculations, or authenticate
model-data provenance. It can miss correlated or compensating errors: a model
with wrong inputs may still satisfy conservation.

## Docs

- [Verification contract, equations, tolerances](docs/VERIFICATION_CONTRACT.md)
- [Scientific limits and independence](docs/SCIENTIFIC_SCOPE.md)
- [Predeclared benchmark and fault-injection protocol](docs/BENCHMARK_PROTOCOL.md)
- [Initial synthetic benchmark results](docs/RESULTS.md)
- [Future adapter contract](docs/ADAPTER_SPEC.md)
- [Competitive overlap and differentiation](docs/PRIOR_ART.md)
- [KTH research concept note](docs/KTH_CONCEPT_NOTE.md)
- [Roadmap](docs/ROADMAP.md)

## Development and release policy

This is a **candidate foundation**, not a published software release. Scientific
benchmark cases are currently hand-constructed, not independently reviewed.
No DOI is assigned, and a green local test run is not evidence of external
validation. A public GitHub release, PyPI distribution, and Zenodo deposit will
require separate publication steps and a fresh review of benchmarks and scope.

Contributions welcome after repository publication. MIT licensed.


## Organization

EnerLint is developed under [Open Energy Methods](https://github.com/Open-Energy-Methods), an independent open-source research-software initiative. See [branding](docs/BRANDING.md).

## Maintainers, issue tracking and brand

EnerLint is maintained under [Open Energy Methods](https://github.com/Open-Energy-Methods), an independent open-source research-software initiative. The [approved OEM vector brand assets](https://github.com/Open-Energy-Methods/.github/tree/main/assets/brand/) are maintained centrally by the organization rather than duplicated in this repository.

Our scientific and user-research development backlog is tracked through [EnerLint issues](https://github.com/Open-Energy-Methods/enerlint/issues), [the scientific roadmap](https://github.com/Open-Energy-Methods/enerlint/issues/36), and the [OEM Agile workflow](https://github.com/Open-Energy-Methods/.github/blob/main/docs/AGILE_PLAYBOOK.md). Work type, priority, severity, stage and sprint are managed in issue fields/labels; a priority label is not evidence of a defect, and passing our checks does not confer engineering certification.
