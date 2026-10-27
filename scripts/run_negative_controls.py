"""Replay frozen developer-authored negative controls and preserve escapes.

Only experiments in docs/negative_controls_v0.1.json are executed. The manifest
was assembled before first CI run of this suite; it is NOT externally
preregistered, blind, or a real-world fault-detection effectiveness estimate.

Usage from repository root:
    python scripts/run_negative_controls.py
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from enerlint import check_case  # noqa: E402
from enerlint.verify import ContractError  # noqa: E402
from scripts.run_analytical_catalog import independent_arithmetic  # noqa: E402

CATALOG = ROOT / "docs" / "negative_controls_v0.1.json"
LEDGER = ROOT / "artifacts" / "ci" / "negative_controls_v0.1.json"
CLASSES = {"fault", "schema_probe", "blind_spot", "metadata_only", "clean_control"}
OPS = {"set", "remove", "batch", "swap", "append", "append_clone",
       "scale_all_flows_and_work", "nonfinite"}


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def git_blob_hash(raw: bytes) -> str:
    # GitHub's blob SHA refers to the LF text stored in the Git index.
    # A Windows working-tree checkout can transparently convert LF -> CRLF.
    # Only normalize that newline representation; actual JSON content changes
    # still alter the pinned blob identifier.
    canonical = raw.replace(b"\r\n", b"\n")
    return hashlib.sha1(
        b"blob " + str(len(canonical)).encode("ascii") + b"\x00" + canonical
    ).hexdigest()


def _get(data: Any, path: str) -> Any:
    part: Any = data
    for key in path.split("."):
        part = part[int(key)] if isinstance(part, list) else part[key]
    return part


def _parent(data: Any, path: str) -> tuple[Any, str]:
    keys = path.split(".")
    if not keys or any(not x for x in keys):
        raise AssertionError("Bad mutation path")
    parent = _get(data, ".".join(keys[:-1])) if len(keys) > 1 else data
    return parent, keys[-1]


def apply_mutation(case: dict[str, Any], instruction: dict[str, Any]) -> dict[str, Any]:
    """Minimal deterministic data-only operator language (no arbitrary execution)."""
    mutated = copy.deepcopy(case)

    def assign(path: str, value: Any) -> None:
        parent, key = _parent(mutated, path)
        if isinstance(parent, list):
            parent[int(key)] = value
        else:
            parent[key] = value

    def remove(path: str) -> None:
        parent, key = _parent(mutated, path)
        if isinstance(parent, list):
            parent.pop(int(key))
        else:
            del parent[key]

    def execute(op: dict[str, Any]) -> None:
        kind = op["op"]
        if kind not in OPS:
            raise AssertionError(f"Unregistered mutation operator: {kind}")
        if kind == "set":
            assign(op["path"], op["value"])
        elif kind == "remove":
            remove(op["path"])
        elif kind == "batch":
            for sub in op["items"]:
                execute(sub)
        elif kind == "swap":
            a, b = op["path_a"], op["path_b"]
            left, right = copy.deepcopy(_get(mutated, a)), copy.deepcopy(_get(mutated, b))
            assign(a, right)
            assign(b, left)
        elif kind == "append":
            _get(mutated, op["path"]).append(copy.deepcopy(op["value"]))
        elif kind == "append_clone":
            values = _get(mutated, op["path"])
            value = copy.deepcopy(values[op["index"]])
            value.update(op["patch"])
            values.append(value)
        elif kind == "scale_all_flows_and_work":
            factor = op["factor"]
            if not isinstance(factor, (int, float)) or factor <= 0 or not math.isfinite(factor):
                raise AssertionError("Invalid scale factor")
            for row in mutated["inlets"] + mutated["outlets"]:
                row["mass_flow_kg_s"] *= factor
            mutated["shaft_work_out_w"] *= factor
        elif kind == "nonfinite":
            if op["special"] not in ("NaN", "Infinity"):
                raise AssertionError("Unrecognized nonfinite probe")
            assign(op["path"], float("nan") if op["special"] == "NaN" else float("inf"))

    execute(instruction)
    if mutated == case and instruction["op"] != "nonfinite":
        raise AssertionError("Mutation did not change the baseline input")
    return mutated


def tagged_nonfinite(value: Any) -> Any:
    """Save intentionally invalid numeric inputs in *valid* JSON for replay."""
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return {"$nonfinite_python_value": "NaN"}
        return {"$nonfinite_python_value": "Infinity" if value > 0 else "-Infinity"}
    if isinstance(value, dict):
        return {k: tagged_nonfinite(v) for k, v in value.items()}
    if isinstance(value, list):
        return [tagged_nonfinite(v) for v in value]
    return value


def equal_number(observed: Any, expected: Any, label: str) -> None:
    if expected is None:
        if observed is not None:
            raise AssertionError(f"{label}: expected unevaluated/null")
        return
    if not math.isclose(float(observed), float(expected), rel_tol=2e-12, abs_tol=1e-6):
        raise AssertionError(f"{label}: observed {observed!r}; frozen {expected!r}")


def oracle_status(arithmetic: dict[str, dict[str, Any]]) -> str:
    return (
        "FAIL" if any(
            row["status"] == "FAIL" for name, row in arithmetic.items()
            if not name.startswith("_")
        ) else "PASS_IN_SCOPE"
    )


def run() -> dict[str, Any]:
    raw = CATALOG.read_bytes()
    doc = json.loads(raw)
    cases = doc["cases"]
    ids = [row["id"] for row in cases]
    if doc["version"] != "0.1.0" or ids != [
        f"NC-{i:03d}" for i in range(1, 40)
    ] or doc["mutation_seed"] != "OEM-NC11-DETERMINISTIC-V0.1-NO-RNG":
        raise AssertionError("Unexpected unfrozen negative-control catalogue revision")
    sources = {}
    for name, entry in doc["baselines"].items():
        path = ROOT / entry["file"]
        if path != ROOT / "examples" / (name + ".json"):
            raise AssertionError("A baseline path escaped the examples directory")
        content = path.read_bytes()
        if git_blob_hash(content) != entry["git_blob_sha1"]:
            raise AssertionError(f"Baseline fixture changed without new catalogue version: {name}")
        base = json.loads(content)
        report = check_case(base)
        if report.status != "PASS_IN_SCOPE":
            raise AssertionError(f"{name}: clean baseline stopped passing")
        sources[name] = {
            "case": base,
            "source_blob_sha1": entry["git_blob_sha1"],
            "case_sha256": report.source_fingerprint_sha256,
        }

    rows = []
    for row in cases:
        if row["kind"] not in CLASSES or row["base"] not in sources:
            raise AssertionError(f"{row['id']}: unregistered source or scenario class")
        base = sources[row["base"]]["case"]
        changed = apply_mutation(base, row["change"])
        archived = tagged_nonfinite(changed)
        serialized_input_hash = canonical_hash(archived)
        directive_hash = canonical_hash(row["change"])
        outcome = row["expected_outcome"]
        check_list = []
        diagnostic = None

        if outcome == "INVALID_INPUT":
            try:
                check_case(changed)
            except ContractError as exc:
                diagnostic = str(exc)
            else:
                raise AssertionError(f"{row['id']}: invalid contract was silently accepted")
            if row["kind"] != "schema_probe" or row["focus_check"] is not None:
                raise AssertionError(f"{row['id']}: malformed input must not be a physics fault")
            observed = "INVALID_INPUT"
        else:
            reference = independent_arithmetic(changed)
            actual = check_case(changed)
            if oracle_status(reference) != outcome or actual.status != outcome:
                raise AssertionError(f"{row['id']}: expected {outcome}, got {actual.status}")
            for check in actual.checks:
                expected = reference[check.name]
                if check.status != expected["status"] or check.unit != expected["unit"]:
                    raise AssertionError(f"{row['id']} {check.name}: independent status/unit mismatch")
                for field in ("residual", "scale", "threshold"):
                    equal_number(getattr(check, field), expected[field],
                                 f"{row['id']} {check.name}.{field}")
                check_list.append({
                    "name": check.name, "status": check.status, "residual": check.residual,
                    "scale": check.scale, "threshold": check.threshold, "unit": check.unit,
                })

            arithmetic = row["expected_arithmetic"]
            if changed["kind"] == "steady_control_volume":
                mapping = {
                    "mass_residual_kg_s": ("steady_mass_closure", "residual"),
                    "mass_threshold_kg_s": ("steady_mass_closure", "threshold"),
                    "energy_residual_w": ("steady_first_law", "residual"),
                    "energy_threshold_w": ("steady_first_law", "threshold"),
                }
            else:
                mapping = {
                    "storage_residual_j": ("storage_energy_closure", "residual"),
                    "storage_threshold_j": ("storage_energy_closure", "threshold"),
                    "capacity_excursion_j": ("storage_capacity", "residual"),
                }
            for field, (check_name, key) in mapping.items():
                if field not in arithmetic:
                    raise AssertionError(f"{row['id']} missing prespecified {field}")
                equal_number(reference[check_name][key], arithmetic[field],
                             f"{row['id']} prespecified {field}")
            by_name = {c.name: c for c in actual.checks}
            if row["focus_check"] is not None:
                focused = by_name[row["focus_check"]]
                expected_check_status = (
                    "FAIL" if outcome == "FAIL" else
                    "NOT_CHECKED" if row["family"] == "missing_optional" else "PASS"
                )
                if focused.status != expected_check_status:
                    raise AssertionError(f"{row['id']} expected {expected_check_status} check")
            observed = actual.status
            if row["kind"] == "fault" and observed != "FAIL":
                raise AssertionError("A declared arithmetic-breaking fault was not caught")
            if row["kind"] in ("blind_spot", "metadata_only", "clean_control") and observed != "PASS_IN_SCOPE":
                raise AssertionError("A predeclared passing control/blind spot was flagged")

        rows.append({
            "id": row["id"], "family": row["family"], "scenario_kind": row["kind"],
            "baseline": row["base"], "base_git_blob_sha1": sources[row["base"]]["source_blob_sha1"],
            "base_case_sha256": sources[row["base"]]["case_sha256"],
            "mutator": row["change"], "mutator_sha256": directive_hash,
            "mutated_case_tagged": archived, "mutated_case_sha256_tagged": serialized_input_hash,
            "expected_status": outcome, "observed_status": observed,
            "focus_check": row["focus_check"],
            "checks": check_list, "input_rejection": diagnostic,
            "interpretation": row["interpretation"],
            "limitations": (
                "No independent physical ground truth; scenario is synthetic. "
                "Nonfinite numeric values in tagged archives require decoder treatment."
            ),
        })

    counts = Counter(x["scenario_kind"] for x in rows)
    expected_counts = {
        "fault": 18, "schema_probe": 11, "blind_spot": 6,
        "metadata_only": 1, "clean_control": 3,
    }
    if dict(counts) != expected_counts:
        raise AssertionError(f"Unexpected frozen scenario distribution: {dict(counts)}")
    summary = {
        "total_cases": len(rows),
        "declared_balance_faults_flagged": counts["fault"],
        "invalid_contracts_rejected_without_physics": counts["schema_probe"],
        "developer_known_escapes": counts["blind_spot"],
        "unobservable_metadata_only_changes": counts["metadata_only"],
        "healthy_transformations_remain_in_scope": counts["clean_control"],
        "independent_external_reviews": 0,
    }
    return {
        "catalog_id": doc["catalog_id"], "catalog_version": doc["version"],
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "mutation_seed": doc["mutation_seed"],
        "design_status": doc["prespecification_status"],
        "summary": summary,
        "cases": rows,
        "scientific_limitations": [
            "Developer-selected faults and clean transformations; no blind or external ground truth.",
            "These counts are not measured real-world sensitivity, specificity, accuracy or safety rates.",
            "Unsupported timestamp/time-step fields reject as invalid; no chronology validation exists.",
            "An unreported physical crossing cannot be inferred from JSON alone.",
            "PASS_IN_SCOPE can include compensated/undetectable errors and nonzero tolerated residuals.",
        ],
    }


def main() -> int:
    output = run()
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n",
                      encoding="utf-8")
    print(json.dumps(output["summary"], indent=2, sort_keys=True))
    print(f"Reproducible fault ledger: {LEDGER.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
