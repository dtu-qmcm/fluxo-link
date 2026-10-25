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
SCHEMA = Path(__file__).parent.parent / "src" / "fluxolink" / "schema" / "fluxolink.yaml"
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


@pytest.mark.integration
def test_benchmark_tier_requires_materialised_network() -> None:
    """A benchmark-tier dataset without a materialised network must be rejected.

    Guards the FluxoDataset tier rule. The same content at the catalog tier
    validates (examples/valid/simple_model_mtf_catalog.yaml), so this proves
    the rule fires on `dataset_type` rather than on the content itself.

    The rule deliberately does NOT require `experiments`: a stoichiometry-based
    run has no tracer, so requiring a LabelingExperiment would force it to
    fabricate one. "Isotope-based method implies a labeling experiment" cannot
    be a LinkML rule (fluxomics_method is nested on SimulationRun and
    slot_conditions cannot nest) and belongs to the Phase 7 validator.
    """
    result = _validate(EXAMPLES / "invalid" / "benchmark_tier_missing_inputs.yaml")
    assert result.returncode != 0, "expected validation to fail but it passed"
    output = result.stdout + result.stderr
    assert "networks" in output


@pytest.mark.integration
def test_catalog_tier_needs_no_materialised_inputs() -> None:
    """A catalog-tier dataset must validate with no networks and no experiments.

    The counterpart of the test above: before the tier fix, every catalog
    document had to fabricate a stub MetabolicNetworkModel purely to satisfy
    the then-required SimulationRun.network_model_id.
    """
    import yaml

    catalog = EXAMPLES / "valid" / "simple_model_mtf_catalog.yaml"
    doc = yaml.safe_load(catalog.read_text())
    assert doc["dataset_type"] == "catalog"
    assert "networks" not in doc
    assert "experiments" not in doc
    assert _validate(catalog).returncode == 0


@pytest.mark.integration
def test_stoichiometric_benchmark_needs_no_labeling_experiment() -> None:
    """A benchmark-tier dataset with no experiments must validate.

    The acceptance test for the 2026-09-18 rule change. A constraint_based run
    has no tracer, so requiring `experiments` at the benchmark tier forced it
    to fabricate a LabelingExperiment plus a TracerIsotopomer with invented
    tracer_fraction and isotopic_purity.
    """
    import yaml

    fixture = EXAMPLES / "valid" / "fba_benchmark_no_experiment.yaml"
    doc = yaml.safe_load(fixture.read_text())
    assert doc["dataset_type"] == "benchmark"
    assert "experiments" not in doc
    assert doc["simulation_runs"][0]["fluxomics_method"] == "constraint_based"
    assert _validate(fixture).returncode == 0


@pytest.mark.integration
def test_conditions_are_referenced_not_inlined() -> None:
    """Conditions live once at dataset level and are referenced by id.

    Before 2026-09-18 both LabelingExperiment.condition and
    SimulationRun.condition inlined their own copy, so one cultivation could be
    described twice with no shared identity and no way to detect divergence.
    """
    import yaml

    doc = yaml.safe_load((EXAMPLES / "valid" / "simple_model_dataset.yaml").read_text())
    declared = {c["id"] for c in doc["conditions"]}
    assert declared == {"COND1", "COND_FBA"}
    for experiment in doc["experiments"]:
        assert experiment["condition"] in declared
    for run in doc["simulation_runs"]:
        if "condition" in run:
            assert run["condition"] in declared
