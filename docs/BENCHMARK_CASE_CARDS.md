# EnerLint benchmark case cards — document revision 0.2 (case IDs v0.1)

**Status:** **ten** complete **maintainer-derived** analytical cards (eight steady CV cases, two storage cases), 27 October 2026. They are **not externally peer reviewed**, not empirical measurements, and not assertions of originality of conservation laws. Each is independently *checkable* from SI arithmetic, not independently *reviewed*. Frozen machine-readable expected values live in [analytical_reference_v0.1.json](analytical_reference_v0.1.json).

This document implements a small, concrete portion of the case-card structure proposed in the internal research plan. The calculations are written here independently of EnerLint source code so a reviewer can check them with a calculator and the stated equations.

## How to read and review a card

Each benchmark should include:

| Field | Requirement |
|---|---|
| Stable benchmark ID / version | Never silently replace or reinterpret an existing case |
| System and boundary | What crosses the control volume, and what does not |
| Assumptions | Time regime, included/omitted physics, sign conventions |
| Reference source | Equation or openly accessible published source; cite version |
| Units and property datum | SI quantities and consistent enthalpy reference where applicable |
| Input artifact and provenance | Exact file path, public permission/licence, and claimed origin |
| Independent oracle | Arithmetic that can be checked without EnerLint |
| Expected checks and tolerances | Status, residual, scale, threshold with justification |
| Known escape or negative control | Exactly which defect is detectable, and which is not |
| Independence/reviewer status | Who derived it; whether another person checked it |
| Rights and limitations | Whether input/output may be redistributed and what cannot be inferred |
| Revision | Why a case changed; preserve prior records |

A **developer-authored expected answer** is not an independent reviewer assessment. The finite-precision tolerance values below are implementation defaults and are *not* justified measurement-error bounds.

---

## TH-CV-001 v0.1 — steady adiabatic compressor

**Purpose:** check a steady, single-inlet, single-outlet mass and first-law energy balance using separately provided SI exports.

**Physical boundary:** compressor control volume. One material inlet and outlet, no declared heat transfer across the boundary, shaft work **into** the compressor. No mass or energy accumulation. Neglect changes in kinetic and potential energy. No chemical reaction or internal fluid-property assessment. Uniform common enthalpy reference is assumed.

**Source:** first-law steady control-volume equation with the explicit sign convention recorded in [the verification contract](VERIFICATION_CONTRACT.md). This is an elementary manually derived reference, not a new scientific contribution.

| Quantity | Value | Units |
|---|---:|---|
| Inlet mass flow | 2 | kg/s |
| Outlet mass flow | 2 | kg/s |
| Inlet specific enthalpy | 300,000 | J/kg |
| Outlet specific enthalpy | 420,000 | J/kg |
| Heat entering boundary | 0 | W |
| Shaft work *leaving* boundary | −240,000 | W |

**Independent reference arithmetic** (using the values above, not EnerLint functions):

```text
R_mass   = m_in - m_out
         = 2 - 2 = 0 kg/s

R_energy = (m_in * h_in) - (m_out * h_out) + Q_in - W_out
         = (2 * 300000) - (2 * 420000) + 0 - (-240000)
         = 0 W
```

**Implementation thresholds for this one case:**
- Mass scale = |2| + |2| = 4 kg/s; threshold = max(1e−9, 1e−8 × 4) = **4e−8 kg/s**.
- Mean reference enthalpy = (2 × 300,000 + 2 × 420,000) / 4 = **360,000 J/kg**.
- Energy scale = 2 × |300,000 − 360,000| + 2 × |420,000 − 360,000| + 0 + 240,000 = **480,000 W**; threshold = max(1 W, 1e−8 × 480,000 W) = **1 W**.
- **Expected:** `steady_mass_closure = PASS`, `steady_first_law = PASS`; case `PASS_IN_SCOPE`.

**Deliberate failing mutation:** change `shaft_work_out_w` from −240,000 W to +240,000 W, keeping all other values fixed. Then `R_energy = −480,000 W`, so `steady_first_law = FAIL`.

**Deliberate *escaping* mutation:** change each of the two mass flows from 2 to **2.2 kg/s** and shaft work from −240,000 to **−264,000 W**, without changing enthalpies. The new energy residual is `2.2 × 300000 − 2.2 × 420000 − (−264000) = 0 W`; mass residual is also zero. This is an intentionally incorrect answer **relative to the original target operating point**, but both declared conservation equations still pass. Without an independent operating-point constraint, EnerLint cannot reject it on balance grounds.

**Input:** [`examples/steady_compressor.json`](../examples/steady_compressor.json), with synthetic provenance encoded in the file. Mutation code: [`scripts/run_foundation_benchmark.py`](../scripts/run_foundation_benchmark.py). The test and its author-created modifications may be redistributed under the repository's MIT license; no private/industrial data are included in this case.

**Reviewer/independence status:** independently laid-out *arithmetic* by the project maintainer; **no external scientific review**. All results and expected outcomes remain correlated with the developer's own benchmark design. **Not evidence** of compressor performance, measurement accuracy, operating-point correctness, or industrial fault detection.

---

## TH-ST-001 v0.1 — one-hour idealized thermal store

**Purpose:** check constant-rate interval energy accounting and a declared energy capacity.

**Physical boundary:** lumped stored-energy inventory with one aggregate charging rate, one aggregate discharging rate, and one aggregate outward loss rate. Rates are constant averages for this interval; no temperature distribution, heat-transfer coefficient, exergy or state-dependent storage behavior is modelled. Energy reference is fixed at the declared nonnegative zero-energy state.

| Quantity | Value | Units |
|---|---:|---|
| Initial stored energy | 2,000,000,000 | J |
| Final stored energy | 2,216,000,000 | J |
| Charge into store | 120,000 | W |
| Discharge out of store | 50,000 | W |
| Loss out of store | 10,000 | W |
| Interval duration | 3,600 | s |
| Declared capacity | 3,000,000,000 | J |

**Independent reference arithmetic:**

```text
Net heat rate      = 120000 - 50000 - 10000 = 60000 W
Integrated net heat = 60000 * 3600 = 216000000 J
Change in inventory = 2216000000 - 2000000000 = 216000000 J
R_storage           = 216000000 - 216000000 = 0 J
Capacity constraint = 0 <= 2000000000, 2216000000 <= 3000000000
```

**Implementation thresholds for this one case:**
- Storage scale = |216,000,000| + |120,000 × 3600| + |50,000 × 3600| + |10,000 × 3600| = **864,000,000 J**.
- Storage threshold = max(1 J, 1e−8 × 864,000,000 J) = **8.64 J**.
- Capacity threshold: **0 J** (declared exact constraint, not measurement uncertainty).
- **Expected:** `storage_energy_closure = PASS`, `storage_capacity = PASS`; case `PASS_IN_SCOPE`.

**Deliberate failing mutation:** increase final inventory by **5,000,000 J** without adjusting integrated heat. The storage residual becomes **+5,000,000 J**, so closure fails.

**Known limitations:** a passing result cannot establish usable outlet temperature, power deliverability, insulation correctness, thermal stratification, measurement validity or chronology between samples. In particular, this case says nothing about irregular time-series intervals.

**Input:** [`examples/storage_interval.json`](../examples/storage_interval.json), a hand-constructed example published with this MIT-licensed repository. No measured data or third-party confidential material.

**Reviewer/independence status:** maintainer-derived manual calculation; **external review outstanding**. These results are software test oracles, not an experiment on an actual energy store.

---

## TH-CV-002 v0.1 — adiabatic turbine

**System/boundary:** one inlet and outlet, no declared heat transfer, shaft power **out**. Steady, nonreacting, no accumulation or modeled kinetic/potential terms; inlet/outlet fluid properties use one assumed compatible specific-enthalpy datum.

**Input:** [`examples/steady_turbine.json`](../examples/steady_turbine.json), synthetic and MIT-distributed.

| Port or crossing | Value | Unit |
|---|---:|---|
| Inlet and outlet mass flow | 2 each | kg/s |
| Inlet → outlet enthalpy | 700,000 → 500,000 | J/kg |
| Heat into boundary | 0 | W |
| Shaft work out | +400,000 | W |

**Independent manual oracle:**

```text
R_m = 2 - 2 = 0 kg/s
R_E = 2(700000) - 2(500000) + 0 - 400000 = 0 W
Mass scale = 4 kg/s; threshold = 4e-8 kg/s
h_ref = [2(700000)+2(500000)] / 4 = 600000 J/kg
Energy scale = 2|700000-600000| + 2|500000-600000| + |400000|
             = 800000 W; threshold = 1 W
```

**Expected checks:** mass `PASS`, first-law `PASS`; whole case `PASS_IN_SCOPE`. **Negative control:** change shaft work out to −400,000 W; `R_E = +800000 W`, first law `FAIL`.

**Known escape / limitations:** correlated changes to turbine flow and power can still balance; no turbine isentropic efficiency, exhaust state, mechanical losses or actual power-curve reference is tested. **Reviewer:** maintainer-only hand arithmetic, no external review; public synthetic redistribution under project MIT.

---

## TH-CV-003 v0.1 — aggregate adiabatic two-circuit heat exchanger

**System/boundary:** both cold and hot loops enclosed by **one** steady, adiabatic aggregate boundary; no shaft work or chemical sources, negligible external kinetic/potential terms. The distinct loops are each assumed mass-balanced and each uses its own internally compatible enthalpy datum; their absolute zeros need not be equal if each circuit is separately conserved.

**Input:** [`examples/steady_heat_exchanger.json`](../examples/steady_heat_exchanger.json), hand-constructed and MIT-distributed.

| Port | Mass (kg/s) | Enthalpy (J/kg) |
|---|---:|---:|
| Cold inlet → outlet | 1 → 1 | 100,000 → 200,000 |
| Hot inlet → outlet | 2 → 2 | 500,000 → 450,000 |

**Independent manual oracle:**

```text
R_m = (1 + 2) - (1 + 2) = 0 kg/s
R_E = [1(100000) + 2(500000)] - [1(200000) + 2(450000)] = 0 W
Cold receives +100000 W; hot supplies −100000 W; aggregate transfer cancels
Mass scale = 6 kg/s; threshold = 6e-8 kg/s
h_ref = [100000+1000000+200000+900000]/6 = 366666.666... J/kg
Energy scale = Σ_ports m|h-h_ref| = 866666.666... W
Energy threshold = 1 W
```

**Expected:** both steady checks `PASS`; `PASS_IN_SCOPE`. **Negative control:** change cold outlet enthalpy to 201,000 J/kg, unchanged others; `R_E = −1000 W`, first law `FAIL`.

**Known escape / limitations:** matching aggregate powers do not demonstrate exchanger pinch-point feasibility, finite area, fluid mixing, fouling, temperature effectiveness, property-source validity or each loop's real integrity. **Reviewer:** maintainer-only; no independent external review. **Rights:** original synthetic data under MIT.

---

## TH-CV-004 v0.1 — nonadiabatic compressor

**System/boundary:** one steady compressor with heat **into** (+10 kW) and shaft work **into** (−50 kW under the out-positive convention), with no accumulation, chemical reaction or kinetic/potential flow terms. The fluid's inlet and outlet are declared to share one compatible reference.

**Input:** [`examples/steady_nonadiabatic_compressor.json`](../examples/steady_nonadiabatic_compressor.json), synthetic and MIT-distributed.

```text
m_in = m_out = 1 kg/s;  h_in = 200000 J/kg;  h_out = 260000 J/kg
Q_in = +10000 W; W_out = -50000 W
R_m = 1 - 1 = 0 kg/s
R_E = 1(200000) - 1(260000) + 10000 - (-50000) = 0 W
Mass scale = 2 kg/s; threshold = 2e-8 kg/s
h_ref = (200000+260000)/2 = 230000 J/kg
Energy scale = 30000 + 30000 + 10000 + 50000 = 120000 W
Energy threshold = 1 W
```

**Expected:** mass and first-law `PASS`. **Negative control:** reverse declared heat to −10,000 W without adjusting shaft work; `R_E = −20000 W`, first law `FAIL`.

**Known escape:** heat and work errors can compensate. A conservation pass does not check pressure ratio, real compressor heat transfer or thermodynamic efficiency. **Reviewer:** maintainer-only, external critique pending. **Rights:** original synthetic under MIT.

---

## TH-CV-005 v0.1 — ideal two-inlet adiabatic mixer

**System/boundary:** two separately named fluid inlets join to one outlet in a steady nonreacting mixing volume; adiabatic with no shaft work. Mixture enthalpy is *assumed*, not calculated by a fluid property solver. This is not a general multi-species chemical mixing model.

**Input:** [`examples/steady_mixer_adiabatic.json`](../examples/steady_mixer_adiabatic.json), MIT-covered synthetic export.

```text
Inlet A: 2 kg/s at 100000 J/kg; inlet B: 3 kg/s at 300000 J/kg
Outlet: 5 kg/s at 220000 J/kg; Q_in = 0; W_out = 0
R_m = (2+3) - 5 = 0 kg/s
R_E = 2(100000) + 3(300000) - 5(220000) = 0 W
Mass scale = (2+3)+5 = 10 kg/s; threshold = 1e-7 kg/s
h_ref = [200000+900000+1100000]/10 = 220000 J/kg
Energy scale = 2|100000-220000| + 3|300000-220000|
             + 5|220000-220000| = 480000 W
Energy threshold = 1 W
```

**Expected:** mass and first law `PASS`. **Negative control:** outlet h becomes 219,000 J/kg; `R_E = +5000 W`, first law `FAIL`.

**Known escape / limitations:** a wrong composition, outlet phase/temperature, or thermodynamic property model can still yield a numerically balanced assumed enthalpy. No chemistry, pressure drop, actual fluid composition or mixing entropy is assessed. **Reviewer:** maintainer only; not externally reviewed.

---

## TH-CV-006 v0.1 — adiabatic equal-enthalpy splitter

**System/boundary:** one material inlet divides into two outlets; steady nonreacting flow, zero external heat and shaft-work crossings, common material and enthalpy datum. Equal branch enthalpies are an explicit synthetic assumption, not a predicted pressure/temperature field.

**Input:** [`examples/steady_splitter_adiabatic.json`](../examples/steady_splitter_adiabatic.json), author-synthetic MIT dataset.

```text
Inlet: 5 kg/s at 250000 J/kg
Outlets: 2 kg/s at 250000 J/kg + 3 kg/s at 250000 J/kg
R_m = 5 - (2+3) = 0 kg/s
R_E = 5(250000) - 2(250000) - 3(250000) = 0 W
Mass scale = 5 + 2 + 3 = 10 kg/s; threshold = 1e-7 kg/s
h_ref = [5(250000)+2(250000)+3(250000)]/10 = 250000 J/kg
Energy scale = Σ m|h-h_ref| + |Q| + |W| = 0 W
Energy threshold = 1 W (absolute software floor)
```

**Expected:** both steady checks `PASS`. **Negative control:** set branch-A outlet mass to 2.25 kg/s, keeping other terms fixed; `R_m = −0.25 kg/s` and `R_E = −62500 W`, both `FAIL`.

**Known escape:** changing branch split 2:3 to 1:4 with unchanged total mass/enthalpy conserves both equations yet violates a *particular intended split fraction*. Pressure drops, valves and branch operating constraints are not checked. **Reviewer:** maintainer only; synthetic data MIT-redistributable.

---

## TH-CV-007 v0.1 — turbine with heat loss

**System/boundary:** steady, one-inlet turbine delivering shaft work and losing heat across the chosen boundary. Heat **out** is negative under EnerLint's heat-in-positive convention. Enthalpies share a declared basis. Kinetic/potential terms and accumulation are excluded.

**Input:** [`examples/steady_turbine_heat_loss.json`](../examples/steady_turbine_heat_loss.json), synthetic MIT reference.

```text
m_in = m_out = 1.5 kg/s; h_in = 800000; h_out = 600000 J/kg
Q_in = -30000 W; W_out = +270000 W
R_m = 1.5 - 1.5 = 0 kg/s
R_E = 1.5(800000) - 1.5(600000) - 30000 - 270000 = 0 W
Mass scale = 3 kg/s; threshold = 3e-8 kg/s
h_ref = [1.5(800000) + 1.5(600000)]/3 = 700000 J/kg
Energy scale = 150000 + 150000 + 30000 + 270000 = 600000 W
Energy threshold = 1 W
```

**Expected:** mass and energy `PASS`. **Negative control:** incorrectly report `Q_in=+30000 W` at the same shaft work; `R_E=+60000 W`, first law `FAIL`.

**Known escape:** adding the same heat/power offset to both `Q_in` and `W_out` preserves the residual; therefore the result is not a heat-loss or power-measurement calibration. **Reviewer:** maintainer only; external check outstanding; synthetic MIT case.

---

## TH-CV-008 v0.1 — exchanger with external heat loss

**System/boundary:** aggregate hot+cold circuits inside one steady control volume; an additional 30 kW escapes to the environment. The heat crosses the **outer boundary** (not an internal cold/hot exchange). Separate fluid circuits are assumed individually mass-conserved with compatible property references within each circuit. No shaft crossing.

**Input:** [`examples/steady_heat_exchanger_heat_loss.json`](../examples/steady_heat_exchanger_heat_loss.json), synthetic and MIT-distributed.

```text
Cold: 2 kg/s, 100000 -> 160000 J/kg; gain = 2(160000-100000) = 120000 W
Hot:  1 kg/s, 500000 -> 350000 J/kg; loss = 1(500000-350000) = 150000 W
External Q_in = -30000 W; W_out = 0 W
R_m = (2+1) - (2+1) = 0 kg/s
R_E = [2(100000)+1(500000)]-[2(160000)+1(350000)]-30000 = 0 W
Mass scale = 6 kg/s; threshold = 6e-8 kg/s
h_ref = [200000+500000+320000+350000]/6 = 228333.333... J/kg
Energy scale = Σ_ports m|h-h_ref| + 30000 = 816666.666... W
Energy threshold = 1 W
```

**Expected:** mass and first-law `PASS`. **Negative control:** omit the *known* heat loss by reporting `Q_in=0` instead, leaving exported enthalpies intact; `R_E=+30000 W`, first law `FAIL`.

**Known escape / limitations:** if the exporter simultaneously adjusts a port enthalpy, the missing loss can be hidden. Aggregate closure does not demonstrate each circuit's operating conditions, actual heat-transfer area, pinch point or measurement accuracy. **Reviewer:** maintainer only; no external scientific review.

---

## TH-ST-002 v0.1 — discharging storage with capacity **not supplied**

**System/boundary:** a lumped, constant-rate *single* thermal energy inventory discharged over 2400 seconds, with a separate heat-loss rate and no charging. All terms use a declared fixed nonnegative energy zero. No temperature, stratification, chronology or deliverable power check is possible.

**Input:** [`examples/storage_discharge_no_capacity.json`](../examples/storage_discharge_no_capacity.json), synthetic and MIT-distributed. **`capacity_j` is intentionally absent**; absence is not the same as reporting a zero capacity.

```text
E_initial = 700000000 J; E_final = 364000000 J; dt = 2400 s
Q_charge = 0 W; Q_discharge = 120000 W; Q_loss = 20000 W
Stored-energy change = 364000000 - 700000000 = -336000000 J
Integrated charge = 0 J; discharge = 288000000 J; loss = 48000000 J
R_storage = -336000000 - (0 - 288000000 - 48000000) = 0 J
Energy scale = 336000000 + 0 + 288000000 + 48000000 = 672000000 J
Energy threshold = max(1 J, 1e-8 * 672000000 J) = 6.72 J
```

**Expected:** `storage_energy_closure = PASS`, `storage_capacity = NOT_CHECKED`, overall `PASS_IN_SCOPE`. `NOT_CHECKED` has null numerical threshold, scale and residual. **Negative control:** set `E_final=365000000 J`, retaining all rates; `R_storage=+1000000 J`, energy closure `FAIL`; capacity still `NOT_CHECKED`.

**Known escape:** any physically infeasible storage capacity/temperature/heat loss characteristic may remain invisible without those constraints; a successful energy balance is not a capacity certificate. **Reviewer:** maintainer-derived hand accounting only; not independently peer reviewed; MIT synthetic example.

---

## Change and review register

| Date | Version | Change | Reviewer |
|---|---|---|---|
| 2026-10-27 | 0.1 | First two complete worked benchmark case cards | Not independently reviewed |
| 2026-10-27 | 0.2 | Added eight independently hand-checkable case cards, ten-case frozen oracle and distinct negative controls | Maintainer self-check only; external review pending |

To review: independently recompute all ten case oracles and their scales **without consulting** `src/enerlint/verify.py`, verify the sign conventions and omitted terms, then examine the compensation and optional-capacity cases. A separate Decimal-based evaluator [recomputes these reference equations](../scripts/run_analytical_catalog.py), but it was also written by the maintainer. Its existence is not third-party validation. Record disagreement and correction as an issue rather than quietly changing the expected outcome.

**Still outstanding:** external technical examination of these ten maintainer-generated references, manufactured/independent comparison cases, at least twenty varied prespecified faults, native-solver comparisons, and blinded tests. The earlier four-case foundation ledger is intentionally preserved rather than overwritten. See [benchmark protocol](BENCHMARK_PROTOCOL.md), [external review issue #25](https://github.com/Open-Energy-Methods/enerlint/issues/25) and [expansion issue #9](https://github.com/Open-Energy-Methods/enerlint/issues/9).
