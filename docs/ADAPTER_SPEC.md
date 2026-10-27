# Adapters — design contract (NOT IMPLEMENTED)

An adapter for an upstream tool must convert model outputs into **explicit
EnerLint case JSON** without importing upstream solver residuals or convergence
flags as evidence of passing an independent physical check.

Required adapter responsibilities:

1. Identify physical model and software version, solver settings, numerical
   units, and data source. Include artifact digests when possible.
2. Require an explicit boundary selector. For example, a compressor's suction
   and discharge, shaft coupling, and any heat leakage must all be represented.
3. Convert units with a separately tested conversion path. Do not infer units
   from magnitude or variable names outside the adapter's documented schema.
4. Reject or mark data insufficient if any required model output is missing.
5. Use reproducible mapping metadata for signs and flow directions.
6. Declare assumptions such as steady state and neglected kinetic/potential
   terms. Do not silently assert assumptions not present in the source model.
7. Record provenance: upstream project, exact source files/artifacts/hashes,
   declared original versus synthetic evidence class.
8. Call only the public `enerlint.check_case` API, and report any exclusions.

Candidate integrations **only**: ThermoTwin-F, OpenSteamOpt, TESPy/CoolProp,
PyPSA, pandapower, Modelica FMUs, and generic CSV exports. No adapter is
currently implemented or tested. Integration must respect source licensing.
