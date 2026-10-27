"""Freeze/replay developer-selected Decimal-vs-binary64 conditioning cases.

Case numerical edits are decimal *text* inserted as JSON number tokens, not
pre-rounded through binary64. This matters for testing lost input precision.
No external scientific reviewer is implied.

Run: python scripts/run_tolerance_precision_stress.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.audit_numeric_conditioning import audit_text  # noqa: E402

CATALOG = ROOT / "docs" / "tolerance_precision_cases_v0.1.json"
OUTPUT = ROOT / "artifacts" / "ci" / "tolerance_precision_stress_v0.1.json"
NUMBER = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$")


def text_case(base: dict, edits: list[dict]) -> str:
    """Safely substitute strictly validated decimal literals after serialization."""
    obj = json.loads(json.dumps(base))
    tokens: dict[str, str] = {}
    for n, edit in enumerate(edits):
        value = edit["decimal"]
        if not isinstance(value, str) or not NUMBER.fullmatch(value):
            raise AssertionError("Invalid predeclared JSON numeric literal")
        token = f"__NUMERIC_STRESS_TOKEN_{n}__"
        parts = edit["path"].split(".")
        target = obj
        for p in parts[:-1]:
            target = target[int(p)] if isinstance(target, list) else target[p]
        key = int(parts[-1]) if isinstance(target, list) else parts[-1]
        if key not in target if not isinstance(target, list) else key >= len(target):
            raise AssertionError("Unknown stress mutation field")
        target[key] = token
        tokens[token] = value
    rendered = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    for token, value in tokens.items():
        rendered = rendered.replace('"' + token + '"', value)
    json.loads(rendered)  # check syntax; this need not preserve large precision
    return rendered


def run() -> dict:
    raw = CATALOG.read_bytes()
    data = json.loads(raw)
    scenarios = data["cases"]
    if data["version"] != "0.1.0" or [x["id"] for x in scenarios] != [
        f"TP-{i:03d}" for i in range(1, 11)
    ]:
        raise AssertionError("Frozen precision stress case list changed")
    ledger = []
    for scenario in scenarios:
        name = scenario["base"]
        if name not in ("steady_compressor", "storage_interval"):
            raise AssertionError("Unregistered source baseline")
        filename = ROOT / "examples" / (name + ".json")
        source = json.loads(filename.read_text(encoding="utf-8"))
        text = text_case(source, scenario["edits"])
        result = audit_text(text)
        actual_exact = None
        if result["evaluated"]:
            statuses = [x["exact_decimal_status"] for x in result["checks"]]
            actual_exact = "FAIL" if "FAIL" in statuses else "PASS_IN_SCOPE"
        expected = (
            scenario["expected_classification"],
            scenario["expected_decimal_status"],
            scenario["expected_core_status"],
        )
        actual = (result["classification"], actual_exact, result["core_status"])
        if expected != actual:
            raise AssertionError(f"{scenario['id']} changed: expected {expected}, actual {actual}")
        ledger.append({
            "id": scenario["id"],
            "source_file": str(filename.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256": hashlib.sha256(
                filename.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest(),
            "submitted_json": text,
            "submitted_json_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "expected": {
                "classification": expected[0],
                "decimal_status": expected[1],
                "core_status": expected[2],
            },
            "observation": result,
            "interpretation": scenario["interpretation"],
        })
    counts = dict(Counter(row["observation"]["classification"] for row in ledger))
    if counts != {
        "DECIMAL_BINARY_AGREEMENT": 7,
        "DECISION_DISAGREEMENT": 2,
        "CORE_REJECTED": 1,
    }:
        raise AssertionError(f"Unexpected stress study classifications: {counts}")
    return {
        "catalog": data["catalog_id"],
        "version": data["version"],
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "study_type": "developer-selected numerical arithmetic stress, not independent physical validation",
        "summary": {"total": len(ledger), **counts, "independent_external_reviews": 0},
        "cases": ledger,
        "limits": data["caveats"],
    }


def main() -> int:
    result = run()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
                      encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"Numerical stress evidence: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
