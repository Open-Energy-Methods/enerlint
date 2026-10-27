# First-law tolerance and numerical conditioning — internal technical review

**27 October 2026 · EnerLint #3 · maintainer-led critical review · NOT an independent external scientific critique**

**Decision:** the frozen `check_case` v0.1.0 input/report format and initial tolerances have **not been silently changed**. Two constructed counterexamples demonstrate that, at large enthalpy datums, binary64 decisions can disagree with the algebra implied by decimal source JSON. Therefore **unqualified confidence in large-datum first-law PASS/FAIL is not justified**. The separate optional precision audit helps characterize—not universally correct or bound—these discrepancies.

## 1. Recomputed equations and dimensions

| Quantity | Declared residual | Default abs. | Default relative | Scale |
|---|---|---:|---:|---|
| Steady mass (kg/s) | `sum(m_in)-sum(m_out)` | `1e-9 kg/s` | `1e-8` | `m_in + m_out` |
| Steady energy (W) | `sum(m*h)_in - sum(m*h)_out + Q_in - W_out` | `1 W` | `1e-8` | `sum(m*abs(h-h_ref)) + abs(Q) + abs(W)` |
| Storage energy (J) | `E_f-E_i -(Q_charge-Q_discharge-Q_loss)*dt` | `1 J` | `1e-8` | `abs(ΔE)+sum(abs(Q_i*dt))` |
| Storage capacity (J) | positive endpoint excursion outside declared capacity | `0 J` | `0` | `0` |

The threshold is `max(abs_tolerance, relative_tolerance*scale)`; equality is a *pass*. A passing result can have a nonzero residual, and these defaults are **not** metrological uncertainty or calibrated acceptance criteria. `h_ref` is a computed mass-weighted center, *not* a verified thermodynamic property reference. Equalities above use the declared sign convention; they do not prove physical boundary completeness.

## 2. Two counterexamples to naive reliance on the current decision

The frozen [ten-case precision stress source](tolerance_precision_cases_v0.1.json) contains raw decimal-number edits to the original synthetic compressor (2 kg/s, Δh=120,000 J/kg, work input 240,000 W). The stress tool avoids converting altered literals into binary64 *before* writing the candidate JSON.

| Source case | Exact arithmetic on written decimal JSON | Binary64 core | What it shows |
|---|---|---|---|
| `TP-003`: h_in=1,000,000,000,000,300,000; h_out=1,000,000,000,000,420,000 J/kg | `R_E=0 W`, **PASS** | `R_E=+128 W`, **FAIL** | A large common datum shift makes a balanced declared case appear wrong due to lost digits |
| `TP-004`: h_in=10,000,000,000,300,000; h_out=10,000,000,000,420,001 J/kg | `R_E=−2 W`, **FAIL** at 1 W floor | `R_E=0 W`, **PASS** | An outlet +1 J/kg (2 W energy impact) is lost in binary64 conversion |

The precise **experimental interpretation** is disagreement with a maintained *decimal-text arithmetic reference*, **not** observed false alarm/negative rates on real energy systems. At these magnitudes the binary64 unit-in-last-place is comparable to or larger than the imposed difference, and the core's upstream `m*h` products are already rounded before `math.fsum` sees them.

Other registered stress cases include normal and 1e12 J/kg reference shifts, a mass-imbalance example, a zero-flow case, a constant-rate storage case, a representability rejection, a 0.5 W residual passing inside the 1 W floor and a 1.5 W residual failing outside it. The deliberately constructed first-law failures and indeterminate high-datum cases remain visible regardless of CI success.

## 3. Reference shifts require mass closure and property compatibility

For a **single compatible material datum** `h'=h+C`, the exact energy residual changes by `C*(sum(m_in)-sum(m_out))`. Thus the energy residual is shift-invariant **only** under exact mass closure. A declared 1e-8-relative mass tolerance may admit an actual small nonzero mass residual, and a very large C can then dominate energy arithmetic. Different fluids, compositions or independently mass-unbalanced circuits cannot freely share or mix reference zeros. The [optional property sidecar](PROPERTY_DATA_ACCEPTANCE.md) checks **author declarations**, not actual backend settings or chemical thermodynamics.

The software should never treat a balanced numerical residual alone as proof of a suitable property-data basis. A centered reformulation may reduce loss of digits on some cases, but one must preserve the explicit correction for mass imbalance. An unqualified blanket replacement of the first-law formula by `sum(m*(h-h_ref))` **changes the mathematics** when mass is not exactly closed; simply switching formulas without a versioned contract and reference suite would be scientifically irresponsible.

## 4. What the optional precision preflight does

Run on a JSON case retaining original decimal literals:

```shell
python scripts/audit_numeric_conditioning.py examples/steady_compressor.json
python scripts/audit_numeric_conditioning.py my-model-export.json --output review.json
```

The [standalone auditor](../scripts/audit_numeric_conditioning.py) separately recomputes equations with Python `decimal.Decimal`, preserving literal JSON decimal values. It also evaluates the *exact arithmetic* of the inputs rounded to binary64 via `Decimal.from_float`. These are compared to `check_case`'s actual binary64 residuals.

**Diagnostic classification:**

- `DECIMAL_BINARY_AGREEMENT`: core and decimal status agree, no residual gap above the review heuristic.
- `PRECISION_CAUTION`: decisions agree but input-rounding or arithmetic residual discrepancy exceeds the **advisory 25% of decimal threshold** trigger (minimum 1e-18 in that check's units).
- `DECISION_DISAGREEMENT`: a checked result differs from exact arithmetic on the input's *decimal text*. **Stop and investigate**; do not rely on the raw PASS/FAIL.
- `CORE_REJECTED`: core input cannot be evaluated; no physical PASS/FAIL is claimed. For this standalone auditor the optional CLI returns nonzero for rejection/disagreement, **without changing EnerLint's frozen check CLI contract**.

The 25% trigger is **an arbitrary review heuristic** to surface risk, not a forward-error theorem, instrument calibration or statistically validated precision limit. `DECIMAL_BINARY_AGREEMENT` is also **not a numerical accuracy guarantee**; agreement of two calculations is insufficient to prove high conditioning or physical correctness. The independent-of-checker numerical implementation is still **maintainer written**. This is an optional *advisory*, not a new core schema field or automatic conversion of `PASS_IN_SCOPE` to `NOT_CHECKED`.

## 5. Acceptance, abstention and false-alarm discipline

- **PASS / FAIL:** when the strict input contract is representable in binary64, the existing core uses the configured residual threshold. Do not interpret PASS as exact equality or model validation.
- **NOT_CHECKED:** storage capacity only if the optional `capacity_j` is missing; residual, scale and threshold are null. The current schema does not support inserting an extra numerical-uncertainty `NOT_CHECKED` check.
- **INVALID_INPUT / ContractError:** missing/unsupported fields, nonfinite values, impossible contract values, nonrepresentable products, aggregate scales and thresholds. Do not silently convert rejected input to a failing physical balance.
- **Advisory disagreement:** if the new optional preflight flags disagreement, the source must be re-exported with a defensible reference precision, or the audit must be repeated with a reviewed numerical formulation. Do not relabel a bad numerical decision as physically validated.

The maintainers' **ten** selected stress cases include exactly **two** source-decimal versus binary64 classification disagreements and **one** explicit representability rejection. This count is *not* a real-world false-alarm rate, false-negative rate or sensitivity estimate. Tests of deliberately constructed examples do not replace independent blind/reference data or an instrument uncertainty budget.

## 6. Alternatives requiring technical review (not silently implemented)

1. A **centered enthalpy residual with mass-imbalance correction** can reduce cancellation without changing exact algebra. The numerical location of the center and how it is computed is itself prone to overflow and rounding; define the algorithm and compare to an independently specified oracle before adoption.
2. A **compensated product/summation** or decimal-path evaluation could reduce rounding errors but might cost performance or create multiple semantics. It does not restore precision never supplied by the simulator.
3. A **condition-number/interval-arithmetic bound** for declared input precision could support automatic abstention. Such a bound requires knowing whether JSON digits actually reflect upstream solver accuracy and a robust error model. No such bound is established here.
4. **Measurement-informed tolerances** should depend on instrument uncertainty, solver discretization, data-export precision, mass and energy flux scale, plant duty and intended context of use. This cannot be inferred from the 1 W / 1 J / 1e-8 software defaults alone.
5. **Nonzero but tolerated mass residuals** must be treated carefully: even a datum shift can produce a materially different first-law residual via `C*R_m`. A passing mass check does not imply mathematical mass equality.

## 7. External sources and review distinction

- [Python `math.fsum` documentation](https://docs.python.org/3/library/math.html#math.fsum) describes the accuracy of summing already-rounded operands. Summation alone cannot undo input or multiplication rounding.
- [Python floating-point representation tutorial](https://docs.python.org/3/tutorial/floatingpoint.html) explains binary representation and why arithmetic comparisons may depart from intended decimal values.
- [NIST publication on computational V&V](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=150040) distinguishes software/code verification from model/solution verification and validation.

These documents support the *general numerical-methodological concerns*. The two example residuals are **project-derived software findings**, not results reported by Python or NIST.

## 8. External reviewer handoff — NOT COMPLETED

**Independent review remains mandatory for the acceptance criteria of [issue #3](https://github.com/Open-Energy-Methods/enerlint/issues/3).** A maintainer's second implementation, an LLM critique, or green CI cannot be represented as a qualified independent technical reviewer.

Ask a numerical-analysis or thermodynamics researcher outside the development team to review the linked source, this audit, the 10 raw JSON stress cases, the numerical-policy defaults and the 39-case negative-control catalogue. Specifically request a dated signed assessment of: first-law centering and datum-shift invariance under mass imbalance; numeric conditioning; high-datum false alarms and missed differences; choice of dimensional and relative thresholds; zero-flow semantics; exact inclusivity; arbitrary-versus-calibrated tolerance policy; when automatic abstention is warranted; and coverage gaps.

Record reviewer affiliation/independence, any conflicts, concrete counterexamples, written critique and resolution in [issue #3](https://github.com/Open-Energy-Methods/enerlint/issues/3), and link a versioned follow-up. **No such reviewer assessment is documented now; #3 must remain open / In Review.**

See [numeric tolerance policy](NUMERICAL_TOLERANCE_POLICY.md), [manufactured stress references](MANUFACTURED_LIMITS.md), [release NO-GO record](RELEASE_READINESS_2026-10-27.md), and [external review tracking #25](https://github.com/Open-Energy-Methods/enerlint/issues/25).
