"""Check ten frozen, maintainer-derived reference cases against EnerLint v0.1.

Independent arithmetic is implemented with decimal.Decimal and reads exported
case quantities; this script DOES NOT import any residual/scale internals from
EnerLint. It compares the separately frozen expected results against both that
arithmetic and the checker output. This is a *developer self-test*, not an
external review or empirical validation.

From repository root after installing -e ".[dev]":
    python scripts/run_analytical_catalog.py
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enerlint import check_case  # noqa: E402

getcontext().prec = 40
CATALOG = ROOT / "docs" / "analytical_reference_v0.1.json"
OUTPUT = ROOT / "artifacts" / "ci" / "analytical_catalog_v0.1.json"
def D(value: Any) -> Decimal:
    """Convert an exported JSON scalar into exact decimal for reference arithmetic."""
    return Decimal(str(value))


def assert_numeric(actual: float | Decimal, expected: float | Decimal, label: str) -> None:
    """Permit only benign float representation differences on recorded scales."""
    if not math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-10):
        raise AssertionError(f"{label}: computed {actual}, frozen reference {expected}")


def independent_arithmetic(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Recalculate SI equations from case numbers without using check_case code."""
    if case["kind"] == "steady_control_volume":
        inputs = [(D(s["mass_flow_kg_s"]), D(s["specific_enthalpy_j_kg"]))
                  for s in case["inlets"]]
        outputs = [(D(s["mass_flow_kg_s"]), D(s["specific_enthalpy_j_kg"]))
                   for s in case["outlets"]]
        rate_in = sum((m for m, _ in inputs), Decimal(0))
        rate_out = sum((m for m, _ in outputs), Decimal(0))
        enthalpy_in = sum((m * h for m, h in inputs), Decimal(0))
        enthalpy_out = sum((m * h for m, h in outputs), Decimal(0))
        heat = D(case["heat_into_volume_w"])
        work = D(case["shaft_work_out_w"])
        mass_scale = rate_in + rate_out
        mass_threshold = max(Decimal("1e-9"), Decimal("1e-8") * mass_scale)
        mass_residual = rate_in - rate_out
        # This is a declared-input reference center, not a certified property datum.
        center = (enthalpy_in + enthalpy_out) / mass_scale if mass_scale else Decimal(0)
        energy_scale = (
            sum((m * abs(h - center) for m, h in inputs + outputs), Decimal(0))
            + abs(heat) + abs(work)
        )
        energy_threshold = max(Decimal(1), Decimal("1e-8") * energy_scale)
        energy_residual = enthalpy_in - enthalpy_out + heat - work
        return {
            "steady_mass_closure": {
                "status": "PASS" if abs(mass_residual) <= mass_threshold else "FAIL",
                "residual": mass_residual,
                "scale": mass_scale,
                "threshold": mass_threshold,
                "unit": "kg/s",
            },
            "steady_first_law": {
                "status": "PASS" if abs(energy_residual) <= energy_threshold else "FAIL",
                "residual": energy_residual,
                "scale": energy_scale,
                "threshold": energy_threshold,
                "unit": "W",
            },
            "_inputs": {
                "enthalpy_in_w": enthalpy_in,
                "enthalpy_out_w": enthalpy_out,
                "heat_into_w": heat,
                "shaft_work_out_w": work,
                "enthalpy_reference_j_kg": center,
            }
        }
    if case["kind"] == "storage_interval":
        duration = D(case["duration_s"])
        delta = D(case["energy_final_j"]) - D(case["energy_initial_j"])
        charge = D(case["heat_charge_into_storage_w"]) * duration
        discharge = D(case["heat_discharge_out_storage_w"]) * duration
        loss = D(case["heat_loss_out_storage_w"]) * duration
        residual = delta - charge + discharge + loss
        scale = abs(delta) + abs(charge) + abs(discharge) + abs(loss)
        threshold = max(Decimal(1), Decimal("1e-8") * scale)
        checks: dict[str, dict[str, Any]] = {
            "storage_energy_closure": {
                "status": "PASS" if abs(residual) <= threshold else "FAIL",
                "residual": residual,
                "scale": scale,
                "threshold": threshold,
                "unit": "J",
            },
            "_inputs": {
                "storage_delta_j": delta,
                "storage_charge_integrated_j": charge,
                "storage_discharge_integrated_j": discharge,
                "storage_loss_integrated_j": loss,
            }
        }
        if "capacity_j" in case:
            capacity = D(case["capacity_j"])
            excursion = max(Decimal(0), D(case["energy_initial_j"]) - capacity,
                            D(case["energy_final_j"]) - capacity)
            checks["storage_capacity"] = {
                "status": "FAIL" if excursion > 0 else "PASS",
                "residual": excursion,
                "scale": Decimal(0),
                "threshold": Decimal(0),
                "unit": "J",
            }
        else:
            checks["storage_capacity"] = {
                "status": "NOT_CHECKED",
                "residual": None, "scale": None, "threshold": None, "unit": None,
            }
        return checks
    raise AssertionError(f"Unsupported catalogue kind: {case['kind']}")


def _check_frozen(case: dict[str, Any], item: dict[str, Any],
                  derived: dict[str, dict[str, Any]]) -> None:
    ref = item["independent_reference"]
    if case["kind"] == "steady_control_volume":
        bridge = {
            "steady_energy_input_w": "enthalpy_in_w",
            "steady_energy_output_w": "enthalpy_out_w",
            "heat_into_volume_w": "heat_into_w",
            "shaft_work_out_w": "shaft_work_out_w",
            "enthalpy_reference_j_kg": "enthalpy_reference_j_kg",
        }
        for recorded, actual in bridge.items():
            assert_numeric(derived["_inputs"][actual], ref[recorded], recorded)
        for recorded, check, key in (
            ("mass_scale_kg_s", "steady_mass_closure", "scale"),
            ("steady_mass_residual_kg_s", "steady_mass_closure", "residual"),
            ("steady_energy_scale_w", "steady_first_law", "scale"),
        ):
            assert_numeric(derived[check][key], ref[recorded], recorded)
    else:
        for key in (
            "storage_delta_j", "storage_charge_integrated_j",
            "storage_discharge_integrated_j", "storage_loss_integrated_j",
        ):
            assert_numeric(derived["_inputs"][key], ref[key], key)
        assert_numeric(derived["storage_energy_closure"]["scale"], ref["storage_scale_j"],
                       "storage_scale_j")

    expected = item["expected_checks"]
    actual_names = {key for key in derived if not key.startswith("_")}
    if set(expected) != actual_names:
        raise AssertionError(f"{item['benchmark_id']}: frozen check names don't match model")
    for name, values in expected.items():
        for key in ("status", "unit"):
            if derived[name][key] != values[key]:
                raise AssertionError(f"{item['benchmark_id']} {name}: wrong {key}")
        for key in ("residual", "scale", "threshold"):
            if values[key] is None:
                if derived[name][key] is not None:
                    raise AssertionError(f"{name} expected no {key}")
            else:
                assert_numeric(derived[name][key], values[key], f"{name}.{key}")


def _mutated(case: dict[str, Any], field: str, value: Any) -> dict[str, Any]:
    changed = copy.deepcopy(case)
    parts = field.split(".")
    target: Any = changed
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    final = parts[-1]
    if isinstance(target, list):
        target[int(final)] = value
    else:
        if final not in target:
            raise AssertionError(f"Mutation targets missing field {field}")
        target[final] = value
    return changed


def execute() -> dict[str, Any]:
    raw = CATALOG.read_bytes()
    catalog = json.loads(raw)
    if catalog["version"] != "0.1.0" or len(catalog["cases"]) != 10:
        raise AssertionError("Analytical catalogue v0.1 must contain exactly ten cases")
    ids = [item["benchmark_id"] for item in catalog["cases"]]
    if len(set(ids)) != 10:
        raise AssertionError("Duplicate analytical catalogue IDs")
    if set(ids) != {f"TH-CV-{i:03d}" for i in range(1, 9)} | {
        "TH-ST-001", "TH-ST-002"
    }:
        raise AssertionError("Unexpected or missing frozen catalogue IDs")

    out: list[dict[str, Any]] = []
    for item in catalog["cases"]:
        source = ROOT / item["case_file"]
        if not source.is_relative_to(ROOT / "examples") or source.suffix != ".json":
            raise AssertionError("Catalogue input must refer to a JSON example")
        base = json.loads(source.read_text(encoding="utf-8"))
        derived = independent_arithmetic(base)
        _check_frozen(base, item, derived)
        report = check_case(base)
        if report.status != item["expected_report_status"]:
            raise AssertionError(f"{item['benchmark_id']}: baseline status differs")
        assert [c.name for c in report.checks] == list(item["expected_checks"])
        for check in report.checks:
            expected = item["expected_checks"][check.name]
            if check.status != expected["status"] or check.unit != expected["unit"]:
                raise AssertionError(f"{item['benchmark_id']}: checker {check.name} state differs")
            for key in ("residual", "scale", "threshold"):
                value = getattr(check, key)
                if expected[key] is None:
                    if value is not None:
                        raise AssertionError(f"{check.name}.{key}: should be unevaluated")
                else:
                    assert_numeric(value, expected[key], f"{item['benchmark_id']} {check.name}.{key}")

        mutation = item["deliberate_mutation"]
        fault_case = _mutated(base, mutation["field"], mutation["replacement"])
        oracle_fault = independent_arithmetic(fault_case)
        fault_check = oracle_fault[mutation["expected_failure_check"]]
        if fault_check["status"] != "FAIL":
            raise AssertionError(f"{item['benchmark_id']}: mutation does not fail independent check")
        assert_numeric(fault_check["residual"], mutation["expected_failure_residual"],
                       f"{item['benchmark_id']} fault oracle")
        observed_fault = check_case(fault_case)
        checks = {check.name: check for check in observed_fault.checks}
        if observed_fault.status != "FAIL" or checks[mutation["expected_failure_check"]].status != "FAIL":
            raise AssertionError(f"{item['benchmark_id']}: selected fault was not flagged")
        assert_numeric(checks[mutation["expected_failure_check"]].residual,
                       mutation["expected_failure_residual"], f"{item['benchmark_id']} fault result")
        out.append({
            "benchmark_id": item["benchmark_id"],
            "case_file": item["case_file"],
            "case_sha256": report.source_fingerprint_sha256,
            "baseline_status": report.status,
            "negative_control_status": observed_fault.status,
            "negative_control_failed_check": mutation["expected_failure_check"],
            "baseline_checks": [
                {"name": x.name, "status": x.status, "residual": x.residual,
                 "threshold": x.threshold, "unit": x.unit}
                for x in report.checks
            ],
        })
    result = {
        "catalog_id": catalog["catalog_id"],
        "catalog_version": catalog["version"],
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "study_type": "developer-authored_analytical_self_test_NOT_external_validation",
        "reviewer_status": catalog["author_review_status"],
        "cases": out,
        "summary": {
            "selected_baselines_pass": sum(x["baseline_status"] == "PASS_IN_SCOPE" for x in out),
            "selected_baselines_total": len(out),
            "selected_faults_flagged": sum(x["negative_control_status"] == "FAIL" for x in out),
            "selected_faults_total": len(out),
            "external_independent_reviews": 0,
        },
        "scientific_limitations": [
            "Expected calculations were derived and reviewed only by the maintainer.",
            "Selected faults do not estimate statistical fault-detection effectiveness.",
            "The unchanged four-case foundation benchmark retains its known compensated escape.",
            "Optional property/boundary review sidecars are not empirical validation.",
        ],
    }
    if result["summary"] != {
        "selected_baselines_pass": 10,
        "selected_baselines_total": 10,
        "selected_faults_flagged": 10,
        "selected_faults_total": 10,
        "external_independent_reviews": 0,
    }:
        raise AssertionError("Frozen catalogue does not meet expected synthetic self-test outcomes")
    return result


def main() -> int:
    report = execute()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
                      encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Analytical catalogue ledger: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
