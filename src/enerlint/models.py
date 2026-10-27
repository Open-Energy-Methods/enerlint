"""Versioned, immutable report objects; not a scientific validity certificate."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

CheckStatus = Literal["PASS", "FAIL", "NOT_CHECKED"]
ReportStatus = Literal["PASS_IN_SCOPE", "FAIL", "INVALID_INPUT"]


def _json_ready(data: dict[str, Any]) -> dict[str, Any]:
    """Convert immutable report tuples into JSON-native arrays.

    dataclasses.asdict preserves tuple containers, but a report returned by
    the Python API must match the published JSON Schema without serialization.
    """
    for name in ("checks", "assumptions", "limitations", "errors"):
        data[name] = list(data[name])
    return data



@dataclass(frozen=True)
class CheckResult:
    name: str
    status: CheckStatus
    description: str
    residual: float | None = None
    unit: str | None = None
    scale: float | None = None
    threshold: float | None = None


@dataclass(frozen=True)
class VerificationReport:
    # The alpha keeps the existing schema_version value and field layout.
    # The machine-readable contract lives in schemas/report-v0.1.0.schema.json.
    schema_version: str
    enerlint_version: str
    case_id: str
    kind: str
    status: ReportStatus
    source_fingerprint_sha256: str
    evidence_class: str
    declared_source: str
    checks: tuple[CheckResult, ...]
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
    errors: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Produce the frozen v0.1.0 field layout; no implicit skipped-check passes."""
        return _json_ready(asdict(self))

    def assert_passed(self) -> None:
        """Fail a pipeline if any check failed or if no check was evaluated."""
        if (
            self.status != "PASS_IN_SCOPE"
            or not any(check.status == "PASS" for check in self.checks)
            or any(check.status == "FAIL" for check in self.checks)
        ):
            raise AssertionError(f"{self.case_id}: {self.status}; errors={self.errors}")


@dataclass(frozen=True)
class InvalidInputReport:
    """Machine-readable rejection: no unverified metadata is treated as trusted.

    CLI --output uses this object when input cannot be read, parsed, or checked.
    Without --output, the existing stderr and exit-code-2 behavior remains.
    """

    schema_version: str
    enerlint_version: str
    errors: tuple[str, ...]
    case_id: None = None
    kind: None = None
    status: Literal["INVALID_INPUT"] = "INVALID_INPUT"
    source_fingerprint_sha256: None = None
    evidence_class: None = None
    declared_source: None = None
    checks: tuple[()] = ()
    assumptions: tuple[()] = ()
    limitations: tuple[str, ...] = (
        "No physical checks performed: input was rejected.",
    )

    def as_dict(self) -> dict[str, Any]:
        """Avoid fabricating a case ID, provenance or fingerprint for invalid input."""
        return _json_ready(asdict(self))


def serialize_report(report: VerificationReport | InvalidInputReport) -> str:
    """Deterministic JSON bytes for an unchanged report object (no timestamps).

    Key order is canonicalized for output; the separate input fingerprint uses
    the established compact canonical JSON representation in verify.py.
    """
    return json.dumps(report.as_dict(), sort_keys=True, indent=2, allow_nan=False) + "\n"
