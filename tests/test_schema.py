"""Tests for schema loading and validation."""

from pathlib import Path
from typing import ClassVar

import yaml

SCHEMA_DIR = Path(__file__).parent.parent / "src" / "fluxolink" / "schema"


def _load_yaml(filename: str) -> dict:
    """Load a YAML file from the schema directory."""
    path = SCHEMA_DIR / filename
    with open(path) as f:
        return yaml.safe_load(f)


class TestSchemaLoading:
    """Tests that all schema YAML files load without errors."""

    def test_main_schema_loads(self) -> None:
        """Test that the main fluxolink.yaml loads."""
        data = _load_yaml("fluxolink.yaml")
        assert data["id"] == "https://w3id.org/fluxolink"
        assert data["name"] == "fluxolink"

    def test_enumerations_schema_loads(self) -> None:
        """Test that the enumerations schema loads."""
        data = _load_yaml("enumerations.yaml")
        assert "enums" in data
        assert "MFASoftwareEnum" in data["enums"]

    def test_investigation_schema_loads(self) -> None:
        """Test that the investigation schema loads."""
        data = _load_yaml("investigation.yaml")
        assert "classes" in data
        assert "Investigation" in data["classes"]

    def test_network_schema_loads(self) -> None:
        """Test that the network schema loads."""
        data = _load_yaml("network.yaml")
        assert "classes" in data
        assert "MetabolicNetworkModel" in data["classes"]
        assert "AtomTransition" in data["classes"]

    def test_experiment_schema_loads(self) -> None:
        """Test that the experiment schema loads."""
        data = _load_yaml("experiment.yaml")
        assert "classes" in data
        assert "LabelingExperiment" in data["classes"]

    def test_simulation_run_schema_loads(self) -> None:
        """Test that the simulation_run schema loads."""
        data = _load_yaml("simulation_run.yaml")
        assert "classes" in data
        assert "SimulationRun" in data["classes"]


class TestEnumerations:
    """Tests that enumerations contain expected values."""

    def test_mfa_software_enum(self) -> None:
        """Test that all target MFA software tools are present."""
        data = _load_yaml("enumerations.yaml")
        software = data["enums"]["MFASoftwareEnum"]["permissible_values"]
        expected = ["freeflux", "13CFLUX2", "influx_si", "INCA"]
        for tool in expected:
            assert tool in software, f"Missing software: {tool}"

    def test_flux_type_enum(self) -> None:
        """Test that flux type enumeration has net/forward/backward/exchange."""
        data = _load_yaml("enumerations.yaml")
        flux_types = data["enums"]["FluxTypeEnum"]["permissible_values"]
        assert set(["net", "forward", "backward", "exchange"]).issubset(set(flux_types.keys()))

    def test_enums_have_ontology_meaning(self) -> None:
        """Test that enum values reference FLUXO ontology terms."""
        data = _load_yaml("enumerations.yaml")
        for _enum_name, enum_def in data["enums"].items():
            for _value_name, value_def in enum_def["permissible_values"].items():
                if "meaning" in value_def:
                    assert value_def["meaning"].startswith("fluxo:FLUXO_"), (
                        f"Invalid meaning URI: {value_def['meaning']}"
                    )


class TestOntologyMapping:
    """Tests that classes have correct ontology mappings."""

    def test_investigation_has_class_uri(self) -> None:
        """Test that Investigation class maps to FLUXO_0000162."""
        data = _load_yaml("investigation.yaml")
        investigation = data["classes"]["Investigation"]
        assert investigation.get("class_uri") == "fluxo:FLUXO_0000162"

    def test_metabolite_has_class_uri(self) -> None:
        """Test that NetworkMetabolite maps to FLUXO_0000172."""
        data = _load_yaml("network.yaml")
        metabolite = data["classes"]["NetworkMetabolite"]
        assert metabolite.get("class_uri") == "fluxo:FLUXO_0000172"

    def test_atom_transition_has_class_uri(self) -> None:
        """Test that AtomTransition maps to FLUXO_0000155."""
        data = _load_yaml("network.yaml")
        at = data["classes"]["AtomTransition"]
        assert at.get("class_uri") == "fluxo:FLUXO_0000155"

    def test_labeling_experiment_has_class_uri(self) -> None:
        """Test that LabelingExperiment maps to FLUXO_0000049."""
        data = _load_yaml("experiment.yaml")
        le = data["classes"]["LabelingExperiment"]
        assert le.get("class_uri") == "fluxo:FLUXO_0000049"


class TestOntologyScopedEnums:
    """Pin the enums whose membership is defined by a FLUXO subtree.

    These guard the failure mode that produced Phase 3t-0: values disappearing
    from an enum while descriptions elsewhere still promise them, with nothing
    failing. Membership here is not a matter of taste — it is whatever the
    ontology places under the stated parent — so the expected sets are written
    out in full and compared exactly.
    """

    # FLUXO:0000021 "fluxomics method" is_a IAO:0000104 plan specification.
    EXPECTED_METHODS: ClassVar[dict[str, str]] = {
        "I_MFA": "fluxo:FLUXO_0000041",
        "C13_MFA": "fluxo:FLUXO_0000042",
        "IST_MFA": "fluxo:FLUXO_0000043",
        "INST_MFA": "fluxo:FLUXO_0000044",
        "dynamic_MFA": "fluxo:FLUXO_0000045",
        "kinetic_flux_profiling": "fluxo:FLUXO_0000295",
        "stoichiometry_based": "fluxo:FLUXO_0000018",
        "constraint_based": "fluxo:FLUXO_0000019",
        "kinetic_modeling": "fluxo:FLUXO_0000294",
    }

    # FLUXO:0000162 "fluxomics investigation" is_a COB:0000035 executed process.
    EXPECTED_INVESTIGATION_TYPES: ClassVar[dict[str, str]] = {
        "MFA": "fluxo:FLUXO_0000040",
        "FBA": "fluxo:FLUXO_0000039",
    }

    def _meanings(self, enum_name: str) -> dict:
        enums = _load_yaml("enumerations.yaml")["enums"]
        values = enums[enum_name]["permissible_values"]
        return {k: (v or {}).get("meaning") for k, v in values.items()}

    def test_fluxomics_method_enum_matches_ontology_subtree(self) -> None:
        """FluxomicsMethodEnum is exactly the FLUXO:0000021 subtree."""
        assert self._meanings("FluxomicsMethodEnum") == self.EXPECTED_METHODS

    def test_investigation_type_enum_matches_ontology_subtree(self) -> None:
        """InvestigationTypeEnum is exactly the FLUXO:0000162 subtree."""
        assert self._meanings("InvestigationTypeEnum") == self.EXPECTED_INVESTIGATION_TYPES

    def test_investigation_terms_are_not_methods(self) -> None:
        """FBA/MFA are investigations, so they must not appear as methods.

        FLUXO:0000039 and FLUXO:0000040 are is_a "fluxomics investigation", not
        is_a "fluxomics method". Mapping either into the method enum — as
        `FBA -> FLUXO_0000039` did until 2026-09-18 — is a category error.
        """
        method_meanings = set(self._meanings("FluxomicsMethodEnum").values())
        assert "fluxo:FLUXO_0000039" not in method_meanings
        assert "fluxo:FLUXO_0000040" not in method_meanings
