"""Published JSON Schema and CLI compatibility tests for alpha report v0.1.0.

JSON Schema is a development-only dependency, not a runtime requirement.
All cases are developer-constructed: no external scientific validation implied.
"""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from importlib.resources import files

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from enerlint import check_case
from enerlint.cli import main
from enerlint.models import CheckResult, InvalidInputReport, serialize_report


@pytest.fixture(scope="module")
def validator():
    text = (
        files("enerlint")
        .joinpath("schemas", "report-v0.1.0.schema.json")
        .read_text(encoding="utf-8")
    )
    schema = json.loads(text)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize(
    "example",
    ["steady_compressor", "steady_turbine", "steady_heat_exchanger", "storage_interval"],
)
def test_current_reference_reports_validate(validator, load_case, example):
    report = check_case(load_case(example))
    validator.validate(report.as_dict())
    assert report.schema_version == "0.1.0"


def test_failed_physical_balance_report_validates(validator, load_case):
    case = load_case("steady_compressor")
    case["shaft_work_out_w"] = 240000.0
    report = check_case(case)
    assert report.status == "FAIL"
    validator.validate(report.as_dict())


def test_optional_capacity_stays_not_checked_and_pass_in_scope(validator, load_case):
    case = load_case("storage_interval")
    del case["capacity_j"]
    report = check_case(case)
    assert report.status == "PASS_IN_SCOPE"
    assert [c.status for c in report.checks] == ["PASS", "NOT_CHECKED"]
    validator.validate(report.as_dict())
    skipped = report.as_dict()["checks"][1]
    assert skipped["name"] == "storage_capacity"
    assert all(skipped[key] is None for key in ("residual", "unit", "scale", "threshold"))


def test_not_checked_cannot_be_relabelled_pass(validator, load_case):
    case = load_case("storage_interval")
    del case["capacity_j"]
    report = check_case(case)
    bad = report.as_dict()
    bad["checks"][1]["status"] = "PASS"
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_not_checked_cannot_have_a_numeric_residual(validator, load_case):
    case = load_case("storage_interval")
    del case["capacity_j"]
    report = check_case(case)
    bad = report.as_dict()
    bad["checks"][1]["residual"] = 0.0
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_scoped_pass_must_contain_an_evaluated_pass(validator, load_case):
    report = check_case(load_case("steady_compressor"))
    empty_pass = replace(
        report,
        checks=(CheckResult("storage_capacity", "NOT_CHECKED", "Capacity not provided"),),
    )
    with pytest.raises(AssertionError):
        empty_pass.assert_passed()
    with pytest.raises(ValidationError):
        validator.validate(empty_pass.as_dict())


def test_scoped_pass_cannot_contain_failed_checks(validator, load_case):
    case = load_case("steady_compressor")
    case["shaft_work_out_w"] = 240000.0
    report = check_case(case)
    bad = report.as_dict()
    bad["status"] = "PASS_IN_SCOPE"
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_fail_status_requires_at_least_one_failed_check(validator, load_case):
    report = check_case(load_case("steady_compressor"))
    bad = report.as_dict()
    bad["status"] = "FAIL"
    with pytest.raises(ValidationError):
        validator.validate(bad)


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", "0.2.0"),
        ("case_id", None),
        ("source_fingerprint_sha256", "not-a-sha"),
    ],
)
def test_schema_rejects_incompatible_or_missing_required_metadata(
    validator, load_case, field, value
):
    report = check_case(load_case("steady_compressor"))
    bad = report.as_dict()
    bad[field] = value
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_schema_rejects_unknown_check_identifier(validator, load_case):
    report = check_case(load_case("steady_compressor"))
    bad = report.as_dict()
    bad["checks"][0]["name"] = "certified_physics"
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_schema_rejects_extra_fields_in_root_or_check(validator, load_case):
    report = check_case(load_case("steady_compressor"))
    for target in ("root", "check"):
        bad = report.as_dict()
        if target == "root":
            bad["accredited"] = True
        else:
            bad["checks"][0]["accredited"] = True
        with pytest.raises(ValidationError):
            validator.validate(bad)


def test_schema_rejects_incorrect_check_unit(validator, load_case):
    report = check_case(load_case("steady_compressor"))
    bad = report.as_dict()
    bad["checks"][0]["unit"] = "W"
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_serialization_is_byte_identical_across_repeated_calls(validator, load_case):
    report = check_case(load_case("steady_compressor"))
    first = serialize_report(report)
    second = serialize_report(report)
    assert first == second
    assert first.endswith("\n")
    assert list(json.loads(first)) == sorted(json.loads(first))
    validator.validate(json.loads(first))
    assert json.loads(first) == report.as_dict()


def test_valid_json_roundtrip_preserves_not_checked(validator, load_case):
    case = load_case("storage_interval")
    del case["capacity_j"]
    report = check_case(case)
    data = json.loads(serialize_report(report))
    assert data["checks"][1]["status"] == "NOT_CHECKED"
    assert json.dumps(data, sort_keys=True) == json.dumps(report.as_dict(), sort_keys=True)
    validator.validate(data)


def test_invalid_input_report_has_no_fabricated_provenance(validator):
    rejected = InvalidInputReport(
        schema_version="0.1.0",
        enerlint_version="0.1.0a0",
        errors=("case: missing required field(s): inlets",),
    )
    data = json.loads(serialize_report(rejected))
    assert data["status"] == "INVALID_INPUT"
    assert data["case_id"] is None
    assert data["source_fingerprint_sha256"] is None
    assert data["checks"] == []
    validator.validate(data)


def test_invalid_input_without_explanation_rejected(validator):
    bad = InvalidInputReport(
        schema_version="0.1.0",
        enerlint_version="0.1.0a0",
        errors=("error",),
    ).as_dict()
    bad["errors"] = []
    with pytest.raises(ValidationError):
        validator.validate(bad)


@pytest.mark.parametrize("invalid_type", ["contract", "syntax", "missing_file"])
def test_cli_invalid_input_writes_machine_readable_report(
    validator, tmp_path, capsys, load_case, invalid_type
):
    case_path = tmp_path / "input.json"
    if invalid_type == "contract":
        case = load_case("steady_compressor")
        del case["shaft_work_out_w"]
        case_path.write_text(json.dumps(case), encoding="utf-8")
    elif invalid_type == "syntax":
        case_path.write_text("{broken json", encoding="utf-8")
    else:
        case_path = tmp_path / "does_not_exist.json"
    output = tmp_path / "reports" / "rejected.json"
    assert main(["check", str(case_path), "--output", str(output)]) == 2
    captured = capsys.readouterr()
    assert "INVALID_INPUT" in captured.err
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["status"] == "INVALID_INPUT"
    assert data["errors"]
    assert data["checks"] == []
    assert data["source_fingerprint_sha256"] is None
    validator.validate(data)


def test_cli_success_and_failure_still_obey_existing_exit_codes(
    validator, load_case, tmp_path, capsys
):
    case = load_case("steady_compressor")
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "report.json"
    input_path.write_text(json.dumps(case), encoding="utf-8")
    assert main(["check", str(input_path), "--output", str(output_path)]) == 0
    pass_report = json.loads(output_path.read_text(encoding="utf-8"))
    validator.validate(pass_report)
    assert pass_report["status"] == "PASS_IN_SCOPE"

    case["shaft_work_out_w"] = 240000.0
    input_path.write_text(json.dumps(case), encoding="utf-8")
    assert main(["check", str(input_path), "--output", str(output_path)]) == 1
    failed_report = json.loads(output_path.read_text(encoding="utf-8"))
    validator.validate(failed_report)
    assert failed_report["status"] == "FAIL"
    assert any(check["status"] == "FAIL" for check in failed_report["checks"])
    capsys.readouterr()
