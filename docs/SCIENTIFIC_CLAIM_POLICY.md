# Scientific evidence and public claims — EnerLint v0.1

**27 October 2026 · policy v0.1 · maintainer-authored; not independently reviewed**

This is a plain-language and technical rulebook for describing what EnerLint actually did. It applies to READMEs, GitHub issues, website notes, documentation, figures, abstracts, public posts, release notes, datasets, and any future research paper. The point is to let people understand the real engineering work without presenting a passing test as approval of a model.

**The rule:** every positive claim must name the precise *check*, *input boundary*, *evidence source*, *comparison or threshold*, *scope*, and *important thing it cannot establish*. If one of those is unknown, narrow the claim. Keep negative/undetected cases.

> A numerical balance can close even when an operating point, input dataset or boundary assumption is wrong. `PASS_IN_SCOPE` is not a finding that a whole simulation is valid.

## 1. Terms: different questions, different evidence

| Term | The question addressed | What it requires | What EnerLint v0.1 actually contributes |
|---|---|---|---|
| **Software testing** | Does *our code* behave as specified for selected cases? | Regression tests and reproducible execution | Selected tests/CI on supported environments. Does not verify independent physical truth |
| **Verification** | Is a specified mathematical/model or implementation requirement satisfied? | Correct specification, numerical/reference checks, adequate boundary, recorded tolerances | Independently **reconstructs only declared exported mass/energy/storage accounting**. It does not independently verify the upstream solver's discretization or solution convergence |
| **Validation** | Is the model credible against reality **for a stated intended context of use**? | Relevant empirical or otherwise independently justified reference evidence, comparison metrics and uncertainties | **Not established** by synthetic conservation residuals |
| **Uncertainty quantification (UQ)** | How do uncertain input/model/numerical/measurement factors affect an output? | Specified uncertainty sources, distributions or bounds, analysis/propagation and sensitivity | **Not implemented**. Binary64 tolerance `1e-8` is not uncertainty quantification |
| **Calibration** | Which parameter values fit reference observations for a specified calibration procedure? | Declared reference observations, objective, optimization/adjustment, residuals and calibration context | **Not implemented**. A balanced compressor is not a calibrated compressor |
| **Certification / accreditation / compliance** | Has an identified competent authority, scheme or standard assessed the defined object for its stated purpose? | Applicable requirements, competent authorized process, traceable decision and scope | **None**. A license, CI pass, DOI, ORCID, university affiliation, GitHub organization or ASME citation is not certification |

Terminology follows the distinction between verification, validation and UQ expressed by [ASME VVUQ](https://www.asme.org/codes-standards/publications-information/verification-validation-uncertainty) and [NIST's 2026 synthesis on uncertainty and model credibility](https://www.nist.gov/publications/methods-uncertainty-quantification-computational-modeling-and-simulation-harmonizing). This policy **does not claim** ASME endorsement, compliance with an ASME standard, or authority to issue official V&V classifications. Read the source standards for their actual definitions and applicability; the table is a project-specific operational paraphrase.

## 2. OEM's **proposed** V0–V5 *evidence descriptors*

These are shorthand for kinds of support that could accompany **one specified claim**. They are **not a certified maturity scale, award, automatic ladder, quality rating, or a property of a repository**. Evidence types can coexist without implying progression; in particular, V5 requires an applicable external process and is **never inferred** from V0–V4. The current report schema deliberately contains **no `evidence_tier`, `validated`, or `certified` field**.

| OEM descriptor | Required evidence for a *scoped* claim | What it **does not** show | Present EnerLint evidence |
|---|---|---|---|
| **V0 — Contract inspection** | Explicit input format, supported units/fields, rejection/abstention behavior, tests of those contracts | Correct numerical solution or physically complete inputs | Available for strict v0.1 input/report cases |
| **V1 — Recomputed physical accounting** | Stated first-law/storage equation, boundary, SI data, independent recomputation *relative to the originating solver's own residual*, signed terms, scales, tolerances | True operating point, correct property references, complete real-world physical boundary, external model validation | Available for specified hand-made and supplied cases, **conditional on their declared inputs and assumptions** |
| **V2 — Independently checkable reference case** | Frozen case specification, **separately stated** analytical/manufactured oracle, provenance, expected values and limitations; reviewer independence must be stated | General accuracy; an author-derived oracle is **not third-party reviewed** | Two complete **maintainer-derived** benchmark case cards and regression tests; no outside review. Describe as *internal V2-style work*, not externally established V2 |
| **V3 — Cross-implementation comparative evidence** | Frozen, rights-cleared cases, fair input availability, distinct implementations/native diagnostic comparison, full outcome ledger including nulls and adverse results | Ground truth when both tools share the same incorrect assumption | **Not yet measured**; D1 protocol is a plan, not a result |
| **V4 — Empirical context-of-use validation evidence** | Independently sourced measurements or other defensible real-world references, instrumentation traceability, UQ, specified operating domain and validation metrics | Validity beyond tested conditions or safety authorization | **No such results published** |
| **V5 — Identified externally governed qualification/compliance evidence** | A **named applicable standard/scheme**, competent assessor and its actual scoped decision and supporting record | Universal correctness; accreditation of an unrelated project or certification by assertion | **None; not a planned alpha claim** |

**Reporting template for any descriptor:** “For [case(s) and revision], [specific method/check] produced [recorded result] against [independently describable reference], under [boundary/uncertainties], with [reviewer identity/status if consented]. This does not establish [most important exclusion].”

A higher descriptor must never appear automatically as a result of a PASS, a passing CI workflow, a paper upload, a Zenodo DOI, stars/forks, a user testimonial, a contributor's job title, or a fabricated review. If a category depends on external reviewers, explicitly record whether they actually performed the review and permitted attribution.

## 3. What an EnerLint status **actually** permits

### `PASS_IN_SCOPE` on `steady_control_volume`

You may say: “For **this declared boundary and exported SI inputs**, the stated mass and/or first-law balance residuals were within the recorded numerical thresholds.”

Do **not** infer that the compressor/turbine was calibrated; the enthalpy values represent physically valid fluid states; all pipes, leaks and auxiliary energy terms were included; a solver converged correctly; an output matches measured operation; or an industrial model is validated.

### `PASS_IN_SCOPE` on `storage_interval`

You may say: “For **this supplied interval and declared constant-average rates**, the reported change in stored energy agrees with the stated charge, discharge and loss accounting within its tolerance.”

If `capacity_j` is omitted, `storage_capacity` is **`NOT_CHECKED`**. You must not say “storage capacity verified” or imply there is enough thermal power, outlet temperature or deliverability.

### `FAIL`, `INVALID_INPUT`, and `NOT_CHECKED`

- `FAIL`: **a declared check failed**. It can be caused by a numerical/model discrepancy or by a mistaken boundary/sign/units declaration. It is not sufficient evidence of a defective plant.
- `INVALID_INPUT`: the current contract could not evaluate the data. This does not mean the upstream model is physically bad; do not call it a “detected physics error.”
- `NOT_CHECKED`: the specified optional calculation was **not performed**. It is neither a pass nor a failure and must not enter evaluated-test denominators as either.
- A `source_fingerprint_sha256` binds to one serialized input JSON object; it is **not a provenance signature or external authenticity certificate**.
- The `evidence_class` and `declared_source` properties are **author-supplied** metadata, not independently verified facts. A self-labelled `experimental` case is not automatically empirical validation.
- The optional author-attested [boundary preflight](CONTROL_VOLUME_BOUNDARY_REVIEW.md) can say `DECLARATION_COMPLETE`; it cannot discover an omitted real physical crossing.

## 4. Examples: what to say and what to reject

| Situation | Acceptable wording | Claim to reject |
|---|---|---|
| Hand-built compressor closes both equations | “The synthetic compressor example satisfies two declared balance checks at the stated thresholds.” | “EnerLint validates gas-turbine compressors.” |
| Deliberate shaft-sign mutation fails | “The selected shaft-work-sign mutation produced a failed first-law residual.” | “EnerLint detects all compressor modelling errors.” |
| Wrong operating point but compensating flows/work | “This compensated error **passed** conservation checks; an external operating-point constraint would be needed.” | “Every PASS indicates a correct operating point.” |
| Storage energy closes with capacity omitted | “Interval energy accounting passed; capacity was **not checked**.” | “Thermal storage verified, including its capacity.” |
| Author marks a case `experimental` | “The submitted metadata labels its origin as experimental; source authenticity is not checked.” | “Real experimental validation was independently confirmed.” |
| Software CI matrix passes | “Defined regression and packaging checks passed on the tested platforms.” | “Scientifically validated by CI.” |
| Case hash is reproducible | “This SHA-256 fingerprint identifies the submitted JSON content under this canonicalization.” | “Provenance independently authenticated.” |
| Unexecuted D1 comparison plan | “A native-versus-independent comparison protocol is documented; the experiment has not yet run.” | “Proven to outperform TESPy or ExerPy.” |
| Repository is linked to a university-trained engineer | “Created as an independent open-source engineering workbench.” | “Approved or officially hosted by KTH or ASME.” |

A reproducible list of the permitted/rejected sample phrasings is also in [`claim_examples_v0.1.json`](claim_examples_v0.1.json). Those structured examples are **test fixtures**, not a trained or comprehensive natural-language content filter.

## 5. Publication gate: mandatory claim-evidence record

Before a new README headline, field note, README badge, figure caption, release note, DOI description, or research abstract states a **scientific result**, record:

1. **Exact sentence** and intended audience; avoid generic “trusted” or “industry-ready” assertions.
2. **Claim owner** and relevant revision, case, software version and report/schema version.
3. **Evidence link:** a frozen input, source equation and/or benchmark card, commands, test output, date and CI/job ID if applicable.
4. **Evidence classification:** the relevant OEM descriptor(s), with reviewer independence clearly distinguished from a maintainer's calculations.
5. **Physical/numerical scope:** model boundaries, omitted terms, tolerances, declared source, software environment, and missing checks.
6. **Counterexample/negative result:** a documented miss, false alarm, abstention, or applicable comparison with existing tools. If none was examined, say so.
7. **Explicit exclusion:** at least the most important thing that the evidence **cannot** prove.
8. **Approval:** maintainer review of the *literal claim and evidence*. For independent-review claims, obtain actual review and permission before naming reviewers.

A claim that fails this checklist gets **narrowed or removed**, not upgraded with marketing language. Public docs need not publish the private founder's research bible. The review register can be a short GitHub issue or document; no invented ethics committee, accreditation board or corporate hierarchy is required.

## 6. What stays off-limits absent new evidence

No assertion that EnerLint:
- is *certified*, *accredited*, *ASME compliant*, approved by KTH/Siemens Energy/ASME/NIST, or subject to independent peer review;
- validates real turbines, nuclear reactors, industrial safety cases, sensors or measured energy storage performance;
- detects all physical/numerical errors, reliably certifies AI-generated simulations, measures empirical sensitivity/specificity, or eliminates the need for engineering judgment;
- establishes calibration or UQ merely from passing a numerical threshold;
- outperforms native diagnostics or competing packages without a preregistered, fair, **executed** comparative study.

If OEM eventually runs independent tests, preserves critical findings and satisfies actual external requirements, report only **what happened** and **under which exact conditions**. Neither project ownership nor publication is a scientific credential.

## 7. Scope and change control

This policy applies to EnerLint v0.1.0a0 and OEM's current workbench description. It does **not** modify the frozen v0.1 input schema, output schema, or established statuses, and does not inject “evidence tiers” into report objects.

A separate [property-reference acceptance policy](PROPERTY_DATA_ACCEPTANCE.md)
documents why `PASS_IN_SCOPE` cannot establish compatible property zeros, fluid
identity, backend accuracy or mixture admissibility. The optional preflight only
assesses declared metadata consistency.

The [synthetic negative-control registry](NEGATIVE_CONTROL_STUDY.md) distinguishes physics-balance failures, contract rejections, compensated escapes and clean metamorphic controls. Never treat the developer-chosen cases or `INVALID_INPUT` events as measured real-world fault-detection accuracy.

The [numerical conditioning review](NUMERICAL_CONDITIONING_REVIEW_2026-10-27.md) includes both a source-decimal balance that binary64 falsely flags *relative to that declared arithmetic* and an out-of-tolerance decimal discrepancy that binary64 misses. Do not claim that numerical PASS/FAIL is reliable under arbitrary very large enthalpy reference offsets, or that `math.fsum` restores bits lost during input/product rounding.

The [scientific scope](SCIENTIFIC_SCOPE.md), [report contract](REPORT_SCHEMA.md), [benchmark case cards](BENCHMARK_CASE_CARDS.md), and [native comparison protocol](EXPERIMENT_D1_THERMAL_COMPARISON.md) give specific technical boundaries. Changes to public scientific claims should include a dated example and corresponding evidence. Retain previous assertions in git history. Solicited independent critique remains **open** ([issue #25](https://github.com/Open-Energy-Methods/enerlint/issues/25)).

**Policy owner:** OEM creator/maintainer. **External status:** unreviewed project editorial/scientific rule, not legal or standards advice.
