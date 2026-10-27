# EnerLint release-readiness decision — 27 October 2026

**Project:** [EnerLint](https://github.com/Open-Energy-Methods/enerlint) · **Current source version:** `0.1.0a0` · **Decision:** **NO-GO for public GitHub/PyPI/Zenodo release at this time** · **Decision maker for any later release:** creator/maintainer, after re-running the checklist.

This is a release-readiness *audit of an already public experimental source repository*, not an attempt to characterize it as a company product or a scientific certification. No tag, uploaded package, DOI, or external validation is created by this document.

## Executive determination

EnerLint has a substantial **testable software alpha foundation**, including dimensional mass/first-law and one-interval storage checks, deterministic versioned reports, boundary and property-reference author-attestation sidecars, negative controls, an explicitly undetected compensated compressor fault, CI, and separately installable wheel/source distributions.

**That does not clear this build for external claims of model validation or for a versioned archive/public package publication.** Unresolved blockers: maintainer-approved third-party/individual rights review, PyPI ownership/reservation verification under the publishing account, independent scientific critique/real-model evidence for stronger physical-validity claims, and a **separate founder publication decision**. A source snapshot may be technically citable as a Git commit without the institution, the toolkit or the methods being endorsed.

## Gate review

| Gate | Evidence today | Outcome / follow-up |
|---|---|---|
| Version and package identity | `pyproject.toml` names `enerlint`, alpha `0.1.0a0`; matching `CITATION.cff` and tests | **Prepared**; exact publication version to be chosen later |
| Public GitHub ownership | Current repository [Open-Energy-Methods/enerlint](https://github.com/Open-Energy-Methods/enerlint) is accessible through the connected maintainer app | **Confirmed repository access**; not proof of corporate registration or trademark rights |
| CI / test matrix | [Scientific core](https://github.com/Open-Energy-Methods/enerlint/actions/workflows/ci.yml), Ubuntu/Windows/macOS on CPython 3.10/3.13; previous verified [6/6 successful run](https://github.com/Open-Energy-Methods/enerlint/actions/runs/40556948027) | **Previous commit passes**. Final candidate commit must get its own 6/6 green run and CFF/twine validation; never substitute an older green run |
| Clean installation and runtime | Fresh venv wheel/sdist smoke tests: PASS, FAIL, INVALID_INPUT; runtime declares zero external dependencies | **Prepared**. Not evidence of solver-model validity |
| Package contents | [Explicit source manifest](../MANIFEST.in) includes license, citation, benchmark docs, examples, scripts and tests, excluding outreach/branding notes | **Prepared**, to confirm from final built archive's manifest |
| Security/publishing hygiene | [Bounded scan and SHA-256 build manifest](CI_SECURITY_AND_REPRODUCIBILITY.md) tests selected secrets/files/paths/metadata; build artifacts retained 14 days | **Internal CI gate**; not a comprehensive security or independently signed provenance audit |
| Python packaging license metadata | `license = "MIT"`, `license-files = ["LICENSE"]`, setuptools PEP 639 support (`>=77.0.3`), distributed licence-content and metadata checks | **Corrected**. Cite [PyPA packaging guidance](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) |
| Author citation | CFF 1.2.0; Abhijith Sivaprasadan; **ORCID 0009-0009-8429-1266**; project URL and matching alpha version; **no DOI/date-released claim** | **Corrected**. CFF schema validation added to CI; the old, unrelated ORCID was wrong and must not be repeated |
| Third-party source and data rights | [File-level inventory](RELEASE_RIGHTS_REGISTER.md) and MIT text are available; code, synthetic fixtures and sources recorded as maintainer-led/AI-assisted with original provenance **not independently attested** | **NOT CLEARED** until creator reviews author/IP provenance per shipped file and records any needed permissions |
| Scientific baseline | [Foundation ledger](RESULTS.md): **4/4** hand-built baselines pass, **6/6** selected injected faults fail, **1** compensating compressor mistake passes; bounded benchmark cards | **Internal self-tests only**; not population detection estimates or real-model validation |
| False-alarm / missed-fault study | [Benchmark protocol](BENCHMARK_PROTOCOL.md) and [D1 comparison design](EXPERIMENT_D1_THERMAL_COMPARISON.md) written | **NOT EXECUTED**. No comparative performance, false-positive rate or empirically validated sensitivity claim |
| Independent scientific review | Reviewer question set and issue [#25](https://github.com/Open-Energy-Methods/enerlint/issues/25) documented | **NOT COMPLETED**. Necessary before claiming external scientific review; not replaced by CI |
| External solver/data evidence | No rights-cleared independently exported industrial/public real-model case validated in this audit | **MISSING** for real-world validation or superiority claims |
| PyPI project/ownership | Public web listing could not be conclusively established during audit; no authenticated PyPI owner or publisher account check was performed | **NOT VERIFIED**. Project names can be reserved even without visible distributions; see [PyPI naming rules](https://docs.pypi.org/project-management/choosing-a-name/). Do not infer name availability or ownership from a web search |
| Software release/tag/DOI | GitHub Releases listing returned no release during this audit; no publish action performed | **NOT RELEASED**. Verify exact tag availability and repository settings again before later actions |
| Publication authorization | User requested release-readiness preparation, **not** creation of a release | **NOT GRANTED**. Separate human approval and final GO record required |

## Minimal public claims currently supportable

> “EnerLint is an experimental open-source Python alpha for independently rechecking specified conservation and interval-energy accounting relationships in declared model exports. Its initial reference cases and fault injections are developer-authored. A compensated compressor error passes the balance checks; no independent real-model validation or certification is claimed.”

Do **not** claim a published PyPI package, validated field performance, peer review, ASME/NIST certification, KTH or Siemens sponsorship, a release DOI, guaranteed error detection or correct thermophysical reference states.

## Scope of this NO-GO

This decision **does not ask for a shutdown or removal of the existing public source repository**. It prevents unreviewed *release actions and stronger claims* while leaving contributors free to inspect and criticize the openly visible alpha. Formal peer review is **not universally a prerequisite for responsibly releasing an explicitly experimental alpha**; the remaining gate is a founder choice and honest labeling, especially for a potential Zenodo archival release.

A narrow, well-labelled **public pre-release** could be reconsidered earlier than independent empirical validation *if* source rights, owner authorization, package publication details, citation metadata, archive checks and risk statements are complete. Such a pre-release would not be a declaration of validated science.

## Publication preflight (complete only for the exact release candidate)

- [ ] Creator signs off the [file-level source and data rights register](RELEASE_RIGHTS_REGISTER.md); any unauthorized or unclear assets are removed or cleared.
- [ ] All six CI jobs are green for the exact intended commit; built archives and their per-run SHA-256 manifest are retained/reviewed; source and wheel file contents are compared.
- [ ] CFF schema validation, `twine check` and `License-Expression: MIT` distribution metadata are verified.
- [ ] PyPI name and **authenticated project ownership** are confirmed if PyPI publication is desired. PyPI registration/trusted-publisher setup is a distinct account action.
- [ ] Benchmark/release notes state the 4 self-tests, 6 selected failures, known compensating miss, null comparisons, absence of empirical validation, and known scientific scope.
- [ ] Independent review status is accurately worded; no invented external endorsements.
- [ ] Review release identifier, source commit, installation instructions, Python support, license, ORCID, repository URL, changelog, optional Zenodo/GitHub linking and archive contents.
- [ ] Record a **new, dated GO/NO-GO** based on that frozen candidate and secure the maintainer's explicit release approval.
- [ ] Only **after** those conditions: consider a GitHub pre-release/tag, then a Zenodo deposit/DOI if desired, and an optional PyPI release. DOI is an archival identifier, not experimental validation.

## What #5 can correctly close

The **task of documenting an honest release audit, correcting metadata and recording blockers** can be closed when the final CI, CFF, `twine` and source-distribution checks pass. That does **not** close independent scientific-review issues or turn this **NO-GO** decision into **GO**. Later publication merits a separate ticket and human choice.

Related: [release notes draft](RELEASE_NOTES_CANDIDATE.md), [rights register](RELEASE_RIGHTS_REGISTER.md), [CI source of truth](CI_SECURITY_AND_REPRODUCIBILITY.md), [scientific claims](SCIENTIFIC_CLAIM_POLICY.md) and [roadmap](ROADMAP.md).
