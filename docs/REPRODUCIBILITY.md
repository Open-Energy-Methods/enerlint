# Reproducing the EnerLint alpha software checks

**Scope:** source installation, tests, built artifacts and synthetic CLI behavior. This is a *software packaging and regression testing protocol*, not an independent scientific study.

## Prerequisites

- Python **3.10 or newer**, with `venv` and `pip` installed.
- A clean public checkout of [EnerLint](https://github.com/Open-Energy-Methods/enerlint).
- Internet access to install the development/build dependencies (not needed by EnerLint's core runtime).
- No proprietary model data, credentials or paid service.

## Route A: editable development install

From the root of a fresh checkout:

```shell
python -m venv .venv
# Activate this environment using the command appropriate to your operating system:
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Unix-like shell: source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/run_foundation_benchmark.py
python -m enerlint check examples/steady_compressor.json
```

The working directory is the checkout; the editable install deliberately points to the source files. Python imports can fail if the package is neither installed nor on the module search path. That failure is an *environment/preparation* problem, not a numerical validation result.

## Route B: build both archive formats and test installed code

```shell
python -m pip install build
python -m build --wheel --sdist
python scripts/verify_distributions.py
```

The smoke script creates a **new isolated virtual environment for each artifact** in a temporary directory, installs it using `pip`, and runs the installed module away from the repository. It checks:

1. Wheel includes the EnerLint module and package metadata.
2. Both a wheel and a source-distribution archive exist.
3. The import resolves inside the new virtual environment, not the source checkout.
4. The hand-constructed compressor sample exits 0 with `PASS_IN_SCOPE`.
5. An inverted compressor shaft-work sign exits 1 with a failed first-law check.
6. A missing required field exits 2 with `INVALID_INPUT`.

The script deliberately does **not** label any of those examples independently validated. It needs access to the checkout's example JSON to provide an input case, but it exercises the *installed* package for the numerical checks.

## Route C: inspect build security and create a per-run manifest

After Route B produces `dist/*.whl` and `dist/*.tar.gz`:

```shell
python scripts/audit_release_artifacts.py
```

This bounded check scans git-tracked source and both distribution archives for selected high-confidence secret formats, sensitive filenames, archive path hazards, missing package license/schema and unexpected runtime dependencies. It writes a **run-specific** manifest to `artifacts/ci/build-manifest.json` with the exact archive SHA-256 hashes, Python/build-tool versions and explicit limitations. It does **not** establish exhaustive secret detection, signed provenance or byte-for-byte reproducibility.

The [Scientific core workflow](../.github/workflows/ci.yml) uploads this manifest **along with the audited wheel and sdist** as a 14-day GitHub Actions artifact. The SHA hashes describe that one build; a successful upload is not a tagged or reviewed release. See [security and artifact-audit control record](CI_SECURITY_AND_REPRODUCIBILITY.md).

## Current GitHub CI coverage

The [Scientific core workflow](../.github/workflows/ci.yml) runs on Linux, Windows and macOS, using CPython 3.10 and 3.13. It performs an editable installation, the pytest suite, the synthetic benchmark ledger, the isolated wheel/sdist smoke test, and the CLI demonstrations.

Successful CI shows this bounded protocol worked in those environments. It does not guarantee that intermediate CPython versions, specific operating-system releases, other Python interpreters, air-gapped installation or external modelling interfaces behave identically.

## Expected reference results

- The original alpha smoke benchmark currently includes four hand-built baselines, six selected injected faults and one deliberately undetected compensated error.
- The [benchmark case cards](BENCHMARK_CASE_CARDS.md) document two cases with hand arithmetic and default thresholds that can be checked *without reading source code*.
- The [foundation results](RESULTS.md) label developer-selected cases as self-tests.
- No sensitivity/specificity estimate over real-world mistakes, model validation, or independent reference audit follows from these test counts.

## Troubleshooting and reporting

If artifact installation fails, copy the **Python version, operating system, commands, exact error, and whether the failure occurred in the editable, wheel or sdist route** into a GitHub issue. Do not send industrial input files, work permits, personal credentials or confidential datasets.

If a numerical test fails, preserve the input JSON, the declared physical boundary, the computed residual, the threshold and the expected independent calculation. Explain whether the failure suggests a code defect, an incorrect test reference, an unsupported assumption or an ambiguous physical boundary.

## Publication gate

A clean install is necessary for a credible alpha, but **not sufficient**. Public software release and archive decisions remain separate from external scientific review, fair native-tool comparisons, rights review and statements about maturity.
