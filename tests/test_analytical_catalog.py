"""Frozen ten-case analytical catalogue; independent reference arithmetic self-tests.

Maintainer-authored expected values and failure mutations are not external
scientific reviews. Never infer population detection or validation rates.
"""

from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path

import pytest

from enerlint import check_case
from scripts.run_analytical_catalog import (
    CATALOG, ROOT, _mutated, execute, independent_arithmetic,
)

EXPECTED_IDS = {
    *(f"TH-CV-{i:03d}" for i in range(1, 9)),
    "TH-ST-001", "TH-ST-002",
}


@pytest.fixture(scope="module")
def catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def test_ten_distinct_cards_span_requested_thermal_families(catalog):
    rows = catalog["cases"]
    assert len(rows) == 10
    assert {r["benchmark_id"] for r in rows} == EXPECTED_IDS
    labels = " ".join(r["system"].lower() for r in rows)
    for component in ("compressor", "turbine", "mixer", "splitter", "exchanger", "storage"):
        assert component in labels
    assert all(r["benchmark_version"] == "0.1" for r in rows)
    assert all(r["reviewer_status"].startswith("Maintainer-authored") for r in rows)
    assert "not independently peer reviewed" in catalog["author_review_status"]


def test_every_case_is_a_public_existing_synthetic_json_file(catalog):
    for row in catalog["cases"]:
        path = ROOT / row["case_file"]
        assert path.is_relative_to(ROOT / "examples")
        assert path.is_file()
        obj = json.loads(path.read_text(encoding="utf-8"))
        assert obj["schema_version"] == "0.1.0"
        assert obj["provenance"]["evidence_class"] == "hand_constructed"
        assert row["source_permission"].startswith("Maintainer-declared")
        assert row["expected_report_status"] == "PASS_IN_SCOPE"


def test_decimal_oracle_checks_ten_positive_and_ten_negative_cases():
    result = execute()
    assert result["summary"] == {
        "selected_baselines_pass": 10,
        "selected_baselines_total": 10,
        "selected_faults_flagged": 10,
        "selected_faults_total": 10,
        "external_independent_reviews": 0,
    }
    assert len({x["case_sha256"] for x in result["cases"]}) == 10
    assert len(result["catalog_sha256"]) == 64
    assert all(row["baseline_status"] == "PASS_IN_SCOPE" for row in result["cases"])
    assert all(row["negative_control_status"] == "FAIL" for row in result["cases"])


@pytest.mark.parametrize(
    "benchmark_id",
    [f"TH-CV-{i:03d}" for i in range(1, 9)] + ["TH-ST-001", "TH-ST-002"],
)
def test_frozen_mutation_is_distinct_from_unchanged_baseline(catalog, benchmark_id):
    row = next(r for r in catalog["cases"] if r["benchmark_id"] == benchmark_id)
    case = json.loads((ROOT / row["case_file"]).read_text(encoding="utf-8"))
    mutation = row["deliberate_mutation"]
    changed = _mutated(case, mutation["field"], mutation["replacement"])
    assert changed != case
    assert changed["case_id"] == case["case_id"]
    oracle = independent_arithmetic(changed)
    failing = oracle[mutation["expected_failure_check"]]
    assert failing["status"] == "FAIL"
    assert failing["residual"] == Decimal(str(mutation["expected_failure_residual"]))


def test_mixer_and_splitter_have_physical_mass_and_energy_closure(catalog):
    for label in ("TH-CV-005", "TH-CV-006"):
        row = next(r for r in catalog["cases"] if r["benchmark_id"] == label)
        obj = json.loads((ROOT / row["case_file"]).read_text(encoding="utf-8"))
        checks = independent_arithmetic(obj)
        assert checks["steady_mass_closure"]["residual"] == Decimal("0")
        assert checks["steady_first_law"]["residual"] == Decimal("0")
        report = check_case(obj)
        assert report.status == "PASS_IN_SCOPE"
        assert set(x.name for x in report.checks) == {
            "steady_mass_closure", "steady_first_law"
        }


def test_storage_missing_capacity_is_explicitly_not_checked(catalog):
    row = next(r for r in catalog["cases"] if r["benchmark_id"] == "TH-ST-002")
    obj = json.loads((ROOT / row["case_file"]).read_text(encoding="utf-8"))
    assert "capacity_j" not in obj
    checks = check_case(obj).checks
    assert [c.status for c in checks] == ["PASS", "NOT_CHECKED"]
    assert checks[1].residual is None
    assert checks[1].threshold is None


def test_independent_analytical_oracle_does_not_need_enerlint_verification(monkeypatch):
    # Independent arithmetic uses SI case fields, not check_case internals.
    case = json.loads((ROOT / "examples/steady_mixer_adiabatic.json").read_text())
    def broken_checker(_):
        raise AssertionError("not allowed to call checker for reference arithmetic")
    monkeypatch.setattr("scripts.run_analytical_catalog.check_case", broken_checker)
    oracle = independent_arithmetic(case)
    assert oracle["steady_first_law"]["residual"] == Decimal(0)
    assert oracle["steady_first_law"]["scale"] == Decimal(480000)


def test_catalogue_does_not_replace_four_case_foundation_benchmark():
    from scripts.run_foundation_benchmark import run

    old = run()
    assert old["summary"]["synthetic_baselines_total"] == 4
    assert old["summary"]["deliberate_faults_total"] == 6
    assert old["summary"]["known_compensating_error_escaped"] is True


def test_unchanged_target_compensation_remains_an_escape():
    source = json.loads((ROOT / "examples/steady_compressor.json").read_text())
    wrong = copy.deepcopy(source)
    for stream in wrong["inlets"] + wrong["outlets"]:
        stream["mass_flow_kg_s"] *= 1.1
    wrong["shaft_work_out_w"] *= 1.1
    assert wrong["shaft_work_out_w"] != source["shaft_work_out_w"]
    assert check_case(wrong).status == "PASS_IN_SCOPE"
