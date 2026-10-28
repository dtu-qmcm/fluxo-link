"""Tests for the flat flux table (fluxolink-flatten) and the core profile page."""

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from fluxolink.flatten import COLUMNS, flux_records, main

ROOT = Path(__file__).parent.parent
VALID = ROOT / "examples" / "valid"
FLUX_RECORD_SCHEMA = ROOT / "src" / "fluxolink" / "schema" / "flux_record.yaml"


def _load(name: str) -> dict:
    return yaml.safe_load((VALID / name).read_text(encoding="utf-8"))


def test_one_row_per_flux_result() -> None:
    doc = _load("simple_model_mtf_roundtrip.yaml")
    rows = flux_records(doc)
    expected = sum(
        len((run.get("flux_solution") or {}).get("flux_results") or [])
        for run in doc["simulation_runs"]
    )
    assert len(rows) == expected > 0
    assert all(list(row) == COLUMNS for row in rows)
    r2 = next(r for r in rows if r["reaction_id"] == "R2" and r["flux_type"] == "net")
    assert r2["value"] == 110.0
    assert r2["software_name"] == "influx_si"
    assert r2["run_mode"] == "forward_simulation"
    assert r2["solution_role"] == "reference"


def test_context_is_joined_from_the_record() -> None:
    rows = flux_records(_load("minimal_core_record.yaml"))
    assert len(rows) == 2
    pgi = rows[0]
    assert pgi["organism_name"] == "Escherichia coli"
    assert pgi["strain"] == "BW25113"
    assert pgi["specific_growth_rate"] == 0.6
    assert pgi["stationary"] is True
    assert pgi["tracer"] == "Gluc_ext: 100000 x 0.8, 111111 x 0.2"
    assert pgi["investigation_name"].startswith("Glucose 13C-MFA")
    assert (pgi["lower_ci"], pgi["upper_ci"], pgi["confidence_level"]) == (58.0, 64.1, 0.95)
    assert pgi["chi_square_p_value"] == 0.30


def test_other_software_uses_its_free_text_name() -> None:
    rows = flux_records(_load("simple_model_dataset.yaml"))
    assert {r["software_name"] for r in rows} == {"freeflux", "COBRApy"}


def test_rows_validate_against_the_flux_record_schema(tmp_path: Path) -> None:
    rows = []
    for path in sorted(VALID.glob("*.yaml")):
        rows += flux_records(yaml.safe_load(path.read_text(encoding="utf-8")))
    table = {"records": [{k: v for k, v in r.items() if v is not None} for r in rows]}
    out = tmp_path / "table.yaml"
    out.write_text(yaml.safe_dump(table), encoding="utf-8")
    validate = Path(sys.executable).parent / "linkml-validate"
    result = subprocess.run(
        [str(validate), "-s", str(FLUX_RECORD_SCHEMA), "-C", "FluxRecordTable", str(out)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        # linkml-validate reads files with the locale encoding; ours are UTF-8.
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cli_writes_csv_and_jsonl(tmp_path: Path) -> None:
    source = str(VALID / "minimal_core_record.yaml")
    csv_out = tmp_path / "f.csv"
    assert main([source, "-o", str(csv_out)]) == 0
    lines = csv_out.read_text(encoding="utf-8").splitlines()
    assert lines[0].split(",")[:3] == ["dataset_id", "run_id", "reaction_id"]
    assert len(lines) == 3
    jsonl = tmp_path / "f.jsonl"
    assert main([source, "-o", str(jsonl)]) == 0
    first = json.loads(jsonl.read_text(encoding="utf-8").splitlines()[0])
    assert first["reaction_id"] == "PGI"


def test_core_profile_page_is_up_to_date() -> None:
    """docs/core_profile.md is generated from the schema; it must not be stale."""
    script = ROOT / "scripts" / "gen_core_profile.py"
    result = subprocess.run(
        [sys.executable, str(script), "--check"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_core_subset_is_small() -> None:
    """The core profile stays a small fraction of the schema."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from gen_core_profile import render

    page = render()
    header = next(line for line in page.splitlines() if "core fields in" in line)
    n_core = int(header.split("**")[1].split()[0])
    assert 40 <= n_core <= 70
