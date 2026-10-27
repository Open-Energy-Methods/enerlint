import copy

import pytest

from enerlint import check_case
from enerlint.faults import inject_fault


@pytest.mark.parametrize(
    "fault,case_name,expected_failed_checks",
    [
        ("outlet_mass_scale", "steady_compressor", {"steady_mass_closure", "steady_first_law"}),
        ("outlet_enthalpy_scale", "steady_compressor", {"steady_first_law"}),
        ("invert_shaft_work", "steady_compressor", {"steady_first_law"}),
        ("invert_heat", "steady_turbine", {"steady_first_law"}),
        ("storage_final_offset", "storage_interval", {"storage_energy_closure"}),
        ("storage_duration_scale", "storage_interval", {"storage_energy_closure"}),
    ],
)
def test_faults_are_detected(load_case, fault, case_name, expected_failed_checks):
    case = load_case(case_name)
    if fault == "invert_heat":
        # A valid model with heat input and adjusted shaft power is necessary
        # for a meaningful heat-sign mutation.
        case["heat_into_volume_w"] = 5000.0
        case["shaft_work_out_w"] += 5000.0
    baseline = check_case(case)
    assert baseline.status == "PASS_IN_SCOPE"
    untouched = copy.deepcopy(case)
    corrupted = inject_fault(case, fault)
    report = check_case(corrupted)
    assert case == untouched, "Fault injection must not mutate source"
    assert report.status == "FAIL"
    actual = {c.name for c in report.checks if c.status == "FAIL"}
    assert expected_failed_checks <= actual
    assert corrupted["case_id"].endswith(fault)
    assert report.source_fingerprint_sha256 != baseline.source_fingerprint_sha256


def test_fault_rejection_when_heat_zero(load_case):
    with pytest.raises(ValueError, match="zero heat"):
        inject_fault(load_case("steady_compressor"), "invert_heat")


def test_unknown_fault_and_invalid_factor_rejected(load_case):
    x = load_case("steady_compressor")
    with pytest.raises(ValueError, match="Unknown fault"):
        inject_fault(x, "black_box_magic")
    with pytest.raises(ValueError, match="factor must"):
        inject_fault(x, "outlet_mass_scale", factor=-1)
