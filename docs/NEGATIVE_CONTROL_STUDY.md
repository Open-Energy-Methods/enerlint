# Developer-selected negative-control programme — NC11 v0.1

**27 October 2026 · EnerLint issue #11 · 39 deterministically frozen scenarios**

This catalogue is a **software self-test experiment**, not scientific validation or a real-world fault-detection evaluation. The scenarios, their declared outcome classes and numerical expectations were designed by the maintainer and committed before the new test suite was first executed in CI. They are **not externally preregistered, blinded or independently adjudicated**. The [frozen JSON manifest](negative_controls_v0.1.json) is the authoritative declaration, rather than outcomes reconstructed after observing the checker.

The study operates on **exported input JSON**, not on an independently implemented thermal solver or measured plant. What constitutes an actual fault is stipulated, not measured. The `FAIL` status indicates a specified conservation/capacity check failed; `INVALID_INPUT` means an unsupported, malformed or unrepresentable input was rejected **without** a physical evaluation. A model may be physically wrong and still return `PASS_IN_SCOPE`.

## Registered design and denominator discipline

| Scenario class | Count | Meaning |
|---|---:|---|
| Declared balance-breaking faults | 18 | Cases whose **selected conservation/capacity check** must fail |
| Strict-schema/contract probes | 11 | Cases expected to raise `ContractError` and produce `INVALID_INPUT` at CLI level |
| Known escaped faults | 6 | Deliberate deviations from an assumed target operating point, missing optional check, or error inside tolerance, all expected to `PASS_IN_SCOPE` |
| Metadata-only chronology probe | 1 | Untrusted description changed, with no time-series semantics actually tested |
| Metamorphic clean controls | 3 | Valid transformations expected to remain `PASS_IN_SCOPE` |

**Never publish (18/18) as empirical fault-detection sensitivity.** These are hand-picked source cases, not unknown or representative real failures. Do not include the 11 contract errors as physical detections. Do not count the three clean controls as empirical true negatives or infer a false-positive rate. Do not classify the metadata-only probe as a demonstrated timestamp-drift fault.

## Reproducibility and prespecification

- Deterministic seed: `OEM-NC11-DETERMINISTIC-V0.1-NO-RNG`. This is a fixed identifier, **not** a pseudorandom generator seed; no random sampling takes place.
- The [manifest](negative_controls_v0.1.json) pins **the exact Git blob SHA-1** of each of six author-derived baseline JSON files. The runner rejects altered baselines without a new versioned catalogue.
- Every NC ID specifies the base, mutation operator/values, expected status, optional target check, qualitative interpretation, and (where evaluable) frozen independently computed residual/threshold values.
- [`run_negative_controls.py`](../scripts/run_negative_controls.py) deep-copies the case, applies only the documented data-only operators, independently recalculates accounting using Decimal arithmetic, compares with EnerLint output and records every resulting source case and SHA-256 digest.
- For NaN/Infinity probes, the replay ledger stores a **valid JSON tagged representation**, e.g. `{"$nonfinite_python_value": "NaN"}`, instead of pretending that the invalid number is standards-compliant JSON. The runner injects the corresponding non-finite Python float and requires `ContractError`.
- The original four-case foundation, ten-case analytical catalogue and thirteen limiting-case numerical catalogue are **not replaced**. Overlapping faults/physics must not be summed as independent data.

## Scenario register

| ID | Fault family | Intent | Base case | Expected outcome |
|---|---|---|---|---|
| `NC-001` | sign | Compressor shaft-work sign inverted | `steady_compressor` | `FAIL` |
| `NC-002` | sign | Turbine work sign inverted | `steady_turbine` | `FAIL` |
| `NC-003` | sign | Heat flow sign inverted | `steady_nonadiabatic_compressor` | `FAIL` |
| `NC-004` | mass | Outlet flow overstated | `steady_compressor` | `FAIL` |
| `NC-005` | mass | Inlet flow understated | `steady_compressor` | `FAIL` |
| `NC-006` | unit_scale | kJ/kg quantity assigned into J/kg field | `steady_compressor` | `FAIL` |
| `NC-007` | unit_scale | Work magnitude multiplied by 1000 | `steady_compressor` | `FAIL` |
| `NC-008` | swap | Compressor inlet/outlet enthalpies swapped | `steady_compressor` | `FAIL` |
| `NC-009` | swap | Heat exchanger hot/cold outlet enthalpies swapped | `steady_heat_exchanger` | `FAIL` |
| `NC-010` | dropped_stream | Declared hot outlet dropped | `steady_heat_exchanger` | `FAIL` |
| `NC-011` | double_count | Hot outlet counted twice with unique name | `steady_heat_exchanger` | `FAIL` |
| `NC-012` | leak | Explicit leak revealed by mass and energy discrepancy | `steady_compressor` | `FAIL` |
| `NC-013` | storage_duration | Time interval stretched without integrated energy update | `storage_interval` | `FAIL` |
| `NC-014` | storage_inventory | Final thermal inventory wrong by 10 MJ | `storage_interval` | `FAIL` |
| `NC-015` | storage_swap | Start/end thermal inventory swapped | `storage_interval` | `FAIL` |
| `NC-016` | storage_swap | Charge and discharge rates interchanged | `storage_interval` | `FAIL` |
| `NC-017` | capacity | End-of-interval energy exceeds capacity | `storage_interval` | `FAIL` |
| `NC-018` | boundary | Shaft-work crossing interpreted on wrong side | `steady_nonadiabatic_compressor` | `FAIL` |
| `NC-019` | missing_required | Missing required work is contract rejection, not physics diagnosis | `steady_compressor` | `INVALID_INPUT` |
| `NC-020` | missing_required | Missing required heat is contract rejection | `steady_compressor` | `INVALID_INPUT` |
| `NC-021` | duplicate_name | Duplicate named port forbidden | `steady_heat_exchanger` | `INVALID_INPUT` |
| `NC-022` | unknown_units | Unexpected kJ/kg key cannot replace mandatory SI field | `steady_compressor` | `INVALID_INPUT` |
| `NC-023` | time_schema | Timestamp key unsupported in v0.1 steady input | `steady_compressor` | `INVALID_INPUT` |
| `NC-024` | time_schema | Discrete time-step key unsupported in single-interval input | `storage_interval` | `INVALID_INPUT` |
| `NC-025` | storage_duration | Zero time interval invalid | `storage_interval` | `INVALID_INPUT` |
| `NC-026` | storage_sign | Negative loss violates nonnegative-outflow contract | `storage_interval` | `INVALID_INPUT` |
| `NC-027` | nonfinite | Nonfinite shaft-work number invalid | `steady_compressor` | `INVALID_INPUT` |
| `NC-028` | nonfinite | Nonfinite enthalpy invalid | `steady_compressor` | `INVALID_INPUT` |
| `NC-029` | assumption | Steady-state assumption false is out of scope | `steady_compressor` | `INVALID_INPUT` |
| `NC-030` | compensated | Mass-flow and shaft-work scaling changes operating point undetected | `steady_compressor` | `PASS_IN_SCOPE` |
| `NC-031` | compensated | Wrong enthalpy datum offset offset by work, closure alone misses | `steady_compressor` | `PASS_IN_SCOPE` |
| `NC-032` | compensated | Correlated heat/work offset preserves first law | `steady_nonadiabatic_compressor` | `PASS_IN_SCOPE` |
| `NC-033` | split_fraction | Wrong split ratio conserves aggregate mass and energy | `steady_splitter_adiabatic` | `PASS_IN_SCOPE` |
| `NC-034` | missing_optional | Capacity not provided remains NOT_CHECKED, not a validated capacity | `storage_interval` | `PASS_IN_SCOPE` |
| `NC-035` | tolerance | Small nonzero 0.2 W residual tolerated by 1 W absolute floor | `steady_compressor` | `PASS_IN_SCOPE` |
| `NC-036` | chronology | Prose mutation does not prove clock offset, illustrates no timestamp validation | `storage_interval` | `PASS_IN_SCOPE` |
| `NC-037` | invariance | Permuting inlet order leaves conservation invariant | `steady_heat_exchanger` | `PASS_IN_SCOPE` |
| `NC-038` | invariance | Common enthalpy zero shift leaves mass-balanced residual invariant | `steady_compressor` | `PASS_IN_SCOPE` |
| `NC-039` | invariance | Matched heat/work changes algebraically conserve energy; only a control | `steady_turbine` | `PASS_IN_SCOPE` |

## Interpreting the escape classes

The six registered `blind_spot` scenarios expose concrete incompleteness of conservation-only checking: (1) compressor flow and shaft-power scaling that changes the target operating point; (2) outlet enthalpy offset compensated by shaft work; (3) offsetting heat and work errors; (4) a wrong splitter branch allocation at constant total mass/enthalpy; (5) absence of optional storage capacity, yielding `NOT_CHECKED`; and (6) a real nonzero 0.2 W residual within the default 1 W energy threshold. All six are expected to return `PASS_IN_SCOPE` by design. These failures of *observability* do not imply that the device or simulation would be safe or correct.

The timestamp/time-step examples are more limited. The v0.1 contract has **no timestamp or time-series sequencing field**: adding a timestamp or a `time_step_s` field violates strict input shape and is an **input rejection**, not a successfully identified clock drift or timestep inconsistency. Editing a free-text `declared_source` string does not create temporal evidence. A real chronology experiment needs a versioned time-indexed data contract and an independent chronological oracle.

## Reproduction

```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_negative_controls.py
python scripts/run_negative_controls.py
```

The standalone runner fails with an explicit diagnostic if any predeclared expected status, independently recomputed check, input baseline Git blob, reported residual, or selected control behavior changes. It writes `artifacts/ci/negative_controls_v0.1.json`, including each **reconstructed tagged input**, canonical SHA-256 and the observed result, along with the selected failure/escape status.

The [CI workflow](../.github/workflows/ci.yml) runs this on Ubuntu/Windows/macOS with Python 3.10/3.13, and uploads its ledger alongside built wheel/sdist, build SHA-256 manifest, and previous benchmark ledgers. Green CI establishes the specified software assertions, not externally measured physics.

## Scientific acceptance still open

Independent critique of selection and false-alarm interpretations is necessary ([#25](https://github.com/Open-Energy-Methods/enerlint/issues/25)). The [numeric tolerance audit](https://github.com/Open-Energy-Methods/enerlint/issues/3) remains open. Actual blind or held-out studies require source-side faults in separate modelling tools, rights-cleared measurements/reference quantities, calibrated uncertainty and reported false negatives **against independently established ground truth**.

**Allowed public statement:** “EnerLint includes 39 maintainer-selected replayable synthetic test scenarios, explicitly distinguishing failed balances, rejected input contracts, known escapes and invariant controls.”

**Not allowed:** “EnerLint detects all common faults”, “95% accurate”, “externally prespecified”, “validated real-world detection”, “certified”, or “a proper time-series fault detector.”
