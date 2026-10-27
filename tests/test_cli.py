import json
from pathlib import Path

import pytest

from enerlint.cli import main


def test_cli_valid_report(tmp_path, load_case, capsys):
    case_path = tmp_path / "case.json"
    case_path.write_text(json.dumps(load_case("steady_compressor")), encoding="utf-8")
    output = tmp_path / "reports" / "result.json"
    assert main(["check", str(case_path), "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "PASS_IN_SCOPE"
    assert "PASS_IN_SCOPE" in capsys.readouterr().out


def test_cli_failed_balance_exit_1(tmp_path, load_case):
    case = load_case("steady_compressor")
    case["shaft_work_out_w"] = 240000
    case_path = tmp_path / "bad.json"
    case_path.write_text(json.dumps(case), encoding="utf-8")
    assert main(["check", str(case_path)]) == 1


def test_cli_invalid_contract_exit_2(tmp_path, load_case, capsys):
    case = load_case("steady_compressor")
    del case["inlets"]
    case_path = tmp_path / "missing.json"
    case_path.write_text(json.dumps(case), encoding="utf-8")
    assert main(["check", str(case_path)]) == 2
    assert "INVALID_INPUT" in capsys.readouterr().err


def test_cli_invalid_json_and_missing_file_exit_2(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not-json", encoding="utf-8")
    assert main(["check", str(path)]) == 2
    assert main(["check", str(tmp_path / "not_here.json")]) == 2


def test_unsupported_kind_rejected(load_case):
    x = load_case("steady_compressor")
    x["kind"] = "certify_nuclear_reactor"
    from enerlint.verify import ContractError, check_case
    with pytest.raises(ContractError, match="Unsupported"):
        check_case(x)
