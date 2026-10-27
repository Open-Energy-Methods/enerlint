"""Run synthetic manufactured/limiting references, preserving failures and misses.

All expected results are frozen in docs/manufactured_limits_v0.1.json.
Independent arithmetic is performed with decimal.Decimal in a separate module
from EnerLint's core binary64 checker. Developer-authored evidence, not
independent scientific review or real-world performance validation.

Usage:
    python scripts/run_manufactured_limits.py
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
# Script-file execution sets sys.path[0] to scripts/, not necessarily the repo root.
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from enerlint import check_case  # noqa: E402
from enerlint.verify import ContractError  # noqa: E402
from scripts.run_analytical_catalog import independent_arithmetic  # noqa: E402

CATALOG = ROOT / "docs" / "manufactured_limits_v0.1.json"
OUTPUT = ROOT / "artifacts" / "ci" / "manufactured_limits_v0.1.json"


def close(actual: Any, expected: Any, label: str) -> None:
    if expected is None:
        if actual is not None:
            raise AssertionError(f"{label}: expected null")
    elif not math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError(f"{label}: {actual!r} != frozen expected {expected!r}")


def mutate(obj: dict[str, Any], field: str, replacement: Any) -> dict[str, Any]:
    result = copy.deepcopy(obj)
    parts = field.split(".")
    target: Any = result
    for piece in parts[:-1]:
        target = target[int(piece)] if isinstance(target, list) else target[piece]
    key = parts[-1]
    if isinstance(target, list):
        target[int(key)] = replacement
    else:
        if key not in target:
            raise AssertionError(f"Unknown mutation target {field}")
        target[key] = replacement
    return result


def status_from_reference(ref: dict[str, dict[str, Any]]) -> str:
    return (
        "FAIL" if any(value["status"] == "FAIL"
                      for key, value in ref.items() if not key.startswith("_"))
        else "PASS_IN_SCOPE"
    )


def compare_reference(case: dict[str, Any], frozen: dict[str, Any], report: Any, label: str) -> None:
    reference = independent_arithmetic(case)
    names = {name for name in reference if not name.startswith("_")}
    if names != set(frozen):
        raise AssertionError(f"{label}: unexpected set of check IDs")
    if status_from_reference(reference) != report.status:
        raise AssertionError(f"{label}: independently calculated overall status differs")

    observed = {check.name: check for check in report.checks}
    if set(observed) != names:
        raise AssertionError(f"{label}: core report contains different check IDs")
    for check_name, expected in frozen.items():
        calculated, measured = reference[check_name], observed[check_name]
        for key in ("status", "unit"):
            if expected[key] != calculated[key] or expected[key] != getattr(measured, key):
                raise AssertionError(f"{label}:{check_name}.{key} differs")
        for key in ("residual", "scale", "threshold"):
            close(calculated[key], expected[key], f"{label}.{check_name}.{key} independent")
            close(getattr(measured, key), expected[key], f"{label}.{check_name}.{key} checker")


def run() -> dict[str, Any]:
    source = CATALOG.read_bytes()
    catalog = json.loads(source)
    rows = catalog["cases"]
    if catalog["version"] != "0.1.0" or len(rows) != 13:
        raise AssertionError("Expected frozen manufactured/limiting v0.1 catalogue of 13 cases")
    ids = [entry["id"] for entry in rows]
    if ids != [f"TH-LM-{i:03d}" for i in range(1, 14)]:
        raise AssertionError("Unexpected order, missing or duplicate case ID")
    recorded = []
    for entry in rows:
        case, label = entry["case"], entry["id"]
        if case["provenance"]["evidence_class"] != "hand_constructed":
            raise AssertionError(f"{label}: unexpected evidence class")

        if entry["expected_status"] == "INVALID_INPUT":
            try:
                check_case(case)
            except ContractError as exc:
                if entry["expected_contract_error"] not in str(exc):
                    raise AssertionError(f"{label}: wrong rejection reason: {exc}") from exc
                recorded.append({
                    "id": label, "classification": "INVALID_INPUT",
                    "contract_evaluated": False, "rejection_kind": entry["expected_contract_error"],
                    "perturbations": [],
                })
            else:
                raise AssertionError(f"{label}: unacceptable invalid case was evaluated")
            continue

        reference = independent_arithmetic(case)
        report = check_case(case)
        if report.status != entry["expected_status"]:
            raise AssertionError(f"{label}: baseline observed {report.status}")
        compare_reference(case, entry["expected_checks"], report, label)
        mutations = []
        for index, event in enumerate(entry["perturbations"]):
            changed = mutate(case, event["field"], event["replacement"])
            if changed == case:
                raise AssertionError(f"{label}: perturbation {index} had no effect")
            oracle = independent_arithmetic(changed)
            checker = check_case(changed)
            selected_name = event["expected_check"]
            calculated = oracle[selected_name]
            observed = {c.name: c for c in checker.checks}[selected_name]
            if (
                status_from_reference(oracle) != event["expected_status"]
                or checker.status != event["expected_status"]
            ):
                raise AssertionError(f"{label} mutation {index}: outcome differs")
            expected_result = (
                "PASS" if event["expected_status"] == "PASS_IN_SCOPE" else "FAIL"
            )
            if calculated["status"] != expected_result or observed.status != expected_result:
                raise AssertionError(f"{label} mutation {index}: specific check status differs")
            close(calculated["residual"], event["expected_residual"],
                  f"{label}.{index} independent residual")
            close(observed.residual, event["expected_residual"],
                  f"{label}.{index} binary64 residual")
            mutations.append({
                "field": event["field"], "replacement": event["replacement"],
                "status": checker.status, "selected_check": selected_name,
                "observed_residual": observed.residual,
                "observed_threshold": observed.threshold,
                "tolerated_mismatch": checker.status == "PASS_IN_SCOPE",
            })
        recorded.append({
            "id": label, "classification": "EVALUATED",
            "contract_evaluated": True,
            "status": report.status,
            "checks": [
                {"name": c.name, "status": c.status, "residual": c.residual,
                 "scale": c.scale, "threshold": c.threshold, "unit": c.unit}
                for c in report.checks
            ],
            "perturbations": mutations,
        })
    all_mutations = [mutation for row in recorded for mutation in row["perturbations"]]
    summary = {
        "cases_total": len(recorded),
        "evaluated_limit_cases": sum(row["contract_evaluated"] for row in recorded),
        "invalid_inputs_correctly_rejected": sum(
            row["classification"] == "INVALID_INPUT" for row in recorded
        ),
        "evaluated_scoped_passes": sum(
            row.get("status") == "PASS_IN_SCOPE" for row in recorded
        ),
        "selected_perturbations": len(all_mutations),
        "selected_perturbations_failed": sum(x["status"] == "FAIL" for x in all_mutations),
        "selected_perturbations_tolerated": sum(
            x["tolerated_mismatch"] for x in all_mutations
        ),
        "independent_external_reviews": 0,
    }
    expected_summary = {
        "cases_total": 13, "evaluated_limit_cases": 11,
        "invalid_inputs_correctly_rejected": 2, "evaluated_scoped_passes": 11,
        "selected_perturbations": 13, "selected_perturbations_failed": 11,
        "selected_perturbations_tolerated": 2, "independent_external_reviews": 0,
    }
    if summary != expected_summary:
        raise AssertionError(f"Unexpected manufactured self-test counts: {summary}")
    return {
        "catalog_id": catalog["catalog_id"],
        "version": catalog["version"],
        "catalog_sha256": hashlib.sha256(source).hexdigest(),
        "study_type": "developer-authored manufactured numerical software tests",
        "review_status": catalog["independence"],
        "meaning_of_pass": catalog["meaning_of_pass"],
        "summary": summary,
        "cases": recorded,
        "limitations": [
            "No independent author/peer review or real-model data.",
            "No measured false-positive, missed-fault or detection rate.",
            "Tolerated numerical mismatch is not physical truth.",
            "INVALID_INPUT means no balance checks were computed.",
            "Extreme-value and limiting manufactured examples are not operating conditions.",
        ],
    }


def main() -> int:
    result = run()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
                      encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"Manufactured limiting catalogue ledger: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
