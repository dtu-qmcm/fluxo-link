"""Tests for the semantic / tier validator (src/fluxolink/validate.py).

Each test starts from one small, fully valid isotope-MFA dataset and breaks
exactly one thing, so a failing test points at one rule. The schema-level
checks are exercised too, because `fluxolink-validate` runs both.
"""

import copy
from pathlib import Path

import pytest

from fluxolink.validate import (
    ERROR,
    WARNING,
    main,
    parse_positions,
    schema_issues,
    validate_dataset,
    validate_file,
)

EXAMPLES = Path(__file__).parent.parent / "examples"

BASE: dict = {
    "id": "DS",
    "dataset_type": "benchmark",
    "investigations": [{"id": "INV", "name": "Toy benchmark"}],
    "conditions": [
        {
            "id": "COND",
            "organism_name": "Escherichia coli",
            "strain": "K-12",
            "specific_growth_rate": 0.5,
            "growth_rate_unit": "1/h",
        }
    ],
    "networks": [
        {
            "id": "NET",
            "metabolites": [
                {"id": "A", "n_tracked_atoms": 3},
                {"id": "B", "n_tracked_atoms": 3},
                {"id": "C", "n_tracked_atoms": 2},
                {"id": "D", "n_tracked_atoms": 1},
            ],
            "reactions": [
                {
                    "id": "R1",
                    "reversibility": False,
                    "reactants": [{"metabolite_id": "A"}],
                    "products": [{"metabolite_id": "B"}],
                    "atom_transition_variants": [
                        {
                            "variant_id": "R1",
                            "transitions": [
                                {
                                    "reactant_metabolite_id": "A",
                                    "reactant_atom_index": i,
                                    "product_metabolite_id": "B",
                                    "product_atom_index": i,
                                }
                                for i in (1, 2, 3)
                            ],
                        }
                    ],
                },
                {
                    "id": "R2",
                    "reversibility": False,
                    "reactants": [{"metabolite_id": "B"}],
                    "products": [{"metabolite_id": "C"}, {"metabolite_id": "D"}],
                    "atom_transition_variants": [
                        {
                            "variant_id": "R2",
                            "transitions": [
                                {
                                    "reactant_metabolite_id": "B",
                                    "reactant_atom_index": 1,
                                    "product_metabolite_id": "D",
                                    "product_atom_index": 1,
                                },
                                {
                                    "reactant_metabolite_id": "B",
                                    "reactant_atom_index": 2,
                                    "product_metabolite_id": "C",
                                    "product_atom_index": 1,
                                },
                                {
                                    "reactant_metabolite_id": "B",
                                    "reactant_atom_index": 3,
                                    "product_metabolite_id": "C",
                                    "product_atom_index": 2,
                                },
                            ],
                        }
                    ],
                },
            ],
            "flux_constraints": [
                {
                    "id": "FC1",
                    "constraint_type": "equality",
                    "expression": "R1 = 100",
                }
            ],
        }
    ],
    "experiments": [
        {
            "id": "EXP",
            "investigation_id": "INV",
            "condition": "COND",
            "data_origin": "experimental",
            "network_model_id": "NET",
            "stationary": True,
            "labeled_sources": [
                {
                    "id": "LS",
                    "metabolite_id": "A",
                    "tracers": [
                        {
                            "labeling_pattern": "100",
                            "tracer_fraction": 0.8,
                            "isotopic_purity": 0.99,
                        },
                        {
                            "labeling_pattern": "000",
                            "tracer_fraction": 0.2,
                            "isotopic_purity": 1.0,
                        },
                    ],
                }
            ],
            "mid_measurements": [
                {
                    "id": "M_C",
                    "metabolite_id": "C",
                    "atom_positions": "1-2",
                    "analytical_method": "GC_MS",
                    "data_points": [
                        {"isotopologue_index": 0, "value": 0.7, "standard_deviation": 0.01},
                        {"isotopologue_index": 1, "value": 0.2, "standard_deviation": 0.01},
                        {"isotopologue_index": 2, "value": 0.1, "standard_deviation": 0.01},
                    ],
                }
            ],
            "flux_measurements": [
                {
                    "id": "F1",
                    "reaction_id": "R1",
                    "flux_type": "net",
                    "value": 100.0,
                    "standard_deviation": 1.0,
                }
            ],
        }
    ],
    "simulation_runs": [
        {
            "id": "RUN",
            "investigation_id": "INV",
            "network_model_id": "NET",
            "experiment_id": ["EXP"],
            "fluxomics_method": "IST_MFA",
            "run_mode": ["estimation"],
            "run_status": "completed",
            "optimization_method": "nlsic",
            "software": {"id": "SW", "software_name": "influx_si", "version": "7.4.3"},
            "flux_solution": {
                "id": "SOL",
                "solution_role": "estimated",
                "flux_results": [
                    {
                        "reaction_id": "R1",
                        "flux_type": "net",
                        "value": 100.0,
                        "lower_ci": 98.0,
                        "upper_ci": 102.0,
                        "flux_unit": "mmol/gDW/h",
                    }
                ],
            },
            "goodness_of_fit": {
                "wssr": 1.2,
                "degrees_of_freedom": 1,
                "chi_square_p_value": 0.27,
            },
        }
    ],
}


def _doc() -> dict:
    return copy.deepcopy(BASE)


def _rules(issues, severity=ERROR) -> set[str]:
    return {i.rule for i in issues if i.severity == severity}


def test_base_document_is_clean() -> None:
    """The reference document passes schema and semantic checks at the benchmark tier."""
    doc = _doc()
    assert schema_issues(doc) == []
    issues = validate_dataset(doc)
    assert issues == [], [str(i) for i in issues]


def test_dangling_reference_is_an_error() -> None:
    doc = _doc()
    doc["experiments"][0]["condition"] = "NOPE"
    assert "reference-integrity" in _rules(validate_dataset(doc))


def test_unknown_metabolite_in_measurement_is_an_error() -> None:
    doc = _doc()
    doc["experiments"][0]["mid_measurements"][0]["metabolite_id"] = "Z"
    assert "reference-integrity" in _rules(validate_dataset(doc))


def test_duplicate_ids_are_an_error() -> None:
    doc = _doc()
    doc["investigations"].append({"id": "INV", "name": "twin"})
    assert "duplicate-id" in _rules(validate_dataset(doc))


def test_stationary_experiment_with_inst_method_is_an_error() -> None:
    """Probe P1 of PATH_FORWARD §13.16: stationary=true with INST_MFA."""
    doc = _doc()
    doc["simulation_runs"][0]["fluxomics_method"] = "INST_MFA"
    assert "stationarity-method" in _rules(validate_dataset(doc))


def test_nonstationary_experiment_needs_time_points() -> None:
    """Probe P2: a non-stationary experiment whose data carry no time."""
    doc = _doc()
    doc["experiments"][0]["stationary"] = False
    doc["simulation_runs"][0]["fluxomics_method"] = "INST_MFA"
    issues = validate_dataset(doc)
    assert "inst-time" in _rules(issues)
    assert "inst-run-time" in _rules(issues, WARNING)


def test_tracer_fractions_above_one_are_an_error() -> None:
    """Probe P5: two forms summing to 1.6."""
    doc = _doc()
    doc["experiments"][0]["labeled_sources"][0]["tracers"][1]["tracer_fraction"] = 0.8
    assert "tracer-fraction-sum" in _rules(validate_dataset(doc))


def test_tracer_fractions_below_one_warn_about_natural_abundance() -> None:
    doc = _doc()
    doc["experiments"][0]["labeled_sources"][0]["tracers"][1]["tracer_fraction"] = 0.1
    assert "tracer-fraction-sum" in _rules(validate_dataset(doc), WARNING)


def test_labeling_pattern_longer_than_molecule_is_an_error() -> None:
    """Probe P4: a 4-position pattern on a 3-atom metabolite."""
    doc = _doc()
    doc["experiments"][0]["labeled_sources"][0]["tracers"][0]["labeling_pattern"] = "1000"
    assert "labeling-pattern-length" in _rules(validate_dataset(doc))


def test_atom_mapped_twice_is_an_error() -> None:
    """The INCA v51 contradiction: one reactant atom mapped to two product atoms."""
    doc = _doc()
    transitions = doc["networks"][0]["reactions"][1]["atom_transition_variants"][0]["transitions"]
    transitions[1]["reactant_atom_index"] = 1
    assert "atom-mapped-twice" in _rules(validate_dataset(doc))


def test_repeated_participant_needs_instance_index() -> None:
    doc = _doc()
    reaction = doc["networks"][0]["reactions"][1]
    reaction["products"].append({"metabolite_id": "D"})
    assert "participant-instance" in _rules(validate_dataset(doc))
    reaction["products"][-1]["instance"] = 2
    assert "participant-instance" not in _rules(validate_dataset(doc))


def test_atom_transition_must_name_a_participant_instance() -> None:
    doc = _doc()
    transition = doc["networks"][0]["reactions"][1]["atom_transition_variants"][0]["transitions"][
        0
    ]
    transition["product_instance"] = 2
    assert "atom-transition-participant" in _rules(validate_dataset(doc))


def test_dangling_atom_is_allowed() -> None:
    """An efflux atom with no product side is valid; a half-filled product side is not."""
    doc = _doc()
    transition = doc["networks"][0]["reactions"][1]["atom_transition_variants"][0]["transitions"][
        0
    ]
    del transition["product_metabolite_id"]
    del transition["product_atom_index"]
    assert schema_issues(doc) == []
    assert "atom-transition-incomplete" not in _rules(validate_dataset(doc))
    transition["product_metabolite_id"] = "D"
    assert "atom-transition-incomplete" in _rules(validate_dataset(doc))


def test_atom_index_beyond_molecule_is_an_error() -> None:
    doc = _doc()
    transition = doc["networks"][0]["reactions"][0]["atom_transition_variants"][0]["transitions"][
        0
    ]
    transition["product_atom_index"] = 4
    assert "atom-index-range" in _rules(validate_dataset(doc))


def test_ci_must_contain_value() -> None:
    doc = _doc()
    doc["simulation_runs"][0]["flux_solution"]["flux_results"][0]["lower_ci"] = 101.0
    assert "ci-order" in _rules(validate_dataset(doc))


def test_sampled_ci_may_exclude_the_estimate() -> None:
    """Monte Carlo quantiles can miss the point estimate; analytic intervals cannot."""
    doc = _doc()
    result = doc["simulation_runs"][0]["flux_solution"]["flux_results"][0]
    result["lower_ci"] = 101.0
    result["confidence_interval_method"] = "monte_carlo"
    issues = validate_dataset(doc)
    assert "ci-order" not in _rules(issues)
    assert "ci-order" in _rules(issues, WARNING)
    result["upper_ci"] = 100.5
    assert "ci-order" in _rules(validate_dataset(doc))


def test_constraint_needs_a_target() -> None:
    doc = _doc()
    del doc["networks"][0]["flux_constraints"][0]["expression"]
    assert "constraint-target" in _rules(validate_dataset(doc))


def test_flux_measurement_may_be_an_expression() -> None:
    doc = _doc()
    measurement = doc["experiments"][0]["flux_measurements"][0]
    del measurement["reaction_id"]
    assert "measurement-target" in _rules(validate_dataset(doc))
    measurement["flux_expression"] = "R1-R2"
    assert "measurement-target" not in _rules(validate_dataset(doc))


def test_isotope_run_without_experiment() -> None:
    doc = _doc()
    del doc["simulation_runs"][0]["experiment_id"]
    assert "isotope-method-experiment" in _rules(validate_dataset(doc))
    doc["dataset_type"] = "catalog"
    issues = validate_dataset(doc)
    assert "isotope-method-experiment" not in _rules(issues)
    assert "isotope-method-experiment" in _rules(issues, WARNING)


def test_completed_run_without_results_warns() -> None:
    doc = _doc()
    del doc["simulation_runs"][0]["flux_solution"]
    assert "results-extracted" in _rules(validate_dataset(doc), WARNING)


def test_other_needs_free_text() -> None:
    doc = _doc()
    doc["simulation_runs"][0]["software"]["software_name"] = "other"
    assert "other-companion" in _rules(validate_dataset(doc))


def test_growth_rate_needs_unit() -> None:
    doc = _doc()
    del doc["conditions"][0]["growth_rate_unit"]
    assert "growth-rate-unit" in _rules(validate_dataset(doc))


@pytest.mark.parametrize(
    ("where", "slot"),
    [
        (("experiments", 0, "labeled_sources", 0, "tracers", 0), "isotopic_purity"),
        (("experiments", 0, "labeled_sources", 0, "tracers", 0), "tracer_fraction"),
        (("experiments", 0, "mid_measurements", 0, "data_points", 0), "standard_deviation"),
        (("experiments", 0, "flux_measurements", 0), "standard_deviation"),
        (("experiments", 0, "flux_measurements", 0), "value"),
        (("experiments", 0), "labeled_sources"),
        (("experiments", 0, "mid_measurements", 0), "analytical_method"),
        (("simulation_runs", 0, "software"), "version"),
        (("simulation_runs", 0), "optimization_method"),
        (("simulation_runs", 0), "fluxomics_method"),
        (("conditions", 0), "specific_growth_rate"),
    ],
)
def test_benchmark_tier_requires_demoted_fields(where: tuple, slot: str) -> None:
    """Fields demoted to `recommended` in the schema are required at the benchmark tier only."""
    doc = _doc()
    target = doc
    for key in where:
        target = target[key]
    del target[slot]
    if slot == "specific_growth_rate":
        del target["growth_rate_unit"]
    assert schema_issues(doc) == [], "the field must no longer be schema-required"
    assert "benchmark-required" in _rules(validate_dataset(doc))
    doc["dataset_type"] = "catalog"
    assert "benchmark-required" not in _rules(validate_dataset(doc))


def test_synthetic_benchmark_needs_no_cultivation() -> None:
    """A synthetic benchmark has no culture, so it must not be forced to invent one."""
    doc = _doc()
    del doc["conditions"]
    exp = doc["experiments"][0]
    del exp["condition"]
    del exp["mid_measurements"][0]["analytical_method"]
    exp["data_origin"] = "synthetic"
    assert validate_dataset(doc) == []
    exp["data_origin"] = "experimental"
    assert "benchmark-required" in _rules(validate_dataset(doc))


def test_planned_run_needs_no_version() -> None:
    doc = _doc()
    run = doc["simulation_runs"][0]
    run["run_status"] = "planned"
    run["run_mode"] = []
    del run["flux_solution"]
    del run["goodness_of_fit"]
    del run["software"]["version"]
    del run["optimization_method"]
    assert "benchmark-required" not in _rules(validate_dataset(doc))


def test_reaction_needs_a_participant() -> None:
    doc = _doc()
    reaction = doc["networks"][0]["reactions"][0]
    del reaction["reactants"]
    assert schema_issues(doc) == [], "a pure influx reaction is schema-valid"
    assert "reaction-participants" not in _rules(validate_dataset(doc))
    del reaction["products"]
    del reaction["atom_transition_variants"]
    assert "reaction-participants" in _rules(validate_dataset(doc))


def test_all_zero_mid_group_is_flagged_as_placeholder() -> None:
    doc = _doc()
    for point in doc["experiments"][0]["mid_measurements"][0]["data_points"]:
        point["value"] = 0.0
    assert "mid-placeholder" in _rules(validate_dataset(doc), WARNING)


def _with_generated_inputs(doc: dict) -> dict:
    doc["source_files"] = [
        {"id": "SRC", "path": "model.fml", "format": "FluxML", "role": ["network"]},
        {
            "id": "GEN",
            "path": "runs/model.netw",
            "format": "MTF",
            "role": ["network"],
            "generated_by": "fluxomics_data_converter",
            "derived_from": ["SRC"],
        },
    ]
    doc["equivalence_checks"] = [
        {
            "id": "CHK",
            "files": ["GEN"],
            "network_model_id": "NET",
            "experiment_id": ["EXP"],
            "equivalent": True,
            "expected_differences": ["[reaction] A_out: drain added for terminal pool A"],
        }
    ]
    return doc


def test_equivalence_check_is_valid_and_consistent() -> None:
    doc = _with_generated_inputs(_doc())
    assert schema_issues(doc) == []
    assert validate_dataset(doc) == []
    doc["equivalence_checks"][0]["differences"] = ["[tracer] GLC: purity 0.99 vs none"]
    assert "equivalence-consistency" in _rules(validate_dataset(doc))
    doc["equivalence_checks"][0]["equivalent"] = False
    assert "equivalence-consistency" not in _rules(validate_dataset(doc))


def test_derived_from_must_resolve() -> None:
    doc = _with_generated_inputs(_doc())
    doc["source_files"][1]["derived_from"] = ["NOPE"]
    assert "reference-integrity" in _rules(validate_dataset(doc))
    doc["source_files"][1]["derived_from"] = ["GEN"]
    assert "reference-integrity" in _rules(validate_dataset(doc))


def test_parse_positions() -> None:
    assert parse_positions("1-3,5") == [1, 2, 3, 5]
    assert parse_positions("2,3") == [2, 3]
    assert parse_positions(4) == [4]
    assert parse_positions("C1") is None


@pytest.mark.integration
@pytest.mark.parametrize("name", [p.name for p in sorted((EXAMPLES / "valid").glob("*.yaml"))])
def test_valid_examples_have_no_semantic_errors(name: str) -> None:
    """Every valid fixture also passes the semantic checks at its own tier."""
    issues = validate_file(EXAMPLES / "valid" / name)
    errors = [str(i) for i in issues if i.severity == ERROR]
    assert errors == []


@pytest.mark.integration
def test_cli_exit_codes(tmp_path: Path) -> None:
    import yaml

    good = tmp_path / "good.yaml"
    good.write_text(yaml.safe_dump(_doc()), encoding="utf-8")
    assert main([str(good), "-q"]) == 0
    bad_doc = _doc()
    bad_doc["experiments"][0]["condition"] = "NOPE"
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump(bad_doc), encoding="utf-8")
    assert main([str(bad), "-q"]) == 1
    assert main([str(bad), "--no-schema", "-q"]) == 1
