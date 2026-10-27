# Numeric tolerance and representability policy — alpha review note

**27 October 2026 · Maintainer-authored technical note. External scientific critique still needed.**

EnerLint's first-law and storage checks compare a *declared* residual against a dimensional threshold. They are output-consistency checks, not uncertainty quantification, calibration, equipment certification or evidence that a model's physical assumptions are right.

This note addresses [issue #3](https://github.com/Open-Energy-Methods/enerlint/issues/3) and records the behavior targeted by the synthetic regression matrix in [`tests/test_numerical_bounds.py`](../tests/test_numerical_bounds.py).

## 1. Residual definitions and physical scope

Steady nonreacting control volume, with explicit signed heat **into** and shaft work **out of** the boundary; kinetic/potential transport and accumulation explicitly neglected:

```text
R_m = sum(m_in) - sum(m_out)                                      [kg/s]
R_E = sum(m_in*h_in) - sum(m_out*h_out) + Q_into - W_out           [W]
```

For one storage interval with explicitly declared constant-average rates:

```text
R_S = E_final - E_initial - (Q_charge - Q_discharge - Q_loss)*dt   [J]
```

The equations alone cannot determine that the physical boundary is correct, the property data share a consistent datum, a simulation's operating point is intended, or the input is measured rather than fabricated.

## 2. Alpha numerical decision rule

Each evaluated check is **PASS** only if:

```text
abs(residual) <= max(absolute_tolerance, relative_tolerance * scale)
```

| Check | Default absolute tolerance | Default relative tolerance | Current scale |
|---|---:|---:|---|
| Steady mass | 1e−9 kg/s | 1e−8 | `|m_in| + |m_out|` |
| Steady first-law energy | 1 W | 1e−8 | `Σ m · |h − h_ref| + |Q_into| + |W_out|` |
| Interval stored energy | 1 J | 1e−8 | `|E_f−E_i| + |Q_charge·dt| + |Q_discharge·dt| + |Q_loss·dt|` |
| Declared storage capacity | 0 J | 0 | Exact endpoint bounds on declared energy |

Here `h_ref` is the stream-mass-weighted mean enthalpy calculated by the current implementation, if total declared stream mass flow is nonzero. It is **not** a verified or external material-property reference state. For a genuinely mass-balanced boundary, a *uniform* shift of all specific-enthalpy datums does not mathematically alter the energy residual, and does not inflate the intended relative scale.

The 1 W/1 J/1e−8 defaults are **software decisions**, not universally defensible engineering accuracy limits. For measured work, tolerance choice requires a separate measurement-uncertainty and instrumentation model that EnerLint does not yet implement. A residual inside a broad tolerance can pass despite a real but smaller inconsistency.

**Do not claim that this scale is universally optimal.** It is an initial way to avoid a common failure mode in which absolute stream enthalpy datums dominate the threshold even though only energy *differences* carry information.

## 3. Valid cases, adversarial cases and deliberately indeterminate cases

| Example | Intended result | Reason |
|---|---|---|
| Equal inlet/outlet mass, ideal first-law closure | `PASS_IN_SCOPE` | Declared residuals within threshold |
| Add same finite enthalpy datum to all material streams in mass-closed case | Nominally unchanged pass/fail | A uniform datum should not create a physical difference; floating-point limits still apply |
| Slight enthalpy perturbation causing 0.5 W residual | Energy `PASS` at default | 0.5 W is within the 1 W software default; **not** measurement validation |
| Perturbation causing 1.5 W residual | Energy `FAIL` at default | Explicitly outside that same threshold |
| Zero material flow, zero heat, zero shaft work | Scoped conservation `PASS` | Balanced empty-throughput model; **not** proof such equipment operation is physically admissible |
| Zero material flow with nonzero heat in, no work | First-law energy `FAIL` | No balancing exported term |
| Nonconserving mass, even if an enthalpy shift could alter the energy residual | Whole case `FAIL` | Mass closure is an independent required check |
| Missing optional storage capacity | Storage closure `PASS`, capacity `NOT_CHECKED` | The checker cannot assert a capacity it was not given |
| Missing required input / unsupported unit conventions | `ContractError` / CLI exit 2 | Must not infer zeros or unit conversions |
| Overflowing product, aggregate or tolerance despite individually finite input numbers | `ContractError` / CLI exit 2 | Cannot faithfully evaluate the claimed residual/threshold in binary64 |
| Correlated wrong flow and shaft work that preserve both balances | May pass **in scope** | An operating-point reference is outside the balance-only oracle |

These are hand-constructed classes chosen by the maintainer, not estimates of real fault prevalence, physical uncertainty, or software sensitivity/specificity.

## 4. Finite numbers can still produce unrepresentable aggregates

The input contract requires finite numeric SI values, but binary64 operations on finite numbers can produce an unrepresentable result:

- `m*h` can overflow even if `m` and `h` are finite.
- The total stream-rate scale may overflow when adding two individually finite, enormous flow rates.
- The weighted enthalpy-reference numerator may overflow while each individual mass–enthalpy product is finite.
- Integrating a finite power over a finite duration can overflow.
- The product of a finite relative tolerance and a finite residual scale may overflow.

EnerLint now catches nonrepresentable `math.fsum` aggregates and reports a `ContractError`, rather than exposing an unhandled Python `OverflowError`. The CLI maps a `ContractError` to **`INVALID_INPUT`, exit code 2**. This is conservative software behavior, not a finding that the physical process violates conservation.

**Important remaining limitation:** overflow checks do **not** prove numerical conditioning. A difference much smaller than the input's floating-point unit-in-the-last-place can be lost during JSON→float conversion, mass×enthalpy multiplication, reference construction or subtraction. `math.fsum` improves addition accuracy but cannot recover bits already lost in products or input representation. Extremely large common enthalpy datums and near-equal thermodynamic states may therefore be *indeterminate without higher-precision or reformulated reference calculations*. Such indeterminacy is **not automatically detected** by the current alpha. A future research task should quantify the conditioning and fail closed when a specified accuracy requirement cannot be met.

## 5. False alarms, missed faults and validation boundary

Tests should present independently specified, known-valid and known-invalid reference cases together, preserving their correlation by case family. `FAIL` means an exported set of numbers violates a *specified check*, not necessarily that the physical simulation is bad: the declared boundary, signs or unit references might be mistaken.

Tests of the same code with independently hand-entered expected values are developer regression tests, not an outside adjudication. Do not report false-alarm rates or scientific detection probabilities from the selected synthetic examples alone. The full false-positive, false-negative and abstention experiment remains a separate project task.

## 6. External critique request — still open

A reviewer should independently assess:

1. Whether these residual scales are physically and numerically defensible for varied thermal component boundaries.
2. How small/zero-flow cases should be labeled when property state validity is out of scope.
3. Whether the first-law residual should be reformulated using centered enthalpies plus explicit mass-imbalance compensation to improve conditioning.
4. How to detect when the inputs' numerical precision is too coarse to test the desired residual.
5. Which tolerances follow justified measurement uncertainty and which are merely convenient software defaults.
6. Whether a configured native solver already captures the relevant failure class.

The maintainer must record criticism, null outcomes and any revised formula/tolerance under a versioned change, with prior results preserved.

**Status:** software edge-case handling improved; tolerance science and external review **not completed**.
