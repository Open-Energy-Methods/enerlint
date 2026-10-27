"""Build-artifact smoke check in *fresh* environments, away from the source tree.

Usage after `python -m build`:
    python scripts/verify_distributions.py

This is a packaging/CLI reproducibility gate, not scientific peer review.
Runs on Python 3.10+ using only the standard library.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
EXAMPLE = ROOT / "examples" / "steady_compressor.json"


def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode not in (0,):
        raise RuntimeError(
            f"Command failed ({result.returncode}): {command!r}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def check_code(command: list[str], *, cwd: Path, expected: int) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != expected:
        raise AssertionError(
            f"Expected exit {expected}, got {result.returncode}: {command!r}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def interpreter(environment: Path) -> Path:
    if sys.platform == "win32":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def check_wheel_contents(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert any(p == "enerlint/verify.py" for p in names), "Missing runtime module in wheel"
        assert any(p.startswith("enerlint-") and p.endswith(".dist-info/METADATA") for p in names), (
            "Missing wheel package metadata"
        )
        assert not any("founders_research_bible" in p.lower() for p in names), (
            "Do not ship private planning documents"
        )


def check_install(artifact: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="enerlint-distribution-") as folder:
        scratch = Path(folder).resolve()
        environment = scratch / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        py = interpreter(environment)
        assert py.is_file(), f"Expected interpreter at {py}"
        run([str(py), "-m", "pip", "install", "--no-deps", str(artifact)], cwd=scratch)

        # Working outside the checkout avoids accidentally importing the local src/ directory.
        result = run(
            [
                str(py), "-c",
                "import enerlint, pathlib; "
                "print(pathlib.Path(enerlint.__file__).resolve())",
            ],
            cwd=scratch,
        )
        installed_file = Path(result.stdout.strip()).resolve()
        assert installed_file.is_relative_to(environment), (
            f"Imported the wrong module, not from isolated venv: {installed_file}"
        )

        passing = check_code(
            [str(py), "-m", "enerlint", "check", str(EXAMPLE)],
            cwd=scratch,
            expected=0,
        )
        passing_report = json.loads(passing.stdout)
        assert passing_report["status"] == "PASS_IN_SCOPE"
        assert passing_report["case_id"] == "synthetic_adiabatic_compressor"

        # Make one physically inconsistent case without relying on package fault helpers.
        baseline = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        baseline["shaft_work_out_w"] = 240000.0
        bad_input = scratch / "work_sign_wrong.json"
        bad_input.write_text(json.dumps(baseline), encoding="utf-8")
        failed = check_code(
            [str(py), "-m", "enerlint", "check", str(bad_input)],
            cwd=scratch,
            expected=1,
        )
        failed_report = json.loads(failed.stdout)
        assert failed_report["status"] == "FAIL"
        assert "steady_first_law" in {
            x["name"] for x in failed_report["checks"] if x["status"] == "FAIL"
        }

        # Invalid inputs must never silently turn into an apparent pass.
        del baseline["heat_into_volume_w"]
        invalid_input = scratch / "missing_heat.json"
        invalid_input.write_text(json.dumps(baseline), encoding="utf-8")
        invalid = check_code(
            [str(py), "-m", "enerlint", "check", str(invalid_input)],
            cwd=scratch,
            expected=2,
        )
        assert "INVALID_INPUT" in invalid.stderr
        print(f"PASS isolated {artifact.name} | import, PASS, FAIL, INVALID_INPUT")


def main() -> int:
    wheels = sorted(DIST.glob("enerlint-*.whl"))
    sdists = sorted(DIST.glob("enerlint-*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError(
            f"Expected one wheel and one sdist under dist/, got {wheels!r} and {sdists!r}. "
            "Run 'python -m build' after clearing dist/."
        )
    check_wheel_contents(wheels[0])
    for artifact in wheels + sdists:
        check_install(artifact)
    print("Both distribution formats imported and ran from isolated environments.")
    print("This checks packaging and declared CLI behavior only, not external scientific validity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
