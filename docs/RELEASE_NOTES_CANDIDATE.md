# EnerLint — candidate release notes (DRAFT; NOT RELEASED)

**Provisional software version:** `0.1.0a0` · **Release/tag:** none created · **PyPI/Zenodo DOI:** none assigned.

## What exists in this alpha

EnerLint is an MIT-licensed, experimental Python package that checks whether specified, author-declared energy engineering model outputs satisfy scoped physical accounting equations:

- Steady, nonreacting open-system **mass** and **first-law energy** residuals with explicit inlet/outlet, heat and shaft-work signs.
- A single declared thermal storage **energy interval** and optional capacity constraint.
- Strict SI JSON input, finite numerical checks, explicit abstention/error states, deterministic, schema-versioned JSON reports and source-input fingerprints.
- Optional **author-attested** physical-boundary and property-reference metadata reviews; these **do not authenticate** that the real physical boundary, fluid values or reference settings are correct.

## Reproducible internal synthetic evidence

The developer-selected foundation ledger reports **four hand-built balanced examples, all passing; six selected injected faults, all flagged; and one compensated compressor error that still passes** the balance checks. The fault-injection examples are *not* statistically sampled from real plant or solver failures. The positive cases and hand-derived benchmark oracles have **not** undergone external peer review, and the current package does **not** establish real-world detection rates, measured fidelity or industrial validation.

The compensated-error example deliberately scales compressor flows and shaft work together; the declared conservation residuals still close despite the changed target operating point. This is a scientific limitation, not a bug the tool can magically eliminate.

## Software verification and distribution

Current CI tests support Python 3.10 and 3.13 on Ubuntu, Windows and macOS, run the developer test suite and packaging smoke checks, validate report schema and preserve intentionally failing examples. A separate artifact hygiene scan examines selected credential patterns, source/package contents and license metadata, creating per-run SHA-256 and build-tool manifests. **The final candidate CI result must be checked before any publication.**

The runtime declares no third-party Python dependencies. Scientific reference libraries such as CoolProp, IAPWS and REFPROP are **not** used to validate exported property values.

## Known limitations (release blocker/required disclosure)

- No independent experimental or real-model validation; no verified false-alarm, missed-fault, sensitivity or specificity estimates.
- A balance pass is not proof of the model's intended operating point, upstream solver correctness, physical boundary completeness or property origin.
- Optional storage capacity, if not provided, is `NOT_CHECKED` rather than passing.
- Unavailable/unrepresentable inputs are `INVALID_INPUT`, not an independently detected physics error.
- Numerical tolerances are specified software defaults, not calibrated measurement uncertainty.
- Standalone boundary/property review files are author declarations and are not part of the frozen core input/report schema.
- A preregistered native-tool comparison has not been executed; superiority is not claimed.
- Code/data source rights, exact release version, repository publication authorization, archive contents and package registry ownership require fresh release-gate review.

## Citation

Author: **Abhijith Sivaprasadan** · ORCID **[0009-0009-8429-1266](https://orcid.org/0009-0009-8429-1266)** · [repository](https://github.com/Open-Energy-Methods/enerlint) · [CITATION.cff](../CITATION.cff).

Until a tagged release exists, cite the precise GitHub repository commit and access date, not an invented DOI or published release date. The file's local alpha version is not proof that a package has been published.

**Status:** This is an unapproved *draft*. Do not use it as a GitHub release description or Zenodo record without completing the [release decision checklist](RELEASE_READINESS_2026-10-27.md) and obtaining the creator's approval.
