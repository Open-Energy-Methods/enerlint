"""Author-attestation preflight for the documented v0.1 CV contract.

A passing preflight demonstrates only that mandatory declarations have been
provided consistently with the input; it does not authenticate those claims.
"""

import copy
import json
from pathlib import Path

import pytest

from enerlint.verify import ContractError, fingerprint
from scripts.review_control_volume import DECLARATIONS, main, review

ROOT = Path(__file__).resolve().parents[1]
REVIEW_FILE = ROOT / "examples" / "steady_compressor.boundary-review.json"


@pytest.fixture
def compressor_review():
    return json.loads(REVIEW_FILE.read_text(encoding="utf-8"))


def test_declaration_is_bound_to_exact_compressor_example(load_case, compressor_review):
    case = load_case("steady_compressor")
    assert compressor_review["input_sha256"] == fingerprint(case)
    assert review(case, compressor_review) == "PASS_IN_SCOPE"


@pytest.mark.parametrize("declaration_name", DECLARATIONS)
def test_each_missing_or_false_scope_attestation_rejected(
    load_case, compressor_review, declaration_name
):
    case = load_case("steady_compressor")
    for answer in (False, None, "yes"):
        bad = copy.deepcopy(compressor_review)
        bad["declarations"][declaration_name] = answer
        with pytest.raises(ContractError, match=declaration_name):
            review(case, bad)
    bad = copy.deepcopy(compressor_review)
    del bad["declarations"][declaration_name]
    with pytest.raises(ContractError, match="declarations"):
        review(case, bad)


def test_missing_boundary_description_or_evidence_rejected(load_case, compressor_review):
    for name in ("boundary_description", "evidence_note", "author"):
        bad = copy.deepcopy(compressor_review)
        bad[name] = ""
        with pytest.raises(ContractError, match=name):
            review(load_case("steady_compressor"), bad)


def test_omitted_declared_inlet_or_extra_material_port_rejected(load_case, compressor_review):
    for names in ([], ["not_an_inlet"], ["inlet", "leak"], ["inlet", "inlet"]):
        bad = copy.deepcopy(compressor_review)
        bad["declared_inlets"] = names
        with pytest.raises(ContractError, match="declared_inlets"):
            review(load_case("steady_compressor"), bad)


def test_changed_case_stales_the_review_even_if_its_balances_close(
    load_case, compressor_review
):
    case = load_case("steady_compressor")
    for stream in case["inlets"] + case["outlets"]:
        stream["mass_flow_kg_s"] *= 1.1
    case["shaft_work_out_w"] *= 1.1
    # Deliberate known escape: the numeric checker still passes.
    with pytest.raises(ContractError, match="sha256 mismatch"):
        review(case, compressor_review)


def test_wrong_physical_sign_is_not_hidden_by_complete_declaration(
    load_case, compressor_review
):
    case = load_case("steady_compressor")
    case["shaft_work_out_w"] = 240000
    declaration = copy.deepcopy(compressor_review)
    declaration["input_sha256"] = fingerprint(case)
    # Author completeness may pass for physically inconsistent exported numbers;
    # calling code must not call this a verified operating point.
    assert review(case, declaration) == "FAIL"


def test_missing_explicit_heat_or_shaft_power_rejected(load_case, compressor_review):
    for name in ("heat_into_volume_w", "shaft_work_out_w"):
        case = load_case("steady_compressor")
        del case[name]
        with pytest.raises(ContractError, match="missing required"):
            review(case, compressor_review)


def test_missing_adiabatic_reason_rejected(load_case, compressor_review):
    bad = copy.deepcopy(compressor_review)
    del bad["zero_heat_reason"]
    with pytest.raises(ContractError, match="zero_heat_reason"):
        review(load_case("steady_compressor"), bad)


def test_zero_shaft_work_requires_separate_justification(load_case, compressor_review):
    case = load_case("steady_heat_exchanger")
    review_data = copy.deepcopy(compressor_review)
    review_data["case_id"] = case["case_id"]
    review_data["input_sha256"] = fingerprint(case)
    review_data["declared_inlets"] = [x["name"] for x in case["inlets"]]
    review_data["declared_outlets"] = [x["name"] for x in case["outlets"]]
    review_data["boundary_description"] = "Aggregate adiabatic exchanger; no shaft-work boundary"
    review_data["zero_heat_reason"] = "Synthetic aggregate exchanger has no external heat crossing"
    with pytest.raises(ContractError, match="zero_work_reason"):
        review(case, review_data)
    review_data["zero_work_reason"] = "No rotating shaft crosses the aggregate boundary"
    assert review(case, review_data) == "PASS_IN_SCOPE"


def test_unexpected_review_fields_rejected(load_case, compressor_review):
    bad = copy.deepcopy(compressor_review)
    bad["signed_off_by_external_reviewer"] = "no reviewer"
    with pytest.raises(ContractError, match="unexpected"):
        review(load_case("steady_compressor"), bad)


def test_version_mismatch_rejected(load_case, compressor_review):
    bad = copy.deepcopy(compressor_review)
    bad["review_version"] = "0.2.0"
    with pytest.raises(ContractError, match="review_version"):
        review(load_case("steady_compressor"), bad)


def test_review_cli_success_does_not_claim_physical_validation(capsys):
    rc = main([
        str(ROOT / "examples" / "steady_compressor.json"),
        str(REVIEW_FILE),
    ])
    captured = capsys.readouterr()
    assert rc == 0
    assert "DECLARATION_COMPLETE" in captured.out
    assert "AUTHOR ATTESTATION ONLY" in captured.out
    assert "physical_check=PASS_IN_SCOPE" in captured.out


def test_review_cli_missing_file_returns_exit_two(capsys, tmp_path):
    rc = main([
        str(ROOT / "examples" / "steady_compressor.json"),
        str(tmp_path / "does-not-exist.json"),
    ])
    assert rc == 2
    assert "BOUNDARY_REVIEW_INCOMPLETE" in capsys.readouterr().err
