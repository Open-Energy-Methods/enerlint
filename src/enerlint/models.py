"""Immutable, machine-readable results. No inference of certification or external validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

CheckStatus = Literal["PASS", "FAIL", "NOT_CHECKED"]
ReportStatus = Literal["PASS_IN_SCOPE", "FAIL", "INVALID_INPUT"]


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
        """Return JSON-serializable data for stable, auditable reporting."""
        return asdict(self)

    def assert_passed(self) -> None:
        """Fail an engineering CI pipeline when declared checks do not pass."""
        if self.status != "PASS_IN_SCOPE":
            raise AssertionError(f"{self.case_id}: {self.status}; errors={self.errors}")
