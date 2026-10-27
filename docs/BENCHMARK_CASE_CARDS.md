# EnerLint benchmark case cards — version 0.1

**Status:** first two complete **author-derived** cards, 27 October 2026. These are *not* independently reviewed, not empirical measurements, and not assertions of originality of conservation laws.

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

## Change and review register

| Date | Version | Change | Reviewer |
|---|---|---|---|
| 2026-10-27 | 0.1 | First two complete worked benchmark case cards | Not independently reviewed |

To review: recompute all four residuals and their scales **without consulting** `src/enerlint/verify.py`, verify the sign conventions and omitted terms, then examine the compensation case. Record disagreement and correction as an issue rather than quietly changing the expected outcome.

**Next cases are *targets*, not achievements:** ten analytical reference cases across compressors, turbines, mixers, splitters, exchangers and storage; manufactured cases; and blinded fault tests. See [benchmark protocol](BENCHMARK_PROTOCOL.md) and [the work tracker](https://github.com/Open-Energy-Methods/enerlint/issues/17).
