# D1 — does an external thermal balance checker add anything?

**Protocol draft v0.1 · 27 October 2026 · experiment NOT executed**

The purpose is to test a claim, not confirm it: **under equivalent information, does EnerLint flag useful, consequential model-output inconsistencies that a well-configured native thermal-model workflow does not already flag?**

This is a *proposed* study, based on the workbench's internal research plan (experiment D1). This file contains **no experimental results, independent reviewers, external data, or superiority claims**.

## Comparison and minimum baseline

Choose one publicly reproducible, appropriately licensed thermal simulation workflow (candidate: TESPy, plus applicable native diagnostics and, if comparable, ExerPy). Freeze the chosen versions, settings, case exports and native validation options **before** inspecting fault-detection results. Read each product's documentation so native diagnostic coverage is not accidentally understated.

The five candidate physical case families are:

1. Single-inlet compressor with nonzero shaft work and declared heat exchange.
2. Single-inlet turbine with output work and energy balance.
3. Two-stream heat exchanger with independently stated in/out boundaries.
4. Mixer or splitter with multiple mass flow boundaries.
5. A steady multi-component process example that can be bounded at component and whole-system levels.

A candidate becomes an **included case only after** its full specification, equation, SI units, intended operating point, allowed export fields, data licence, and reference oracle have been registered. If the chosen native tool cannot model a family without altering its physics, replace or explicitly exclude it.

## Prespecified fault families (minimum ten, separate from case count)

Each mutation needs a machine-readable ID, affected field, magnitude, expected oracle behavior, severity interpretation, and reviewer status before testing:

- Incorrect heat crossing sign.
- Incorrect nonzero shaft-work sign.
- Omitted one material outlet.
- Duplicated inlet boundary crossing.
- Isolated outlet flow perturbation.
- Isolated outlet enthalpy perturbation.
- J/kg↔kJ/kg scale error.
- A property-reference mismatch when physically admissible and explicitly modelled.
- Correlated flow/work change that **passes** conservation by design.
- An incorrect but internally balanced operating point.

Not all cases are appropriate for all faults. Some should yield `INVALID_INPUT` or `NOT_CHECKED`, not `FAIL`; explicitly register expectations.

## Fairness control

Every trial must record what each method receives:

| Dimension | Native diagnostic | EnerLint |
|---|---|---|
| Model equations / network topology | Record exactly | Not available unless explicitly exported |
| Inlet/outlet states | Record | Record |
| Boundary/sign conventions | Record | Record |
| Solver convergence status | Record | Not used |
| Independent external operating-point reference | Only if provided | Only if provided |
| Allowed extra properties / tolerances | Record | Record |

A detection possible only because EnerLint receives **additional information** is an *integration advantage*, not an algorithmic superiority result. Conversely, native detection based on inaccessible internal states is not evidence of an unfair comparison. Report both information asymmetries.

Two layers should be reported separately:
1. **Equal supplied evidence:** what each method can conclude using harmonized observations.
2. **Natural workflow:** what each tool detects with its normal available data, recording the extra data and user effort.

## Predefined result fields

For each trial:

```text
trial_id; case_id; fault_class; fault_magnitude; reference_oracle;
native_configuration; native_status; enerlint_status; expected_label;
native_inputs; enerlint_inputs; extra_information; review_status;
adjudicated_outcome; ambiguity_reason; runtime_seconds;
setup_minutes; investigation_minutes; source_commit; data_rights
```

Record the four outcome classes:

- **Both detect:** shared detection.
- **Only native detects:** EnerLint offers no added detection on this trial.
- **Only EnerLint detects under equal evidence:** candidate incremental detection, pending oracle/reviewer checks.
- **Neither detects / cannot determine:** observed escape or abstention, never silently omitted.

A **false alarm** is when a permitted, independently adjudicated valid case is rejected. Separate invalid/unchecked inputs from actual test failures. Do not compute meaningful real-world sensitivity from developer-selected cases or treat correlated mutations as independent population observations.

## Reproducibility and decision gate

- Preserve exact solver and checker versions, original/modified exports, reference equations, expected labels, commands and public permissions.
- Run from clean environments; ideally have the reference labels reviewed by someone other than the checker author.
- Record native configuration even when it finds an error more easily than EnerLint.
- Compare numerical residuals and tolerances, not only green/red status.
- Include no confidential industrial data, and do not publish another author's material without permission.
- Do not quote a detection advantage until an actual reproducible and fairly controlled run supports it.
- If native checks already cover the useful cases more cheaply, prefer contributing a benchmark/upstream fix to launching another adapter.

**Execution status: NOT STARTED.** The immediate work is to select and rights-clear a baseline workflow, document its native diagnostic behavior and freeze the first five case cards. Track work and negative findings at [issue #18](https://github.com/Open-Energy-Methods/enerlint/issues/18).
