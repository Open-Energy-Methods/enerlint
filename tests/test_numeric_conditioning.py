"""Numerical conditioning review: arithmetic disagreement, not empirical V&V."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit_numeric_conditioning import audit_text, main as audit_cli
from scripts.run_tolerance_precision_stress import CATALOG, ROOT, run, text_case


@pytest.fixture(scope="module")
def stress():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def evidence():
    return run()


def test_ten_frozen_cases_include_both_kinds_of_precision_error(stress, evidence):
    assert len(stress["cases"]) == 10
    assert evidence["summary"] == {
        "total": 10,
        "DECIMAL_BINARY_AGREEMENT": 7,
        "DECISION_DISAGREEMENT": 2,
        "CORE_REJECTED": 1,
        "independent_external_reviews": 0,
    }
    assert len({row["submitted_json_sha256"] for row in evidence["cases"]}) == 10
    assert all(row["observation"]["classification"] == row["expected"]["classification"]
               for row in evidence["cases"])


def test_datum_shift_causes_false_failure_relative_to_textual_decimal_oracle(evidence):
    case = evidence["cases"][2]
    result = case["observation"]
    assert case["id"] == "TP-003"
    assert result["classification"] == "DECISION_DISAGREEMENT"
    assert result["core_status"] == "FAIL"
    by_name = {row["name"]: row for row in result["checks"]}
    energy = by_name["steady_first_law"]
    assert energy["exact_decimal_status"] == "PASS"
    assert energy["decimal_json_residual"] == "0"
    assert abs(energy["core_binary64_residual"]) == 128.0
    assert energy["decision_disagreement"]
    assert energy["review_threshold_triggered"]


def test_lost_one_joule_per_kilogram_is_missed_at_large_offset(evidence):
    case = evidence["cases"][3]
    assert case["id"] == "TP-004"
    energy = next(row for row in case["observation"]["checks"]
                  if row["name"] == "steady_first_law")
    assert energy["exact_decimal_status"] == "FAIL"
    assert energy["decimal_json_residual"] == "-2"
    assert energy["core_status"] == "PASS"
    assert energy["core_binary64_residual"] == 0
    assert case["observation"]["core_status"] == "PASS_IN_SCOPE"


def test_normal_datum_shift_is_benign_and_balances_agree(evidence):
    for index in [0, 1]:
        x = evidence["cases"][index]["observation"]
        assert x["classification"] == "DECIMAL_BINARY_AGREEMENT"
        assert x["core_status"] == "PASS_IN_SCOPE"
        assert next(r for r in x["checks"]
                    if r["name"] == "steady_first_law")["decimal_json_residual"] == "0"


def test_input_tolerance_floor_is_not_zero_physical_residual(evidence):
    near = evidence["cases"][8]["observation"]
    past = evidence["cases"][9]["observation"]
    near_check = next(x for x in near["checks"] if x["name"] == "steady_first_law")
    past_check = next(x for x in past["checks"] if x["name"] == "steady_first_law")
    assert near_check["decimal_json_residual"] == "-0.50"
    assert near_check["exact_decimal_status"] == "PASS"
    assert past_check["decimal_json_residual"] == "-1.50"
    assert past_check["exact_decimal_status"] == "FAIL"


def test_nonrepresentable_float_input_abstains_not_passes(evidence):
    x = evidence["cases"][7]["observation"]
    assert x["classification"] == "CORE_REJECTED"
    assert x["core_status"] == "INVALID_INPUT"
    assert not x["evaluated"]
    assert x["checks"] == []


def test_advisory_does_not_change_core_report_schema(load_case):
    case = load_case("steady_compressor")
    before = json.dumps(case)
    result = audit_text(before)
    assert result["classification"] == "DECIMAL_BINARY_AGREEMENT"
    assert case == json.loads(before)
    assert result["core_schema_version"] == "0.1.0"
    assert "notes" not in result


def test_cli_exit_1_on_decimal_binary_disagreement(tmp_path, stress, capsys):
    scenario = stress["cases"][2]
    base = json.loads((ROOT / "examples/steady_compressor.json").read_text())
    raw = text_case(base, scenario["edits"])
    path = tmp_path / "shift.json"
    out = tmp_path / "advisory.json"
    path.write_text(raw, encoding="utf-8")
    assert audit_cli([str(path), "--output", str(out)]) == 1
    result = json.loads(out.read_text())
    assert result["classification"] == "DECISION_DISAGREEMENT"
    assert json.loads(capsys.readouterr().out)["classification"] == "DECISION_DISAGREEMENT"


def test_cli_exit_zero_when_stable(tmp_path, capsys, load_case):
    path = tmp_path / "normal.json"
    path.write_text(json.dumps(load_case("steady_compressor")), encoding="utf-8")
    assert audit_cli([str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["core_status"] == "PASS_IN_SCOPE"


def test_decimal_literal_edits_are_not_prequantized(stress):
    scenario = stress["cases"][3]
    base = json.loads((ROOT / "examples/steady_compressor.json").read_text())
    text = text_case(base, scenario["edits"])
    assert "10000000000420001" in text
    assert '"10000000000420001"' not in text
    assert json.loads(text)["outlets"][0]["specific_enthalpy_j_kg"] == 10000000000420001
