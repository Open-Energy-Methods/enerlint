"""Explicit textbook calculations from human-readable benchmark case cards.

These constants are specified here rather than derived using EnerLint code.
Their correctness still requires independent human scientific review.
"""

from decimal import Decimal

from enerlint import check_case


def test_cv_001_analytical_reference(load_case):
    m = Decimal("2")
    h_in, h_out = Decimal("300000"), Decimal("420000")
    q_in, w_out = Decimal("0"), Decimal("-240000")
    mass_residual = m - m
    energy_residual = m * h_in - m * h_out + q_in - w_out
    h_reference = (m * h_in + m * h_out) / (2 * m)
    energy_scale = m * abs(h_in - h_reference) + m * abs(h_out - h_reference) + abs(w_out)
    assert mass_residual == Decimal("0")
    assert energy_residual == Decimal("0")
    assert energy_scale == Decimal("480000")

    report = check_case(load_case("steady_compressor"))
    checks = {item.name: item for item in report.checks}
    assert report.status == "PASS_IN_SCOPE"
    assert checks["steady_mass_closure"].residual == float(mass_residual)
    assert checks["steady_mass_closure"].threshold == float(Decimal("4e-8"))
    assert checks["steady_first_law"].residual == float(energy_residual)
    assert checks["steady_first_law"].scale == float(energy_scale)
    assert checks["steady_first_law"].threshold == 1.0


def test_cv_001_known_compensating_escape(load_case):
    case = load_case("steady_compressor")
    case["inlets"][0]["mass_flow_kg_s"] = 2.2
    case["outlets"][0]["mass_flow_kg_s"] = 2.2
    case["shaft_work_out_w"] = -264000
    # The expected reference operating point is unchanged, but its balances cannot reject this change.
    m = Decimal("2.2")
    assert m * Decimal("300000") - m * Decimal("420000") - Decimal("-264000") == 0
    assert m - m == 0
    report = check_case(case)
    assert report.status == "PASS_IN_SCOPE"
    assert all(check.status == "PASS" for check in report.checks)


def test_st_001_analytical_reference(load_case):
    charge, discharge, loss = Decimal("120000"), Decimal("50000"), Decimal("10000")
    seconds = Decimal("3600")
    initial, final = Decimal("2000000000"), Decimal("2216000000")
    delta_energy = final - initial
    interval_terms = (charge * seconds, discharge * seconds, loss * seconds)
    reference_residual = delta_energy - (interval_terms[0] - interval_terms[1] - interval_terms[2])
    reference_scale = abs(delta_energy) + sum(abs(t) for t in interval_terms)
    reference_threshold = max(Decimal("1"), reference_scale * Decimal("1e-8"))
    assert delta_energy == Decimal("216000000")
    assert reference_residual == 0
    assert reference_scale == Decimal("864000000")
    assert reference_threshold == Decimal("8.64")

    report = check_case(load_case("storage_interval"))
    checks = {check.name: check for check in report.checks}
    assert report.status == "PASS_IN_SCOPE"
    assert checks["storage_energy_closure"].residual == float(reference_residual)
    assert checks["storage_energy_closure"].scale == float(reference_scale)
    assert checks["storage_energy_closure"].threshold == float(reference_threshold)
    assert checks["storage_capacity"].status == "PASS"


def test_st_001_known_out_of_balance_case(load_case):
    case = load_case("storage_interval")
    case["energy_final_j"] += 5_000_000
    report = check_case(case)
    assert report.status == "FAIL"
    energy_check = next(x for x in report.checks if x.name == "storage_energy_closure")
    assert energy_check.residual == 5_000_000
