# Scientific independence and limitations

## What the implementation independently reconstructs

- Mass flow rate in/out of a *declared steady control volume*.
- Energy transport using separately exported mass-flow and specific enthalpy.
- The heat/shaft-work contribution specified with explicit direction.
- Energy accumulated by a storage interval from exported states and time-average
  heat rates (not a simulated thermal-field history).
- Optional physical capacity bounds for stored energy.

The checker does not reuse the upstream solver's computed balance residual or
convergence flag. It *may*, however, ingest the same modeled data and boundary
assumptions, and hence shares potential systematic errors at that level.
Independent physical validation requires independent evidence beyond this tool.

## Boundaries of the evidence

| A passing test can support | A passing test cannot establish |
|---|---|
| Given SI states close the stated mass/energy equation | Sensor calibration or upstream measurement truth |
| Given stored energy is consistent across one averaged interval | Correct PCM/thermocline dynamics or deliverable process heat |
| Declared output obeys a mass/energy equality to a tolerance | Correct control-volume selection or modeling assumptions |
| A deliberate mutation trips a named residual | Sensitivity to all real-world engineering mistakes |
| Report corresponds to a SHA-256-bound JSON object | Source provenance authenticity or independent study replication |

## Independence hierarchy (suggested for future research)

0. **Internal solver success**: solver completed/converged; no independent test.
1. **External residual check**: physically derived residual independently
   implemented, but uses exported data and declared boundary (v0.1).
2. **Independent reference**: results compared with separate trusted analytical
   or published benchmark and uncertainty envelope (not yet done externally).
3. **Independent implementation**: compare distinct implementations and solver
   formulations (not yet done).
4. **Empirical validation**: independent measurements with traceable instruments,
   uncertainties and a documented validation protocol (not yet done).

These are descriptive evidence categories, not externally certified levels.

## Explicit exclusions

- Safety certification, design verification or regulatory compliance.
- Reactive thermodynamics, kinetic/potential transport effects, two-phase flow
  model validation, chemical/electrical energy without declared adaptations.
- Thermophysical property packages or independent state validity checks.
- Real-time online fault detection, SCADA, power-plant control.
- AC power-flow, relay/protection, frequency and transient stability.
- Finite-element, CFD or neutron-transport discretization verification.
- Claims about real industrial, grid, or nuclear-system performance.

These may become later, separately reviewed work packages; they must not be
implied from the initial tests.
