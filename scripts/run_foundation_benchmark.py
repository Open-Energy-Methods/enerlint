"""Run only registered *synthetic* foundational checks; no external validation.

Execute: PYTHONPATH=src python scripts/run_foundation_benchmark.py
No random AI-generated cases or outside data are used in this evidence ledger.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from enerlint import check_case  # noqa: E402
from enerlint.faults import inject_fault  # noqa: E402

EXAMPLES = ROOT / "examples"
OUT = ROOT / "artifacts" / "foundation_benchmark.json"
BASELINES = (
    "steady_compressor", "steady_turbine", "steady_heat_exchanger", "storage_interval"
)
FAULTS = (
    ("steady_compressor", "outlet_mass_scale"),
    ("steady_compressor", "outlet_enthalpy_scale"),
    ("steady_compressor", "invert_shaft_work"),
    ("steady_turbine", "invert_heat"),
    ("storage_interval", "storage_final_offset"),
    ("storage_interval", "storage_duration_scale"),
)


def read(name: str) -> dict:
    return json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))


def compact_report(x: dict) -> dict:
    report = check_case(x)
    return {
        "case_id": report.case_id,
        "status": report.status,
        "case_sha256": report.source_fingerprint_sha256,
        "checks": [
            {"name": c.name, "status": c.status, "residual": c.residual,
             "threshold": c.threshold, "unit": c.unit}
            for c in report.checks
        ],
    }


def run() -> dict:
    baseline_rows = []
    for example in BASELINES:
        baseline_rows.append({"reference_case": example, **compact_report(read(example))})
    fault_rows = []
    for example, fault in FAULTS:
        case = read(example)
        if fault == "invert_heat":
            case["heat_into_volume_w"] = 5000.0
            case["shaft_work_out_w"] += 5000.0
        assert check_case(case).status == "PASS_IN_SCOPE", "Fault baseline invalid"
        corrupted = inject_fault(case, fault)
        fault_rows.append({"reference_case": example, "mutation": fault,
                           **compact_report(corrupted)})
    # Deliberately compensating changes: expected to remain undetected, not
    # added to the numerator for any fault-detection effectiveness claim.
    x = copy.deepcopy(read("steady_compressor"))
    for state in x["inlets"] + x["outlets"]:
        state["mass_flow_kg_s"] *= 1.1
    x["shaft_work_out_w"] *= 1.1
    escape = compact_report(x)
    result = {
        "study_type": "hand_constructed_synthetic_software_selftest",
        "disclaimer": (
            "These scenarios and mutations are selected by the developer. Results demonstrate "
            "self-test behavior, NOT measured fault-detection sensitivity, validation, or "
            "superiority against existing software."
        ),
        "baseline_cases": baseline_rows,
        "fault_cases": fault_rows,
        "known_undetectable_compensating_error": escape,
        "summary": {
            "synthetic_baselines_pass": sum(r["status"] == "PASS_IN_SCOPE" for r in baseline_rows),
            "synthetic_baselines_total": len(baseline_rows),
            "deliberate_faults_detected": sum(r["status"] == "FAIL" for r in fault_rows),
            "deliberate_faults_total": len(fault_rows),
            "known_compensating_error_escaped": escape["status"] == "PASS_IN_SCOPE",
        },
    }
    if result["summary"] != {
        "synthetic_baselines_pass": 4,
        "synthetic_baselines_total": 4,
        "deliberate_faults_detected": 6,
        "deliberate_faults_total": 6,
        "known_compensating_error_escaped": True,
    }:
        raise AssertionError("Foundation benchmark outcome changed; inspect ledgers")
    checksum = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    result["ledger_sha256_without_this_field"] = checksum
    return result


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    outcome = run()
    OUT.write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome["summary"], indent=2))
    print("Ledger:", OUT)
