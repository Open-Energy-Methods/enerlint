import copy
import math

import pytest

from enerlint import check_case, check_steady_control_volume
from enerlint.verify import ContractError


@pytest.mark.parametrize("name", ["steady_compressor", "steady_heat_exchanger", "steady_turbine"])
def test_hand_derived_balances_pass(load_case, name):
    report = check_case(load_case(name))
    assert report.status == "PASS_IN_SCOPE"
    assert all(c.status == "PASS" for c in report.checks)
    assert all(c.residual == 0.0 for c in report.checks)
    assert len(report.source_fingerprint_sha256) == 64
    report.assert_passed()


def test_compressor_sign_convention(load_case):
    x = load_case("steady_compressor")
    x["shaft_work_out_w"] = abs(x["shaft_work_out_w"])
    report = check_steady_control_volume(x)
    assert report.status == "FAIL"
    energy = report.checks[1]
    assert energy.residual == -480000.0
    assert energy.unit == "W"
    with pytest.raises(AssertionError):
        report.assert_passed()


def test_heat_exchanger_mass_error(load_case):
    x = load_case("steady_heat_exchanger")
    x["outlets"][1]["mass_flow_kg_s"] += 0.5
    r = check_case(x)
    assert r.status == "FAIL"
    assert {c.name for c in r.checks if c.status == "FAIL"} == {
        "steady_mass_closure", "steady_first_law"
    }


def test_heat_added_to_compressor_is_accounted(load_case):
    x = load_case("steady_compressor")
    x["heat_into_volume_w"] = 5000.0
    x["shaft_work_out_w"] = -235000.0
    assert check_case(x).status == "PASS_IN_SCOPE"


def test_tolerance_transparent_not_magic_pass(load_case):
    x = load_case("steady_compressor")
    x["outlets"][0]["specific_enthalpy_j_kg"] += 0.2
    report = check_case(x)
    # Energy discrepancy 0.4W: the declared default absolute 1W permits it.
    assert report.status == "PASS_IN_SCOPE"
    assert report.checks[1].residual == pytest.approx(-0.4)
    assert report.checks[1].threshold == 1.0
    x["tolerances"] = {"energy_w": {"abs": 0.1, "rel": 0.0}}
    report = check_case(x)
    assert report.status == "FAIL"
    assert report.checks[1].threshold == 0.1


def test_never_infer_omitted_zero_work(load_case):
    x = load_case("steady_compressor")
    del x["shaft_work_out_w"]
    with pytest.raises(ContractError, match="missing required"):
        check_case(x)


def test_reject_units_not_explicitly_supported(load_case):
    x = load_case("steady_compressor")
    x["outlets"][0]["specific_enthalpy_kj_kg"] = x["outlets"][0].pop("specific_enthalpy_j_kg") / 1000
    with pytest.raises(ContractError, match="specific_enthalpy_j_kg"):
        check_case(x)


def test_forged_explicit_assumption_is_rejected(load_case):
    x = load_case("steady_compressor")
    x["assumptions"]["steady_state"] = False
    with pytest.raises(ContractError, match="requires explicitly true"):
        check_case(x)


def test_missing_kinetic_assumption_not_silently_accepted(load_case):
    x = load_case("steady_compressor")
    del x["assumptions"]["neglect_kinetic_potential"]
    with pytest.raises(ContractError, match="missing required"):
        check_case(x)


def test_nonfinite_values_and_bools_rejected(load_case):
    x = load_case("steady_compressor")
    x["outlets"][0]["mass_flow_kg_s"] = float("nan")
    with pytest.raises(ContractError, match="finite"):
        check_case(x)
    x["outlets"][0]["mass_flow_kg_s"] = True
    with pytest.raises(ContractError, match="bool"):
        check_case(x)
    x["outlets"][0]["mass_flow_kg_s"] = math.inf
    with pytest.raises(ContractError, match="finite"):
        check_case(x)


def test_negative_mass_rejected(load_case):
    x = load_case("steady_compressor")
    x["inlets"][0]["mass_flow_kg_s"] = -0.01
    with pytest.raises(ContractError, match=">= 0"):
        check_case(x)


def test_duplicate_stream_name_rejected(load_case):
    x = load_case("steady_heat_exchanger")
    x["inlets"][1]["name"] = x["inlets"][0]["name"]
    with pytest.raises(ContractError, match="duplicate stream"):
        check_case(x)


def test_source_hash_tracks_changed_values(load_case):
    x = load_case("steady_compressor")
    r = check_case(x)
    x["inlets"][0]["specific_enthalpy_j_kg"] += 100
    assert check_case(x).source_fingerprint_sha256 != r.source_fingerprint_sha256


def test_common_reference_shift_is_invariant_for_mass_closed_case(load_case):
    original = load_case("steady_heat_exchanger")
    changed = copy.deepcopy(original)
    for s in changed["inlets"] + changed["outlets"]:
        s["specific_enthalpy_j_kg"] += 1000000.0
    a = check_case(original)
    b = check_case(changed)
    assert a.status == b.status == "PASS_IN_SCOPE"
    assert a.checks[1].residual == b.checks[1].residual == 0.0


def test_stream_order_is_invariant(load_case):
    original = load_case("steady_heat_exchanger")
    modified = copy.deepcopy(original)
    modified["inlets"].reverse()
    modified["outlets"].reverse()
    assert [c.residual for c in check_case(original).checks] == [
        c.residual for c in check_case(modified).checks
    ]


def test_enthalpy_reference_is_not_invariant_when_mass_balance_is_broken(load_case):
    x = load_case("steady_compressor")
    x["outlets"][0]["mass_flow_kg_s"] = 1.9
    original = check_case(x)
    z = copy.deepcopy(x)
    z["inlets"][0]["specific_enthalpy_j_kg"] += 200000
    z["outlets"][0]["specific_enthalpy_j_kg"] += 200000
    new = check_case(z)
    assert original.status == new.status == "FAIL"
    assert original.checks[1].residual != new.checks[1].residual


def test_compensating_error_can_escape_conservation_detection(load_case):
    # Explicit known limitation: scaling all flows AND shaft power can keep
    # both conservation equations closed despite wrong model operating point.
    x = load_case("steady_compressor")
    for s in x["inlets"] + x["outlets"]:
        s["mass_flow_kg_s"] *= 1.1
    x["shaft_work_out_w"] *= 1.1
    assert check_case(x).status == "PASS_IN_SCOPE"


def test_energy_scale_not_inflated_by_common_enthalpy_datum_shift(load_case):
    x = load_case("steady_heat_exchanger")
    # Deliberately introduce a small thermodynamic error to exercise a
    # nonzero residual while retaining mass closure.
    x["outlets"][0]["specific_enthalpy_j_kg"] += 0.2
    b = copy.deepcopy(x)
    for stream in b["inlets"] + b["outlets"]:
        stream["specific_enthalpy_j_kg"] += 10000000.0
    r1, r2 = check_case(x), check_case(b)
    assert r1.checks[1].scale == pytest.approx(r2.checks[1].scale, abs=1e-8)
    assert r1.checks[1].threshold == pytest.approx(r2.checks[1].threshold, abs=1e-8)
    assert r1.checks[1].residual == pytest.approx(r2.checks[1].residual, abs=1e-8)
