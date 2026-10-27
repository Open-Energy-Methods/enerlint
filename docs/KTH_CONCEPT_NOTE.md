# KTH-facing research concept (DRAFT; no affiliation or endorsement)

**Working title:** EnerLint — Independent physical-output verification and
fault-injection testing for energy engineering research software.

**Research motivation:** Energy simulations can converge and produce plots
while exported physical flows violate selected conservation laws, time-indexing
contracts, or explicit operating constraints. Also, some incorrect results
*still conserve energy*. We propose a reproducible, solver-independent method
for identifying what can and cannot be established by external checks.

**Main research question:** With a controlled benchmark of correct and
fault-injected engineering-model outputs, which physical and numerical errors
are detected by independent checkers versus incumbent solvers' native QA?

**Candidate first work package:**
1. Define explicit mass/energy closure, control boundaries, SI and tolerance
   contracts for steady compressors, turbines and heat exchangers.
2. Implement a transparent, solver-independent evaluator and machine-readable
   evidence report with optional check coverage.
3. Predefine and execute fault-injection and metamorphic benchmarks.
4. Compare with existing thermal simulation quality/diagnostic mechanisms.
5. Extend cautiously to measured thermal plant or storage cases when permitted.

**Potential groups for technical criticism, not partners or sponsors:** KTH
Heat and Power Technology, Applied Thermodynamics and Refrigeration, and
researchers studying open-source research-software robustness. A prospective
teaching demonstration could be based on a public synthetic thermal cycle.

**Status and limitations:** Existing local alpha with hand-constructed tests;
no KTH endorsement, grant funding, data transfer, or independent benchmark
review. Not ready for safety/operational engineering.

**Near-term request to researcher:** A 20–30 minute methodological review of
three questions: Is the boundary specification physically honest? Which
independent baseline would constitute a meaningful test? What existing
software capability already duplicates the proposed contribution?

**Possible funded research-engineering activity (hypothetical):** Software
architecture, independent benchmark design, cross-tool experiments and
reproducible public release. Employment requires separate confirmed funding
and formal recruitment; this concept note is not a hiring request.
