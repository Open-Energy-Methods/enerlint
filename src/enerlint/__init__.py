"""EnerLint: solver-independent, scope-limited energy engineering checks."""

from .models import CheckResult, VerificationReport
from .verify import check_case, check_steady_control_volume, check_storage_interval

__all__ = [
    "CheckResult",
    "VerificationReport",
    "check_case",
    "check_steady_control_volume",
    "check_storage_interval",
]

__version__ = "0.1.0a0"
