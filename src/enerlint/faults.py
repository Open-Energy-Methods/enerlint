"""Deliberate physical-output corruptions for scientific negative controls.

These mutate exported case data, *not* the upstream simulator's source code.
Detection proves only sensitivity to the named mutation for the stated case.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any


def inject_fault(case: Mapping[str, Any], fault: str, *, factor: float = 1.2) -> dict[str, Any]:
    """Return a new dictionary with exactly one declared fault.

    Supported: outlet_mass_scale, outlet_enthalpy_scale, invert_shaft_work,
    invert_heat, storage_final_offset, storage_duration_scale.
    """
    import math

    if not isinstance(factor, (int, float)) or isinstance(factor, bool):
        raise ValueError("factor must be a numeric value")
    if not math.isfinite(factor) or factor <= 0 or factor == 1:
        raise ValueError("factor must be finite, positive, and != 1")
    mutated = copy.deepcopy(dict(case))
    kind = mutated.get("kind")
    if fault in ("outlet_mass_scale", "outlet_enthalpy_scale", "invert_shaft_work", "invert_heat"):
        if kind != "steady_control_volume":
            raise ValueError(f"{fault} requires a steady_control_volume")
        if fault == "outlet_mass_scale":
            mutated["outlets"][0]["mass_flow_kg_s"] *= factor
        elif fault == "outlet_enthalpy_scale":
            mutated["outlets"][0]["specific_enthalpy_j_kg"] *= factor
        elif fault == "invert_shaft_work":
            if mutated["shaft_work_out_w"] == 0:
                raise ValueError("Cannot invert zero shaft work")
            mutated["shaft_work_out_w"] *= -1
        else:
            if mutated["heat_into_volume_w"] == 0:
                raise ValueError("Cannot invert zero heat")
            mutated["heat_into_volume_w"] *= -1
    elif fault in ("storage_final_offset", "storage_duration_scale"):
        if kind != "storage_interval":
            raise ValueError(f"{fault} requires a storage_interval")
        if fault == "storage_final_offset":
            mutated["energy_final_j"] *= factor
        else:
            mutated["duration_s"] *= factor
    else:
        raise ValueError(f"Unknown fault: {fault}")
    mutated["case_id"] = mutated["case_id"] + "__" + fault
    mutated["provenance"]["declared_source"] = (
        "Deliberately corrupted copy of: " + str(case["provenance"]["declared_source"])
    )
    return mutated
