"""Optional pre-run checklist for the strict v0.1.0 control-volume contract.

This checks completeness and consistency of *author declarations*, not whether
the author correctly identified every physical crossing. It does not change
EnerLint's existing input or report schema or replace a first-law calculation.

Usage:
    python scripts/review_control_volume.py CASE.json REVIEW.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from enerlint import check_case
from enerlint.verify import ContractError, fingerprint

REVIEW_VERSION = "0.1.0"
DECLARATIONS = (
    "all_material_crossings_included",
    "material_port_directions_reviewed",
    "all_heat_crossings_included",
    "all_shaft_work_crossings_included",
    "other_energy_crossings_absent_or_accounted",
    "no_mass_or_energy_accumulation",
    "kinetic_potential_omission_justified",
    "no_unmodeled_reactions_or_mass_sources",
    "enthalpy_references_compatible",
)
REQUIRED = {
    "review_version",
    "case_id",
    "input_sha256",
    "boundary_description",
    "declared_inlets",
    "declared_outlets",
    "declarations",
    "evidence_note",
    "author",
}
OPTIONAL = {"zero_heat_reason", "zero_work_reason"}


def _require(condition: bool, explanation: str) -> None:
    if not condition:
        raise ContractError(f"boundary review: {explanation}")


def _string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    _require(isinstance(value, str) and bool(value.strip()), f"{key} must be nonempty text")
    return value


def _ports(value: Any, name: str) -> list[str]:
    _require(isinstance(value, list) and bool(value), f"{name} must be a nonempty list")
    _require(
        all(isinstance(x, str) and bool(x.strip()) for x in value),
        f"{name} must contain only nonempty port names",
    )
    _require(len(set(value)) == len(value), f"{name} has duplicate port names")
    return value


def review(case: Any, declaration: Any) -> str:
    """Return the *separate* physical report status when declared preflight is complete.

    Raises ContractError for an incorrect, stale or incomplete review. A
    DECLARATION_COMPLETE result means only that every required question was
    answered and structurally matched the supplied case; it is not independent
    evidence that the physical boundary is right.
    """
    _require(isinstance(case, dict), "case must be a JSON object")
    _require(case.get("kind") == "steady_control_volume", "only steady_control_volume is supported")
    # Fail closed on unsupported/malformed case input; physical FAIL is allowed.
    physical = check_case(case)
    _require(isinstance(declaration, dict), "review must be a JSON object")
    keys = set(declaration)
    missing, unknown = REQUIRED - keys, keys - REQUIRED - OPTIONAL
    _require(not missing, f"missing review fields: {', '.join(sorted(missing))}")
    _require(not unknown, f"unexpected review fields: {', '.join(sorted(unknown))}")
    _require(
        declaration["review_version"] == REVIEW_VERSION,
        f"review_version must equal {REVIEW_VERSION}",
    )
    _require(declaration["case_id"] == case["case_id"], "case_id does not match input case")
    digest = _string(declaration, "input_sha256")
    _require(bool(re.fullmatch(r"[a-f0-9]{64}", digest)), "input_sha256 must be lowercase SHA-256")
    _require(digest == fingerprint(case), "input_sha256 mismatch (review is stale or for another input)")
    for key in ("boundary_description", "evidence_note", "author"):
        _string(declaration, key)
    for key, source in (("declared_inlets", "inlets"), ("declared_outlets", "outlets")):
        stated = _ports(declaration[key], key)
        actual = [stream["name"] for stream in case[source]]
        _require(set(stated) == set(actual), f"{key} do not match the input's {source} names")
    answers = declaration["declarations"]
    _require(isinstance(answers, dict), "declarations must be an object")
    _require(set(answers) == set(DECLARATIONS), "declarations must answer exactly the required questions")
    for name in DECLARATIONS:
        _require(answers[name] is True, f"declarations.{name} is not explicitly true")
    if case["heat_into_volume_w"] == 0:
        _string(declaration, "zero_heat_reason")
    if case["shaft_work_out_w"] == 0:
        _string(declaration, "zero_work_reason")
    return physical.status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check completeness of an author-declared thermal boundary")
    parser.add_argument("case", type=Path)
    parser.add_argument("review", type=Path)
    args = parser.parse_args(argv)
    try:
        case = json.loads(args.case.read_text(encoding="utf-8"))
        declaration = json.loads(args.review.read_text(encoding="utf-8"))
        physical_status = review(case, declaration)
    except (OSError, UnicodeError, json.JSONDecodeError, ContractError) as exc:
        print(f"BOUNDARY_REVIEW_INCOMPLETE: {exc}", file=sys.stderr)
        return 2
    print(
        f"DECLARATION_COMPLETE: {case['case_id']} | physical_check={physical_status}\n"
        "AUTHOR ATTESTATION ONLY: completeness of the real physical boundary is not established."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
