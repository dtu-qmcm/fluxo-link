"""Validation tests for the example datasets in examples/.

These run the merged schema against real, hand-authored FluxoDataset
instances (positive) and a deliberately-broken instance (negative), so the
Phase 3j required-field constraints are proven to fire. Validation is done
via the `linkml-validate` CLI, which resolves schema imports relative to the
schema file (the in-process validate() helper resolves them against CWD).
"""

import subprocess
import sys
from pathlib import Path

import pytest

BIN = Path(sys.executable).parent
VALIDATE = BIN / "linkml-validate"
SCHEMA = Path(__file__).parent.parent / "src" / "fluxo_schema" / "schema" / "fluxo_schema.yaml"
EXAMPLES = Path(__file__).parent.parent / "examples"


def _validate(data_file: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(VALIDATE), "-s", str(SCHEMA), str(data_file)],
        capture_output=True,
        text=True,
    )


@pytest.mark.integration
@pytest.mark.parametrize("name", [p.name for p in sorted((EXAMPLES / "valid").glob("*.yaml"))])
def test_valid_examples_pass(name: str) -> None:
    """Every dataset under examples/valid/ must validate cleanly."""
    result = _validate(EXAMPLES / "valid" / name)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.integration
def test_invalid_example_is_rejected() -> None:
    """The invalid dataset must fail on the intentionally-omitted required fields."""
    result = _validate(EXAMPLES / "invalid" / "missing_required_fields.yaml")
    assert result.returncode != 0, "expected validation to fail but it passed"
    output = result.stdout + result.stderr
    assert "tracer_fraction" in output
    assert "isotopic_purity" in output
    assert "standard_deviation" in output
