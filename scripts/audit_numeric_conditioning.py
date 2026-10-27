"""Optional precision preflight for the *actual decimal numbers in a JSON file*.

This does not change EnerLint's frozen v0.1 report or decision. It compares
decimal-text arithmetic, exact arithmetic on binary64-quantized input operands,
and the core's binary64 result. It can reveal decision disagreements but
cannot bound uncertainty in the upstream measurements or identify actual
fluid-property reference states.

Usage: python scripts/audit_numeric_conditioning.py examples/steady_compressor.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from enerlint import check_case  # noqa: E402
from enerlint.verify import ContractError  # noqa: E402


def _bad_json_number(value: str) -> None:
    raise ValueError(f"Nonstandard JSON numeric constant {value} is unsupported")


def _decimal(v: int | float | Decimal) -> Decimal:
    if isinstance(v, Decimal):
        return v
    if isinstance(v, float):
        return Decimal.from_float(v)
    return Decimal(v)


def _threshold(kind: str, key: str, case: dict[str, Any]) -> tuple[Decimal, Decimal]:
    tolerances = case.get("tolerances", {})
    entry = tolerances.get(key)
    default_abs = Decimal("1e-9") if kind == "mass" else Decimal(1)
    return (
        _decimal(entry["abs"]) if entry is not None else default_abs,
        _decimal(entry["rel"]) if entry is not None else Decimal("1e-8"),
    )


def _calculate(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Use high precision for the *declared numeric inputs*, not core internals."""
    with localcontext() as ctx:
        ctx.prec = 90
        if case["kind"] == "steady_control_volume":
            inlet = [(_decimal(p["mass_flow_kg_s"]),
                      _decimal(p["specific_enthalpy_j_kg"])) for p in case["inlets"]]
            outlet = [(_decimal(p["mass_flow_kg_s"]),
                       _decimal(p["specific_enthalpy_j_kg"])) for p in case["outlets"]]
            mi = sum((m for m, _ in inlet), Decimal(0))
            mo = sum((m for m, _ in outlet), Decimal(0))
            h_in = sum((m * h for m, h in inlet), Decimal(0))
            h_out = sum((m * h for m, h in outlet), Decimal(0))
            q, w = _decimal(case["heat_into_volume_w"]), _decimal(case["shaft_work_out_w"])
            mass_scale = mi + mo
            center = (h_in + h_out) / mass_scale if mass_scale else Decimal(0)
            energy_scale = (
                sum((m * abs(h - center) for m, h in inlet + outlet), Decimal(0))
                + abs(q) + abs(w)
            )
            m_abs, m_rel = _threshold("mass", "mass_kg_s", case)
            e_abs, e_rel = _threshold("energy", "energy_w", case)
            checks = {
                "steady_mass_closure": (mi - mo, max(m_abs, m_rel * mass_scale)),
                "steady_first_law": (
                    h_in - h_out + q - w,
                    max(e_abs, e_rel * energy_scale),
                ),
            }
        elif case["kind"] == "storage_interval":
            dt = _decimal(case["duration_s"])
            initial, final = _decimal(case["energy_initial_j"]), _decimal(case["energy_final_j"])
            charge = _decimal(case["heat_charge_into_storage_w"]) * dt
            discharge = _decimal(case["heat_discharge_out_storage_w"]) * dt
            loss = _decimal(case["heat_loss_out_storage_w"]) * dt
            delta = final - initial
            scale = abs(delta) + abs(charge) + abs(discharge) + abs(loss)
            e_abs, e_rel = _threshold("energy", "energy_j", case)
            checks = {
                "storage_energy_closure": (
                    delta - charge + discharge + loss, max(e_abs, e_rel * scale)
                ),
            }
            if "capacity_j" in case:
                cap = _decimal(case["capacity_j"])
                checks["storage_capacity"] = (
                    max(Decimal(0), initial - cap, final - cap), Decimal(0)
                )
        else:
            raise ValueError("Unknown supported case type")

        return {
            key: {
                "residual": residual,
                "threshold": threshold,
                "status": "PASS" if abs(residual) <= threshold else "FAIL",
            }
            for key, (residual, threshold) in checks.items()
        }


def audit_text(text: str) -> dict[str, Any]:
    """Three-way numerical comparison with no modification to core result."""
    try:
        encoded = json.loads(text, parse_float=Decimal, parse_int=int,
                             parse_constant=_bad_json_number)
        binary = json.loads(text, parse_constant=_bad_json_number)
        report = check_case(binary)
    except (ContractError, ValueError, TypeError, OverflowError) as exc:
        return {
            "classification": "CORE_REJECTED",
            "core_status": "INVALID_INPUT",
            "reason": str(exc),
            "evaluated": False,
            "checks": [],
            "note": "A rejected input has no physical PASS or FAIL.",
        }

    exact = _calculate(encoded)
    quantized = _calculate(binary)
    observed = {item.name: item for item in report.checks}
    rows = []
    disagreement = False
    caution = False
    for name, reference in exact.items():
        core = observed[name]
        binary_input = quantized[name]
        # Decimal.from_float captures the *exact* binary64 approximation of
        # the reported float, not a rounded display string.
        core_residual = Decimal.from_float(core.residual)
        input_quantization = binary_input["residual"] - reference["residual"]
        arithmetic_roundoff = core_residual - binary_input["residual"]
        total_discrepancy = core_residual - reference["residual"]
        mismatch = core.status != reference["status"]
        # A heuristic warning, NOT a proved forward-error bound. A relative
        # default of 1e-8 is not measurement UQ, and this 25% threshold is
        # purely a review trigger, not another physics tolerance.
        review_trigger = max(Decimal("1e-18"), reference["threshold"] / 4)
        sensitive = (
            abs(input_quantization) > review_trigger
            or abs(arithmetic_roundoff) > review_trigger
        )
        disagreement = disagreement or mismatch
        caution = caution or sensitive
        rows.append({
            "name": name,
            "exact_decimal_status": reference["status"],
            "core_status": core.status,
            "decimal_json_residual": str(reference["residual"]),
            "decimal_json_threshold": str(reference["threshold"]),
            "core_binary64_residual": core.residual,
            "core_binary64_threshold": core.threshold,
            "quantized_operands_residual": str(binary_input["residual"]),
            "input_conversion_residual_effect": str(input_quantization),
            "binary_arithmetic_residual_effect": str(arithmetic_roundoff),
            "core_minus_decimal_json_residual": str(total_discrepancy),
            "decision_disagreement": mismatch,
            "review_threshold_triggered": sensitive,
        })

    classification = (
        "DECISION_DISAGREEMENT" if disagreement else
        "PRECISION_CAUTION" if caution else
        "DECIMAL_BINARY_AGREEMENT"
    )
    return {
        "classification": classification,
        "core_status": report.status,
        "evaluated": True,
        "case_id": report.case_id,
        "checks": rows,
        "core_schema_version": report.schema_version,
        "note": (
            "Optional diagnostic only. The decimal JSON numbers are a reference "
            "for arithmetic—not measurements, an upstream solver, independent "
            "scientific validation, or a precision guarantee. An exact/text "
            "versus binary64 discrepancy needs expert review."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Strict SI JSON case")
    parser.add_argument("--output", type=Path, help="Save advisory JSON (not core v0.1 report)")
    args = parser.parse_args(argv)
    result = audit_text(args.input.read_text(encoding="utf-8"))
    serialized = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    # Nonzero signals material discrepancy to a caller, not a changed
    # check_case status. A rejected input is also nonzero for a preflight.
    return 1 if result["classification"] in ("DECISION_DISAGREEMENT", "CORE_REJECTED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
