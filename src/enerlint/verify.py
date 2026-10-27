"""Independent balance reconstruction from *exported* SI quantities.

Never imports or calls an upstream energy model/solver. It does not establish
whether an upstream physical model or its original assumptions are correct.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any

from .models import CheckResult, VerificationReport

SCHEMA_VERSION = "0.1.0"
VERSION = "0.1.0a0"
EVIDENCE_CLASSES = frozenset(
    {"hand_constructed", "model_export", "experimental", "published_reference"}
)
GENERAL_LIMITATIONS = (
    "Checks test only the declared physical boundary and supplied SI quantities.",
    "PASS_IN_SCOPE is not model validation, measurement validation, or safety certification.",
    "The source classification is author-declared, not independently authenticated.",
)


class ContractError(ValueError):
    """A supplied case cannot be evaluated under the strict v0.1 contract."""


def fingerprint(payload: Mapping[str, Any]) -> str:
    """Hash the canonical JSON input; does not authenticate the original source."""
    try:
        serialized = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (ValueError, TypeError, OverflowError) as exc:
        raise ContractError("Input is not finite, JSON-serializable data") from exc
    return hashlib.sha256(serialized).hexdigest()


def _mapping(data: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise ContractError(f"{label} must be a JSON object")
    return data


def _fields(data: Mapping[str, Any], label: str, required: set[str], optional: set[str] | None = None) -> None:
    permitted = required | (optional or set())
    missing = required - set(data)
    unexpected = set(data) - permitted
    if missing:
        raise ContractError(f"{label}: missing required field(s): {', '.join(sorted(missing))}")
    if unexpected:
        raise ContractError(f"{label}: unexpected field(s): {', '.join(sorted(unexpected))}")


def _text(data: Mapping[str, Any], key: str, label: str) -> str:
    value = data[key]
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label}.{key} must be a nonempty string")
    return value


def _number(data: Mapping[str, Any], key: str, label: str, *, minimum: float | None = None, strictly_positive: bool = False) -> float:
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label}.{key} must be a finite numeric SI value (not a bool)")
    try:
        output = float(value)
    except (ValueError, OverflowError) as exc:
        raise ContractError(f"{label}.{key} is outside supported numeric range") from exc
    if not math.isfinite(output):
        raise ContractError(f"{label}.{key} must be finite")
    if minimum is not None and output < minimum:
        raise ContractError(f"{label}.{key} must be >= {minimum}")
    if strictly_positive and output <= 0:
        raise ContractError(f"{label}.{key} must be > 0")
    return output


def _common(case: Mapping[str, Any]) -> tuple[str, str, str]:
    if case.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"schema_version must equal {SCHEMA_VERSION!r}")
    case_id = _text(case, "case_id", "case")
    provenance = _mapping(case["provenance"], "provenance")
    _fields(provenance, "provenance", {"evidence_class", "declared_source"})
    evidence_class = _text(provenance, "evidence_class", "provenance")
    if evidence_class not in EVIDENCE_CLASSES:
        raise ContractError("provenance.evidence_class must be one of: " + ", ".join(sorted(EVIDENCE_CLASSES)))
    declared_source = _text(provenance, "declared_source", "provenance")
    return case_id, evidence_class, declared_source


def _tolerance(value: Any, label: str, *, default_abs: float) -> tuple[float, float]:
    if value is None:
        return default_abs, 1e-8
    tolerance = _mapping(value, label)
    _fields(tolerance, label, {"abs", "rel"})
    return (
        _number(tolerance, "abs", label, minimum=0),
        _number(tolerance, "rel", label, minimum=0),
    )


def _check(name: str, description: str, residual: float, scale: float, unit: str, tol: tuple[float, float]) -> CheckResult:
    if not math.isfinite(residual) or not math.isfinite(scale):
        raise ContractError(f"{name}: nonfinite residual/scale (numeric overflow)")
    threshold = max(tol[0], tol[1] * scale)
    if not math.isfinite(threshold):
        raise ContractError(f"{name}: threshold overflow")
    return CheckResult(
        name=name,
        status="PASS" if abs(residual) <= threshold else "FAIL",
        description=description,
        residual=residual,
        unit=unit,
        scale=scale,
        threshold=threshold,
    )



def _finite_sum(terms: Any, label: str) -> float:
    """Sum validated numeric terms; fail closed on unrepresentable aggregates.

    Individual finite SI inputs do not imply their aggregate fits in binary64.
    An ambiguous overflow must be INVALID_INPUT, never a numerical PASS.
    """
    try:
        result = math.fsum(terms)
    except (OverflowError, ValueError) as exc:
        raise ContractError(
            f"{label}: numeric aggregation overflow or loss of representability"
        ) from exc
    if not math.isfinite(result):
        raise ContractError(f"{label}: nonfinite numeric aggregate")
    return result


def _stream_list(value: Any, label: str) -> list[tuple[float, float]]:
    if not isinstance(value, list) or not value:
        raise ContractError(f"{label} must be a nonempty array")
    streams = []
    names = set()
    for idx, item in enumerate(value):
        name = f"{label}[{idx}]"
        stream = _mapping(item, name)
        _fields(stream, name, {"name", "mass_flow_kg_s", "specific_enthalpy_j_kg"})
        stream_name = _text(stream, "name", name)
        if stream_name in names:
            raise ContractError(f"{label}: duplicate stream name {stream_name!r}")
        names.add(stream_name)
        streams.append(
            (
                _number(stream, "mass_flow_kg_s", name, minimum=0),
                _number(stream, "specific_enthalpy_j_kg", name),
            )
        )
    return streams


def _result(
    case: Mapping[str, Any],
    checks: tuple[CheckResult, ...],
    assumptions: tuple[str, ...],
    limitations: tuple[str, ...],
) -> VerificationReport:
    case_id, evidence_class, declared_source = _common(case)
    return VerificationReport(
        schema_version=SCHEMA_VERSION,
        enerlint_version=VERSION,
        case_id=case_id,
        kind=str(case["kind"]),
        status="FAIL" if any(check.status == "FAIL" for check in checks) else "PASS_IN_SCOPE",
        source_fingerprint_sha256=fingerprint(case),
        evidence_class=evidence_class,
        declared_source=declared_source,
        checks=checks,
        assumptions=assumptions,
        limitations=GENERAL_LIMITATIONS + limitations,
    )


def check_steady_control_volume(case: Mapping[str, Any]) -> VerificationReport:
    """Check steady mass and first-law closure using an explicit boundary.

    Sign convention: q_dot > 0 INTO control volume; w_dot > 0 OUT of
    control volume. Work into compressor is therefore NEGATIVE shaft_work_out_w.
    Neglect kinetic/potential energy only when explicitly declared.
    """
    case = _mapping(case, "case")
    _fields(
        case,
        "case",
        {
            "schema_version", "kind", "case_id", "provenance", "assumptions",
            "inlets", "outlets", "heat_into_volume_w", "shaft_work_out_w",
        },
        {"tolerances"},
    )
    if case["kind"] != "steady_control_volume":
        raise ContractError("kind must be 'steady_control_volume'")
    _common(case)
    assumptions = _mapping(case["assumptions"], "assumptions")
    _fields(assumptions, "assumptions", {"steady_state", "neglect_kinetic_potential"})
    if assumptions["steady_state"] is not True or assumptions["neglect_kinetic_potential"] is not True:
        raise ContractError("v0.1 requires explicitly true steady_state and neglect_kinetic_potential assumptions")
    ins = _stream_list(case["inlets"], "inlets")
    outs = _stream_list(case["outlets"], "outlets")
    q = _number(case, "heat_into_volume_w", "case")
    w = _number(case, "shaft_work_out_w", "case")
    tolerances = case.get("tolerances", {})
    tolerances = _mapping(tolerances, "tolerances")
    _fields(tolerances, "tolerances", set(), {"mass_kg_s", "energy_w"})
    mass_tol = _tolerance(tolerances.get("mass_kg_s"), "tolerances.mass_kg_s", default_abs=1e-9)
    energy_tol = _tolerance(tolerances.get("energy_w"), "tolerances.energy_w", default_abs=1.0)
    mass_in = _finite_sum((m for m, _ in ins), "Inlet mass rates")
    mass_out = _finite_sum((m for m, _ in outs), "Outlet mass rates")
    energy_in_terms = [m * h for m, h in ins]
    energy_out_terms = [m * h for m, h in outs]
    if not all(math.isfinite(v) for v in energy_in_terms + energy_out_terms):
        raise ContractError("Transport energy overflow: check SI quantities and numeric magnitudes")
    mass = _check(
        "steady_mass_closure",
        "sum(inlet mass rates) - sum(outlet mass rates) = 0",
        _finite_sum([mass_in, -mass_out], "Steady mass residual"),
        _finite_sum([abs(mass_in), abs(mass_out)], "Steady mass scale"),
        "kg/s",
        mass_tol,
    )
    # Relative tolerance must not inflate merely because an enthalpy-property
    # database uses a different (common) zero datum. Reconstruct a reference
    # from the weighted mean state rather than summing absolute m*h magnitudes.
    # For a mass-conserving boundary, this scale is invariant under a uniform
    # enthalpy datum shift. Different chemical/species datums remain outside
    # v0.1's verification scope.
    mass_total = _finite_sum([mass_in, mass_out], "Total stream mass rate")
    h_reference = (
        _finite_sum(energy_in_terms + energy_out_terms, "Enthalpy reference numerator") / mass_total
        if mass_total > 0 else 0.0
    )
    if not math.isfinite(h_reference):
        raise ContractError("Enthalpy reference calculation overflow")
    energy_scale_terms = [
        m * abs(h - h_reference) for m, h in ins + outs
    ] + [abs(q), abs(w)]
    if not all(math.isfinite(v) for v in energy_scale_terms):
        raise ContractError("Enthalpy deviation scale overflow")
    energy = _check(
        "steady_first_law",
        "sum(m_dot*h)_in - sum(m_dot*h)_out + Q_into - W_out = 0",
        _finite_sum(energy_in_terms + [-v for v in energy_out_terms] + [q, -w], "Steady energy residual"),
        _finite_sum(energy_scale_terms, "Steady energy scale"),
        "W",
        energy_tol,
    )
    return _result(
        case,
        (mass, energy),
        (
            "Steady-state control volume (no mass/energy accumulation).",
            "Kinetic and potential flow-energy terms explicitly neglected.",
            "Positive heat is into volume; positive shaft work is out of volume.",
            "All supplied values declared in SI units; dimensional conversion not performed.",
        ),
        (
            "Does not check fluid equations of state, temperatures, pressures, or phase validity.",
            "Does not prove the equipment model, fluid properties, or boundary is correct.",
            "Heat/work inputs must represent all relevant modeled heat and work crossings.",
        ),
    )


def check_storage_interval(case: Mapping[str, Any]) -> VerificationReport:
    """Verify integrated storage energy in a single constant-rate interval."""
    case = _mapping(case, "case")
    _fields(
        case,
        "case",
        {
            "schema_version", "kind", "case_id", "provenance", "duration_s",
            "energy_initial_j", "energy_final_j", "assumptions", "heat_charge_into_storage_w",
            "heat_discharge_out_storage_w", "heat_loss_out_storage_w",
        },
        {"capacity_j", "tolerances"},
    )
    if case["kind"] != "storage_interval":
        raise ContractError("kind must be 'storage_interval'")
    _common(case)
    assumptions = _mapping(case["assumptions"], "assumptions")
    _fields(assumptions, "assumptions", {"constant_interval_rates"})
    if assumptions["constant_interval_rates"] is not True:
        raise ContractError("v0.1 storage requires explicitly true constant_interval_rates")
    dt = _number(case, "duration_s", "case", strictly_positive=True)
    initial = _number(case, "energy_initial_j", "case", minimum=0)
    final = _number(case, "energy_final_j", "case", minimum=0)
    charge = _number(case, "heat_charge_into_storage_w", "case", minimum=0)
    discharge = _number(case, "heat_discharge_out_storage_w", "case", minimum=0)
    loss = _number(case, "heat_loss_out_storage_w", "case", minimum=0)
    tolerances = _mapping(case.get("tolerances", {}), "tolerances")
    _fields(tolerances, "tolerances", set(), {"energy_j"})
    tol = _tolerance(tolerances.get("energy_j"), "tolerances.energy_j", default_abs=1.0)
    interval_terms = [charge * dt, -discharge * dt, -loss * dt]
    if not all(math.isfinite(v) for v in interval_terms):
        raise ContractError("Integrated energy overflow: check rates and duration")
    delta = _finite_sum([final, -initial], "Storage energy change")
    residual = _finite_sum([delta] + [-v for v in interval_terms], "Storage energy residual")
    scale = _finite_sum([abs(delta)] + [abs(v) for v in interval_terms], "Storage energy scale")
    checks = [
        _check(
            "storage_energy_closure",
            "E_final - E_initial = (Q_charge - Q_discharge - Q_loss) * dt",
            residual, scale, "J", tol,
        )
    ]
    if "capacity_j" in case:
        capacity = _number(case, "capacity_j", "case", strictly_positive=True)
        excursion = max(0.0, initial - capacity, final - capacity)
        checks.append(
            _check("storage_capacity", "0 <= E_initial,E_final <= capacity", excursion, 0.0, "J", (0.0, 0.0))
        )
    else:
        checks.append(
            CheckResult(
                "storage_capacity", "NOT_CHECKED", "No capacity_j supplied; capacity constraint untested"
            )
        )
    return _result(
        case,
        tuple(checks),
        (
            "Constant average rates over the declared interval; SI joules, seconds, watts.",
            "Heat charge into storage >= 0; discharge and loss outward >= 0.",
            "Storage energy is nonnegative relative to the declared zero-energy reference.",
        ),
        (
            "Does not validate storage temperature, exergy, or deliverability constraints.",
            "Does not verify a time-series chronology or inferred sub-interval behavior.",
        ),
    )


def check_case(case: Mapping[str, Any]) -> VerificationReport:
    """Dispatch a strict v0.1 case; fail closed for unsupported types."""
    case = _mapping(case, "case")
    if case.get("kind") == "steady_control_volume":
        return check_steady_control_volume(case)
    if case.get("kind") == "storage_interval":
        return check_storage_interval(case)
    raise ContractError("Unsupported case.kind (supported: steady_control_volume, storage_interval)")
