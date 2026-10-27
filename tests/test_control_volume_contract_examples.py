"""Direct independent arithmetic and omitted-crossing counterexamples for CV-0.1."""

import copy

import pytest

from enerlint import check_case
from enerlint.verify import ContractError


def test_nonadiabatic_compressor_has_both_signed_heat_and_work(load_case):
    case = load_case("steady_nonadiabatic_compressor")
    assert (
        1 * 200_000 - 1 * 260_000 + 10_000 - (-50_000)
    ) == 0
    report = check_case(case)
    assert report.status == "PASS_IN_SCOPE"
    assert [(c.name, c.status) for c in report.checks] == [
        ("steady_mass_closure", "PASS"),
        ("steady_first_law", "PASS"),
    ]
    assert report.checks[0].residual == 0
    assert report.checks[1].residual == 0


def test_wrong_heat_direction_is_a_real_first_law_failure(load_case):
    case = load_case("steady_nonadiabatic_compressor")
    case["heat_into_volume_w"] = -10_000
    expected = 200_000 - 260_000 - 10_000 - (-50_000)
    assert expected == -20_000
    report = check_case(case)
    assert report.status == "FAIL"
    assert report.checks[0].status == "PASS"
    assert report.checks[1].status == "FAIL"
    assert report.checks[1].residual == float(expected)


def test_explicit_leak_port_exposes_mass_and_energy_failures(load_case):
    case = load_case("steady_compressor")
    case["outlets"].append({
        "name": "hypothetical_leak",
        "mass_flow_kg_s": 0.1,
        "specific_enthalpy_j_kg": 300_000.0,
    })
    reference_mass = 2 - (2 + 0.1)
    reference_energy = 2 * 300_000 - 2 * 420_000 - 0.1 * 300_000 - (-240_000)
    assert reference_mass == pytest.approx(-0.1)
    assert reference_energy == -30_000
    report = check_case(case)
    assert report.status == "FAIL"
    assert report.checks[0].status == "FAIL"
    assert report.checks[1].status == "FAIL"
    assert report.checks[0].residual == pytest.approx(reference_mass)
    assert report.checks[1].residual == float(reference_energy)


def test_unreported_leak_is_not_magic_detected_from_closed_original_case(load_case):
    # This test documents a structural escape rather than a successful detection.
    report = check_case(load_case("steady_compressor"))
    assert report.status == "PASS_IN_SCOPE"
    assert all(c.status == "PASS" for c in report.checks)


@pytest.mark.parametrize("missing", ["heat_into_volume_w", "shaft_work_out_w", "inlets", "outlets"])
def test_unreported_required_crossings_cannot_be_silently_zero(load_case, missing):
    case = load_case("steady_nonadiabatic_compressor")
    del case[missing]
    with pytest.raises(ContractError, match="missing required"):
        check_case(case)


@pytest.mark.parametrize("extra", ["accumulation_j", "reaction_heat_w", "leak_w", "electrical_power_w"])
def test_unsupported_physics_fields_are_rejected_not_ignored(load_case, extra):
    case = load_case("steady_compressor")
    case[extra] = 0
    with pytest.raises(ContractError, match="unexpected field"):
        check_case(case)


@pytest.mark.parametrize("field", ["steady_state", "neglect_kinetic_potential"])
def test_unsupported_dynamic_or_kinetic_case_rejected(load_case, field):
    case = load_case("steady_compressor")
    case["assumptions"][field] = False
    with pytest.raises(ContractError, match="explicitly true"):
        check_case(case)


def test_no_physical_claim_about_boundary_in_input_hash(load_case):
    original = load_case("steady_compressor")
    altered = copy.deepcopy(original)
    altered["provenance"]["declared_source"] = (
        "Identical synthetic physics, different author-described source"
    )
    a, b = check_case(original), check_case(altered)
    assert a.status == b.status == "PASS_IN_SCOPE"
    assert a.source_fingerprint_sha256 != b.source_fingerprint_sha256
    # Source fingerprint binds declared JSON, not independent physical truth.
