"""CLI exit codes: 0 PASS_IN_SCOPE; 1 physical failed checks; 2 invalid input."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import InvalidInputReport, serialize_report
from .verify import ContractError, SCHEMA_VERSION, VERSION, check_case


def _save_report(destination: Path, contents: str) -> bool:
    """Write a JSON artifact, with a clear failure if the path is unusable."""
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents, encoding="utf-8", newline="\n")
    except OSError as exc:
        print(f"REPORT_WRITE_ERROR: {exc}", file=sys.stderr)
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="enerlint", description="Independently check declared energy-engineering output cases"
    )
    parser.add_argument("--version", action="version", version=f"enerlint {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Check strict SI JSON case")
    check.add_argument("input", type=Path, help="Case JSON document")
    check.add_argument(
        "--output", type=Path,
        help="Save schema-versioned JSON, including INVALID_INPUT reports, to this path",
    )
    args = parser.parse_args(argv)
    if args.command != "check":
        return 2
    try:
        raw = args.input.read_text(encoding="utf-8")
        case = json.loads(raw)
        result = check_case(case)
    except (OSError, UnicodeError, json.JSONDecodeError, ContractError) as exc:
        print(f"INVALID_INPUT: {exc}", file=sys.stderr)
        if args.output:
            rejected = InvalidInputReport(
                schema_version=SCHEMA_VERSION,
                enerlint_version=VERSION,
                errors=(str(exc),),
            )
            if not _save_report(args.output, serialize_report(rejected)):
                return 2
        return 2

    data = serialize_report(result)
    if args.output:
        if not _save_report(args.output, data):
            return 2
        print(f"{result.status}: {result.case_id} | report: {args.output}")
    else:
        print(data, end="")
    return 0 if result.status == "PASS_IN_SCOPE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
