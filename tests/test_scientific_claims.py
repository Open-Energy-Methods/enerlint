"""Scientific-claim boundaries supported by concrete alpha counterexamples.

These tests are *negative evidence checks*, not an automated natural-language
claim auditor. The policy and all examples remain author-written and unreviewed.
"""
from __future__ import annotations

import copy
import json
from importlib.resources import files
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from enerlint import check_case
from enerlint.models import InvalidInputReport

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs" / "claim_examples_v0.1.json"
POLICY = ROOT / "docs" / "SCIENTIFIC_CLAIM_POLICY.md"


def test_claim_examples_have_explicit_decisions_and_limitations():
    data = json.loads(EXAMPLES.read_text(encoding="utf-8"))
    assert data["schema_version"] == "0.1.0"
    assert data["policy_id"] == "oem-enerlint-scientific-claims-v0.1"
    assert "not a universal" in data["purpose"]
    examples = data["examples"]
    assert len(examples) >= 16
    ids = [example["id"] for example in examples]
    assert len(ids) == len(set(ids))
    decisions = {example["decision"] for example in examples}
    assert decisions == {"ALLOWED", "REJECT"}
    for entry in examples:
        assert set(entry) == {
            "id", "decision", "claim", "available_evidence", "limitation", "scenario"
        }
        assert all(isinstance(value, str) and bool(value.strip()) for value in entry.values())
    for scenario in (
        "steady_cv_pass", "compensating_pass", "storage_missing_capacity",
        "author_claim_experimental", "ci_only", "invalid_input",
        "author_boundary_attestation", "planned_d1"
    ):
        matched = [example for example in examples if example["scenario"] == scenario]
        assert any(example["decision"] == "ALLOWED" for example in matched), scenario
        assert any(example["decision"] == "REJECT" for example in matched), scenario


def test_public_policy_identifies_oem_labels_as_unaccredited_and_specific():
    source = POLICY.read_text(encoding="utf-8")
    assert "not a certified maturity scale" in source
    assert "not an automatic" not in source or "automatic" in source
    for descriptor in ("V0 —", "V1 —", "V2 —", "V3 —", "V4 —", "V5 —"):
        assert descriptor in source
    for distinct_term in (
        "Verification", "Validation", "Uncertainty quantification",
        "Calibration", "Certification",
    ):
        assert distinct_term.lower() in source.lower()
    assert "ASME" in source and "not a certified" in source
    assert "NOT_CHECKED" in source and "PASS_IN_SCOPE" in source


def test_physically_wrong_operating_point_can_pass_both_checks(load_case):
    reference = load_case("steady_compressor")
    target = check_case(reference)
    wrong = copy.deepcopy(reference)
    for port in wrong["inlets"] + wrong["outlets"]:
        port["mass_flow_kg_s"] *= 1.1
    wrong["shaft_work_out_w"] *= 1.1
    computed = check_case(wrong)

    assert wrong["inlets"][0]["mass_flow_kg_s"] != reference["inlets"][0]["mass_flow_kg_s"]
    assert wrong["shaft_work_out_w"] != reference["shaft_work_out_w"]
    assert target.status == computed.status == "PASS_IN_SCOPE"
    assert all(check.status == "PASS" for check in computed.checks)
    assert [check.residual for check in computed.checks] == [0.0, 0.0]
    assert computed.source_fingerprint_sha256 != target.source_fingerprint_sha256
    # There is no independent reference/measurement in the checker output.
    assert "operating_point_verified" not in computed.as_dict()


def test_scoped_storage_pass_does_not_check_omitted_capacity(load_case):
    case = load_case("storage_interval")
    case.pop("capacity_j")
    report = check_case(case)
    assert report.status == "PASS_IN_SCOPE"
    by_name = {c.name: c for c in report.checks}
    assert by_name["storage_energy_closure"].status == "PASS"
    capacity = by_name["storage_capacity"]
    assert capacity.status == "NOT_CHECKED"
    assert (capacity.residual, capacity.scale, capacity.threshold, capacity.unit) == (
        None, None, None, None
    )


def test_fake_experimental_declaration_does_not_change_physics_or_prove_origin(load_case):
    case = load_case("steady_compressor")
    original = check_case(case)
    labeled = copy.deepcopy(case)
    labeled["provenance"]["evidence_class"] = "experimental"
    labeled["provenance"]["declared_source"] = (
        "Author asserts measurement provenance, without independent evidence"
    )
    report = check_case(labeled)
    assert report.status == original.status == "PASS_IN_SCOPE"
    assert [(c.name, c.residual) for c in report.checks] == [
        (c.name, c.residual) for c in original.checks
    ]
    assert report.evidence_class == "experimental"
    assert report.declared_source == labeled["provenance"]["declared_source"]
    assert report.source_fingerprint_sha256 != original.source_fingerprint_sha256
    assert "provenance_authenticity_verified" not in report.as_dict()
    assert any("not independently authenticated" in s for s in report.limitations)


def test_invalid_input_contains_no_physical_checks():
    report = InvalidInputReport(
        schema_version="0.1.0", enerlint_version="0.1.0a0",
        errors=("Required shaft work was omitted",),
    )
    assert report.status == "INVALID_INPUT"
    assert report.as_dict()["checks"] == []
    assert report.as_dict()["case_id"] is None


@pytest.mark.parametrize("extra_field", ["validated", "accredited", "certified", "evidence_tier"])
def test_versioned_report_schema_rejects_unearned_evidence_fields(load_case, extra_field):
    source = files("enerlint").joinpath("schemas", "report-v0.1.0.schema.json")
    schema = json.loads(source.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    report = check_case(load_case("steady_compressor")).as_dict()
    validator.validate(report)
    report[extra_field] = True if extra_field != "evidence_tier" else "V5"
    with pytest.raises(ValidationError):
        validator.validate(report)


def test_missing_author_boundary_check_does_not_prevent_numeric_pass(load_case):
    # The optional, separate preflight is not required by strict v0.1 check_case.
    # No code path can see a pipe/auxiliary transfer absent from the source JSON.
    report = check_case(load_case("steady_compressor"))
    assert report.status == "PASS_IN_SCOPE"
    assert "boundary_completeness_certified" not in report.as_dict()
    assert any("boundary" in s.lower() for s in report.limitations)
