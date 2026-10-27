# Thermal control-volume boundaries: review before calculating

**Technical note CV-0.1 · 27 October 2026 · maintainer-derived, not externally reviewed.**

This is the physical side of EnerLint's [strict v0.1 verification contract](VERIFICATION_CONTRACT.md), with a voluntary, separate [author boundary-review preflight](../scripts/review_control_volume.py). Its role is to make important omissions visible **before** a mass or first-law result is interpreted. It cannot recover information that an exporter never supplied.

## 1. Draw the system first

```text
                             Q_into (+)
                                |
                     +----------v-----------+
      inlet stream ->|    control volume    |-> outlet stream
       mdot >= 0     |   (no accumulation)  |   mdot >= 0
       h, J/kg       +----------+-----------+   h, J/kg
                                |
                             W_out (+)
```

- The control surface is chosen by the modeller. **Crossings** count: mass at ports, heat through the surface, and work delivered or consumed across the surface.
- Flow direction is represented by separate `inlets` and `outlets` arrays; every `mass_flow_kg_s` is a nonnegative *magnitude*. Reversing an actual flow must move the stream between arrays. In/out names are not inferred from a prefix.
- `heat_into_volume_w` is positive **into** the volume and negative **out**. `shaft_work_out_w` is positive **out** (turbine) and negative **into** (compressor). This is a boundary crossing convention, not an instruction that all machines have to have work.
- Declare *measured or deliberately assumed* zero heat/work with numeric `0.0`. An absent required field is **INVALID_INPUT**; writing zero is an assertion the exporter must justify.
- No mass or energy accumulation is modelled. `steady_state=true` is an explicit required declaration, not something EnerLint proves from a single data row.
- The checker neglects changes in kinetic/potential flow energy **only when** `neglect_kinetic_potential=true` is declared. If those terms are consequential, the present contract is insufficient.
- Only nonreacting fluid enthalpy transport is in scope; no unmodelled species generation, chemical heat of reaction, leaks, electrical work across an expanded boundary, or other source terms should exist outside the supplied crossings. If they do, reformulate the boundary or abstain. The software cannot detect an unreported leak.
- Each specific enthalpy is a **declared** `J/kg` on a consistent property basis. A reference shift common to mass-balanced same-fluid streams is mathematically harmless, but inconsistent fluid/species reference choices can invalidate an apparent balance. EnerLint does **not** verify property reference compatibility; see [property-reference work](https://github.com/Open-Energy-Methods/enerlint/issues/15).

## 2. Equations and terms

The general steady-state total-energy rate conservation for a nonreacting open control volume, before simplifying, is:

```text
0 = Σ_in [m_dot (h + V²/2 + gz)] - Σ_out [m_dot (h + V²/2 + gz)]
    + Q_into - W_out
```

For EnerLint v0.1, **only when** kinetic and potential contributions are explicitly negligible, the reconstructed declared residuals are:

```text
R_m [kg/s] = Σ_in m_dot - Σ_out m_dot

R_E [W]    = Σ_in (m_dot·h) - Σ_out (m_dot·h)
             + Q_into - W_out
```

The checker compares each residual with its own [dimensional tolerance](NUMERICAL_TOLERANCE_POLICY.md). A test which passes within those tolerances is a **check of supplied numbers**, not a derivation that this boundary is physically complete. The `R_E` equation does not introduce explicit terms for accumulation, chemical generation, kinetic/potential transport or a separate electrically defined input. If an omitted term matters, returning `PASS_IN_SCOPE` cannot substantiate full first-law closure of the real process.

### What is unsupported versus what is an actual zero?

| Physical circumstance | Correct v0.1 treatment | Reason |
|---|---|---|
| No external heat transfer across a justified adiabatic boundary | Supply `heat_into_volume_w: 0.0` and document the assumption | Explicit **declared zero**, not measured validation |
| Zero shaft crossing for an aggregate heat exchanger | Supply `shaft_work_out_w: 0.0` and justify | No rotating-shaft boundary |
| Unknown or unreported shaft power | Do not substitute zero; **abstain or reject** | Cannot establish balance |
| Fluid leak not included in exported ports | Reject the physical boundary interpretation; first list the leak as an outlet if known | Balance code cannot infer it |
| Non-negligible flow kinetic or potential terms | Current case is **out of scope** | `neglect_kinetic_potential=true` would be unjustified |
| Periodic/variable-energy accumulation | Use a different validated contract; current steady case is **out of scope** | Current API assumes no accumulation |
| Exothermic reacting flow, incompatible reference enthalpies | Out of scope pending a new contract/reference policy | The supplied equation alone is not sufficient |
| Correctly reported nonzero heat into compressor | Signed positive `Q_into`, negative `W_out` | Both terms must appear |
| Omitted `heat_into_volume_w` or `shaft_work_out_w` key | `ContractError` / CLI exit **2** | Strict required fields |
| Extra undeclared `leak_w`, `accumulation_j` or `reaction_heat_w` field | `ContractError` / CLI exit **2** | Contract does not silently incorporate unknown physics |

## 3. Independent hand-checkable reference examples

The arithmetic below is authored **separately from the EnerLint implementation**, although it is still by the project maintainer. The starting values are synthetic and may be redistributed with this MIT-licensed repository. No equipment was measured and no scientific peer review has occurred.

| Boundary | Material crossings | Heat in | Work out | Mass residual | Energy residual |
|---|---|---:|---:|---:|---:|
| [Adiabatic compressor](../examples/steady_compressor.json) | 2 kg/s @ 300 kJ/kg → 2 kg/s @ 420 kJ/kg | 0 W | −240,000 W | 0 kg/s | 0 W |
| [Turbine](../examples/steady_turbine.json) | 2 kg/s @ 700 kJ/kg → 2 kg/s @ 500 kJ/kg | 0 W | +400,000 W | 0 kg/s | 0 W |
| [Aggregate heat exchanger](../examples/steady_heat_exchanger.json) | cold 1 kg/s @ 100 → 200 kJ/kg; hot 2 kg/s @ 500 → 450 kJ/kg | 0 W | 0 W | 0 kg/s | 0 W |
| [Nonadiabatic compressor](../examples/steady_nonadiabatic_compressor.json) | 1 kg/s @ 200 → 260 kJ/kg | +10,000 W | −50,000 W | 0 kg/s | 0 W |

```text
Adiabatic compressor:       R_E = 2(300000) - 2(420000) + 0 - (-240000) = 0 W
Turbine:                    R_E = 2(700000) - 2(500000) + 0 - 400000 = 0 W
Aggregate heat exchanger:   R_E = (1(100000)+2(500000)) - (1(200000)+2(450000)) = 0 W
Nonadiabatic compressor:    R_E = 1(200000) - 1(260000) + 10000 - (-50000) = 0 W
```

The exchanger ports are all counted in one *aggregate* boundary; a different component boundary requires a different heat-transfer crossing. Their apparent cancellation is not evidence that heat-transfer correlations or fluid thermodynamic properties are correct.

### Negative control: explicitly include the missing port

Start with the adiabatic compressor and *add* a separately declared hypothetical leak outlet, `m_leak=0.1 kg/s`, `h_leak=300000 J/kg`, leaving the original inlet, outlet and shaft-work values untouched:

```text
R_m = 2.0 - (2.0 + 0.1) = -0.1 kg/s
R_E = 2(300000) - 2(420000) - 0.1(300000) - (-240000) = -30000 W
```

Both mismatches exceed the case's default tolerances. **But** if the exporter excludes the leak from the JSON entirely, EnerLint sees the original closed compressor and may still return `PASS_IN_SCOPE`. This is precisely why physical-boundary selection must not be automated away.

### Another known escape: compensating error

Scale both compressor flow rates and work by 10%, leaving enthalpies unchanged. The two declared balances still close while the operating point differs from the target. See [field note 001](https://open-energy-methods.github.io/notes/001-a-pass-isnt-proof.html) and the [benchmark case card](BENCHMARK_CASE_CARDS.md). Conservation is necessary under this contract, not sufficient evidence of operating-point correctness.

## 4. Pre-run review checklist (the human owns the answers)

Before entering numbers, a reviewer should answer **yes, no, or unknown**—and record the reason rather than turning an unknown into a zero:

1. What is inside the drawn boundary (equipment housing, shaft, connected motor, fluid ports)? Why this boundary?
2. Have all *material* crossings been enumerated—including vents, leaks, bypasses, drains and recirculation ports crossing this particular surface?
3. Do the `inlets`/`outlets` names and nonnegative magnitudes agree with observed/assumed physical directions?
4. Have all heat flows crossing the surface been included, signed consistently, with each *zero* justified?
5. Have all shaft-work and other energy transfers crossing the surface been accounted for, with each zero justified?
6. Are mass and energy accumulation genuinely absent for the chosen time window?
7. Are changes in flow kinetic and potential energy negligible at the requested tolerance?
8. Are reactions, species creation and unmodelled source terms absent or explicitly outside the checked model?
9. Are all enthalpy values in J/kg and referenced consistently with the chosen boundary/species? Is the property basis documented?
10. Is an independent expectation of the operating point available? If not, is that uncertainty prominently disclosed?

If any answer is **no** or **unknown**, do not assert the *real* boundary is verified. Revise the boundary and inputs, seek appropriate evidence, or defer the check. Questions 1–9 have a matching explicit declaration in the optional preflight; question 10 remains a reminder that conservation cannot validate an operating point.

## 5. Machine-checkable *author-attested* sidecar, separate from EnerLint input v0.1

The [sample declaration](../examples/steady_compressor.boundary-review.json) is bound to the example's `case_id` and canonical input SHA-256 and enumerates the same material port names. It requires **true** answers for the nine defined preflight statements, nonempty boundary/evidence/author text, and reasons whenever a heat or shaft-work crossing is numerically zero.

```bash
python -m pip install -e ".[dev]"
python scripts/review_control_volume.py \
    examples/steady_compressor.json \
    examples/steady_compressor.boundary-review.json
```

A completed checklist exits **0** and prints `DECLARATION_COMPLETE` alongside the *separate* numeric status, plus an **AUTHOR ATTESTATION ONLY** warning. Missing, stale, inconsistent, unsupported or unanswered declarations exit **2** with `BOUNDARY_REVIEW_INCOMPLETE`.

This preflight **does not alter** the strict EnerLint v0.1 input contract, `check_case`, the report schema, its status vocabulary or the `enerlint check` CLI. The standard checker **does not require this sidecar**; if it is omitted, the existing scoped balance may still pass. The preflight is an additional, opt-in discipline for reviewers—not a claim to discover invisible ports or certify the boundary.

The SHA-256 checks whether the review relates to unchanged JSON values; it does not authenticate the model, a third-party dataset or the truth of an author's answer. Completing a checklist—even all YES—**cannot independently establish the actual plant/solver boundary**.

## 6. External review remains open

A different engineer should challenge the stated boundary and residual terms, redo one example without consulting EnerLint output, identify misleading omissions, and review enthalpy reference assumptions. This work is part of [the independent critique request](https://github.com/Open-Energy-Methods/enerlint/issues/25); CI green does not substitute for it.

**Release statement allowed today:** “EnerLint checks declared, strictly scoped steady mass and first-law energy balances, and provides an optional author-attested control-volume review.” **Not allowed:** “EnerLint detects all omitted energy flows, validates control-volume boundaries or certifies physical models.”
