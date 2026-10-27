# Property-data and enthalpy-reference acceptance — v0.1 alpha

**27 October 2026 · OEM / EnerLint #15 · author-derived technical policy, not external scientific review**

EnerLint v0.1 does **not** calculate density, enthalpy, mixture composition, pressure-temperature states, phase changes or saturation properties. It only reconstructs conservation checks using **numbers exported by someone else**. A successful residual cannot establish that those exported properties are comparable, physically admissible or accurate.

The [standalone optional property-reference reviewer](../scripts/review_property_references.py) is a *metadata consistency preflight*, not a thermophysical property engine. It changes **neither** the frozen strict input JSON (`schema_version=0.1.0`) nor the versioned verification report. Existing `enerlint check` remains usable **without** it and can still return `PASS_IN_SCOPE` for a case whose enthalpy datums are unknowably inconsistent.

## 1. Why absolute enthalpy needs a reference basis

For a steady nonreacting control volume (kinetic/potential changes neglected), the energy residual is

```text
R_E = Σ_in m_dot*h - Σ_out m_dot*h + Q_in - W_out
```

Specific enthalpy is defined **relative to a reference state**. Software and property tables may choose different reference values. The official [CoolProp High-Level Interface reference-state documentation](https://coolprop.org/coolprop/HighLevelAPI.html#reference-states) describes configurable reference states; [NIST REFPROP documentation](https://pages.nist.gov/REFPROP-docs/) explains why absolute enthalpy values from different tools cannot be assumed equal. These sources motivate the acceptance rule; **they are not assertions of interoperability** between their property predictions.

If the *same* constant enthalpy offset `C` applies to every inlet/outlet stream in a single consistently referenced, **exactly mass-balanced** material circuit, then

```text
R'_E = R_E + C*(Σ_in m_dot - Σ_out m_dot) = R_E
```

For several independently mass-balanced circuits, each circuit may have its *own* constant offset `C_j`:

```text
R'_E = R_E + Σ_j C_j * R_mass,j
```

This is why an **aggregate heat-exchanger boundary** can consistently combine independent cold/hot circuits, even if their raw enthalpy zeros differ, **provided every circuit is separately conserved and the sources use an internally consistent fluid/composition reference**. It is not permission to mix unrelated property values within a mass-exchanging stream.

If any per-circuit mass residual is nonzero, a reference change can alter the energy residual; when the offset is large, even a small near-tolerance mass error can significantly alter energy accounting. **The sidecar's per-circuit mass-tolerance check is a screening rule, not a proof of reference invariance.** When the required quantitative accuracy depends on this term, the modeller must bound `|C_j * R_mass,j|` or use a single fully compatible basis.

For reacting/mixing streams with species changes, chemical reference energies and mixture composition must be treated explicitly; such general checks are **outside EnerLint v0.1**.

## 2. Accepted, rejected and indeterminate sources

| Case | Decision for the **optional property review** | Reason |
|---|---|---|
| One working-fluid circuit; all stream records declare the same fluid ID, fixed composition ID, backend/version and enthalpy reference ID | **Declaration complete** | Consistent *claims* about one reference basis; no external property authentication |
| Aggregate heat exchanger; separately mass-balanced hot/cold loops have different reference state IDs and fluid identities, constant *within* each loop | **Declaration complete** | No cross-loop mass exchange; separate constant zeros cancel if each loop is **exactly** mass-balanced |
| Same material circuit with outlet reference `ASHRAE` and inlet `DEF` | **Reject / abstain** | Different reference zeros can introduce a spurious enthalpy difference |
| Same circuit mixing CoolProp/REFPROP outputs without an explicitly audited transformation | **Reject / abstain** | Matching numerical units are not a common datum or a common equation of state |
| Missing/blank fluid, composition, backend ID/version, reference ID, or missing inlet/outlet metadata | **Reject / abstain** | Cannot document the comparison basis |
| Grouped streams with globally balanced mass but one fluid circuit has net mass imbalance | **Reject / abstain** | Arbitrary independent reference shifts would not cancel on that circuit |
| Provenance says a fluid or source is `experimental` | **No extra trust** | Declarations and hashes do not authenticate a property or instrument |
| One reporter says temperatures/pressures fall in property-model range | **Not checked** | The v0.1 checker does not ingest or validate thermodynamic states |
| Different fluids chemically reacting, mixing with composition changes, or transferring material across declared circuits | **Out of scope / abstain** | Nonreacting enthalpy-only accounting is insufficient for a general chemical-species energy balance |
| A source/backend is unknown but numbers happen to close | **No property conclusion** | Conservation checks can pass with incompatible zeros or compensated errors |

### What needs a genuine external property source?

A claim that an enthalpy matches a particular pressure/temperature/phase requires a separate, rights-cleared, versioned, independently specified property reference and a comparison **with uncertainty/validity limits**. Potential future sources could include CoolProp, the NIST REFPROP package or IAPWS formulations where applicable. The current code has **no runtime dependency on any of them**, does not embed their tables and does not validate their licensed data. Do not call a synthetic `manual_synthetic_reference` label a trusted thermophysical backend.

For a real-model export, record fluid and composition definitions (e.g. mixtures and fractions), actual backend implementation and version, stated reference state **and any changed reference-state settings**, exported SI units, and the originating case/data rights. In CoolProp, reference-state changes should be controlled during program initialization; its docs warn against changing them mid-calculation. Preserve the original project settings or a reproducible export script, not merely a convenient descriptor in JSON.

## 3. Worked synthetic examples

### Example A — same reference used consistently

From [`steady_compressor.json`](../examples/steady_compressor.json), one inlet and outlet share a declared manual synthetic working-fluid reference, with 2 kg/s and 300,000 → 420,000 J/kg. With 240 kW shaft work **into** the control volume:

```text
R_mass = 2 - 2 = 0 kg/s
R_E    = 2*300000 - 2*420000 - (-240000) = 0 W
```

A uniform addition of +1,000,000 J/kg to **both** stream enthalpies still gives zero energy residual. This checks mathematical gauge invariance for an exactly mass-balanced circuit; it does not validate a physical fluid. [Declaration example](../examples/steady_compressor.property-review.json).

### Example B — separate heat-exchanger circuits

From [`steady_heat_exchanger.json`](../examples/steady_heat_exchanger.json): cold loop 1 kg/s, 100,000 → 200,000 J/kg; hot loop 2 kg/s, 500,000 → 450,000 J/kg. Both circuits separately conserve mass.

```text
R_E = (1*100000 + 2*500000) - (1*200000 + 2*450000) = 0 W
```

A +1,000,000 J/kg *common shift within cold loop only*, and a −200,000 J/kg shift *within hot loop only*, do not change the aggregate residual in exact arithmetic. The property review allows distinct reference IDs for separate mass-closed loops, not for individual ends of the same loop. [Declaration example](../examples/steady_heat_exchanger.property-review.json).

### Example C — **false pass** with incompatible zero and compensated work

Start with the compressor (original outlet 420,000 J/kg, work out −240,000 W). Apply an **invented, inconsistent** +100,000 J/kg offset to the *outlet alone*; also alter the declared shaft work to −440,000 W:

```text
R_mass = 2 - 2 = 0 kg/s
R_E = 2*300000 - 2*520000 - (-440000) = 0 W
```

The original `enerlint check` returns **`PASS_IN_SCOPE`**, because the given numbers close. The optional property review flags mismatched `reference_state_id` values and returns **`PROPERTY_REVIEW_INCOMPLETE` / exit 2**. That is a synthetic metadata conflict, *not* experimental detection of the true reference state. [Input](../examples/steady_mismatched_reference_compensated.json) · [declaration](../examples/steady_mismatched_reference_compensated.property-review.json).

### Example D — aggregate mass closes, separate circuits do not

Consider the exchanger's original streams, except cold outlet mass becomes 0.9 kg/s and hot outlet becomes 2.1 kg/s. Aggregate mass still closes at 3 kg/s in/3 kg/s out, but cold loop has +0.1 kg/s mass residual and hot loop has −0.1 kg/s. Independent arbitrary offsets would change aggregate energy residual.

The sidecar rejects non-conserved **per-circuit** group declarations even when the aggregate `steady_mass_closure` check passes.

## 4. Optional sidecar review and exact contract

The [preflight script](../scripts/review_property_references.py) consumes the unchanged strict v0.1 case plus a separate declaration file:

```bash
python -m pip install -e ".[dev]"
python scripts/review_property_references.py \
    examples/steady_compressor.json \
    examples/steady_compressor.property-review.json

python scripts/review_property_references.py \
    examples/steady_heat_exchanger.json \
    examples/steady_heat_exchanger.property-review.json
```

Each declaration must contain `review_version=0.1.0`, `case_id`, canonical `input_sha256`, nonempty `author` and `basis_note`, and a `stream_properties` list containing **exactly one record per** `(direction, name)` case port. A record requires:

```json
{
  "direction": "inlet",
  "name": "inlet",
  "circuit_id": "working_fluid",
  "fluid_id": "declared_species",
  "composition_id": "fixed_composition_or_pure",
  "backend_id": "manual_or_property_backend",
  "backend_version": "specific_version",
  "reference_state_id": "documented_reference_setting",
  "source_note": "source and property calculation description"
}
```

The preflight verifies: strict record shape; **full port coverage**; no duplicate/unknown names; exact basis-string agreement *within each circuit*; nonempty inlet/outlet sets per circuit; group mass closure within the initial default mass tolerance; matching case ID and input hash. A mismatch/unknown declaration fails closed as a metadata error.

**Return labels:** `PROPERTY_DECLARATION_COMPLETE` with the separate underlying balance-check status means the author has supplied internally consistent metadata, **not property verification**. A failed preflight emits `PROPERTY_REVIEW_INCOMPLETE` and exits 2. Both are different from `enerlint check` statuses. Neither creates external verification evidence.

This tool cannot detect a dishonest but internally consistent declaration, incorrect fluid composition, backend defects, inconsistent physical heat/work measurements, or a near-mass-balanced circuit with consequential large reference offsets. It also does **not** compare the exported enthalpy values with actual backend calculations. To assess those, retain source data and do a separately reviewed property-model comparison; do not automatically promote the sidecar result to the report schema.

## 5. Compatibility and reviewer status

- No changes to input keys, strict schema version, main `check_case`, report `schema_version=0.1.0`, or the runtime dependency set.
- The new metadata gate is *optional* and can be omitted; therefore no claim that EnerLint automatically detects incompatible property references is permitted.
- Developer-authored synthetic fixtures and adversarial tests are not independent benchmarking or measured validation.
- A future adapter could optionally **require** an explicit property provenance artifact, after a versioned input/adapter design and comparative study; that decision must be a separate release gate.
- Independently evaluate the scope with [issue #25](https://github.com/Open-Energy-Methods/enerlint/issues/25). Numerical conditioning remains [issue #3](https://github.com/Open-Energy-Methods/enerlint/issues/3); false alarm/detection rates remain unsupported.

**Permitted public statement:** “EnerLint documents an optional author-attested property-reference consistency preflight for declared steady control-volume streams.” **Not permitted:** “EnerLint validates real fluid properties, authenticates thermodynamic reference states, or supports arbitrary mixing and chemical reactions.”
