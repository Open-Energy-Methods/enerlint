import pytest

from enerlint import check_case, check_storage_interval
from enerlint.verify import ContractError


def test_storage_reference_passes(load_case):
    r = check_case(load_case("storage_interval"))
    assert r.status == "PASS_IN_SCOPE"
    assert all(x.status == "PASS" for x in r.checks)
    assert r.checks[0].residual == 0.0


def test_storage_state_error_fails(load_case):
    x = load_case("storage_interval")
    x["energy_final_j"] += 5000000
    r = check_storage_interval(x)
    assert r.status == "FAIL"
    assert r.checks[0].residual == 5000000


def test_storage_duration_error_fails(load_case):
    x = load_case("storage_interval")
    x["duration_s"] += 300
    assert check_case(x).status == "FAIL"


def test_missing_capacity_is_not_checked(load_case):
    x = load_case("storage_interval")
    del x["capacity_j"]
    r = check_case(x)
    assert r.status == "PASS_IN_SCOPE"
    assert r.checks[1].status == "NOT_CHECKED"
    assert r.checks[1].threshold is None


def test_capacity_violation_fails(load_case):
    x = load_case("storage_interval")
    x["capacity_j"] = 2100000000.0
    assert check_case(x).status == "FAIL"
    assert check_case(x).checks[1].status == "FAIL"


def test_negative_losses_rejected(load_case):
    x = load_case("storage_interval")
    x["heat_loss_out_storage_w"] = -100
    with pytest.raises(ContractError, match=">= 0"):
        check_case(x)


def test_zero_time_rejected(load_case):
    x = load_case("storage_interval")
    x["duration_s"] = 0
    with pytest.raises(ContractError, match="> 0"):
        check_case(x)


def test_negative_state_rejected(load_case):
    x = load_case("storage_interval")
    x["energy_initial_j"] = -1
    with pytest.raises(ContractError, match=">= 0"):
        check_case(x)


def test_storage_rate_assumption_must_be_explicit(load_case):
    x = load_case("storage_interval")
    del x["assumptions"]
    with pytest.raises(ContractError, match="missing required"):
        check_case(x)
    x["assumptions"] = {"constant_interval_rates": False}
    with pytest.raises(ContractError, match="explicitly true"):
        check_case(x)
