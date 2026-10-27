"""Predeclared developer-selected negative controls; not measured fault accuracy."""

from __future__ import annotations

import copy
import json

import pytest

from enerlint import check_case
from enerlint.cli import main as cli_main
from enerlint.verify import ContractError
from scripts.run_negative_controls import (
    CATALOG, ROOT, apply_mutation, canonical_hash, git_blob_hash, run, tagged_nonfinite,
)

KINDS = {
    "fault": 18, "schema_probe": 11,
    "blind_spot": 6, "metadata_only": 1, "clean_control": 3,
}


@pytest.fixture(scope="module")
def frozen():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def outcomes():
    return run()


def test_frozen_register_has_39_cases_six_immutable_baselines(frozen):
    rows = frozen["cases"]
    assert [r["id"] for r in rows] == [f"NC-{i:03d}" for i in range(1, 40)]
    assert set(frozen["baselines"]) == {
        "steady_compressor", "steady_turbine", "steady_heat_exchanger",
        "steady_nonadiabatic_compressor", "steady_splitter_adiabatic", "storage_interval",
    }
    assert frozen["mutation_seed"] == "OEM-NC11-DETERMINISTIC-V0.1-NO-RNG"
    assert all(row["change"]["op"] and row["interpretation"] for row in rows)
    assert {kind: sum(r["kind"] == kind for r in rows) for kind in KINDS} == KINDS
    for name, meta in frozen["baselines"].items():
        raw = (ROOT / meta["file"]).read_bytes()
        assert meta["file"] == f"examples/{name}.json"
        assert git_blob_hash(raw) == meta["git_blob_sha1"]
        assert check_case(json.loads(raw)).status == "PASS_IN_SCOPE"


def test_ledger_replays_all_mutations_and_preserves_outcomes(outcomes):
    assert outcomes["summary"] == {
        "total_cases": 39,
        "declared_balance_faults_flagged": 18,
        "invalid_contracts_rejected_without_physics": 11,
        "developer_known_escapes": 6,
        "unobservable_metadata_only_changes": 1,
        "healthy_transformations_remain_in_scope": 3,
        "independent_external_reviews": 0,
    }
    assert len(outcomes["catalog_sha256"]) == 64
    assert len({r["mutator_sha256"] for r in outcomes["cases"]}) == 39
    assert all(r["expected_status"] == r["observed_status"] for r in outcomes["cases"])
    assert all(len(r["base_git_blob_sha1"]) == 40 for r in outcomes["cases"])
    assert all(len(r["mutated_case_sha256_tagged"]) == 64 for r in outcomes["cases"])


@pytest.mark.parametrize("number", range(1, 40))
def test_mutator_reconstructs_expected_case_class(frozen, number):
    row = frozen["cases"][number - 1]
    baseline = json.loads((ROOT / frozen["baselines"][row["base"]]["file"]).read_text())
    original = copy.deepcopy(baseline)
    changed = apply_mutation(baseline, row["change"])
    assert baseline == original
    assert canonical_hash(tagged_nonfinite(changed)) != canonical_hash(original)
    if row["expected_outcome"] == "INVALID_INPUT":
        with pytest.raises(ContractError):
            check_case(changed)
    else:
        assert check_case(changed).status == row["expected_outcome"]


def test_declared_failures_are_distinct_from_schema_rejections(outcomes):
    for row in outcomes["cases"]:
        if row["scenario_kind"] == "fault":
            assert row["observed_status"] == "FAIL"
            assert row["checks"]
            assert not row["input_rejection"]
            assert any(check["status"] == "FAIL" for check in row["checks"])
        elif row["scenario_kind"] == "schema_probe":
            assert row["observed_status"] == "INVALID_INPUT"
            assert row["checks"] == []
            assert row["input_rejection"]


def test_blind_spots_preserve_known_escapes(outcomes):
    spots = [r for r in outcomes["cases"] if r["scenario_kind"] == "blind_spot"]
    assert len(spots) == 6
    assert all(r["observed_status"] == "PASS_IN_SCOPE" for r in spots)
    omitted_capacity = next(r for r in spots if r["family"] == "missing_optional")
    assert next(c for c in omitted_capacity["checks"]
                if c["name"] == "storage_capacity")["status"] == "NOT_CHECKED"
    near_tolerance = next(r for r in spots if r["family"] == "tolerance")
    energy = next(c for c in near_tolerance["checks"] if c["name"] == "steady_first_law")
    assert energy["status"] == "PASS"
    assert energy["residual"] != 0
    assert abs(energy["residual"]) <= energy["threshold"]


def test_timestamp_probes_do_not_claim_temporal_validation(outcomes):
    rejected = [r for r in outcomes["cases"] if r["family"] == "time_schema"]
    assert len(rejected) == 2
    assert all(r["observed_status"] == "INVALID_INPUT" for r in rejected)
    description_only = next(r for r in outcomes["cases"] if r["scenario_kind"] == "metadata_only")
    assert description_only["observed_status"] == "PASS_IN_SCOPE"
    assert "no timestamp validation" in " ".join(outcomes["scientific_limitations"]).lower()


def test_nonfinite_exceptions_are_tagged_without_leaking_nonstandard_json(outcomes):
    for row in (r for r in outcomes["cases"] if r["family"] == "nonfinite"):
        assert row["observed_status"] == "INVALID_INPUT"
        encoded = json.dumps(row["mutated_case_tagged"], allow_nan=False)
        assert "$nonfinite_python_value" in encoded
        assert "NaN" in encoded or "Infinity" in encoded


def test_clean_controls_are_not_counted_as_fault_detection(outcomes):
    controls = [r for r in outcomes["cases"] if r["scenario_kind"] == "clean_control"]
    assert len(controls) == 3
    assert all(r["observed_status"] == "PASS_IN_SCOPE" for r in controls)
    assert all(r["checks"] for r in controls)


@pytest.mark.parametrize(
    "number,exit_code",
    [(1, 1), (19, 2), (30, 0), (34, 0)],
)
def test_cli_exit_codes_for_fault_reject_and_known_escape(tmp_path, frozen, number, exit_code):
    row = frozen["cases"][number - 1]
    base = json.loads((ROOT / frozen["baselines"][row["base"]]["file"]).read_text())
    mutated = apply_mutation(base, row["change"])
    filename = tmp_path / (row["id"] + ".json")
    filename.write_text(json.dumps(mutated, allow_nan=False) + "\n", encoding="utf-8")
    assert cli_main(["check", str(filename), "--output", str(tmp_path / "report.json")]) == exit_code
    output = json.loads((tmp_path / "report.json").read_text())
    assert output["status"] == row["expected_outcome"]
    if exit_code == 2:
        assert output["checks"] == []
