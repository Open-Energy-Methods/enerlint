# Initial prior-art boundary — not a novelty determination

The project does not claim to invent mass/energy conservation checks or
metamorphic testing. Related tools already provide extensive functionalities:

- [TESPy](https://tespy.readthedocs.io/): thermal cycle modeling, balances,
  solver diagnostics, and physically meaningful component relationships.
- [ExerPy](https://exerpy.readthedocs.io/): exergy analysis of thermodynamic
  networks and external models.
- [pandapower](https://pandapower.readthedocs.io/): electrical-network diagnostics
  and model validation routines.
- [PyPSA](https://docs.pypsa.org/): energy/power-system optimization and network
  consistency functionality.
- [CoolProp](https://coolprop.org/) and [iapws](https://pypi.org/project/iapws/):
  physical property libraries; avoid reimplementing steam tables.
- [BuildingsPy](https://simulationresearch.lbl.gov/modelica/buildingspy/):
  simulation regression and Modelica-oriented validation workflows.

Proposed contribution: *portable, independently specified conservation-output
contracts and benchmarked fault-injection tests*, with explicit scope limits
and machine-readable reports. This is a research hypothesis about utility and
comparative performance, **not** evidence of unique novelty.

Before claiming differentiation, establish a matched test suite and compare
EnergyVerify/EnerLint tests with the incumbent tools' own validation features.
Source links above are informational; feature availability depends on tool
version and warrants re-verification before publication.
