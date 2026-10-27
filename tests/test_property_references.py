"""Conservative metadata review; not thermodynamic property or measurement validation."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from enerlint import check_case
from enerlint.verify import ContractError, fingerprint
from scripts.review_property_references import main, review

ROOT = Path(__file__).resolve().parents[1] / "examples"


def fixture(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def linked(case_name: str):
    return fixture(case_name + ".json"), fixture(case_name + ".property-review.json")


@pytest.mark.parametrize("name", ["steady_compressor", "steady_heat_exchanger"])
def test_reference_metadata_covers_all_ports_in_a_frozen_case(name):
    case, declaration = linked(name)
    assert declaration["input_sha256"] == fingerprint(case)
    assert review(case, declaration) == "PASS_IN_SCOPE"


def test_different_closed_exchanger_circuits_can_have_different_reference_zeros():
    case, declaration = linked("steady_heat_exchanger")
    assert len({r["reference_state_id"] for r in declaration["stream_properties"]}) == 2
    assert review(case, declaration) == "PASS_IN_SCOPE"
    for row in case["inlets"] + case["outlets"]:
        shift = 1000000 if row["name"].startswith("cold_") else -200000
        row["specific_enthalpy_j_kg"] += shift
    declaration["input_sha256"] = fingerprint(case)
    result = check_case(case)
    assert result.status == "PASS_IN_SCOPE"
    assert result.checks[1].residual == pytest.approx(0.0, abs=1e-7)
    assert review(case, declaration) == "PASS_IN_SCOPE"


def test_wrong_reference_and_compensated_work_still_pass_raw_balance():
    case, declaration = linked("steady_mismatched_reference_compensated")
    assert declaration["input_sha256"] == fingerprint(case)
    raw = check_case(case)
    assert raw.status == "PASS_IN_SCOPE"
    assert all(item.status == "PASS" for item in raw.checks)
    assert raw.checks[1].residual == pytest.approx(0.0, abs=1e-8)
    with pytest.raises(ContractError, match="mismatched fluid/composition/backend/reference"):
        review(case, declaration)


@pytest.mark.parametrize("field", [
    "fluid_id", "composition_id", "backend_id", "backend_version", "reference_state_id",
])
def test_incompatible_property_basis_in_one_circuit_abstains(field):
    case, declaration = linked("steady_compressor")
    declaration["stream_properties"][1][field] = "incompatible_revision"
    with pytest.raises(ContractError, match="mismatched fluid/composition/backend/reference"):
        review(case, declaration)


def test_same_declaration_cannot_certify_data_because_source_can_lie():
    case, declaration = linked("steady_compressor")
    assert review(case, declaration) == "PASS_IN_SCOPE"
    # An attacker can enter the same strings for two fundamentally different
    # sources: the sidecar checks *consistency*, not source authenticity.
    declaration["stream_properties"][1]["source_note"] = "Arbitrary assertion by data author"
    assert review(case, declaration) == "PASS_IN_SCOPE"


@pytest.mark.parametrize("change", ["flow", "enthalpy", "provenance"])
def test_case_change_requires_new_source_fingerprint(change):
    case, declaration = linked("steady_compressor")
    if change == "flow":
        case["inlets"][0]["mass_flow_kg_s"] = 2.1
    elif change == "enthalpy":
        case["outlets"][0]["specific_enthalpy_j_kg"] += 100000
    else:
        case["provenance"]["declared_source"] = "Changed author declaration"
    with pytest.raises(ContractError, match="input_sha256 mismatch"):
        review(case, declaration)


@pytest.mark.parametrize("edit", ["remove_port", "duplicate_port", "unknown_port", "unknown_field"])
def test_incomplete_or_unexpected_property_metadata_is_rejected(edit):
    case, declaration = linked("steady_compressor")
    if edit == "remove_port":
        declaration["stream_properties"].pop()
    elif edit == "duplicate_port":
        declaration["stream_properties"].append(copy.deepcopy(declaration["stream_properties"][0]))
    elif edit == "unknown_port":
        declaration["stream_properties"][1]["name"] = "does-not-exist"
    else:
        declaration["stream_properties"][1]["property_verified"] = True
    with pytest.raises(ContractError, match="stream_properties|duplicated|undeclared"):
        review(case, declaration)


def test_global_mass_balance_can_pass_while_per_circuit_balance_fails():
    case, declaration = linked("steady_heat_exchanger")
    case["outlets"][0]["mass_flow_kg_s"] = 0.9
    case["outlets"][1]["mass_flow_kg_s"] = 2.1
    declaration["input_sha256"] = fingerprint(case)
    numeric = check_case(case)
    assert numeric.checks[0].status == "PASS"  # Aggregate in/out mass = 3 kg/s.
    with pytest.raises(ContractError, match="not mass-closed"):
        review(case, declaration)


def test_review_requires_both_inlet_and_outlet_per_circuit():
    case, declaration = linked("steady_compressor")
    declaration["stream_properties"][1]["circuit_id"] = "separate_outlet_only"
    with pytest.raises(ContractError, match="requires both inlet and outlet"):
        review(case, declaration)


@pytest.mark.parametrize("key", ["fluid_id", "reference_state_id", "backend_id", "composition_id", "source_note"])
def test_blank_required_property_metadata_rejected(key):
    case, declaration = linked("steady_compressor")
    declaration["stream_properties"][0][key] = ""
    with pytest.raises(ContractError, match=key):
        review(case, declaration)


def test_unknown_reference_compatibility_does_not_infer_common_zero():
    case, declaration = linked("steady_compressor")
    declaration["stream_properties"][1]["reference_state_id"] = "UNKNOWN"
    with pytest.raises(ContractError, match="mismatched fluid/composition/backend/reference"):
        review(case, declaration)


def test_property_review_is_optional_and_does_not_modify_report_schema():
    case, declaration = linked("steady_compressor")
    original = check_case(case).as_dict()
    assert review(case, declaration) == "PASS_IN_SCOPE"
    assert check_case(case).as_dict() == original
    assert "reference_state_verified" not in original
    assert "property_review_status" not in original


def test_cli_synthetic_reviews_have_explicit_author_attribution(capsys):
    result = main([
        str(ROOT / "steady_heat_exchanger.json"),
        str(ROOT / "steady_heat_exchanger.property-review.json"),
    ])
    captured = capsys.readouterr()
    assert result == 0
    assert "PROPERTY_DECLARATION_COMPLETE" in captured.out
    assert "AUTHOR ATTESTATION ONLY" in captured.out


def test_cli_detects_compensated_mismatch_and_exits_2(capsys):
    result = main([
        str(ROOT / "steady_mismatched_reference_compensated.json"),
        str(ROOT / "steady_mismatched_reference_compensated.property-review.json"),
    ])
    assert result == 2
    assert "PROPERTY_REVIEW_INCOMPLETE" in capsys.readouterr().err
