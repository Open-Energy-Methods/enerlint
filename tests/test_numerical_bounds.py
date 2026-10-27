"""Adversarial binary64 tests for scientific *scope*, not external validation.

The expected outcomes are physical/contract properties, not derived by
calling the implementation under test. All cases are synthetic.
"""

from __future__ import annotations

import copy

import pytest

from enerlint import check_case
from enerlint.cli import main
from enerlint.verify import ContractError


@pytest.mark.parametrize("shift", [0, 1_000_000, -1_000_000, 1_000_000_000_000])
def test_common_enthalpy_reference_shift_keeps_closed_compressor_checks(load_case, shift):
    case = load_case("steady_compressor")
    base_report = check_case(case)
    for stream in case["inlets"] + case["outlets"]:
        stream["specific_enthalpy_j_kg"] += shift

    shifted_report = check_case(case)
    assert shifted_report.status == base_report.status == "PASS_IN_SCOPE"
    assert shifted_report.checks[0].residual == 0
    assert shifted_report.checks[1].residual == 0
    assert shifted_report.checks[1].threshold == base_report.checks[1].threshold


def test_reference_datum_cannot_rescue_mass_imbalance(load_case):
    case = load_case("steady_compressor")
    case["outlets"][0]["mass_flow_kg_s"] = 2.1
    report = check_case(case)
    assert report.status == "FAIL"
    assert report.checks[0].status == "FAIL"


def test_nearly_cancelling_multistream_energy_terms_are_bounded(load_case):
    case = load_case("steady_heat_exchanger")
    case["inlets"] = [
        {"name": "a", "mass_flow_kg_s": 2.0, "specific_enthalpy_j_kg": 3e15 + 1000},
        {"name": "b", "mass_flow_kg_s": 1.0, "specific_enthalpy_j_kg": 3e15 - 2000},
    ]
    case["outlets"] = [
        {"name": "c", "mass_flow_kg_s": 1.0, "specific_enthalpy_j_kg": 3e15},
        {"name": "d", "mass_flow_kg_s": 2.0, "specific_enthalpy_j_kg": 3e15},
    ]
    case["heat_into_volume_w"] = 0.0
    case["shaft_work_out_w"] = 0.0

    report = check_case(case)
    assert report.status == "PASS_IN_SCOPE"
    assert report.checks[1].residual == 0
    assert report.checks[1].threshold == 1.0

    # Move the first stream by 10 J/kg: +20 W, outside the 1 W threshold.
    case["inlets"][0]["specific_enthalpy_j_kg"] += 10.0
    wrong = check_case(case)
    assert wrong.checks[1].status == "FAIL"
    assert wrong.checks[1].residual == 20.0


def test_zero_mass_flow_and_zero_heat_work_are_explicitly_in_scope(load_case):
    case = load_case("steady_compressor")
    for stream in case["inlets"] + case["outlets"]:
        stream["mass_flow_kg_s"] = 0.0
    case["heat_into_volume_w"] = 0.0
    case["shaft_work_out_w"] = 0.0
    report = check_case(case)
    assert report.status == "PASS_IN_SCOPE"
    assert [x.residual for x in report.checks] == [0, 0]
    assert report.checks[1].threshold == 1.0


def test_zero_mass_flow_does_not_hide_nonzero_heat_input(load_case):
    case = load_case("steady_compressor")
    for stream in case["inlets"] + case["outlets"]:
        stream["mass_flow_kg_s"] = 0.0
    case["heat_into_volume_w"] = 10.0
    case["shaft_work_out_w"] = 0.0
    report = check_case(case)
    assert report.status == "FAIL"
    assert report.checks[1].residual == 10.0


@pytest.mark.parametrize(
    "offset,expected",
    [(0.25, "PASS_IN_SCOPE"), (0.75, "FAIL")],
)
def test_absolute_energy_default_threshold_is_a_scoped_decision(load_case, offset, expected):
    case = load_case("steady_compressor")
    case["outlets"][0]["specific_enthalpy_j_kg"] += offset
    report = check_case(case)
    assert report.checks[1].threshold == 1.0
    assert report.status == expected
    assert report.checks[1].residual == -2.0 * offset


def test_explicit_zero_tolerance_requires_exact_closure(load_case):
    case = load_case("steady_compressor")
    case["tolerances"] = {"energy_w": {"abs": 0.0, "rel": 0.0}}
    case["outlets"][0]["specific_enthalpy_j_kg"] += 0.25
    report = check_case(case)
    assert report.status == "FAIL"
    assert report.checks[1].threshold == 0
    assert report.checks[1].residual == -0.5


def test_large_but_representable_flow_and_enthalpy_product(load_case):
    case = load_case("steady_compressor")
    for stream in case["inlets"] + case["outlets"]:
        stream["mass_flow_kg_s"] = 1e150
        stream["specific_enthalpy_j_kg"] = 1e150
    case["shaft_work_out_w"] = 0.0
    report = check_case(case)
    assert report.status == "PASS_IN_SCOPE"
    assert report.checks[0].residual == 0
    assert report.checks[1].residual == 0


def test_finite_individual_flows_can_overflow_mass_scale_and_must_abstain(load_case):
    case = load_case("steady_compressor")
    for stream in case["inlets"] + case["outlets"]:
        stream["mass_flow_kg_s"] = 1e308
        stream["specific_enthalpy_j_kg"] = 0.0
    case["shaft_work_out_w"] = 0.0
    with pytest.raises(ContractError, match="Steady mass scale.*overflow"):
        check_case(case)


def test_finite_individual_fluxes_can_overflow_reference_sum(load_case):
    case = load_case("steady_compressor")
    for stream in case["inlets"] + case["outlets"]:
        stream["mass_flow_kg_s"] = 1e155
        stream["specific_enthalpy_j_kg"] = 1e153
    case["shaft_work_out_w"] = 0.0
    with pytest.raises(ContractError, match="Enthalpy reference numerator.*overflow"):
        check_case(case)


def test_product_overflow_stays_a_contract_error(load_case):
    case = load_case("steady_compressor")
    for stream in case["inlets"] + case["outlets"]:
        stream["mass_flow_kg_s"] = 1e160
        stream["specific_enthalpy_j_kg"] = 1e160
    case["shaft_work_out_w"] = 0.0
    with pytest.raises(ContractError, match="Transport energy overflow"):
        check_case(case)


def test_relative_tolerance_multiplication_overflow_is_not_a_pass(load_case):
    case = load_case("steady_compressor")
    case["inlets"][0]["mass_flow_kg_s"] = 1e100
    case["outlets"][0]["mass_flow_kg_s"] = 1e100
    case["inlets"][0]["specific_enthalpy_j_kg"] = 1.0
    case["outlets"][0]["specific_enthalpy_j_kg"] = 2.0
    case["shaft_work_out_w"] = -1e100
    case["tolerances"] = {"energy_w": {"abs": 0.0, "rel": 1e300}}
    with pytest.raises(ContractError, match="threshold overflow"):
        check_case(case)


def test_storage_interval_product_overflow_fails_closed(load_case):
    case = load_case("storage_interval")
    case["duration_s"] = 1e200
    case["heat_charge_into_storage_w"] = 1e200
    with pytest.raises(ContractError, match="Integrated energy overflow"):
        check_case(case)


def test_missing_optional_storage_capacity_is_not_silently_a_checked_success(load_case):
    case = load_case("storage_interval")
    del case["capacity_j"]
    report = check_case(case)
    assert report.status == "PASS_IN_SCOPE"
    assert report.checks[0].status == "PASS"
    assert report.checks[1].status == "NOT_CHECKED"
    assert report.checks[1].threshold is None
    assert "capacity" in report.checks[1].description.lower()


def test_overflow_is_cli_invalid_input_exit_2_not_traceback(tmp_path, load_case, capsys):
    import json

    case = copy.deepcopy(load_case("steady_compressor"))
    for stream in case["inlets"] + case["outlets"]:
        stream["mass_flow_kg_s"] = 1e308
        stream["specific_enthalpy_j_kg"] = 0.0
    case["shaft_work_out_w"] = 0.0
    path = tmp_path / "unrepresentable.json"
    path.write_text(json.dumps(case), encoding="utf-8")
    assert main(["check", str(path)]) == 2
    captured = capsys.readouterr()
    assert "INVALID_INPUT:" in captured.err
    assert "overflow" in captured.err
    assert "Traceback" not in captured.err
