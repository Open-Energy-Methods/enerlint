# EnerLint

**Independent, scope-limited physical consistency checks for energy-engineering outputs.**

> **Development status:** early alpha foundation. Initial analytical and fault-injection examples are synthetic or hand-derived. The package has not been externally validated or qualified for operational control, certification, procurement, or safety-critical work.

EnerLint is the first project of [Open Energy Methods](https://github.com/Open-Energy-Methods). Its purpose is to independently reconstruct selected conservation equations from exported data rather than trust a solver's own convergence flag. Passing a conservation check **does not validate a model's physics or establish a scientific conclusion**.

The proposed early modules cover steady mass and energy balance, one-interval storage accounting, explicit SI and sign contracts, fault injection and machine-readable reports.

The source code, benchmark ledger, tests and release documentation are being staged for initial review; this repository bootstrap is not yet a software release.
