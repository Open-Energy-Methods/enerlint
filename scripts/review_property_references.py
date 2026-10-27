"""Optional author-declared thermophysical reference review for EnerLint v0.1.

Run from an installed developer checkout, not as a property-model calculation:
    python scripts/review_property_references.py CASE.json REVIEW.json

The review checks declared metadata and independently balanced groups. It
neither validates a real fluid property nor changes the v0.1 case/report schema.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from enerlint import check_case
from enerlint.verify import ContractError, fingerprint

REVIEW_VERSION = "0.1.0"
REQUIRED = frozenset({
    "review_version", "case_id", "input_sha256", "author",
    "basis_note", "stream_properties",
})
PROPERTY_FIELDS = frozenset({
    "direction", "name", "circuit_id", "fluid_id", "composition_id",
    "backend_id", "backend_version", "reference_state_id", "source_note",
})
BASIS_FIELDS = (
    "fluid_id", "composition_id", "backend_id", "backend_version",
    "reference_state_id",
)


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ContractError(f"property review: {detail}")


def nonempty(value: Any, label: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")
    return value


def finite_group_sum(numbers: list[float], label: str) -> float:
    try:
        value = math.fsum(numbers)
    except (ValueError, OverflowError) as exc:
        raise ContractError(f"property review: {label} is not representable") from exc
    require(math.isfinite(value), f"{label} is not finite")
    return value


def review(case: Any, declaration: Any) -> str:
    """Return original numeric status *only after* declaration consistency checks.

    Even when this returns PASS_IN_SCOPE, declared property authenticity and
    thermodynamic state admissibility remain unverified. Raises ContractError
    for unknown/incompatible metadata or unsupported circuits.
    """
    require(isinstance(case, dict), "case must be a JSON object")
    require(case.get("kind") == "steady_control_volume", "only steady_control_volume is supported")
    numeric_report = check_case(case)  # Invalid inputs fail before interpreting metadata.

    require(isinstance(declaration, dict), "review must be a JSON object")
    require(
        set(declaration) == REQUIRED,
        "review must contain exactly the required fields (missing/unknown fields are rejected)",
    )
    require(declaration["review_version"] == REVIEW_VERSION, "review_version mismatch")
    require(declaration["case_id"] == case["case_id"], "case_id does not match input")
    digest = nonempty(declaration["input_sha256"], "input_sha256")
    require(bool(re.fullmatch(r"[a-f0-9]{64}", digest)), "input_sha256 is not a SHA-256 hex digest")
    require(digest == fingerprint(case), "input_sha256 mismatch: stale or incorrect review")
    for key in ("author", "basis_note"):
        nonempty(declaration[key], key)

    properties = declaration["stream_properties"]
    require(isinstance(properties, list) and len(properties) > 0, "stream_properties must be a nonempty array")
    case_ports = {
        (direction, port["name"]): port["mass_flow_kg_s"]
        for direction, key in (("inlet", "inlets"), ("outlet", "outlets"))
        for port in case[key]
    }
    require(len(case_ports) == len(case["inlets"]) + len(case["outlets"]), "ambiguous repeated stream names")
    metadata_by_port: dict[tuple[str, str], dict[str, Any]] = {}
    for idx, row in enumerate(properties):
        require(isinstance(row, dict), f"stream_properties[{idx}] must be an object")
        require(set(row) == PROPERTY_FIELDS, f"stream_properties[{idx}] has missing or unknown fields")
        for key in PROPERTY_FIELDS:
            nonempty(row[key], f"stream_properties[{idx}].{key}")
        direction = row["direction"]
        require(direction in ("inlet", "outlet"), f"stream_properties[{idx}].direction unsupported")
        identity = (direction, row["name"])
        require(identity in case_ports, f"undeclared stream {identity!r}")
        require(identity not in metadata_by_port, f"duplicated stream metadata {identity!r}")
        metadata_by_port[identity] = row
    require(set(metadata_by_port) == set(case_ports), "stream_properties missing a material port")

    circuits: dict[str, list[tuple[tuple[str, str], dict[str, Any]]]] = defaultdict(list)
    for identity, row in metadata_by_port.items():
        circuits[row["circuit_id"]].append((identity, row))

    for circuit_id, rows in circuits.items():
        basis = tuple(rows[0][1][key] for key in BASIS_FIELDS)
        for _, row in rows[1:]:
            require(
                tuple(row[key] for key in BASIS_FIELDS) == basis,
                f"circuit {circuit_id!r} has mismatched fluid/composition/backend/reference basis",
            )
        ins = [float(case_ports[identity]) for identity, _ in rows if identity[0] == "inlet"]
        outs = [float(case_ports[identity]) for identity, _ in rows if identity[0] == "outlet"]
        require(bool(ins and outs), f"circuit {circuit_id!r} requires both inlet and outlet")
        in_total = finite_group_sum(ins, f"circuit {circuit_id} inlet mass")
        out_total = finite_group_sum(outs, f"circuit {circuit_id} outlet mass")
        scale = finite_group_sum([abs(in_total), abs(out_total)], f"circuit {circuit_id} mass scale")
        require(
            abs(in_total - out_total) <= max(1e-9, 1e-8 * scale),
            f"circuit {circuit_id!r} is not mass-closed: independent datum offsets are unsafe",
        )

    return numeric_report.status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check author-declared property-reference metadata; not a fluid property validator"
    )
    parser.add_argument("case", type=Path)
    parser.add_argument("review", type=Path)
    args = parser.parse_args(argv)
    try:
        case = json.loads(args.case.read_text(encoding="utf-8"))
        declaration = json.loads(args.review.read_text(encoding="utf-8"))
        physical_status = review(case, declaration)
    except (OSError, UnicodeError, json.JSONDecodeError, ContractError) as exc:
        print(f"PROPERTY_REVIEW_INCOMPLETE: {exc}", file=sys.stderr)
        return 2
    print(
        f"PROPERTY_DECLARATION_COMPLETE: {case['case_id']} | physical_check={physical_status}\n"
        "AUTHOR ATTESTATION ONLY: fluid identity, reference state and source data are not authenticated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
