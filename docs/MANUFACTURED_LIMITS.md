# Manufactured and limiting reference cases — v0.1

**27 October 2026 · EnerLint #10 · 13 maintainer-derived synthetic cases · external review pending**

This document supplies an independently inspectable **numerical software test** suite, not a claim that the physical system was measured, calibrated or independently model-validated. The maintained implementation is [`src/enerlint/verify.py`](../src/enerlint/verify.py); the separately implemented [Decimal arithmetic oracle](../scripts/run_analytical_catalog.py) recomputes the fundamental equations from each supplied SI case without invoking the checker's equations. A [dedicated runner](../scripts/run_manufactured_limits.py) verifies the frozen reference records and preserves deliberately **missed** errors. Both were written by the project maintainer; independence of code paths is **not external peer review**.

The **immutable-for-this-version** source of all input JSON objects and frozen expected results is [`manufactured_limits_v0.1.json`](manufactured_limits_v0.1.json). Each `TH-LM` ID is stable and version `0.1` is not to be silently redefined. Inputs use the strict v0.1 case schema and invented physical states under the repository's MIT licence; no industrial, experimental or proprietary property values are used.

## Methods and interpretation

For steady, nonreacting control volumes at declared steady state, with flow kinetic/potential changes neglected:

```text
R_m = Σ_in m_dot − Σ_out m_dot
R_E = Σ_in(m_dot·h) − Σ_out(m_dot·h) + Q_into − W_out
threshold_m = max(1e-9 kg/s, 1e-8 × mass_scale)
threshold_E = max(1 W, 1e-8 × centered_energy_scale)
mass_scale = Σ_in m_dot + Σ_out m_dot
centered_energy_scale = Σ_all m_dot |h − weighted_mean(h)| + |Q_into| + |W_out|
```

For constant-rate single storage intervals:

```text
R_storage = (E_final − E_initial) − (Q_charge − Q_discharge − Q_loss) × duration
threshold_storage = max(1 J, 1e-8 × [|ΔE|+|Q_charge dt|+|Q_discharge dt|+|Q_loss dt|])
storage capacity: exact inequality 0 ≤ E_initial, E_final ≤ capacity, when declared
```

A **PASS** means the *declared* residual magnitude does not exceed the software threshold; it can be **nonzero** and is not a certificate of physical conservation at infinite precision. `NOT_CHECKED` means optional data are absent, not a pass. `INVALID_INPUT` means contract rejection **before** producing an evaluated physical balance; the Python API throws `ContractError` and CLI exits 2. Some extreme manufactured conditions deliberately have no credible plant counterpart.

## Frozen case index

| ID | Manufactured/limiting problem | Expected outcome | Numerically important consequence |
|---|---|---|---|
| [TH-LM-001](#th-lm-001) | Zero-flow no-transfer control volume | `PASS_IN_SCOPE` | R=0 W; threshold=1 W |
| [TH-LM-002](#th-lm-002) | Near-zero matched flow and infinitesimal shaft input | `PASS_IN_SCOPE` | R=0 W; threshold=1 W |
| [TH-LM-003](#th-lm-003) | Isenthalpic equal-flow ideal boundary | `PASS_IN_SCOPE` | R=0 W; threshold=1 W |
| [TH-LM-004](#th-lm-004) | Exact inclusive absolute energy threshold | `PASS_IN_SCOPE` | R=1 W; threshold=1 W |
| [TH-LM-005](#th-lm-005) | Exact inclusive absolute mass threshold | `PASS_IN_SCOPE` | R=0 W; threshold=1 W |
| [TH-LM-006](#th-lm-006) | Large common property zero with exact cancellation | `PASS_IN_SCOPE` | R=0 W; threshold=1 W |
| [TH-LM-007](#th-lm-007) | Common +1e12 J/kg enthalpy datum shift | `PASS_IN_SCOPE` | R=0 W; threshold=1 W |
| [TH-LM-008](#th-lm-008) | Reversed port and signed energy crossing | `PASS_IN_SCOPE` | R=0 W; threshold=1 W |
| [TH-LM-009](#th-lm-009) | Power/flow scaling under unchanged enthalpy states | `PASS_IN_SCOPE` | R=0 W; threshold=1 W |
| [TH-LM-010](#th-lm-010) | Ideal lossless storage with exactly filled capacity | `PASS_IN_SCOPE` | R=0 J; threshold=1 J |
| [TH-LM-011](#th-lm-011) | Large cancelling charge/discharge masks a small stored-energy discrepancy | `PASS_IN_SCOPE` | R=0 J; threshold=20.0000002 J |
| [TH-LM-012](#th-lm-012) | Zero-duration storage interval is invalid | `INVALID_INPUT` | No checks run |
| [TH-LM-013](#th-lm-013) | Finite input values with overflowing m-times-h are invalid | `INVALID_INPUT` | No checks run |

## Source case cards and expected mutations

Every case below uses the **same signed-crossing conventions and omissions** as the v0.1 physical contract. Exact numerical expected values (including `scale` and `threshold` for each reported check) are frozen in the JSON catalogue; the guide is a human-oriented map, not a second mutable source of truth.

### TH-LM-001 — Zero-flow no-transfer control volume

**Declared limiting conditions:** Both nonempty port lists report zero mass; heat and shaft crossing zero; steady no-accumulation assumption explicitly true.

**Independently inspectable input:** `lm_zero_flux` (`steady_control_volume`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Ports:** inlet `in` 0 kg/s @ 500000 J/kg. Outlet `out` 0 kg/s @ 600000 J/kg. Heat entering: 0 W; shaft work leaving: 0 W.

**Frozen reference outcomes:** `steady_mass_closure`: **PASS**, residual 0 kg/s, scale 0 kg/s, threshold 1e-9 kg/s; `steady_first_law`: **PASS**, residual 0 W, scale 0 W, threshold 1 W.

**Deliberate alterations:**

- Replace `shaft_work_out_w` with `2`: expected `FAIL`, `steady_first_law` residual -2. Missing nonzero external work is detectable at 1 W absolute floor.

**Limit:** No information on whether a real machine can remain in this idle state.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-002 — Near-zero matched flow and infinitesimal shaft input

**Declared limiting conditions:** Positive flow 1e-12 kg/s on both sides; inlet 100 kJ/kg, outlet 200 kJ/kg; work into CV 1e-7 W.

**Independently inspectable input:** `lm_trace_flow` (`steady_control_volume`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Ports:** inlet `in` 1e-12 kg/s @ 100000 J/kg. Outlet `out` 1e-12 kg/s @ 200000 J/kg. Heat entering: 0 W; shaft work leaving: -1e-7 W.

**Frozen reference outcomes:** `steady_mass_closure`: **PASS**, residual 0 kg/s, scale 2e-12 kg/s, threshold 1e-9 kg/s; `steady_first_law`: **PASS**, residual 0 W, scale 2e-7 W, threshold 1 W.

**Deliberate alterations:**

- Replace `shaft_work_out_w` with `0`: expected `PASS_IN_SCOPE`, `steady_first_law` residual -1e-7. Deliberate 100% trace-work omission remains below 1 W energy floor.
- Replace `shaft_work_out_w` with `2`: expected `FAIL`, `steady_first_law` residual -2.0000001. Macroscopic 2 W perturbation still fails.

**Limit:** Energy absolute floor 1 W dominates trace-scale energy; a significant relative error can pass.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-003 — Isenthalpic equal-flow ideal boundary

**Declared limiting conditions:** One inlet/outlet 2 kg/s at equal 250 kJ/kg; external heat/work zero.

**Independently inspectable input:** `lm_identical_enthalpy` (`steady_control_volume`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Ports:** inlet `in` 2 kg/s @ 250000 J/kg. Outlet `out` 2 kg/s @ 250000 J/kg. Heat entering: 0 W; shaft work leaving: 0 W.

**Frozen reference outcomes:** `steady_mass_closure`: **PASS**, residual 0 kg/s, scale 4 kg/s, threshold 4e-8 kg/s; `steady_first_law`: **PASS**, residual 0 W, scale 0 W, threshold 1 W.

**Deliberate alterations:**

- Replace `heat_into_volume_w` with `2`: expected `FAIL`, `steady_first_law` residual 2. Uncompensated heat crossing is detected.

**Limit:** Real throttling would need other physical constraints; passing balance cannot prove pressure drop.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-004 — Exact inclusive absolute energy threshold

**Declared limiting conditions:** Steady 1 kg/s equal zero-reference enthalpies, Q_in exactly +1 W, W_out 0; residual +1 W equals the default 1 W floor.

**Independently inspectable input:** `lm_exact_energy_threshold` (`steady_control_volume`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Ports:** inlet `in` 1 kg/s @ 0 J/kg. Outlet `out` 1 kg/s @ 0 J/kg. Heat entering: 1 W; shaft work leaving: 0 W.

**Frozen reference outcomes:** `steady_mass_closure`: **PASS**, residual 0 kg/s, scale 2 kg/s, threshold 2e-8 kg/s; `steady_first_law`: **PASS**, residual 1 W, scale 1 W, threshold 1 W.

**Deliberate alterations:**

- Replace `heat_into_volume_w` with `1.01`: expected `FAIL`, `steady_first_law` residual 1.01. Slightly above exact inclusive 1 W floor fails.

**Limit:** PASS_IN_SCOPE does not mean R_E=0; threshold inclusivity is a numeric policy.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-005 — Exact inclusive absolute mass threshold

**Declared limiting conditions:** Zero inlet flow and a 1e-9 kg/s outlet crossing; zero enthalpy, Q/W; residual is -1e-9 kg/s.

**Independently inspectable input:** `lm_exact_mass_threshold` (`steady_control_volume`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Ports:** inlet `in` 0 kg/s @ 0 J/kg. Outlet `out` 1e-9 kg/s @ 0 J/kg. Heat entering: 0 W; shaft work leaving: 0 W.

**Frozen reference outcomes:** `steady_mass_closure`: **PASS**, residual -1e-9 kg/s, scale 1e-9 kg/s, threshold 1e-9 kg/s; `steady_first_law`: **PASS**, residual 0 W, scale 0 W, threshold 1 W.

**Deliberate alterations:**

- Replace `outlets.0.mass_flow_kg_s` with `1.01e-9`: expected `FAIL`, `steady_mass_closure` residual -1.01e-9. Residual just outside absolute mass threshold fails.

**Limit:** Physically exact steady mass conservation is not satisfied; only configured software tolerance permits PASS.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-006 — Large common property zero with exact cancellation

**Declared limiting conditions:** Two 1 kg/s inlets at 1e15 ± 1000 J/kg, 2 kg/s outlet at 1e15 J/kg; adiabatic and no work.

**Independently inspectable input:** `lm_large_cancellation` (`steady_control_volume`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Ports:** inlet `a` 1 kg/s @ 1000000000001000 J/kg; inlet `b` 1 kg/s @ 999999999999000 J/kg. Outlet `out` 2 kg/s @ 1000000000000000 J/kg. Heat entering: 0 W; shaft work leaving: 0 W.

**Frozen reference outcomes:** `steady_mass_closure`: **PASS**, residual 0 kg/s, scale 4 kg/s, threshold 4e-8 kg/s; `steady_first_law`: **PASS**, residual 0 W, scale 2000 W, threshold 1 W.

**Deliberate alterations:**

- Replace `inlets.0.specific_enthalpy_j_kg` with `1000000000001004`: expected `FAIL`, `steady_first_law` residual 4. Four J/kg noncompensating change is represented and detected.

**Limit:** Large absolute values are representable but smaller-than-ULP changes may disappear; not a property-data validity test.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-007 — Common +1e12 J/kg enthalpy datum shift

**Declared limiting conditions:** 2 kg/s compressor input 1e12+300k and output 1e12+420k; W_out=-240k W; common offset cancels under exact mass closure.

**Independently inspectable input:** `lm_common_datum_shift` (`steady_control_volume`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Ports:** inlet `in` 2 kg/s @ 1000000300000 J/kg. Outlet `out` 2 kg/s @ 1000000420000 J/kg. Heat entering: 0 W; shaft work leaving: -240000 W.

**Frozen reference outcomes:** `steady_mass_closure`: **PASS**, residual 0 kg/s, scale 4 kg/s, threshold 4e-8 kg/s; `steady_first_law`: **PASS**, residual 0 W, scale 480000 W, threshold 1 W.

**Deliberate alterations:**

- Replace `outlets.0.specific_enthalpy_j_kg` with `1000000420002`: expected `FAIL`, `steady_first_law` residual -4. Changing only one reference endpoint is rejected by first-law accounting.

**Limit:** A common shift is mathematically harmless only with mass closure and a compatible fluid basis; individual port offsets are unsafe.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-008 — Reversed port and signed energy crossing

**Declared limiting conditions:** Algebraic reversal of a nonadiabatic compressor case: inlet h260k, outlet h200k, Q_in=-10k, W_out=+50k for 1 kg/s.

**Independently inspectable input:** `lm_boundary_reversal` (`steady_control_volume`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Ports:** inlet `in` 1 kg/s @ 260000 J/kg. Outlet `out` 1 kg/s @ 200000 J/kg. Heat entering: -10000 W; shaft work leaving: 50000 W.

**Frozen reference outcomes:** `steady_mass_closure`: **PASS**, residual 0 kg/s, scale 2 kg/s, threshold 2e-8 kg/s; `steady_first_law`: **PASS**, residual 0 W, scale 120000 W, threshold 1 W.

**Deliberate alterations:**

- Replace `heat_into_volume_w` with `10000`: expected `FAIL`, `steady_first_law` residual 20000. Reversing ports without preserving the corresponding heat sign breaks balance.

**Limit:** Algebraic reversal of a steady equation is not proof of a physically reversible process.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-009 — Power/flow scaling under unchanged enthalpy states

**Declared limiting conditions:** Scale baseline compressor inlet/outlet flows from 2 to 20 kg/s and shaft input from 240 to 2400 kW; no heat crossing.

**Independently inspectable input:** `lm_flow_power_scaled` (`steady_control_volume`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Ports:** inlet `in` 20 kg/s @ 300000 J/kg. Outlet `out` 20 kg/s @ 420000 J/kg. Heat entering: 0 W; shaft work leaving: -2400000 W.

**Frozen reference outcomes:** `steady_mass_closure`: **PASS**, residual 0 kg/s, scale 40 kg/s, threshold 4e-7 kg/s; `steady_first_law`: **PASS**, residual 0 W, scale 4800000 W, threshold 1 W.

**Deliberate alterations:**

- Replace `shaft_work_out_w` with `-2399990`: expected `FAIL`, `steady_first_law` residual -10. Uncompensated ten-watt change still fails despite scaled flow.

**Limit:** All balances close at an entirely different operating point, exposing the known conservation-only escape.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-010 — Ideal lossless storage with exactly filled capacity

**Declared limiting conditions:** Single interval duration 600 s; E rises 500k to 800k J by 500 W charging; zero loss/discharge; capacity exactly 800k J.

**Independently inspectable input:** `lm_ideal_storage_capacity` (`storage_interval`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Inventory/interval:** initial 500000 J, final 800000 J, Δt 600 s, charge 500 W, discharge 0 W, loss 0 W, capacity 800000 J.

**Frozen reference outcomes:** `storage_energy_closure`: **PASS**, residual 0 J, scale 600000 J, threshold 1 J; `storage_capacity`: **PASS**, residual 0 J, scale 0 J, threshold 0 J.

**Deliberate alterations:**

- Replace `capacity_j` with `799999`: expected `FAIL`, `storage_capacity` residual 1. Any positive capacity excursion fails the zero-tolerance capacity constraint.

**Limit:** An energy capacity check at equality does not test power or usable outlet temperature.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-011 — Large cancelling charge/discharge masks a small stored-energy discrepancy

**Declared limiting conditions:** Ten seconds, initial inventory 1e9 J, charge 100000001 W, discharge 100000000 W, loss zero; final inventory initial+10 J.

**Independently inspectable input:** `lm_storage_near_cancellation` (`storage_interval`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Inventory/interval:** initial 1000000000 J, final 1000000010 J, Δt 10 s, charge 100000001 W, discharge 100000000 W, loss 0 W, capacity **NOT SUPPLIED**.

**Frozen reference outcomes:** `storage_energy_closure`: **PASS**, residual 0 J, scale 2000000020 J, threshold 20.0000002 J; `storage_capacity`: **NOT_CHECKED**, residual NOT_CHECKED , scale NOT_CHECKED , threshold NOT_CHECKED .

**Deliberate alterations:**

- Replace `energy_final_j` with `1000000020`: expected `PASS_IN_SCOPE`, `storage_energy_closure` residual 10. Ten-joule inventory error is below relative threshold and remains a scoped pass.
- Replace `energy_final_j` with `1000000110`: expected `FAIL`, `storage_energy_closure` residual 100. Hundred-joule inventory error exceeds the threshold and is flagged.

**Limit:** Relative energy threshold of 20.0000002 J permits a 10 J inventory mistake; not a fault sensitivity claim.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-012 — Zero-duration storage interval is invalid

**Declared limiting conditions:** Rate and state values are finite but dt=0; contract requires a strictly positive interval.

**Independently inspectable input:** `lm_invalid_zero_duration` (`storage_interval`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Inventory/interval:** initial 100 J, final 100 J, Δt 0 s, charge 0 W, discharge 0 W, loss 0 W, capacity **NOT SUPPLIED**.

**Expected:** `ContractError`, with diagnostic containing `must be > 0`; numerical residuals are **not evaluated**.

**Limit:** Do not conflate an invalid mathematical interval with an evaluated conservation failure.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

### TH-LM-013 — Finite input values with overflowing m-times-h are invalid

**Declared limiting conditions:** One inlet and outlet, each 1e308 kg/s with h=1e308 J/kg. Inputs individually parse as finite binary64 but products overflow.

**Independently inspectable input:** `lm_invalid_transport_overflow` (`steady_control_volume`) in [JSON catalogue](manufactured_limits_v0.1.json).

**Ports:** inlet `in` 1e+308 kg/s @ 1e+308 J/kg. Outlet `out` 1e+308 kg/s @ 1e+308 J/kg. Heat entering: 0 W; shaft work leaving: 0 W.

**Expected:** `ContractError`, with diagnostic containing `Transport energy overflow`; numerical residuals are **not evaluated**.

**Limit:** No numerical closure result is meaningful. This is not a physically plausible flow and must be rejected rather than passed.

**Independence and rights:** maintainer-derived synthetic numbers; not externally reviewed, not empirical validation. Original case and prose are made available under the project's MIT licence.

---

## Explicit limiting/convergence sequences

The regression suite varies an otherwise balanced compressor's flow and shaft power together with factors `10⁰`, `10⁻³`, `10⁻⁶`, `10⁻⁹` and `10⁻¹²` (same enthalpy endpoints). It tests that each resulting declared residual stays within the stated threshold while the absolute tolerance progressively dominates; **this is an algebraic/numerical limiting study, not a solver mesh-convergence or time-step-convergence study**. A genuine convergence-order benchmark would require specifying an independently solved discretized model, which EnerLint v0.1 does not provide.

The exact-threshold cases, near-zero flow and large charge/discharge cancellation preserve the critical **non-detections** in the evidence ledger. In particular, a removed `1e-7 W` shaft term passes when the energy floor is `1 W`, and a `10 J` inventory discrepancy passes when the tolerance is approximately `20 J`. These are limitations of a deliberately broad numeric threshold policy, not proof that those physical errors are harmless.

## Reproduce the developer self-test

```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_manufactured_limits.py
python scripts/run_manufactured_limits.py
```

The command records the 13 source cases, their expected statuses, all perturbations and the **two tolerated nonzero discrepancies** in the independent run ledger `artifacts/ci/manufactured_limits_v0.1.json`. CI should upload that file with the ten-case analytical catalogue, distribution archives and the per-run SHA-256 build manifest. The original four-case foundation ledger and ten-case [analytical reference catalogue](BENCHMARK_CASE_CARDS.md) remain **unchanged**; reused physics is not counted as an independent empirical dataset.

**Open gates:** quantitative tolerance justification and conditioning scrutiny ([issue #3](https://github.com/Open-Energy-Methods/enerlint/issues/3)), review by an external engineer ([issue #25](https://github.com/Open-Energy-Methods/enerlint/issues/25)), and a rights-cleared independently implemented model comparison. A green CI run only supports reproducible software checks.
