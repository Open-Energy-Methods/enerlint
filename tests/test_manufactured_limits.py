"""Manufactured and limiting numerical references, not empirical validation."""

from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path

import pytest

from enerlint import check_case
from enerlint.verify import ContractError
from scripts.run_analytical_catalog import independent_arithmetic
from scripts.run_manufactured_limits import CATALOG, mutate, run

IDS = [f"TH-LM-{n:03d}" for n in range(1, 14)]


@pytest.fixture(scope="module")
def frozen():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def test_catalog_has_thirteen_distinct_and_accountable_references(frozen):
    rows = frozen["cases"]
    assert [row["id"] for row in rows] == IDS
    assert all(row["version"] == "0.1" for row in rows)
    assert all(row["case"]["provenance"]["evidence_class"] == "hand_constructed"
               for row in rows)
    assert "No external peer review" in frozen["independence"]
    assert all(row["physical_conditions"].strip() and row["limitations"].strip()
               for row in rows)
    assert sum(row["expected_status"] == "INVALID_INPUT" for row in rows) == 2
    assert sum(row["expected_status"] == "PASS_IN_SCOPE" for row in rows) == 11
    assert sum(len(row["perturbations"]) for row in rows) == 13


def test_frozen_decimal_ledger_preserves_fails_and_numeric_escapes():
    result = run()
    assert result["summary"] == {
        "cases_total": 13,
        "evaluated_limit_cases": 11,
        "invalid_inputs_correctly_rejected": 2,
        "evaluated_scoped_passes": 11,
        "selected_perturbations": 13,
        "selected_perturbations_failed": 11,
        "selected_perturbations_tolerated": 2,
        "independent_external_reviews": 0,
    }
    assert len(result["catalog_sha256"]) == 64
    assert all(x["classification"] == "INVALID_INPUT" for x in result["cases"][-2:])


@pytest.mark.parametrize("index", range(11))
def test_each_evaluated_case_matches_decimal_oracle(frozen, index):
    case = frozen["cases"][index]["case"]
    independent = independent_arithmetic(case)
    report = check_case(case)
    assert report.status == "PASS_IN_SCOPE"
    assert all(x["status"] != "FAIL" for k, x in independent.items()
               if not k.startswith("_"))
    for observed in report.checks:
        calculated = independent[observed.name]
        assert observed.status == calculated["status"]
        assert observed.unit == calculated["unit"]


@pytest.mark.parametrize("index", [11, 12])
def test_non_evaluable_cases_reject_instead_of_passing(frozen, index):
    row = frozen["cases"][index]
    with pytest.raises(ContractError, match=row["expected_contract_error"]):
        check_case(row["case"])


def test_zero_mass_can_be_valid_with_explicit_zero_external_crossings(frozen):
    case = frozen["cases"][0]["case"]
    report = check_case(case)
    assert report.status == "PASS_IN_SCOPE"
    assert [(c.residual, c.scale, c.threshold) for c in report.checks] == [
        (0.0, 0.0, 1e-9),
        (0.0, 0.0, 1.0),
    ]


def test_tiny_flow_is_valid_but_abs_energy_tolerance_can_mask_power(frozen):
    row = frozen["cases"][1]
    base = check_case(row["case"])
    lost_work = mutate(row["case"], "shaft_work_out_w", 0.0)
    result = check_case(lost_work)
    assert base.status == result.status == "PASS_IN_SCOPE"
    assert abs(result.checks[1].residual) > 0
    assert abs(result.checks[1].residual) < result.checks[1].threshold
    # This perturbation removes 100% of the 1e-7 W baseline shaft input.
    assert row["case"]["shaft_work_out_w"] == -1e-7


def test_inclusive_absolute_mass_and_energy_thresholds(frozen):
    energy = check_case(frozen["cases"][3]["case"])
    mass = check_case(frozen["cases"][4]["case"])
    assert energy.checks[1].residual == energy.checks[1].threshold == 1.0
    assert abs(mass.checks[0].residual) == mass.checks[0].threshold == 1e-9
    assert energy.status == mass.status == "PASS_IN_SCOPE"
    assert check_case(mutate(frozen["cases"][3]["case"], "heat_into_volume_w", 1.01)).status == "FAIL"
    assert check_case(mutate(frozen["cases"][4]["case"],
                             "outlets.0.mass_flow_kg_s", 1.01e-9)).status == "FAIL"


def test_cancellation_and_datum_shift_do_not_artificially_inflate_threshold(frozen):
    cancel = check_case(frozen["cases"][5]["case"])
    shifted = check_case(frozen["cases"][6]["case"])
    assert cancel.checks[1].residual == 0
    assert cancel.checks[1].scale == 2000.0
    assert cancel.checks[1].threshold == 1.0
    assert shifted.checks[1].residual == 0
    assert shifted.checks[1].scale == 480000.0
    assert shifted.checks[1].threshold == 1.0


@pytest.mark.parametrize("exponent", [0, 3, 6, 9, 12])
def test_manufactured_flow_and_power_converge_to_zero_without_change_in_status(
    frozen, exponent,
):
    case = copy.deepcopy(frozen["cases"][8]["case"])
    factor = 10.0 ** (-exponent)
    for stream in case["inlets"] + case["outlets"]:
        stream["mass_flow_kg_s"] *= factor
    case["shaft_work_out_w"] *= factor
    oracle = independent_arithmetic(case)
    report = check_case(case)
    assert oracle["steady_mass_closure"]["residual"] == Decimal(0)
    assert oracle["steady_first_law"]["residual"] == Decimal(0)
    assert report.status == "PASS_IN_SCOPE"
    assert abs(report.checks[1].residual) <= report.checks[1].threshold


def test_equal_capacity_is_valid_and_one_joule_violation_is_failure(frozen):
    base = frozen["cases"][9]["case"]
    assert check_case(base).checks[1].status == "PASS"
    failure = mutate(base, "capacity_j", 799999.0)
    assert check_case(failure).checks[1].status == "FAIL"
    assert check_case(failure).checks[1].threshold == 0


def test_large_opposing_storage_rates_allow_tolerated_error(frozen):
    base = frozen["cases"][10]["case"]
    baseline = check_case(base)
    assert baseline.checks[0].threshold == pytest.approx(20.0000002)
    missed = check_case(mutate(base, "energy_final_j", 1000000020))
    flagged = check_case(mutate(base, "energy_final_j", 1000000110))
    assert missed.status == "PASS_IN_SCOPE"
    assert missed.checks[0].residual == 10
    assert flagged.status == "FAIL"
    assert flagged.checks[0].residual == 100


def test_invalid_float_overflow_is_not_a_conservation_failure(frozen):
    with pytest.raises(ContractError, match="Transport energy overflow"):
        check_case(frozen["cases"][12]["case"])


def test_external_sensitivity_not_inferred_from_selected_self_tests(frozen):
    row = frozen["cases"][10]
    assert "not a fault sensitivity claim" in row["limitations"]
    assert all(row["expected_status"] != "FAIL"
               for row in frozen["cases"])
