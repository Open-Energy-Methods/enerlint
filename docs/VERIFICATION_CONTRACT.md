# v0.1 verification contract

## Formal scope

EnerLint evaluates supplied **model outputs** under a declared and strictly
bounded conservation equation. It does **not** call the originating solver or
reproduce the originating optimization model. The declarer must supply all
cross-boundary mass, heat and shaft-work terms consistent with the boundary.

Data contract: UTF-8 JSON, `schema_version = "0.1.0"`; strict SI keys.
Unknown fields or missing required fields cause `ContractError` and CLI exit 2.
A unit is conveyed by the field name rather than guessed from numeric magnitude.
No conversion between kJ/kg and J/kg occurs silently.

### Provenance declaration

All case types require:

```
"provenance": {
  "evidence_class": "hand_constructed | model_export | experimental | published_reference",
  "declared_source": "a nonempty description of where the values originated"
}
```

This is an author declaration, not evidence authentication. A false declaration
cannot be detected from the JSON alone. An SHA-256 binds each report to the
canonical JSON object (sorted keys; compact separators); it does **not** prove
that the JSON reflects original instrumentation or a repository's run artifacts.

The companion [control-volume boundary review](CONTROL_VOLUME_BOUNDARY_REVIEW.md)
shows port diagrams, signed heat/work examples, a hypothetical leak counterexample,
and an **optional** author-attested preflight. It is deliberately separate from
the unchanged strict `0.1.0` case and report schemas: completing the preflight
cannot prove all actual physical crossings have been found.

## Steady control-volume mass balance

`mass_in - mass_out = 0`, both streams oriented using separate `inlets` and
`outlets` arrays. Flows must be finite nonnegative kg/s, and each stream has an
explicit name and `specific_enthalpy_j_kg`.

## Steady control-volume first law

```
  R_E [W] = sum(inlet mdot*h) - sum(outlet mdot*h)
          + heat_into_volume_w - shaft_work_out_w
```

This form neglects kinetic/potential flow energy. Both `steady_state: true` and
`neglect_kinetic_potential: true` **must be explicitly declared**. No hidden
mass accumulation, leakage, chemical reaction, phase/mixing energy or omitted
auxiliaries should cross the specified boundary. The equation is a restricted
steady, non-reacting flow-model check.

Sign convention: `heat_into_volume_w` > 0 INTO the boundary; positive
`shaft_work_out_w` leaves the boundary. Compressor power entering the system
has negative sign; turbine output is positive. Set physical zero quantities to
an explicit JSON number `0.0`—never omit them.

### Examples by hand

**Compressor:** 2 kg/s, 300 kJ/kg inlet to 420 kJ/kg outlet; `Q_into=0`,
`W_out=-240000 W` gives:

```
2*300000 - 2*420000 + 0 - (-240000) = 0 W
```

**Two-stream heat exchanger:** Cold: 1 kg/s from 100 to 200 kJ/kg; hot:
2 kg/s from 500 to 450 kJ/kg; aggregate boundary adiabatic with no shaft work:

```
(1*100000 + 2*500000) - (1*200000 + 2*450000) = 0 W
```

**Turbine:** 2 kg/s, 700 to 500 kJ/kg; shaft output 400000 W:

```
2*700000 - 2*500000 - 400000 = 0 W
```

These examples are hand-constructed tests, not empirical calibration.

## Thermal storage single-interval energy

```
R_storage [J] = E_final - E_initial
                 - (Q_charge - Q_discharge - Q_loss)*duration_s
```

An explicit `"assumptions": {"constant_interval_rates": true}` is required.
All rates are **constant interval averages** in watts, duration is >0 seconds,
and initial/final stored energies are >=0 joules relative to the declared zero
reference. Heat charge/discharge/loss input magnitudes are >=0. If `capacity_j`
is supplied, the initial/final energy values are constrained within [0,capacity].
Otherwise capacity is explicitly `NOT_CHECKED`.

This **does not** compute heat transfer as a function of temperature or state
of charge. A capacity check may pass despite a physically impossible thermal
outlet temperature.

## Tolerances

Residual `R` passes when:

```
    abs(R) <= max(abs_tolerance, relative_tolerance * scale)
```

- Steady mass: default abs 1e-9 kg/s; relative 1e-8.
- Steady energy: default abs 1 W; relative 1e-8.
- Storage energy: default abs 1 J; relative 1e-8.
- Capacity bounds: exact (0 J tolerance) for declared energy range.

Mass scale: `abs(m_in) + abs(m_out)`.
Energy scale: sum of absolute `m_dot * (h - h_ref)` for all in/out streams,
plus |Q| + |W|, where `h_ref` is the mass-weighted mean of all inlet/outlet
specific enthalpies (zero if all flows are zero). For a mass-balanced boundary,
this tolerance scale is invariant under a **common** enthalpy datum shift;
independently chosen material/species reference states are not addressed.
Storage scale: |delta E| plus magnitudes of integrated heat flows. Threshold
and scale are included in report.

Numerical aggregation is performed with `math.fsum` where applicable. A finite
individual input may still produce an unrepresentable product, aggregate, or
threshold in binary64; EnerLint raises `ContractError` (CLI exit 2)
rather than treating such a result as a scientific pass. This does **not**
eliminate loss of precision in input conversion, multiplication, or severe
cancellation. See the [numeric tolerance and conditioning review
note](NUMERICAL_TOLERANCE_POLICY.md), including deliberately valid, invalid,
undetectable and numerically indeterminate cases.

**These thresholds are software defaults, not accuracy requirements or
engineering standards.** Domain-specific tolerances must be justified by
measurement uncertainty, solver precision and research purpose, and supplied
through the case. Zero tolerances are allowed but rarely appropriate in
floating-point analysis.

## No blanket validity conclusion

`PASS_IN_SCOPE` means all present, applicable implemented checks passed, not
that all desirable checks were available. For example, missing `capacity_j`
produces a `NOT_CHECKED` check without preventing a scoped energy pass.

Compensating errors may preserve balances. If all mass flows and shaft work are
scaled by the same factor, a compressor can still satisfy both equations despite
its modeled operating point being wrong. Phase consistency and input truth
remain unverified.
