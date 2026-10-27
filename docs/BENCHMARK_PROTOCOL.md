# Initial benchmark and negative-control protocol

**Study type:** predeclared *software test* experiment, not empirical
model validation. All bundled inputs are synthetic hand-constructed cases.

## Primary question

Does the verifier (a) pass known closed SI cases, (b) flag a specified set of
independently introduced balance faults, (c) reject incomplete/ambiguous input,
and (d) preserve expected metamorphic invariances?

## Baseline cases (analytically checked)

1. Adiabatic steady compressor, 2 kg/s, 300 -> 420 kJ/kg,
   W_out=-240 kW: zero mass/energy residual.
2. Adiabatic steady turbine, 2 kg/s, 700 -> 500 kJ/kg,
   W_out=+400 kW: zero mass/energy residual.
3. Adiabatic two-stream heat exchanger: cold +100 kW, hot -100 kW,
   zero overall mass/energy residual.
4. One-hour thermal store: +120 kW charge, -50 kW discharge,
   -10 kW loss: energy increases by 216 MJ, within 3 GJ capacity.

## Registered corruptions and expected detection

| Mutation | Expected behavior |
|---|---|
| Outlet mass flow scaled without compensating other crossings | Mass and energy FAIL |
| Outlet specific enthalpy scaled alone | Energy FAIL |
| Nonzero compressor shaft-work sign inverted | Energy FAIL |
| Nonzero turbine heat-crossing sign inverted | Energy FAIL |
| Final stored energy increased without matching flow | Storage closure FAIL |
| Time duration altered without matching state changes | Storage closure FAIL |
| Required work removed from JSON | INVALID_INPUT |
| Wrong enthalpy field (`kJ/kg` label) | INVALID_INPUT |
| Required steady-state assumption false/missing | INVALID_INPUT |
| NaN, infinity, bool in numerical field | INVALID_INPUT |

The current tests implement these but have not been independently peer reviewed.
The fault injected has an expected outcome by construction; this cannot be
interpreted as predictive accuracy on unknown simulator faults.

## Metamorphic invariances (valid transformations)

- Reordering streams changes neither mass nor energy residual.
- Adding one common specific-enthalpy datum shift to all streams does not
  change the energy residual **if mass conservation holds**.
- Declared heat input and corresponding shaft work change can preserve the
  same energy balance (case remains valid).

## Known undetectable error

Scale all compressor mass flows and its shaft work by the same factor while
keeping enthalpy endpoints fixed: conservation remains satisfied. This is a
**test that EnerLint must not pretend to detect**. Detection without a
separate operating-point or equipment map reference would be a false claim.

## Expansion gate (not yet achieved)

- Minimum 10 independently documented reference problems.
- Minimum 20 diverse and prespecified fault cases with expected outcomes.
- At least 2 independently implemented modeling tools.
- At least 1 reviewer outside the package author to evaluate the cases.
- Measure fault-detection rate and false-positive rate on separate case families.
- Frozen numerical tolerances before holding-out benchmark execution.
- Publish failures and known escapes alongside successful detections.

A peer-reviewed publication or institutionally adopted tool requires much more
than these initial thresholds, which are targets rather than evidence of quality.
