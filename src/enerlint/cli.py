"""CLI exit codes: 0 PASS_IN_SCOPE; 1 physical failed checks; 2 invalid input."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import VerificationReport
from .verify import ContractError, VERSION, check_case


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="enerlint", description="Independently check declared energy-engineering output cases"
    )
    parser.add_argument("--version", action="version", version=f"enerlint {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Check strict SI JSON case")
    check.add_argument("input", type=Path, help="Case JSON document")
    check.add_argument("--output", type=Path, help="Save report as JSON, else print to stdout")
    args = parser.parse_args(argv)
    if args.command != "check":
        return 2
    try:
        raw = args.input.read_text(encoding="utf-8")
        case = json.loads(raw)
        result = check_case(case)
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"INVALID_INPUT: {exc}", file=sys.stderr)
        return 2
    data = json.dumps(result.as_dict(), indent=2, allow_nan=False) + "\n"
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(data, encoding="utf-8")
        except OSError as exc:
            print(f"REPORT_WRITE_ERROR: {exc}", file=sys.stderr)
            return 2
        print(f"{result.status}: {result.case_id} | report: {args.output}")
    else:
        print(data, end="")
    return 0 if result.status == "PASS_IN_SCOPE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
