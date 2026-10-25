from __future__ import annotations

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer
)


metamodel_version = "1.11.0"
version = "0.1.0"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias = True,
        validate_by_name = True,
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )





class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'fluxo',
     'default_range': 'string',
     'description': 'A LinkML data model for metabolic flux analysis (MFA) '
                    'investigations, including isotope-based MFA (13C-MFA, '
                    'IST-MFA, INST-MFA) and stoichiometry-based methods (FBA). '
                    'Grounded in the FLUXO ontology. Supports data from tools such '
                    'as freeflux, 13CFLUX2, influx_si, INCA, COBRApy, and others.',
     'id': 'https://w3id.org/fluxolink',
     'imports': ['linkml:types',
                 'enumerations',
                 'investigation',
                 'network',
                 'experiment',
                 'simulation_run'],
     'license': 'Apache-2.0',
     'name': 'fluxolink',
     'prefixes': {'ORCID': {'prefix_prefix': 'ORCID',
                            'prefix_reference': 'http://identifiers.org/orcid/'},
                  'fluxo': {'prefix_prefix': 'fluxo',
                            'prefix_reference': 'http://purl.obolibrary.org/obo/'},
                  'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'},
                  'obo': {'prefix_prefix': 'obo',
                          'prefix_reference': 'http://purl.obolibrary.org/obo/'},
                  'schema': {'prefix_prefix': 'schema',
                             'prefix_reference': 'http://schema.org/'}},
     'source_file': 'src/fluxolink/schema/fluxolink.yaml',
     'title': 'FluxoLink'} )

class MFASoftwareEnum(str, Enum):
    """
    13C-MFA software tools as defined in the FLUXO ontology.
    """
    freeflux = "freeflux"
    """
    FreeFlux - open source Python package for MFA
    """
    number_13CFLUX2 = "13CFLUX2"
    """
    13CFLUX2 - MFA software using FluxML
    """
    influx_si = "influx_si"
    """
    influx_si - MFA software with FTBL input
    """
    INCA = "INCA"
    """
    INCA - Isotopomer Network Compartmental Analysis (MATLAB)
    """
    mfapy = "mfapy"
    """
    MFApy - Python MFA package
    """
    OpenFLUX2 = "OpenFLUX2"
    """
    OpenFLUX2 - open source MFA tool
    """
    BayFlux = "BayFlux"
    """
    BayFlux - Bayesian flux estimation
    """
    other = "other"
    """
    Other software not listed; specify via the companion software_name_other free-text slot.
    """


class FluxomicsMethodEnum(str, Enum):
    """
    Fluxomics method types — every value is a descendant of FLUXO:0000021 ("fluxomics method"), which is_a IAO:0000104 plan specification. A method is the plan a SimulationRun realises. Investigation types (FLUXO:0000039 flux balance analysis, FLUXO:0000040 metabolic flux analysis) are is_a "fluxomics investigation", not methods — see InvestigationTypeEnum.
    """
    I_MFA = "I_MFA"
    """
    Isotope-based metabolic flux analysis — the parent method, used when the labeling regime is left unspecified.
    """
    C13_MFA = "C13_MFA"
    """
    13C metabolic flux analysis
    """
    IST_MFA = "IST_MFA"
    """
    Isotopically stationary MFA
    """
    INST_MFA = "INST_MFA"
    """
    Isotopically non-stationary MFA
    """
    dynamic_MFA = "dynamic_MFA"
    """
    Dynamic isotope-based MFA
    """
    kinetic_flux_profiling = "kinetic_flux_profiling"
    """
    Kinetic flux profiling
    """
    stoichiometry_based = "stoichiometry_based"
    """
    Stoichiometry-based fluxomics method — no isotope labeling, so no tracer, atom transitions or MID measurements.
    """
    constraint_based = "constraint_based"
    """
    Constraint-based fluxomics method — the method realised by a flux balance analysis investigation.
    """
    kinetic_modeling = "kinetic_modeling"
    """
    Kinetic modeling fluxomics method
    """


class InvestigationTypeEnum(str, Enum):
    """
    Fluxomics investigation types — the FLUXO:0000162 ("fluxomics investigation") subtree. An investigation is a completely executed planned process; the method it realises is recorded per run in FluxomicsMethodEnum.
    """
    MFA = "MFA"
    """
    Metabolic flux analysis
    """
    FBA = "FBA"
    """
    Flux balance analysis
    """


class InputFormatEnum(str, Enum):
    """
    File formats used as input for MFA software tools.
    """
    FluxML = "FluxML"
    """
    FluxML XML format
    """
    FTBL = "FTBL"
    """
    FTBL tabular format
    """
    MTF = "MTF"
    """
    MTF format
    """
    freeflux_csv = "freeflux_csv"
    """
    FreeFlux CSV format
    """
    INCA_mat = "INCA_mat"
    """
    INCA MATLAB .mat format
    """
    other = "other"
    """
    Other input format not listed; specify via the companion input_format_other free-text slot.
    """


class IsotopicStateSpaceEnum(str, Enum):
    """
    Isotopic state-space representations used in MFA computation.
    """
    isotopomer = "isotopomer"
    """
    Isotopomer representation
    """
    cumomer = "cumomer"
    """
    Cumomer representation
    """
    EMU = "EMU"
    """
    Elementary Metabolite Unit representation
    """


class AnalyticalMethodEnum(str, Enum):
    """
    Analytical measurement methods for isotopologue data.
    """
    GC_MS = "GC_MS"
    """
    Gas chromatography-mass spectrometry
    """
    LC_MS = "LC_MS"
    """
    Liquid chromatography-mass spectrometry
    """
    tandem_MS = "tandem_MS"
    """
    Tandem mass spectrometry (MS/MS)
    """
    IRMS = "IRMS"
    """
    Isotope ratio mass spectrometry
    """
    NMR = "NMR"
    """
    Nuclear magnetic resonance
    """
    other = "other"
    """
    Other analytical method not listed; specify via the companion analytical_method_other free-text slot.
    """


class FluxTypeEnum(str, Enum):
    """
    Types of metabolic flux values.
    """
    net = "net"
    """
    Net flux (forward minus backward)
    """
    forward = "forward"
    """
    Forward flux
    """
    backward = "backward"
    """
    Backward (reverse) flux
    """
    exchange = "exchange"
    """
    Exchange flux (min of forward and backward)
    """


class AtomAnnotationTypeEnum(str, Enum):
    """
    Annotation notation types for atom transitions.
    """
    letter = "letter"
    """
    Letter-based atom annotation (a-z, A-Z)
    """
    FluxML = "FluxML"
    """
    FluxML-defined atom mapping notation
    """
    InChI = "InChI"
    """
    InChI-based atom mapping notation
    """


class ReactionTypeEnum(str, Enum):
    """
    Types of reactions in a metabolic network model.
    """
    metabolic = "metabolic"
    """
    Standard metabolic reaction
    """
    transport = "transport"
    """
    Transport reaction between compartments
    """
    exchange = "exchange"
    """
    Exchange reaction at network boundary
    """
    biomass = "biomass"
    """
    Abstract biomass reaction
    """
    demand = "demand"
    """
    Demand reaction
    """
    sink = "sink"
    """
    Sink reaction
    """


class ConstraintTypeEnum(str, Enum):
    """
    Types of flux constraints.
    """
    equality = "equality"
    """
    Flux equality constraint (fixed linear combination)
    """
    inequality = "inequality"
    """
    Flux inequality constraint (bounds on combination)
    """
    bound = "bound"
    """
    Individual flux bound (lower/upper)
    """


class ScaleMethodEnum(str, Enum):
    """
    Scaling methods for measurement groups.
    """
    auto = "auto"
    """
    Automatic scaling
    """
    one = "one"
    """
    Scale to one
    """


class ConfidenceIntervalMethodEnum(str, Enum):
    """
    Method used to compute confidence intervals on estimated fluxes or pool sizes. No FLUXO terms; left unmapped.
    """
    profile_likelihood = "profile_likelihood"
    """
    Profile-likelihood / parameter continuation
    """
    parameter_continuation = "parameter_continuation"
    """
    Parameter continuation (sensitivity-based)
    """
    bootstrap = "bootstrap"
    """
    Monte Carlo bootstrap resampling
    """
    grid_search = "grid_search"
    """
    Grid search over parameter space
    """
    other = "other"
    """
    Other method not listed
    """


class NMRMultipletTypeEnum(str, Enum):
    """
    13C NMR multiplet types indicating the labeling state of neighboring carbon atoms. No FLUXO terms; left unmapped.
    """
    S = "S"
    """
    Singlet — carbon unlabeled, neighbors unlabeled.
    """
    DL = "DL"
    """
    Left doublet — carbon labeled, left neighbor unlabeled.
    """
    DR = "DR"
    """
    Right doublet — carbon labeled, right neighbor unlabeled.
    """
    DD = "DD"
    """
    Double doublet — carbon labeled, both neighbors unlabeled.
    """
    T = "T"
    """
    Triplet — carbon labeled, both neighbors labeled.
    """


class FileRoleEnum(str, Enum):
    """
    Role a source file plays in a fluxomics dataset. Mapped to the FLUXO concept the file content represents (not a "file role" per se — FLUXO has no file-role hierarchy; the content class is the closest semantic anchor).
    """
    network = "network"
    """
    Metabolic network model file.
    """
    measurements = "measurements"
    """
    Measurement data file (MID, NMR, flux, pool size).
    """
    tracer = "tracer"
    """
    Tracer / labeled source specification file.
    """
    constraints = "constraints"
    """
    Flux or pool size constraint file.
    """
    simulation = "simulation"
    """
    Simulation configuration / setup file.
    """
    results = "results"
    """
    Simulation output / results file.
    """
    configuration = "configuration"
    """
    Tool or run configuration file.
    """
    other = "other"
    """
    Other role not listed; specify via the SourceFile description free-text slot.
    """


class DatasetTypeEnum(str, Enum):
    """
    Classification of a FluxoDataset by curation tier. FLUXO has no benchmark/catalog dataset distinction; left unmapped pending ontology terms.
    """
    benchmark = "benchmark"
    """
    Tier-2-complete dataset carrying input ground truth (network + experiment + measurements). Subject to the VALIDATION_REQUIREMENTS ruleset.
    """
    catalog = "catalog"
    """
    Tier-1 dataset cataloging results with minimal provenance; Tier-2 input content is optional.
    """



class Investigation(ConfiguredBaseModel):
    """
    A fluxomics investigation comprising one or more isotope labeling experiments or simulation studies.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000162',
         'from_schema': 'https://w3id.org/fluxolink/investigation'})

    id: str = Field(default=..., description="""Unique identifier for the investigation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    name: str = Field(default=..., description="""Human-readable name of the investigation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'LabelingExperiment',
                       'Condition',
                       'FluxoDataset']} })
    description: Optional[str] = Field(default=None, description="""Detailed description of the investigation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation', 'SourceFile', 'FluxoDataset']} })
    publication_doi: Optional[str] = Field(default=None, description="""DOI of the associated publication.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation']} })
    investigation_type: Optional[InvestigationTypeEnum] = Field(default=None, description="""Kind of fluxomics investigation this is (FLUXO:0000162 subtree). Distinct from SimulationRun.fluxomics_method: the investigation is the executed process, the method is the plan each run realises, and one investigation may realise several.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation']} })
    contributors: Optional[list[Contributor]] = Field(default=None, description="""List of contributors to this investigation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation']} })


class Contributor(ConfiguredBaseModel):
    """
    A person who contributed to a fluxomics investigation.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000253',
         'from_schema': 'https://w3id.org/fluxolink/investigation'})

    id: str = Field(default=..., description="""Unique identifier for the contributor.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    name: str = Field(default=..., description="""Full name of the contributor.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'LabelingExperiment',
                       'Condition',
                       'FluxoDataset'],
         'slot_uri': 'fluxo:FLUXO_0000255'} })
    orcid: Optional[str] = Field(default=None, description="""ORCID identifier of the contributor.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Contributor'], 'slot_uri': 'fluxo:FLUXO_0000256'} })
    email: Optional[str] = Field(default=None, description="""Email address of the contributor.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Contributor'], 'slot_uri': 'fluxo:FLUXO_0000257'} })
    organization: Optional[str] = Field(default=None, description="""Affiliated organization.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Contributor'], 'slot_uri': 'fluxo:FLUXO_0000258'} })


class MetabolicNetworkModel(ConfiguredBaseModel):
    """
    A computational representation of a metabolic network, including metabolites, reactions, compartments, and atom transitions.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000127',
         'from_schema': 'https://w3id.org/fluxolink/network'})

    id: str = Field(default=..., description="""Unique identifier for the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    name: Optional[str] = Field(default=None, description="""Human-readable name of the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'LabelingExperiment',
                       'Condition',
                       'FluxoDataset']} })
    compartments: Optional[list[str]] = Field(default=None, description="""List of compartment names in the model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel'], 'slot_uri': 'fluxo:FLUXO_0000058'} })
    metabolites: list[NetworkMetabolite] = Field(default=..., description="""Metabolite definitions in the network.""", min_length=1, json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel']} })
    reactions: list[NetworkReaction] = Field(default=..., description="""Reaction definitions in the network.""", min_length=1, json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel']} })
    flux_constraints: Optional[list[FluxConstraint]] = Field(default=None, description="""Constraints on reaction flux values (bounds, equalities, linear-combination constraints).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel']} })
    pool_size_constraints: Optional[list[PoolSizeConstraint]] = Field(default=None, description="""Constraints on metabolite pool size values.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel']} })


class NetworkMetabolite(ConfiguredBaseModel):
    """
    A metabolite in a metabolic network model.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000172',
         'from_schema': 'https://w3id.org/fluxolink/network'})

    id: str = Field(default=..., description="""Unique metabolite identifier (e.g., G6P_c).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    name: Optional[str] = Field(default=None, description="""Human-readable metabolite name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'LabelingExperiment',
                       'Condition',
                       'FluxoDataset']} })
    formula: Optional[str] = Field(default=None, description="""Chemical formula of the metabolite.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite'], 'slot_uri': 'fluxo:FLUXO_0000199'} })
    charge: Optional[int] = Field(default=None, description="""Metabolite's molecular charge.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite'], 'slot_uri': 'fluxo:FLUXO_0000200'} })
    compartment: Optional[str] = Field(default=None, description="""Compartment where the metabolite resides.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite'], 'slot_uri': 'fluxo:FLUXO_0000058'} })
    n_tracked_atoms: Optional[int] = Field(default=None, description="""Number of atoms of the tracer element in this metabolite (e.g., 6 for carbons in glucose).""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite'], 'slot_uri': 'fluxo:FLUXO_0000183'} })
    inchi: Optional[str] = Field(default=None, description="""InChI identifier for the metabolite.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite'], 'slot_uri': 'fluxo:FLUXO_0000239'} })
    smiles: Optional[str] = Field(default=None, description="""SMILES representation of the metabolite.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite'], 'slot_uri': 'fluxo:FLUXO_0000240'} })
    is_pseudo: Optional[bool] = Field(default=False, description="""Whether this is a pseudo-metabolite (e.g., biomass) with no biological counterpart.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite', 'NetworkReaction'],
         'ifabsent': 'false',
         'slot_uri': 'fluxo:FLUXO_0000061'} })
    aliases: Optional[str] = Field(default=None, description="""Tool-namespaced alternative identifiers (e.g., \"influx_si:v5\", \"freeflux:R1\"). The canonical↔native ID mapping is new information present in no native file — it lives in the dataset, once per entity.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite', 'NetworkReaction']} })


class NetworkReaction(ConfiguredBaseModel):
    """
    A biochemical reaction in a metabolic network model.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000005',
         'from_schema': 'https://w3id.org/fluxolink/network'})

    id: str = Field(default=..., description="""Unique reaction identifier (e.g., PGI, SCS).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    name: Optional[str] = Field(default=None, description="""Human-readable reaction name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'LabelingExperiment',
                       'Condition',
                       'FluxoDataset']} })
    reversibility: bool = Field(default=True, description="""Whether the reaction can proceed in both directions.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction'],
         'ifabsent': 'true',
         'slot_uri': 'fluxo:FLUXO_0000007'} })
    reaction_type: Optional[ReactionTypeEnum] = Field(default=None, description="""The type of reaction.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction']} })
    reactants: list[ReactionParticipant] = Field(default=..., description="""Reactant (educt) participants consumed by the reaction.""", min_length=1, json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction']} })
    products: Optional[list[ReactionParticipant]] = Field(default=None, description="""Product participants produced by the reaction. Recommended rather than strictly required because boundary reactions (sink, demand) legitimately have no products; a conditional rule (required unless boundary reaction) is deferred to Phase 5.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction'], 'recommended': True} })
    atom_transition_variants: Optional[list[AtomTransitionVariant]] = Field(default=None, description="""Atom transition variants for this reaction. Multiple variants exist when symmetric compounds create ambiguity in atom transitions. Recommended rather than required: isotope-based MFA requires transitions for reactions among carbon-tracked metabolites, but stoichiometry-based methods (FBA) and reactions among untracked metabolites have none. The conditional rule (required when n_tracked_atoms > 0) is deferred to Phase 5.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction'], 'recommended': True} })
    is_lumped: Optional[bool] = Field(default=False, description="""Whether this is a lumped reaction combining multiple steps.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction'],
         'ifabsent': 'false',
         'slot_uri': 'fluxo:FLUXO_0000066'} })
    is_pseudo: Optional[bool] = Field(default=False, description="""Whether this is a pseudo-reaction with no biological counterpart.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite', 'NetworkReaction'],
         'ifabsent': 'false',
         'slot_uri': 'fluxo:FLUXO_0000065'} })
    aliases: Optional[str] = Field(default=None, description="""Tool-namespaced alternative identifiers (e.g., \"influx_si:v5\", \"freeflux:R1\"). The canonical↔native ID mapping is new information present in no native file — it lives in the dataset, once per entity.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite', 'NetworkReaction']} })


class ReactionParticipant(ConfiguredBaseModel):
    """
    A metabolite participating in a reaction with a specific stoichiometric coefficient.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000185',
         'from_schema': 'https://w3id.org/fluxolink/network'})

    metabolite_id: str = Field(default=..., description="""Reference to the metabolite identifier in the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult']} })
    stoichiometry: Optional[float] = Field(default=1.0, description="""Stoichiometric coefficient (absolute value). The participant's role (reactant vs product) is determined by which list it appears in on NetworkReaction.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant'],
         'ifabsent': 'float(1.0)',
         'slot_uri': 'fluxo:FLUXO_0000205'} })


class AtomTransitionVariant(ConfiguredBaseModel):
    """
    A variant of atom transitions for a reaction. E.g. reactions involving symmetric compounds have multiple variants because the atom mapping is ambiguous.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000224',
         'from_schema': 'https://w3id.org/fluxolink/network'})

    variant_id: str = Field(default=..., description="""Identifier for this variant (e.g., \"SCS___1\", \"SCS___2\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransitionVariant']} })
    ratio: Optional[float] = Field(default=None, description="""Likelihood (0.0-1.0) of this atom-transition variant, used for scrambling reactions where symmetric compounds make the atom mapping ambiguous. Should sum to 1.0 across all variants of a reaction.""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransitionVariant']} })
    transitions: Optional[list[AtomTransition]] = Field(default=None, description="""Individual atom-to-atom transition mappings.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransitionVariant']} })


class AtomTransition(ConfiguredBaseModel):
    """
    A single atom-to-atom mapping from a reactant atom to a product atom in a reaction.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000155',
         'from_schema': 'https://w3id.org/fluxolink/network'})

    reactant_metabolite_id: str = Field(default=..., description="""Identifier of the reactant metabolite containing the source atom.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition']} })
    reactant_atom_index: int = Field(default=..., description="""Zero-based index of the atom position in the reactant metabolite.""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition'], 'slot_uri': 'fluxo:FLUXO_0000069'} })
    product_metabolite_id: str = Field(default=..., description="""Identifier of the product metabolite containing the destination atom.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition']} })
    product_atom_index: int = Field(default=..., description="""Zero-based index of the atom position in the product metabolite.""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition'], 'slot_uri': 'fluxo:FLUXO_0000069'} })
    annotation_type: Optional[AtomAnnotationTypeEnum] = Field(default=None, description="""The notation used for this atom transition.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition'], 'slot_uri': 'fluxo:FLUXO_0000072'} })


class FluxConstraint(ConfiguredBaseModel):
    """
    A constraint on metabolic flux values in the network model.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000068',
         'from_schema': 'https://w3id.org/fluxolink/network'})

    id: str = Field(default=..., description="""Unique identifier for the constraint.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    reaction_id: str = Field(default=..., description="""Reference to the reaction this constraint applies to.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'FluxMeasurement', 'FluxResult']} })
    constraint_type: ConstraintTypeEnum = Field(default=..., description="""The type of constraint.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    lower_bound: Optional[float] = Field(default=None, description="""Lower bound for the flux value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    upper_bound: Optional[float] = Field(default=None, description="""Upper bound for the flux value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    fixed_value: Optional[float] = Field(default=None, description="""Fixed value for equality constraints.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    expression: Optional[str] = Field(default=None, description="""Mathematical expression for linear combination constraints.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint',
                       'PoolSizeConstraint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000223'} })


class PoolSizeConstraint(ConfiguredBaseModel):
    """
    A constraint on metabolite pool size values in the network model. Parallel to FluxConstraint but applies to a metabolite rather than a reaction.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000068',
         'from_schema': 'https://w3id.org/fluxolink/network'})

    id: str = Field(default=..., description="""Unique identifier for the constraint.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    metabolite_id: str = Field(default=..., description="""Reference to the metabolite this constraint applies to.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult']} })
    constraint_type: ConstraintTypeEnum = Field(default=..., description="""The type of constraint.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    lower_bound: Optional[float] = Field(default=None, description="""Lower bound for the pool size value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    upper_bound: Optional[float] = Field(default=None, description="""Upper bound for the pool size value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    fixed_value: Optional[float] = Field(default=None, description="""Fixed value for equality constraints.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    expression: Optional[str] = Field(default=None, description="""Mathematical expression for linear combination constraints.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint',
                       'PoolSizeConstraint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000223'} })


class LabelingExperiment(ConfiguredBaseModel):
    """
    An isotope labeling experiment defining the tracer setup, biological condition, and associated measurement data for an MFA study.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000049',
         'from_schema': 'https://w3id.org/fluxolink/experiment'})

    id: str = Field(default=..., description="""Unique identifier for the experiment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    name: Optional[str] = Field(default=None, description="""Human-readable name of the experiment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'LabelingExperiment',
                       'Condition',
                       'FluxoDataset']} })
    investigation_id: str = Field(default=..., description="""Reference to the parent investigation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun']} })
    condition: str = Field(default=..., description="""Reference to the cultivation condition for this experiment, defined once in FluxoDataset.conditions.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun']} })
    stationary: bool = Field(default=..., description="""Whether the experiment is isotopically stationary (true) or non-stationary/INST (false). Determines whether time_point is required (enforced via a cross-slot rule, deferred to Phase 5).""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment']} })
    labeled_sources: list[LabeledSource] = Field(default=..., description="""Labeled substrate (tracer mixture) specifications.""", min_length=1, json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment']} })
    mid_measurements: Optional[list[MIDMeasurement]] = Field(default=None, description="""MID (mass isotopologue distribution) measurements.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment']} })
    nmr_measurements: Optional[list[NMRIsotopomerMeasurement]] = Field(default=None, description="""13C NMR isotopomer (multiplet) measurements.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment']} })
    flux_measurements: Optional[list[FluxMeasurement]] = Field(default=None, description="""Measured external flux values.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment']} })
    pool_size_measurements: Optional[list[PoolSizeMeasurement]] = Field(default=None, description="""Measured metabolite pool sizes.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment']} })
    flux_ratio_measurements: Optional[list[FluxRatioMeasurement]] = Field(default=None, description="""Measured flux ratios between reactions.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment']} })
    pool_size_ratio_measurements: Optional[list[PoolSizeRatioMeasurement]] = Field(default=None, description="""Measured pool size ratios between metabolites.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment']} })
    tracer_summary: Optional[str] = Field(default=None, description="""Human-readable tracer description for catalog browsing (e.g., \"100% [1-13C] glucose\"). Machine-readable spec stays in labeled_sources / native files.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment']} })


class LabeledSource(ConfiguredBaseModel):
    """
    A labeled source (tracer mixture) supplied to the biological system. Consists of one or more isotopically labeled tracer isotopomers mixed at specified fractions.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000078',
         'from_schema': 'https://w3id.org/fluxolink/experiment'})

    id: str = Field(default=..., description="""Unique identifier for the labeled source.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    metabolite_id: str = Field(default=..., description="""Reference to the input metabolite in the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult']} })
    input_type: Optional[IsotopicStateSpaceEnum] = Field(default=None, description="""Isotopic state-space representation of the input specification (isotopomer, cumomer, or EMU).""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabeledSource']} })
    profile: Optional[str] = Field(default=None, description="""Time-varying input profile for non-stationary experiments, as a textual list of values (e.g., \"0.5, 1.0, 1.5\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabeledSource']} })
    tracers: Optional[list[TracerIsotopomer]] = Field(default=None, description="""Individual tracer isotopomers in the mixture.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabeledSource']} })


class TracerIsotopomer(ConfiguredBaseModel):
    """
    A specific isotopically labeled form of a tracer molecule, defined by its labeling pattern, fraction, and purity.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000134',
         'from_schema': 'https://w3id.org/fluxolink/experiment'})

    labeling_pattern: str = Field(default=..., description="""Labeling pattern as a binary string where 1 = labeled atom and 0 = unlabeled atom (e.g., \"100000\" for [1-13C]glucose).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TracerIsotopomer']} })
    tracer_fraction: float = Field(default=..., description="""Proportion of this tracer isotopomer in the labeled source. Should sum to <= 1.0 across all tracers for a source.""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['TracerIsotopomer'], 'slot_uri': 'fluxo:FLUXO_0000138'} })
    isotopic_purity: float = Field(default=..., description="""Purity of the isotopic label (e.g., 0.99 for 99 atom % 13C).""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['TracerIsotopomer'], 'slot_uri': 'fluxo:FLUXO_0000139'} })
    cost: Optional[float] = Field(default=None, description="""Relative cost of this tracer, used for optimal experiment design.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['TracerIsotopomer'], 'slot_uri': 'fluxo:FLUXO_0000081'} })
    profile_values: Optional[str] = Field(default=None, description="""Time-varying labeling profile as a textual formula (e.g., \"0.5 + 0.5 * sin(t-1.57)\") for non-stationary inputs.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TracerIsotopomer']} })

    @field_validator('labeling_pattern')
    def pattern_labeling_pattern(cls, v):
        pattern=re.compile(r"^[01xX]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid labeling_pattern format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid labeling_pattern format: {v}"
            raise ValueError(err_msg)
        return v


class MIDMeasurement(ConfiguredBaseModel):
    """
    A group of MID (mass isotopologue distribution) measurements for one metabolite fragment at a given time point.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000143',
         'from_schema': 'https://w3id.org/fluxolink/experiment'})

    id: str = Field(default=..., description="""Unique identifier for the measurement group.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    metabolite_id: str = Field(default=..., description="""Reference to the measured metabolite in the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult']} })
    atom_positions: str = Field(default=..., description="""Traced atom positions (e.g., \"2,3\" or \"1-5\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement']} })
    analytical_method: AnalyticalMethodEnum = Field(default=..., description="""Analytical (mass spectrometry) method for this measurement.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000190'} })
    analytical_method_other: Optional[str] = Field(default=None, description="""Free-text analytical method, used when analytical_method is \"other\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement']} })
    time_point: Optional[float] = Field(default=None, description="""Measurement time point for non-stationary experiments.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000056'} })
    scale_method: Optional[ScaleMethodEnum] = Field(default=None, description="""Scaling method for this measurement group.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement']} })
    error_model_expression: Optional[str] = Field(default=None, description="""Mathematical expression for the error model (e.g., \"sd = 0.01 * value\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement'], 'slot_uri': 'fluxo:FLUXO_0000091'} })
    dataset_id: Optional[str] = Field(default=None, description="""Optional run/batch identifier (influx_si \"Dataset\" column).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement']} })
    natural_abundance_corrected: Optional[bool] = Field(default=None, description="""Whether the MID values have been corrected for natural isotope abundance. If true, correction_algorithm should be specified.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement']} })
    correction_algorithm: Optional[str] = Field(default=None, description="""Algorithm used for natural isotope correction (e.g., \"IsoCor\", \"skyline\", \"in-house\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement']} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement']} })
    replicate: Optional[int] = Field(default=None, description="""Replicate number (1-based) for this measurement group. Carried by miemu; reported in published datasets.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'FluxMeasurement', 'PoolSizeMeasurement']} })
    data_points: Optional[list[MIDDataPoint]] = Field(default=None, description="""Individual MID measurement data points.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement']} })


class MIDDataPoint(ConfiguredBaseModel):
    """
    A single isotopologue measurement value (one m+i entry in an MID).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/fluxolink/experiment'})

    isotopologue_index: int = Field(default=..., description="""Isotopologue mass shift index (m+0, m+1, ..., m+n).""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint']} })
    weight: Optional[str] = Field(default=None, description="""Optional MS/MS fragment weight specifier (e.g., \"2,3\") for tandem-MS measurements.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint']} })
    value: float = Field(default=..., description="""Measured fractional abundance of this isotopologue.""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult']} })
    standard_deviation: float = Field(default=..., description="""Standard deviation (measurement uncertainty) of the value. Explicitly required by influx_si and present across all formats.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })


class FluxMeasurement(ConfiguredBaseModel):
    """
    A measured external flux value for a single reaction.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000124',
         'from_schema': 'https://w3id.org/fluxolink/experiment'})

    id: str = Field(default=..., description="""Unique identifier for the flux measurement.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    reaction_id: str = Field(default=..., description="""Reference to the reaction in the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'FluxMeasurement', 'FluxResult']} })
    flux_type: FluxTypeEnum = Field(default=..., description="""Type of flux (net, forward, backward, exchange).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxMeasurement', 'FluxResult']} })
    value: float = Field(default=..., description="""Measured flux value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000236'} })
    flux_unit: Optional[str] = Field(default=None, description="""Unit of the measured flux (e.g., \"mmol/gDW/h\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxMeasurement', 'FluxResult'],
         'slot_uri': 'fluxo:FLUXO_0000219'} })
    standard_deviation: float = Field(default=..., description="""Standard deviation of the flux measurement.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    time_point: Optional[float] = Field(default=None, description="""Measurement time point (for non-stationary experiments).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000056'} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement']} })
    replicate: Optional[int] = Field(default=None, description="""Replicate number (1-based) for this flux measurement.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'FluxMeasurement', 'PoolSizeMeasurement']} })


class PoolSizeMeasurement(ConfiguredBaseModel):
    """
    A measured metabolite pool size for a single metabolite.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000062',
         'from_schema': 'https://w3id.org/fluxolink/experiment'})

    id: str = Field(default=..., description="""Unique identifier for the pool size measurement.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    metabolite_id: str = Field(default=..., description="""Reference to the metabolite in the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult']} })
    value: float = Field(default=..., description="""Measured pool size value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000062'} })
    pool_size_unit: Optional[str] = Field(default=None, description="""Unit of the measured pool size (e.g., \"mmol/gDW\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['PoolSizeMeasurement', 'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000222'} })
    standard_deviation: float = Field(default=..., description="""Standard deviation of the pool size measurement.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    time_point: Optional[float] = Field(default=None, description="""Measurement time point (for non-stationary experiments).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000056'} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement']} })
    replicate: Optional[int] = Field(default=None, description="""Replicate number (1-based) for this pool size measurement.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'FluxMeasurement', 'PoolSizeMeasurement']} })


class NMRIsotopomerMeasurement(ConfiguredBaseModel):
    """
    A group of 13C NMR isotopomer measurements for one metabolite, providing positional labeling information via multiplet analysis.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000144',
         'from_schema': 'https://w3id.org/fluxolink/experiment'})

    id: str = Field(default=..., description="""Unique identifier for the NMR measurement group.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    metabolite_id: str = Field(default=..., description="""Reference to the measured metabolite in the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult']} })
    analytical_method: Optional[AnalyticalMethodEnum] = Field(default=None, description="""Analytical method used. Use the generic \"NMR\" value: the 1D-13C / 2D-HSQC / 2D-TOCSY sub-types were removed from AnalyticalMethodEnum on 2026-08-24 pending a decision on the NMR attribute set, so naming them here would promise values the enum does not carry.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement']} })
    analytical_method_other: Optional[str] = Field(default=None, description="""Free-text analytical method, used when analytical_method is \"other\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement']} })
    time_point: Optional[float] = Field(default=None, description="""Measurement time point for non-stationary experiments.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000056'} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement']} })
    data_points: Optional[list[NMRIsotopomerDataPoint]] = Field(default=None, description="""Individual NMR isotopomer data points.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement']} })


class NMRIsotopomerDataPoint(ConfiguredBaseModel):
    """
    A single 13C NMR multiplet measurement for one carbon position.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/fluxolink/experiment'})

    atom_position: int = Field(default=..., description="""Carbon position index (1-based) in the metabolite.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['NMRIsotopomerDataPoint']} })
    multiplet_type: NMRMultipletTypeEnum = Field(default=..., description="""NMR multiplet type indicating the labeling state of neighboring carbons. S = singlet, DL = left doublet, DR = right doublet, DD = double doublet, T = triplet.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NMRIsotopomerDataPoint']} })
    value: float = Field(default=..., description="""Measured fractional abundance of this multiplet.""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult']} })
    standard_deviation: float = Field(default=..., description="""Standard deviation of the measurement.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })


class FluxRatioMeasurement(ConfiguredBaseModel):
    """
    A measured flux ratio between two or more reactions.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/fluxolink/experiment'})

    id: str = Field(default=..., description="""Unique identifier for the flux ratio measurement.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    expression: str = Field(default=..., description="""Textual formula referencing reaction IDs (e.g., \"EMP2_v2/(EMP2_v2 + PPP1_v9)\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint',
                       'PoolSizeConstraint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement']} })
    value: float = Field(default=..., description="""Measured ratio value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult']} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation of the ratio.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement']} })


class PoolSizeRatioMeasurement(ConfiguredBaseModel):
    """
    A measured pool size ratio between two or more metabolites.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/fluxolink/experiment'})

    id: str = Field(default=..., description="""Unique identifier for the pool size ratio measurement.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    expression: str = Field(default=..., description="""Textual formula referencing metabolite IDs.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint',
                       'PoolSizeConstraint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement']} })
    value: float = Field(default=..., description="""Measured ratio value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult']} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation of the ratio.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement']} })


class SourceFile(ConfiguredBaseModel):
    """
    Reference to a native MFA file (FluxML, MTF, FTBL, .mat, etc.). The schema references the file; Tier-2 classes optionally carry its parsed content.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000227',
         'from_schema': 'https://w3id.org/fluxolink/experiment'})

    id: str = Field(default=..., description="""Unique identifier for this source file record.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    path: str = Field(default=..., description="""Relative path or URI to the file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    format: InputFormatEnum = Field(default=..., description="""Format of the file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile'], 'slot_uri': 'fluxo:FLUXO_0000229'} })
    format_other: Optional[str] = Field(default=None, description="""Free-text file format, used when format is \"other\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    role: FileRoleEnum = Field(default=..., description="""Role this file plays in the dataset (network, measurements, tracer, etc.).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    checksum: Optional[str] = Field(default=None, description="""\"algorithm:hash\" digest (e.g., \"sha256:abc123...\") for content-integrity verification.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    media_type: Optional[str] = Field(default=None, description="""IANA media type / MIME type (e.g., \"application/xml\", \"text/csv\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    file_size_bytes: Optional[int] = Field(default=None, description="""Size of the file in bytes.""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    description: Optional[str] = Field(default=None, description="""Optional free-text description of the file contents.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation', 'SourceFile', 'FluxoDataset']} })

    @field_validator('checksum')
    def pattern_checksum(cls, v):
        pattern=re.compile(r"^[a-z0-9]+:[0-9a-f]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid checksum format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid checksum format: {v}"
            raise ValueError(err_msg)
        return v


class Condition(ConfiguredBaseModel):
    """
    Cultivation conditions for the biological system under study, including organism, strain, culture medium, and growth rate. Defined once per dataset in FluxoDataset.conditions and referenced by LabelingExperiment.condition and SimulationRun.condition, so a single cultivation is never described twice.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000218',
         'from_schema': 'https://w3id.org/fluxolink/experiment'})

    id: str = Field(default=..., description="""Unique identifier for the condition record.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    name: Optional[str] = Field(default=None, description="""Human-readable name for this condition.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'LabelingExperiment',
                       'Condition',
                       'FluxoDataset']} })
    organism_name: str = Field(default=..., description="""Name of the organism (e.g., Escherichia coli).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Condition'], 'slot_uri': 'fluxo:FLUXO_0000181'} })
    strain: str = Field(default=..., description="""Strain designation (e.g., BW25113).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Condition'], 'slot_uri': 'fluxo:FLUXO_0000182'} })
    culture_medium: Optional[str] = Field(default=None, description="""Growth medium used for cultivation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Condition'], 'slot_uri': 'fluxo:FLUXO_0000184'} })
    specific_growth_rate: float = Field(default=..., description="""Measured specific growth rate of the organism.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Condition'], 'slot_uri': 'fluxo:FLUXO_0000084'} })
    growth_rate_unit: str = Field(default=..., description="""Unit for the growth rate (e.g., 1/h).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Condition'], 'slot_uri': 'fluxo:FLUXO_0000219'} })


class SimulationRun(ConfiguredBaseModel):
    """
    A single simulation run linking an investigation, network model, and experiment to a specific software tool and its results.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000057',
         'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    id: str = Field(default=..., description="""Unique identifier for the simulation run.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    investigation_id: str = Field(default=..., description="""Reference to the parent investigation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun']} })
    network_model_id: Optional[str] = Field(default=None, description="""Reference to the metabolic network model used. Recommended rather than required: a catalog-tier dataset references its network as a SourceFile instead of materialising it, and a hard requirement here would force such datasets to fabricate a stub MetabolicNetworkModel. Benchmark-tier datasets must carry a network — enforced by the FluxoDataset tier rule.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'recommended': True} })
    experiment_id: Optional[list[str]] = Field(default=None, description="""Reference(s) to the labeling experiment(s) used. Singular for single-labeling-experiment MFA; multivalued (2+) for parallel labeling experiments (PLE) jointly fit to one shared flux solution. Optional for non-isotope methods (e.g., FBA).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    fluxomics_method: FluxomicsMethodEnum = Field(default=..., description="""The fluxomics method this run realises — a value from the FLUXO:0000021 subtree. Renamed from mfa_method because the enum now also covers stoichiometry-based, constraint-based and kinetic-modeling methods, for which \"MFA\" is wrong.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    condition: Optional[str] = Field(default=None, description="""Reference to the cultivation condition in FluxoDataset.conditions. Useful for stoichiometry-based runs (which have no labeling experiment); optional for isotope-based MFA, where the condition is reached through the experiment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun']} })
    software: SoftwareInfo = Field(default=..., description="""Software tool and version used for this run.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    input_format: Optional[InputFormatEnum] = Field(default=None, description="""File format of the input data.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'slot_uri': 'fluxo:FLUXO_0000229'} })
    input_format_other: Optional[str] = Field(default=None, description="""Free-text input format, used when input_format is \"other\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    optimization_method: str = Field(default=..., description="""Optimization method used (e.g., Levenberg-Marquardt, BFGS).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'slot_uri': 'fluxo:FLUXO_0000088'} })
    objective_function: Optional[str] = Field(default=None, description="""Mathematical expression for the objective function being optimized (e.g., \"maximize biomass\" for FBA). May be empty for isotope-based MFA where the objective is implicit (minimize WSSR).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'slot_uri': 'fluxo:FLUXO_0000223'} })
    multistart_count: Optional[int] = Field(default=None, description="""Number of optimization restarts (for non-convex problems).""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    random_seed: Optional[int] = Field(default=None, description="""Random seed for reproducibility of stochastic optimizers.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    convergence_tolerance: Optional[float] = Field(default=None, description="""Solver convergence tolerance (e.g., 1e-6).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    stop_time: Optional[float] = Field(default=None, description="""Simulation stop time for non-stationary (INST) MFA.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    initial_values: Optional[FluxSolution] = Field(default=None, description="""Initial flux (and pool size) values for warm-starting the optimizer. Required in practice for isotope-based MFA (INCA/influx_si); optional for FBA. The conditional rule is deferred to Phase 5.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    flux_solution: Optional[FluxSolution] = Field(default=None, description="""Estimated flux values from the simulation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    goodness_of_fit: Optional[GoodnessOfFit] = Field(default=None, description="""Goodness-of-fit statistics for the solution.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    isotopic_state_space: Optional[IsotopicStateSpaceEnum] = Field(default=None, description="""Isotopic state-space representation used for computation (isotopomer, cumomer, or EMU). A benchmarking-fairness parameter — tools differ in their native representation (13CFLUX2 cumomer, INCA cumomer/EMU, miemu EMU).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'slot_uri': 'fluxo:FLUXO_0000146'} })
    input_files: Optional[list[SourceFile]] = Field(default=None, description="""Native input files used for this simulation run (network, measurements, tracers, constraints, configuration).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'slot_uri': 'fluxo:FLUXO_0000266'} })
    output_files: Optional[list[SourceFile]] = Field(default=None, description="""Output / results files produced by this simulation run. Provenance for extracted results (NMDC has_output pattern).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'slot_uri': 'fluxo:FLUXO_0000284'} })


class SoftwareInfo(ConfiguredBaseModel):
    """
    Information about the MFA software tool used for a simulation run.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000102',
         'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    id: str = Field(default=..., description="""Unique identifier for this software info record.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    software_name: MFASoftwareEnum = Field(default=..., description="""Name of the MFA software.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SoftwareInfo']} })
    software_name_other: Optional[str] = Field(default=None, description="""Free-text software name, used when software_name is \"other\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['SoftwareInfo']} })
    version: str = Field(default=..., description="""Version of the software.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SoftwareInfo'], 'slot_uri': 'fluxo:FLUXO_0000243'} })
    url: Optional[str] = Field(default=None, description="""URL to the software repository or documentation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SoftwareInfo']} })


class FluxSolution(ConfiguredBaseModel):
    """
    The estimated flux values (and optionally pool sizes) that best explain the experimental data.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000159',
         'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    id: str = Field(default=..., description="""Unique identifier for the flux solution.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    flux_results: Optional[list[FluxResult]] = Field(default=None, description="""Individual flux value estimates.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxSolution']} })
    pool_size_results: Optional[list[PoolSizeResult]] = Field(default=None, description="""Estimated metabolite pool sizes.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxSolution']} })
    simulated_mids: Optional[list[MIDMeasurement]] = Field(default=None, description="""Simulated MID values predicted by the model, for comparison against measured MIDs (measured-vs-fitted plots, WSSR re-derivation). Present when the solver exposes forward-simulation output. Reuses the MIDMeasurement structure with standard_deviation left unpopulated.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxSolution']} })


class FluxResult(ConfiguredBaseModel):
    """
    An estimated flux value for a single reaction, including uncertainty information.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000123',
         'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    reaction_id: str = Field(default=..., description="""Reference to the reaction in the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'FluxMeasurement', 'FluxResult']} })
    flux_type: FluxTypeEnum = Field(default=..., description="""Type of flux (net, forward, backward, exchange).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxMeasurement', 'FluxResult']} })
    value: float = Field(default=..., description="""Estimated flux value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000236'} })
    lower_ci: Optional[float] = Field(default=None, description="""Lower bound of the confidence interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000262'} })
    upper_ci: Optional[float] = Field(default=None, description="""Upper bound of the confidence interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000263'} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation of the flux estimate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    flux_unit: Optional[str] = Field(default=None, description="""Unit of the flux value (e.g., mmol/gDW/h).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxMeasurement', 'FluxResult'],
         'slot_uri': 'fluxo:FLUXO_0000219'} })
    confidence_interval_method: Optional[ConfidenceIntervalMethodEnum] = Field(default=None, description="""Method used to compute the confidence interval (profile likelihood, parameter continuation, bootstrap, grid search).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult']} })


class PoolSizeResult(ConfiguredBaseModel):
    """
    An estimated metabolite pool size from the flux solution.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000062',
         'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    metabolite_id: str = Field(default=..., description="""Reference to the metabolite in the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult']} })
    value: float = Field(default=..., description="""Estimated pool size value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000062'} })
    lower_ci: Optional[float] = Field(default=None, description="""Lower bound of the confidence interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000262'} })
    upper_ci: Optional[float] = Field(default=None, description="""Upper bound of the confidence interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000263'} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation of the pool size estimate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    pool_size_unit: Optional[str] = Field(default=None, description="""Unit of the pool size (e.g., mmol/gDW).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PoolSizeMeasurement', 'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000222'} })
    confidence_interval_method: Optional[ConfidenceIntervalMethodEnum] = Field(default=None, description="""Method used to compute the confidence interval (profile likelihood, parameter continuation, bootstrap, grid search).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult']} })


class GoodnessOfFit(ConfiguredBaseModel):
    """
    Statistical measures of how well the flux solution fits the experimental data.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000212',
         'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    wssr: Optional[float] = Field(default=None, description="""Weighted sum of squared residuals (variance-weighted).""", json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit'], 'slot_uri': 'fluxo:FLUXO_0000086'} })
    degrees_of_freedom: Optional[int] = Field(default=None, description="""Degrees of freedom in the fit.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit'], 'slot_uri': 'fluxo:FLUXO_0000030'} })
    chi_square_p_value: Optional[float] = Field(default=None, description="""P-value from the chi-square goodness-of-fit test.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit'], 'slot_uri': 'fluxo:FLUXO_0000213'} })
    reduced_chi_square: Optional[float] = Field(default=None, description="""Reduced chi-square statistic (WSSR / degrees of freedom).""", json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit'], 'slot_uri': 'fluxo:FLUXO_0000237'} })


class FluxoDataset(ConfiguredBaseModel):
    """
    Root container aggregating all studies, networks, experiments, and simulation runs in a fluxomics dataset.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000002',
         'from_schema': 'https://w3id.org/fluxolink',
         'rules': [{'description': 'A benchmark-tier dataset carries Tier-2 input '
                                   'ground truth, so the network it is benchmarked '
                                   'against must be materialised in the document '
                                   'rather than only referenced as native files. '
                                   'Catalog-tier datasets (and datasets that leave '
                                   'dataset_type absent) are exempt: they record '
                                   'results plus file-level provenance, and their '
                                   'input content stays in the referenced '
                                   'SourceFiles.\n'
                                   '`experiments` is deliberately NOT required here. A '
                                   'stoichiometry-based run (constraint_based, FBA) '
                                   'has no tracer, so requiring a LabelingExperiment '
                                   'would force it to fabricate one — the same defect '
                                   'that placeholder networks caused before '
                                   '2026-08-24. The real rule is "isotope-based method '
                                   'implies a labeling experiment", and it cannot be '
                                   'written in LinkML: fluxomics_method lives on '
                                   'SimulationRun, nested, and slot_conditions cannot '
                                   'nest. It is enforced by the Phase 7 `fluxo '
                                   'validate --benchmark` gate instead.',
                    'postconditions': {'slot_conditions': {'networks': {'name': 'networks',
                                                                        'required': True}}},
                    'preconditions': {'slot_conditions': {'dataset_type': {'equals_string': 'benchmark',
                                                                           'name': 'dataset_type'}}},
                    'title': 'benchmark_tier_requires_input_ground_truth'}],
         'tree_root': True})

    id: str = Field(default=..., description="""Unique identifier for this dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SourceFile',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    name: Optional[str] = Field(default=None, description="""Human-readable name of the dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'LabelingExperiment',
                       'Condition',
                       'FluxoDataset']} })
    description: Optional[str] = Field(default=None, description="""Detailed description of the dataset contents.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation', 'SourceFile', 'FluxoDataset']} })
    schema_version: Optional[str] = Field(default=None, description="""Version of the FluxoLink schema this dataset conforms to.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    creation_date: Optional[date] = Field(default=None, description="""Date the dataset was created.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    last_modified: Optional[date] = Field(default=None, description="""Date the dataset was last modified.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    fluxo_ontology_version: Optional[str] = Field(default=None, description="""FLUXO ontology release version used for term mappings (e.g., \"2026-04-08\"). Pins the ontology version for traceability.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    dataset_type: Optional[DatasetTypeEnum] = Field(default=None, description="""Classification of this dataset by curation tier. When \"benchmark\", the materialised network is required; when \"catalog\" or absent, input content stays in the referenced SourceFiles. Whether a benchmark also requires labeling experiments depends on the method each run realises, which is nested beyond the reach of a LinkML rule — see the rule below.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    source_files: Optional[list[SourceFile]] = Field(default=None, description="""Native MFA files referenced by this dataset (FluxML, MTF, FTBL, .mat, etc.). Tier-1 provenance layer.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    conditions: Optional[list[Condition]] = Field(default=None, description="""All cultivation conditions in this dataset, defined once and referenced by LabelingExperiment.condition and SimulationRun.condition. Held at dataset level so one cultivation is described exactly once.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    investigations: Optional[list[Investigation]] = Field(default=None, description="""All MFA investigations in this dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    networks: Optional[list[MetabolicNetworkModel]] = Field(default=None, description="""All metabolic network models in this dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    experiments: Optional[list[LabelingExperiment]] = Field(default=None, description="""All labeling experiments in this dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    simulation_runs: Optional[list[SimulationRun]] = Field(default=None, description="""All simulation runs in this dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
Investigation.model_rebuild()
Contributor.model_rebuild()
MetabolicNetworkModel.model_rebuild()
NetworkMetabolite.model_rebuild()
NetworkReaction.model_rebuild()
ReactionParticipant.model_rebuild()
AtomTransitionVariant.model_rebuild()
AtomTransition.model_rebuild()
FluxConstraint.model_rebuild()
PoolSizeConstraint.model_rebuild()
LabelingExperiment.model_rebuild()
LabeledSource.model_rebuild()
TracerIsotopomer.model_rebuild()
MIDMeasurement.model_rebuild()
MIDDataPoint.model_rebuild()
FluxMeasurement.model_rebuild()
PoolSizeMeasurement.model_rebuild()
NMRIsotopomerMeasurement.model_rebuild()
NMRIsotopomerDataPoint.model_rebuild()
FluxRatioMeasurement.model_rebuild()
PoolSizeRatioMeasurement.model_rebuild()
SourceFile.model_rebuild()
Condition.model_rebuild()
SimulationRun.model_rebuild()
SoftwareInfo.model_rebuild()
FluxSolution.model_rebuild()
FluxResult.model_rebuild()
PoolSizeResult.model_rebuild()
GoodnessOfFit.model_rebuild()
FluxoDataset.model_rebuild()
