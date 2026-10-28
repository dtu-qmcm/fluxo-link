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


metamodel_version = "1.12.0"
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
    number_13CFLUX3 = "13CFLUX3"
    """
    13CFLUX v3 (Python package x3cflux) - third-generation FluxML-based engine for stationary and non-stationary 13C-MFA
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
    miemu = "miemu"
    """
    miemu - EMU-based MFA fitting package. No FLUXO term yet; left unmapped.
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
    jupyter_notebook = "jupyter_notebook"
    """
    Jupyter notebook (.ipynb) used as a driver, e.g. a FreeFlux fit scripted in a notebook.
    """
    freeflux_tsv = "freeflux_tsv"
    """
    FreeFlux tab-separated tables (reactions.tsv, measured_MDVs.tsv, ...). FreeFlux's reader rejects .csv, so this is the usual FreeFlux table format.
    """
    freeflux_xlsx = "freeflux_xlsx"
    """
    FreeFlux Excel workbook tables (reactions.xlsx, ...).
    """
    INCA_script = "INCA_script"
    """
    INCA MATLAB script (.m) that builds the model, experiments and options in code. Distinct from INCA_mat, the binary container INCA saves models and results in.
    """
    python_script = "python_script"
    """
    Python driver script (e.g. a FreeFlux .py that sets the tracer, bounds and solver options the data tables omit).
    """
    plain_text = "plain_text"
    """
    Unstructured text output such as a solver log.
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
    auto = "auto"
    """
    Let the tool choose the representation. The FluxML <simulation>@method default, and the value in most real <simulation> elements.
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
    Method used to compute confidence intervals on estimated fluxes or pool sizes. Only bootstrapping has a FLUXO term so far; the other values are left unmapped.
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
    Bootstrap resampling
    """
    grid_search = "grid_search"
    """
    Grid search over parameter space
    """
    linearized = "linearized"
    """
    Linearized (Fisher-information / sensitivity-based) approximation. The default in FreeFlux and INCA.
    """
    monte_carlo = "monte_carlo"
    """
    Monte Carlo resampling of the measurements and re-fitting (a parametric bootstrap; FreeFlux n_runs, INCA montecarlo).
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
    Measurement data file of unspecified kind. Prefer the specific values below when the file holds one kind of measurement, so a consumer can find e.g. the mandatory MID file without parsing file names.
    """
    mid_measurements = "mid_measurements"
    """
    Labeling (MID / NMR / cumomer) measurement file, e.g. influx_si .miso, FreeFlux measured_MDVs.tsv.
    """
    flux_measurements = "flux_measurements"
    """
    Measured flux file, e.g. influx_si .mflux, FreeFlux measured_fluxes.tsv.
    """
    pool_size_measurements = "pool_size_measurements"
    """
    Measured pool size file, e.g. influx_si .mmet.
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
    Tool or run configuration file (e.g. influx_si .opt).
    """
    variable_specification = "variable_specification"
    """
    Free / dependent / constrained variable classification with starting values and bounds, e.g. influx_si .tvar, FreeFlux fluxes.tsv used as initial values.
    """
    driver_script = "driver_script"
    """
    Script that drives the tool and carries settings the data files omit (FreeFlux .py setting the tracer and solver; INCA .m).
    """
    log = "log"
    """
    Solver log or console output (e.g. influx_si .log).
    """
    other = "other"
    """
    Other role not listed; specify via the companion role_other free-text slot.
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


class DataOriginEnum(str, Enum):
    """
    Where the measurement values in an experiment come from. Decides whether cultivation metadata can exist at all (a synthetic benchmark has no culture), and whether a natural-abundance conversion is correct. FLUXO has no term for this distinction yet.
    """
    experimental = "experimental"
    """
    Values measured on a real cultivation.
    """
    synthetic = "synthetic"
    """
    Values generated from a model (e.g. simulated MIDs with added noise) to serve as a benchmark or test case.
    """
    simulated = "simulated"
    """
    Noise-free values computed by forward simulation of a model.
    """


class RunModeEnum(str, Enum):
    """
    What a simulation run did. A run may do several of these (INCA runs estimate then continuate). Distinct from fluxomics_method, which names the method family, and from run_status, which says whether the run happened. No FLUXO terms except forward simulation.
    """
    estimation = "estimation"
    """
    Flux (and pool size) estimation by fitting to data.
    """
    forward_simulation = "forward_simulation"
    """
    Labeling simulation with fixed fluxes; no fitting (influx_si --noopt, INCA simulate(), x3cflux compute_measurements).
    """
    confidence_interval_estimation = "confidence_interval_estimation"
    """
    Confidence-interval computation around a fitted solution (INCA continuate, influx_si sensitivity analysis).
    """
    monte_carlo = "monte_carlo"
    """
    Monte Carlo resampling of measurements with re-fitting (INCA montecarlo, FreeFlux n_runs).
    """
    experimental_design = "experimental_design"
    """
    Optimal tracer / experiment design.
    """
    other = "other"
    """
    Other run mode not listed.
    """


class RunStatusEnum(str, Enum):
    """
    Whether a simulation run was executed. Separates a run that never ran (a FluxML <simulation> block or a prepared script) from one whose results were simply not extracted.
    """
    planned = "planned"
    """
    Specified but not executed, or executed elsewhere with no record here (e.g. a FluxML configuration's <simulation> block).
    """
    completed = "completed"
    """
    Executed to completion.
    """
    failed = "failed"
    """
    Executed but did not finish or did not converge.
    """
    unknown = "unknown"
    """
    Execution state not recorded.
    """


class VariableKindEnum(str, Enum):
    """
    Kind of model variable in a free/dependent/constrained variable specification.
    """
    net_flux = "net_flux"
    """
    Net flux of a reaction.
    """
    exchange_flux = "exchange_flux"
    """
    Exchange flux of a reaction.
    """
    forward_flux = "forward_flux"
    """
    Forward flux of a reaction (INCA parametrises reversible reactions by directional fluxes).
    """
    backward_flux = "backward_flux"
    """
    Backward flux of a reaction.
    """
    pool_size = "pool_size"
    """
    Metabolite pool size.
    """


class VariableTypeEnum(str, Enum):
    """
    Classification of a model variable in the stoichiometric parametrisation (influx_si F/D/C, FluxML <variables>). The partition is a choice of basis, not a property of the solution. FLUXO has no term for it yet.
    """
    free = "free"
    """
    Free (independent) variable estimated by the fit.
    """
    constrained = "constrained"
    """
    Variable fixed to a given value.
    """
    dependent = "dependent"
    """
    Variable computed from the free variables through the stoichiometry; carries no value of its own.
    """


class SolutionRoleEnum(str, Enum):
    """
    What a flux solution represents. A synthetic benchmark knows its true fluxes, which must not be confused with an estimate.
    """
    estimated = "estimated"
    """
    Fitted by the run.
    """
    reference = "reference"
    """
    Known true values of a synthetic benchmark, or values imposed for a forward simulation.
    """
    simulated = "simulated"
    """
    Values produced by forward simulation.
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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset'],
         'in_subset': ['core']} })
    name: str = Field(default=..., description="""Human-readable name of the investigation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
                       'Condition',
                       'FluxoDataset'],
         'in_subset': ['core']} })
    description: Optional[str] = Field(default=None, description="""Detailed description of the investigation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'MetabolicNetworkModel',
                       'SourceFile',
                       'SolverOption',
                       'FluxoDataset']} })
    publication_doi: Optional[str] = Field(default=None, description="""DOI of the associated publication.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation'], 'in_subset': ['core']} })
    investigation_type: Optional[InvestigationTypeEnum] = Field(default=None, description="""Kind of fluxomics investigation this is (FLUXO:0000162 subtree). Distinct from SimulationRun.fluxomics_method: the investigation is the executed process, the method is the plan each run realises, and one investigation may realise several.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation'], 'in_subset': ['core']} })
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
                       'EquivalenceCheck',
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
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
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
                       'EquivalenceCheck',
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
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
                       'Condition',
                       'FluxoDataset']} })
    description: Optional[str] = Field(default=None, description="""Free-text description or comment (FluxML <info><comment>; often cites the source publication).""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'MetabolicNetworkModel',
                       'SourceFile',
                       'SolverOption',
                       'FluxoDataset']} })
    version: Optional[str] = Field(default=None, description="""Model version (FluxML <info><version>).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel', 'SoftwareInfo']} })
    modeler: Optional[str] = Field(default=None, description="""Person who built the model (FluxML <info><modeler>).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel']} })
    model_date: Optional[str] = Field(default=None, description="""Date and time the model was created or last edited (FluxML <info><date>). Distinct from FluxoDataset.creation_date, which dates the dataset, not the model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel']} })
    compartments: Optional[list[str]] = Field(default=None, description="""List of compartment names in the model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel'], 'slot_uri': 'fluxo:FLUXO_0000058'} })
    metabolites: Optional[list[NetworkMetabolite]] = Field(default=None, description="""Metabolite definitions in the network. Recommended rather than required: INCA derives metabolites from reaction strings, so a faithful INCA encoding may list reactions only. A benchmark-tier dataset must list them (enforced by `fluxolink-validate --benchmark`).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel'], 'recommended': True} })
    reactions: list[NetworkReaction] = Field(default=..., description="""Reaction definitions in the network.""", min_length=1, json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel']} })
    default_flux_lower_bound: Optional[float] = Field(default=None, description="""Lower bound applied to every flux that has no explicit bound (INCA m.rates.flx.lb scalar default).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel']} })
    default_flux_upper_bound: Optional[float] = Field(default=None, description="""Upper bound applied to every flux that has no explicit bound (INCA m.rates.flx.ub scalar default).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel']} })
    flux_constraints: Optional[list[FluxConstraint]] = Field(default=None, description="""Constraints on reaction flux values (bounds, equalities, linear-combination constraints) shared by every experiment on this network. Experiment-specific constraints live on LabelingExperiment.flux_constraints.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel', 'LabelingExperiment']} })
    pool_size_constraints: Optional[list[PoolSizeConstraint]] = Field(default=None, description="""Constraints on metabolite pool size values shared by every experiment on this network.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel', 'LabelingExperiment']} })


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
                       'EquivalenceCheck',
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
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
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
    is_external: Optional[bool] = Field(default=None, description="""Whether the metabolite lies outside the system boundary (a substrate or product pool such as Gluc.ext). Not the same as is_pseudo. No FLUXO term yet.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite']} })
    is_balanced: Optional[bool] = Field(default=None, description="""Whether the metabolite is mass-balanced. INCA can exclude a metabolite from the balance (e.g. Glyc.ext). No FLUXO term yet.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite']} })
    symmetry: Optional[str] = Field(default=None, description="""Atom-position permutation under which the molecule is symmetric, written as the 1-based positions in permuted order (e.g. \"4,3,2,1\" for succinate). INCA declares symmetry once per metabolite; FluxML expresses it through reaction variants.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite'], 'slot_uri': 'fluxo:FLUXO_0000064'} })
    aliases: Optional[list[str]] = Field(default=None, description="""Tool-namespaced alternative identifiers (e.g., \"influx_si:v5\", \"freeflux:R1\"). The canonical↔native ID mapping is new information present in no native file — it lives in the dataset, once per entity.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite', 'NetworkReaction']} })

    @field_validator('aliases')
    def pattern_aliases(cls, v):
        pattern=re.compile(r"^[^:\s]+:\S+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.search(element):
                    err_msg = f"Invalid aliases format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.search(v):
            err_msg = f"Invalid aliases format: {v}"
            raise ValueError(err_msg)
        return v


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
                       'EquivalenceCheck',
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
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
                       'Condition',
                       'FluxoDataset']} })
    pathway: Optional[str] = Field(default=None, description="""Pathway the reaction belongs to (FluxML <annotation name=\"pathway\">, the most common annotation in the corpus; FreeFlux section rows).""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction']} })
    reversibility: bool = Field(default=True, description="""Whether the reaction can proceed in both directions.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction'],
         'ifabsent': 'true',
         'slot_uri': 'fluxo:FLUXO_0000007'} })
    reaction_type: Optional[ReactionTypeEnum] = Field(default=None, description="""The type of reaction.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction']} })
    reactants: Optional[list[ReactionParticipant]] = Field(default=None, description="""Reactant (educt) participants consumed by the reaction. Recommended rather than required: a pure influx reaction (\"-> X\", MTF \"X ()\") has none. Every reaction needs at least one reactant or product (checked by `fluxolink-validate`).""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction'], 'recommended': True} })
    products: Optional[list[ReactionParticipant]] = Field(default=None, description="""Product participants produced by the reaction. Recommended rather than strictly required because boundary reactions (sink, demand, efflux) legitimately have no products.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction'], 'recommended': True} })
    atom_transition_variants: Optional[list[AtomTransitionVariant]] = Field(default=None, description="""Atom transition variants for this reaction. Multiple variants exist when symmetric compounds create ambiguity in atom transitions; FluxML participant-level <variant>s are expanded to their Cartesian product here (EC.fml R25 → R25___1 … R25___4). Recommended rather than required: stoichiometry-based methods and reactions among untracked metabolites have none.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction'], 'recommended': True} })
    is_lumped: Optional[bool] = Field(default=False, description="""Whether this is a lumped reaction combining multiple steps.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction'],
         'ifabsent': 'false',
         'slot_uri': 'fluxo:FLUXO_0000066'} })
    is_pseudo: Optional[bool] = Field(default=False, description="""Whether this is a pseudo-reaction with no biological counterpart.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite', 'NetworkReaction'],
         'ifabsent': 'false',
         'slot_uri': 'fluxo:FLUXO_0000065'} })
    is_auto_generated: Optional[bool] = Field(default=None, description="""Whether the reaction was created by a converter rather than authored (e.g. drain reactions added for external pools).""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction', 'FluxConstraint', 'PoolSizeConstraint']} })
    aliases: Optional[list[str]] = Field(default=None, description="""Tool-namespaced alternative identifiers (e.g., \"influx_si:v5\", \"freeflux:R1\"). The canonical↔native ID mapping is new information present in no native file — it lives in the dataset, once per entity.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkMetabolite', 'NetworkReaction']} })

    @field_validator('aliases')
    def pattern_aliases(cls, v):
        pattern=re.compile(r"^[^:\s]+:\S+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.search(element):
                    err_msg = f"Invalid aliases format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.search(v):
            err_msg = f"Invalid aliases format: {v}"
            raise ValueError(err_msg)
        return v


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
                       'PoolSizeResult',
                       'SimulatedMID']} })
    stoichiometry: Optional[float] = Field(default=1.0, description="""Stoichiometric coefficient (absolute value). The participant's role (reactant vs product) is determined by which list it appears in on NetworkReaction.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant'],
         'ifabsent': 'float(1.0)',
         'slot_uri': 'fluxo:FLUXO_0000205'} })
    instance: Optional[int] = Field(default=1, description="""1-based occurrence index for a metabolite that appears more than once on the same side of a reaction (INCA v51 \"Pyr (abc) + Pyr (def)\"; MTF R5 \"E (d) + E (e)\"). Each occurrence is its own participant, and atom transitions name the occurrence they come from. Defaults to 1.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant'], 'ifabsent': 'int(1)'} })


class AtomTransitionVariant(ConfiguredBaseModel):
    """
    A variant of atom transitions for a reaction. E.g. reactions involving symmetric compounds have multiple variants because the atom mapping is ambiguous.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000224',
         'from_schema': 'https://w3id.org/fluxolink/network'})

    variant_id: str = Field(default=..., description="""Identifier for this variant (e.g., \"SCS___1\", \"SCS___2\"). For FluxML space-separated multi-ID reactions (id=\"R25___1 R25___2 R25___3 R25___4\") each ID is one variant.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransitionVariant']} })
    ratio: Optional[float] = Field(default=None, description="""Likelihood (0.0-1.0) of this atom-transition variant, used for scrambling reactions where symmetric compounds make the atom mapping ambiguous. When given for every variant of a reaction the ratios should sum to 1.0; FreeFlux, INCA and many FluxML files carry no ratio and leave it absent.""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransitionVariant']} })
    transitions: Optional[list[AtomTransition]] = Field(default=None, description="""Individual atom-to-atom transition mappings.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransitionVariant']} })


class AtomTransition(ConfiguredBaseModel):
    """
    A single atom-to-atom mapping from a reactant atom to a product atom in a reaction. The product side is absent when a tracked atom leaves the system (efflux reactions with no product).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000155',
         'from_schema': 'https://w3id.org/fluxolink/network'})

    reactant_metabolite_id: str = Field(default=..., description="""Identifier of the reactant metabolite containing the source atom.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition']} })
    reactant_instance: Optional[int] = Field(default=1, description="""Occurrence index (ReactionParticipant.instance) of the reactant molecule the atom comes from. Defaults to 1.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition'], 'ifabsent': 'int(1)'} })
    reactant_atom_index: int = Field(default=..., description="""1-based position of the atom in the reactant metabolite, matching FluxML, MTF, FreeFlux, INCA and the converter's AtomAddress.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition'], 'slot_uri': 'fluxo:FLUXO_0000069'} })
    product_metabolite_id: Optional[str] = Field(default=None, description="""Identifier of the product metabolite containing the destination atom. Absent for a dangling atom that leaves the system.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition']} })
    product_instance: Optional[int] = Field(default=1, description="""Occurrence index (ReactionParticipant.instance) of the product molecule the atom goes to. Defaults to 1.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition'], 'ifabsent': 'int(1)'} })
    product_atom_index: Optional[int] = Field(default=None, description="""1-based position of the atom in the product metabolite. Absent for a dangling atom.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition'], 'slot_uri': 'fluxo:FLUXO_0000069'} })
    element: Optional[str] = Field(default=None, description="""Chemical element of the tracked atom (e.g. \"C\", \"N\"). Needed to keep \"C#1@1\" and \"N#1@1\" apart in multi-element FluxML v3 models; assumed to be the tracer element when absent.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition'], 'slot_uri': 'fluxo:FLUXO_0000132'} })
    annotation_type: Optional[AtomAnnotationTypeEnum] = Field(default=None, description="""The notation used for this atom transition.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AtomTransition'], 'slot_uri': 'fluxo:FLUXO_0000072'} })


class FluxConstraint(ConfiguredBaseModel):
    """
    A constraint on metabolic flux values. Either names one reaction with bounds or a fixed value, or carries a linear-combination expression (FluxML <textual>, influx_si .cnstr) such as \"0.488*R67=bmAla\" or \"v2<=v1\".
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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    name: Optional[str] = Field(default=None, description="""Native name of the constraint, when the format has one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
                       'Condition',
                       'FluxoDataset']} })
    reaction_id: Optional[str] = Field(default=None, description="""Reference to the single reaction this constraint applies to. Absent for a linear-combination constraint, which carries an expression instead.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'FluxMeasurement', 'FluxResult']} })
    flux_type: Optional[FluxTypeEnum] = Field(default=FluxTypeEnum("net"), description="""Flux domain the constraint acts on: net or exchange (FluxML, influx_si), or forward / backward (INCA bounds directional fluxes). Net- and exchange-scoped constraints with identical formula, operator and value are different constraints (three such pairs exist in the EC benchmark's .cnstr). Defaults to net.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'FluxMeasurement', 'FluxResult'],
         'ifabsent': 'string(net)'} })
    constraint_type: ConstraintTypeEnum = Field(default=..., description="""The type of constraint.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    lower_bound: Optional[float] = Field(default=None, description="""Lower bound for the flux value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint', 'VariableSpecification']} })
    upper_bound: Optional[float] = Field(default=None, description="""Upper bound for the flux value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint', 'VariableSpecification']} })
    fixed_value: Optional[float] = Field(default=None, description="""Fixed value for equality constraints.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    expression: Optional[str] = Field(default=None, description="""Full constraint expression as plain text, left-hand side, operator and right-hand side (e.g. \"0.488*R67=bmAla\", \"v2<=v1\"). A constraint the source wrote in MathML is kept verbatim and is recognisable by its leading \"<\". May name entities absent from the network, such as a free yield symbol.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint',
                       'PoolSizeConstraint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000223'} })
    is_auto_generated: Optional[bool] = Field(default=None, description="""Whether a tool generated this constraint as a default rather than a person authoring it (influx_si .cnstr.def rows written by txt2ftbl).""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction', 'FluxConstraint', 'PoolSizeConstraint']} })


class PoolSizeConstraint(ConfiguredBaseModel):
    """
    A constraint on metabolite pool size values. Parallel to FluxConstraint but applies to metabolites. Left unmapped: FLUXO_0000068 is \"linear flux constraint\" and does not cover pool sizes (ontology term request pending).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/fluxolink/network'})

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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    name: Optional[str] = Field(default=None, description="""Native name of the constraint, when the format has one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
                       'Condition',
                       'FluxoDataset']} })
    metabolite_id: Optional[str] = Field(default=None, description="""Reference to the single metabolite this constraint applies to. Absent for a linear-combination constraint.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult',
                       'SimulatedMID']} })
    constraint_type: ConstraintTypeEnum = Field(default=..., description="""The type of constraint.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    lower_bound: Optional[float] = Field(default=None, description="""Lower bound for the pool size value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint', 'VariableSpecification']} })
    upper_bound: Optional[float] = Field(default=None, description="""Upper bound for the pool size value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint', 'VariableSpecification']} })
    fixed_value: Optional[float] = Field(default=None, description="""Fixed value for equality constraints.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint']} })
    expression: Optional[str] = Field(default=None, description="""Full constraint expression as plain text (e.g. \"Suc - 2*Fum <= 0\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint',
                       'PoolSizeConstraint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000223'} })
    is_auto_generated: Optional[bool] = Field(default=None, description="""Whether a tool generated this constraint as a default.""", json_schema_extra = { "linkml_meta": {'domain_of': ['NetworkReaction', 'FluxConstraint', 'PoolSizeConstraint']} })


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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset'],
         'in_subset': ['core']} })
    name: Optional[str] = Field(default=None, description="""Human-readable name of the experiment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
                       'Condition',
                       'FluxoDataset']} })
    investigation_id: Optional[str] = Field(default=None, description="""Reference to the parent investigation. Recommended; required at the benchmark tier (`fluxolink-validate --benchmark`).""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun'],
         'in_subset': ['core'],
         'recommended': True} })
    condition: Optional[str] = Field(default=None, description="""Reference to the cultivation condition for this experiment, defined once in FluxoDataset.conditions. Recommended: no native format carries it, and a synthetic benchmark has no culture. Required at the benchmark tier when data_origin is experimental.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun'],
         'in_subset': ['core'],
         'recommended': True} })
    data_origin: Optional[DataOriginEnum] = Field(default=None, description="""Whether the measurement values are experimental, synthetic or simulated. Decides whether cultivation metadata can exist and whether natural-abundance handling applies.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment'], 'in_subset': ['core']} })
    network_model_id: Optional[str] = Field(default=None, description="""Network the experiment's metabolite and reaction references resolve against. Needed for referential integrity in a dataset with more than one network.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'EquivalenceCheck', 'SimulationRun'],
         'recommended': True} })
    configuration_name: Optional[str] = Field(default=None, description="""Native name of this experiment's configuration (FluxML <configuration>@name, unique within one .fml; INCA experiment id). One FluxML file with several configurations (EC.fml: a_INST, b_INST, a_STAT, b_STAT) becomes one LabelingExperiment per configuration, sharing one network.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun']} })
    comment: Optional[str] = Field(default=None, description="""Free-text comment (FluxML <configuration><comment>).""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'VariableSpecification']} })
    stationary: bool = Field(default=..., description="""Whether the experiment is isotopically stationary (true) or non-stationary/INST (false). Must agree with the fluxomics_method of every run that uses the experiment, and a non-stationary experiment needs time points on its labeling data (both checked by `fluxolink-validate`).""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment'], 'in_subset': ['core']} })
    nominal_time: Optional[float] = Field(default=None, description="""Nominal time of the configuration (FluxML <configuration>@time), in time_unit.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment']} })
    time_unit: Optional[str] = Field(default=None, description="""Unit of every time value in this experiment (e.g. \"s\", \"min\", \"h\"). FluxML <mlabel><timeunit>; INCA sim_tunit.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun'],
         'slot_uri': 'fluxo:FLUXO_0000221'} })
    source_files: Optional[list[str]] = Field(default=None, description="""Native files that carry this experiment's content (by id into FluxoDataset.source_files). Attributes files to experiments explicitly instead of by file-name convention (_a / _b, _stat / _inst).""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'FluxoDataset']} })
    flux_constraints: Optional[list[FluxConstraint]] = Field(default=None, description="""Flux constraints that apply to this experiment only (FluxML per-configuration <constraints>; Syn.fml gives each configuration different bounds). Network-level constraints apply in addition.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel', 'LabelingExperiment']} })
    pool_size_constraints: Optional[list[PoolSizeConstraint]] = Field(default=None, description="""Pool size constraints that apply to this experiment only.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel', 'LabelingExperiment']} })
    labeled_sources: Optional[list[LabeledSource]] = Field(default=None, description="""Labeled substrate (tracer mixture) specifications. Recommended rather than required: FreeFlux sets the tracer in its driver script, so a faithful encoding of its tables has none. Required at the benchmark tier (`fluxolink-validate`).""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment'],
         'in_subset': ['core'],
         'recommended': True} })
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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset'],
         'in_subset': ['core']} })
    name: Optional[str] = Field(default=None, description="""Native name of the tracer mixture (e.g. INCA \"1-13C_Gluc\"), so a tracer can be referred to by the label its tool uses.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
                       'Condition',
                       'FluxoDataset']} })
    metabolite_id: str = Field(default=..., description="""Reference to the input metabolite in the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult',
                       'SimulatedMID'],
         'in_subset': ['core']} })
    input_type: Optional[IsotopicStateSpaceEnum] = Field(default=None, description="""Isotopic state-space representation of the input specification (isotopomer, cumomer, or EMU).""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabeledSource']} })
    profile: Optional[str] = Field(default=None, description="""Time-varying input profile for non-stationary experiments, as a textual list of values (e.g., \"0.5, 1.0, 1.5\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabeledSource']} })
    tracers: Optional[list[TracerIsotopomer]] = Field(default=None, description="""Individual tracer isotopomers in the mixture.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabeledSource'], 'in_subset': ['core']} })


class TracerIsotopomer(ConfiguredBaseModel):
    """
    A specific isotopically labeled form of a tracer molecule, defined by its labeling pattern, fraction, and purity.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000134',
         'from_schema': 'https://w3id.org/fluxolink/experiment'})

    name: Optional[str] = Field(default=None, description="""Native name of this labelled form (e.g. \"[1-13C]Gluc\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
                       'Condition',
                       'FluxoDataset']} })
    labeling_pattern: str = Field(default=..., description="""Labeling pattern as a binary string where 1 = labeled atom and 0 = unlabeled atom (e.g., \"100000\" for [1-13C]glucose). Its length must equal the metabolite's n_tracked_atoms when both are known (checked by `fluxolink-validate`).""", json_schema_extra = { "linkml_meta": {'domain_of': ['TracerIsotopomer'], 'in_subset': ['core']} })
    tracer_fraction: Optional[float] = Field(default=None, description="""Proportion of this tracer isotopomer in the labeled source. Fractions of one source must not sum above 1.0; a remainder below 1.0 is read as natural abundance (checked by `fluxolink-validate`). Recommended; required at the benchmark tier.""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['TracerIsotopomer'],
         'in_subset': ['core'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000138'} })
    isotopic_purity: Optional[float] = Field(default=None, description="""Purity of the isotopic label (e.g., 0.99 for 99 atom % 13C). Recommended; required at the benchmark tier.""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['TracerIsotopomer'],
         'in_subset': ['core'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000139'} })
    cost: Optional[float] = Field(default=None, description="""Relative cost of this tracer, used for optimal experiment design.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['TracerIsotopomer'], 'slot_uri': 'fluxo:FLUXO_0000081'} })
    profile_values: Optional[str] = Field(default=None, description="""Time-varying labeling profile as a textual formula (e.g., \"0.5 + 0.5 * sin(t-1.57)\") for non-stationary inputs.""", json_schema_extra = { "linkml_meta": {'domain_of': ['TracerIsotopomer']} })

    @field_validator('labeling_pattern')
    def pattern_labeling_pattern(cls, v):
        pattern=re.compile(r"^[01xX]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.search(element):
                    err_msg = f"Invalid labeling_pattern format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.search(v):
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
                       'EquivalenceCheck',
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
                       'PoolSizeResult',
                       'SimulatedMID']} })
    fragment_name: Optional[str] = Field(default=None, description="""Native name of the measured fragment (INCA \"Ala2\", FreeFlux \"Glu_12345\"). Needed to match measured and simulated series. The measurement group itself is identified by id.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'SimulatedMID']} })
    measurement_spec: Optional[str] = Field(default=None, description="""Native measurement specification, kept verbatim for round-trip (FluxML \"Ala[2,3]#M0,1,2\", influx_si fragment column).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement', 'SimulatedMID']} })
    atom_positions: Optional[str] = Field(default=None, description="""Traced atom positions (e.g., \"2,3\" or \"1-5\"). Recommended; required at the benchmark tier unless measurement_spec is given.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'SimulatedMID'], 'recommended': True} })
    analytical_method: Optional[AnalyticalMethodEnum] = Field(default=None, description="""Analytical (mass spectrometry) method for this measurement. Recommended: no simulation input format records it. Required at the benchmark tier for experimental data.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000190'} })
    analytical_method_other: Optional[str] = Field(default=None, description="""Free-text analytical method, used when analytical_method is \"other\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement']} })
    time_points: Optional[list[float]] = Field(default=None, description="""Sampling-time grid of this group for non-stationary experiments (FluxML <group>@times). Each data point carries its own time_point; grid points with no datum stay recoverable here.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement'], 'slot_uri': 'fluxo:FLUXO_0000056'} })
    scale_method: Optional[ScaleMethodEnum] = Field(default=None, description="""Scaling method for this measurement group (\"auto\" = estimate a scale factor; \"one\" = values are already normalised).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement'], 'slot_uri': 'fluxo:FLUXO_0000161'} })
    error_model_expression: Optional[str] = Field(default=None, description="""Mathematical expression for the error model (e.g., \"sd = 0.01 * value\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'FluxMeasurement', 'PoolSizeMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000091'} })
    dataset_id: Optional[str] = Field(default=None, description="""Optional run/batch identifier (influx_si \"Dataset\" column).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement']} })
    natural_abundance_corrected: Optional[bool] = Field(default=None, description="""Whether the MID values have been corrected for natural isotope abundance. If true, correction_algorithm should be specified.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement']} })
    correction_algorithm: Optional[str] = Field(default=None, description="""Algorithm used for natural isotope correction (e.g., \"IsoCor\", \"skyline\", \"in-house\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement']} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'VariableSpecification']} })
    replicate: Optional[int] = Field(default=None, description="""Replicate number (1-based) for this measurement group. Carried by miemu; reported in published datasets.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'FluxMeasurement', 'PoolSizeMeasurement']} })
    data_points: Optional[list[MIDDataPoint]] = Field(default=None, description="""Individual MID measurement data points.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement', 'SimulatedMID']} })


class MIDDataPoint(ConfiguredBaseModel):
    """
    A single isotopologue measurement value (one m+i entry in an MID).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/fluxolink/experiment'})

    isotopologue_index: int = Field(default=..., description="""Isotopologue mass shift index (m+0, m+1, ..., m+n).""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint', 'SimulatedMIDDataPoint', 'MeasurementFitResult']} })
    weight: Optional[str] = Field(default=None, description="""Optional MS/MS fragment weight specifier (e.g., \"2,3\") for tandem-MS measurements.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint']} })
    time_point: Optional[float] = Field(default=None, description="""Sampling time of this value (non-stationary experiments only), in the experiment's time_unit. FluxML repeats @time per <datum> and influx_si has a Time column per row.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'SimulatedMIDDataPoint',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000056'} })
    value: Optional[float] = Field(default=None, description="""Measured abundance of this isotopologue. Not bounded to [0, 1]: unscaled groups (scale \"auto\") hold raw intensities, and real files carry tiny negative values. Absent for a declared but unmeasured fragment (a template). Recommended; required at the benchmark tier.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult'],
         'recommended': True} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation (measurement uncertainty) of the value. Explicitly required by influx_si and present across all formats. Recommended; required at the benchmark tier.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'recommended': True,
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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    reaction_id: Optional[str] = Field(default=None, description="""Reference to the measured reaction. Give either reaction_id or flux_expression.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'FluxMeasurement', 'FluxResult'],
         'recommended': True} })
    flux_expression: Optional[str] = Field(default=None, description="""Measured combination of fluxes when the measurement is not a single reaction (FluxML <netflux> body, e.g. \"R63-R63b\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxMeasurement']} })
    flux_type: FluxTypeEnum = Field(default=..., description="""Type of flux (net, forward, backward, exchange).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'FluxMeasurement', 'FluxResult']} })
    value: Optional[float] = Field(default=None, description="""Measured flux value. Absent for a declared but unmeasured flux (a template). Recommended; required at the benchmark tier.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000236'} })
    flux_unit: Optional[str] = Field(default=None, description="""Unit of the measured flux (e.g., \"mmol/gDW/h\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxMeasurement', 'FluxResult'],
         'slot_uri': 'fluxo:FLUXO_0000219'} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation of the flux measurement. Recommended; required at the benchmark tier.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    error_model_expression: Optional[str] = Field(default=None, description="""Error model used instead of a fixed SD (FluxML <errormodel> on <netflux>; INCA \"f.std = f.val/20\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'FluxMeasurement', 'PoolSizeMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000091'} })
    time_point: Optional[float] = Field(default=None, description="""Measurement time point (for non-stationary experiments).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'SimulatedMIDDataPoint',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000056'} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'VariableSpecification']} })
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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    metabolite_id: Optional[str] = Field(default=None, description="""Reference to the measured metabolite. Give either metabolite_id or pool_expression.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult',
                       'SimulatedMID'],
         'recommended': True} })
    pool_expression: Optional[str] = Field(default=None, description="""Measured combination of pools when the signal is pooled (influx_si .mmet \"E+B\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['PoolSizeMeasurement']} })
    value: Optional[float] = Field(default=None, description="""Measured pool size value. Absent for a declared but unmeasured pool (a template). Recommended; required at the benchmark tier.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000062'} })
    pool_size_unit: Optional[str] = Field(default=None, description="""Unit of the measured pool size (e.g., \"mmol/gDW\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['PoolSizeMeasurement', 'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000222'} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation of the pool size measurement. Recommended; required at the benchmark tier.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    error_model_expression: Optional[str] = Field(default=None, description="""Error model used instead of a fixed SD.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'FluxMeasurement', 'PoolSizeMeasurement'],
         'slot_uri': 'fluxo:FLUXO_0000091'} })
    time_point: Optional[float] = Field(default=None, description="""Measurement time point (for non-stationary experiments).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'SimulatedMIDDataPoint',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000056'} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'VariableSpecification']} })
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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    measurement_spec: Optional[str] = Field(default=None, description="""Native measurement specification, kept verbatim for round-trip (e.g. a FluxML <group> textual body).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement', 'SimulatedMID']} })
    metabolite_id: str = Field(default=..., description="""Reference to the measured metabolite in the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult',
                       'SimulatedMID']} })
    analytical_method: Optional[AnalyticalMethodEnum] = Field(default=None, description="""Analytical method used. Use the generic \"NMR\" value: the 1D-13C / 2D-HSQC / 2D-TOCSY sub-types were removed from AnalyticalMethodEnum on 2026-08-24 pending a decision on the NMR attribute set, so naming them here would promise values the enum does not carry.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement']} })
    analytical_method_other: Optional[str] = Field(default=None, description="""Free-text analytical method, used when analytical_method is \"other\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement']} })
    time_point: Optional[float] = Field(default=None, description="""Measurement time point for non-stationary experiments.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'SimulatedMIDDataPoint',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000056'} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'VariableSpecification']} })
    data_points: Optional[list[NMRIsotopomerDataPoint]] = Field(default=None, description="""Individual NMR isotopomer data points.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement', 'SimulatedMID']} })


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
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult']} })
    standard_deviation: float = Field(default=..., description="""Standard deviation of the measurement.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })


class FluxRatioMeasurement(ConfiguredBaseModel):
    """
    A measured flux ratio between two or more reactions.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000029',
         'from_schema': 'https://w3id.org/fluxolink/experiment'})

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
                       'EquivalenceCheck',
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
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult']} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation of the ratio.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'VariableSpecification']} })


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
                       'EquivalenceCheck',
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
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult']} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation of the ratio.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'VariableSpecification']} })


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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset'],
         'in_subset': ['core']} })
    path: str = Field(default=..., description="""Relative path or URI to the file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000297'} })
    format: InputFormatEnum = Field(default=..., description="""Format of the file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000229'} })
    format_other: Optional[str] = Field(default=None, description="""Free-text file format, used when format is \"other\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    role: list[FileRoleEnum] = Field(default=..., description="""Role(s) this file plays in the dataset. Multivalued because one file often plays several: a FluxML .fml is network, constraints, tracer, measurements and simulation setup at once; an INCA .m is all of those plus the driver.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile'], 'in_subset': ['core']} })
    role_other: Optional[str] = Field(default=None, description="""Free-text role, used when role includes \"other\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    checksum: Optional[str] = Field(default=None, description="""\"algorithm:hash\" digest (e.g., \"sha256:abc123...\") for content-integrity verification.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000288'} })
    media_type: Optional[str] = Field(default=None, description="""IANA media type / MIME type (e.g., \"application/xml\", \"text/csv\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    file_size_bytes: Optional[int] = Field(default=None, description="""Size of the file in bytes.""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    description: Optional[str] = Field(default=None, description="""Optional free-text description of the file contents.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'MetabolicNetworkModel',
                       'SourceFile',
                       'SolverOption',
                       'FluxoDataset']} })
    generated_by: Optional[str] = Field(default=None, description="""Tool that generated the file, when it was not authored by hand (e.g. \"txt2ftbl\" for influx_si .def files, \"fluxomics_data_converter\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    generator_version: Optional[str] = Field(default=None, description="""Version of the generating tool.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    generation_date: Optional[str] = Field(default=None, description="""When the file was generated.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile']} })
    derived_from: Optional[list[str]] = Field(default=None, description="""Source file(s) this file was generated from, by id into FluxoDataset.source_files (e.g. a converter-written EC.netw derived from EC.fml; a FluxML file derived from a whole MTF set). Absent for hand-written files. Whether the generated file encodes the same problem is recorded in FluxoDataset.equivalence_checks.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SourceFile'], 'slot_uri': 'prov:wasDerivedFrom'} })

    @field_validator('checksum')
    def pattern_checksum(cls, v):
        pattern=re.compile(r"^[a-z0-9]+:[0-9a-f]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.search(element):
                    err_msg = f"Invalid checksum format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.search(v):
            err_msg = f"Invalid checksum format: {v}"
            raise ValueError(err_msg)
        return v


class EquivalenceCheck(ConfiguredBaseModel):
    """
    The result of re-parsing a set of native files and comparing it with what it should encode: the dataset's own network and labeling experiments, or other source files. One check per encoding, e.g. one for the seven files of a generated MTF set. FLUXO has no term for this yet.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/fluxolink/experiment'})

    id: str = Field(default=..., description="""Unique identifier for the check.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset']} })
    files: list[str] = Field(default=..., description="""The files that were re-parsed and checked, as one encoding (by id into FluxoDataset.source_files).""", min_length=1, json_schema_extra = { "linkml_meta": {'domain_of': ['EquivalenceCheck']} })
    compared_with: Optional[list[str]] = Field(default=None, description="""Files the encoding was compared with. Absent means the dataset's own Tier-2 content (network_model_id / experiment_id below).""", json_schema_extra = { "linkml_meta": {'domain_of': ['EquivalenceCheck']} })
    network_model_id: Optional[str] = Field(default=None, description="""Network compared against when compared_with is absent (needed when the dataset has several networks).""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'EquivalenceCheck', 'SimulationRun']} })
    experiment_id: Optional[list[str]] = Field(default=None, description="""Experiments (configurations) compared against when compared_with is absent, e.g. the one configuration an MTF set holds.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EquivalenceCheck', 'SimulationRun']} })
    equivalent: bool = Field(default=..., description="""True when the comparison found no difference beyond the expected ones.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EquivalenceCheck']} })
    differences: Optional[list[str]] = Field(default=None, description="""One line per unexpected difference, \"[kind] key: detail\" (e.g. \"[atom_transition] SDH: 1 variant mapping(s) only in a\"). Must be empty when equivalent is true.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EquivalenceCheck']} })
    expected_differences: Optional[list[str]] = Field(default=None, description="""Differences the generator introduces by design (e.g. \"[reaction] A_out: drain added for terminal pool A\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['EquivalenceCheck']} })
    checked_by: Optional[str] = Field(default=None, description="""Tool that ran the check (e.g. \"fluxomics_data_converter\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['EquivalenceCheck']} })
    checker_version: Optional[str] = Field(default=None, description="""Version of that tool.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EquivalenceCheck']} })
    check_date: Optional[str] = Field(default=None, description="""When the check was run.""", json_schema_extra = { "linkml_meta": {'domain_of': ['EquivalenceCheck']} })


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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset'],
         'in_subset': ['core']} })
    name: Optional[str] = Field(default=None, description="""Human-readable name for this condition.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
                       'Condition',
                       'FluxoDataset']} })
    organism_name: Optional[str] = Field(default=None, description="""Name of the organism (e.g., Escherichia coli). Recommended; required at the benchmark tier for experimental data.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Condition'],
         'in_subset': ['core'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000181'} })
    strain: Optional[str] = Field(default=None, description="""Strain designation (e.g., BW25113). Recommended; required at the benchmark tier for experimental data.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Condition'],
         'in_subset': ['core'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000182'} })
    culture_medium: Optional[str] = Field(default=None, description="""Growth medium used for cultivation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Condition'], 'slot_uri': 'fluxo:FLUXO_0000184'} })
    specific_growth_rate: Optional[float] = Field(default=None, description="""Measured specific growth rate of the organism. No native format carries it; never auto-fill it from a biomass flux. Recommended; required at the benchmark tier for experimental data.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Condition'],
         'in_subset': ['core'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000084'} })
    growth_rate_unit: Optional[str] = Field(default=None, description="""Unit for the growth rate (e.g., 1/h). Required whenever specific_growth_rate is given.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Condition'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000219'} })


class SimulationRun(ConfiguredBaseModel):
    """
    A single simulation run linking an investigation, network model, and experiment(s) to a specific software tool, its settings and its results. A run can also be planned but not executed (run_status \"planned\"), which is how a FluxML configuration's <simulation> block is recorded.
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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset'],
         'in_subset': ['core']} })
    investigation_id: Optional[str] = Field(default=None, description="""Reference to the parent investigation. Recommended; required at the benchmark tier.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun'],
         'in_subset': ['core'],
         'recommended': True} })
    network_model_id: Optional[str] = Field(default=None, description="""Reference to the metabolic network model used. Recommended rather than required: a catalog-tier dataset references its network as a SourceFile instead of materialising it, and a hard requirement here would force such datasets to fabricate a stub MetabolicNetworkModel. Benchmark-tier datasets must carry a network — enforced by the FluxoDataset tier rule.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'EquivalenceCheck', 'SimulationRun'],
         'recommended': True} })
    experiment_id: Optional[list[str]] = Field(default=None, description="""Reference(s) to the labeling experiment(s) used. Singular for single-labeling-experiment MFA; multivalued (2+) for parallel labeling experiments (PLE) jointly fit to one shared flux solution. Optional for non-isotope methods (e.g., FBA).""", json_schema_extra = { "linkml_meta": {'domain_of': ['EquivalenceCheck', 'SimulationRun'], 'in_subset': ['core']} })
    configuration_name: Optional[str] = Field(default=None, description="""Name of the configuration inside the input file that this run executes (FluxML <configuration>@name). Lets a catalog-tier record say which of several configurations was run without materialising the experiment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun']} })
    fluxomics_method: Optional[FluxomicsMethodEnum] = Field(default=None, description="""The fluxomics method this run realises — a value from the FLUXO:0000021 subtree. IST_MFA requires stationary experiments and INST_MFA non-stationary ones (checked by `fluxolink-validate`). Recommended; required at the benchmark tier.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'in_subset': ['core'], 'recommended': True} })
    run_mode: Optional[list[RunModeEnum]] = Field(default=None, description="""What the run did: estimation, forward simulation, confidence intervals, Monte Carlo, ... Multivalued because one run can do several (INCA estimate then continuate). An influx_si --noopt run and every INCA benchmark script are forward simulations.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'in_subset': ['core']} })
    run_status: Optional[RunStatusEnum] = Field(default=None, description="""Whether the run was executed. \"planned\" records a specified but unexecuted run; \"completed\" with no flux_solution means the results were not extracted.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    condition: Optional[str] = Field(default=None, description="""Reference to the cultivation condition in FluxoDataset.conditions. Useful for stoichiometry-based runs (which have no labeling experiment); optional for isotope-based MFA, where the condition is reached through the experiment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun']} })
    software: SoftwareInfo = Field(default=..., description="""Software tool and version used for this run.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'in_subset': ['core']} })
    input_format: Optional[InputFormatEnum] = Field(default=None, description="""File format of the input data.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'slot_uri': 'fluxo:FLUXO_0000229'} })
    input_format_other: Optional[str] = Field(default=None, description="""Free-text input format, used when input_format is \"other\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    command_line: Optional[str] = Field(default=None, description="""The actual invocation, verbatim (e.g. \"influx_s.py --noopt --prefix simple_model\"). influx_si's .log records it, and it can differ from the .opt file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    optimization_method: Optional[str] = Field(default=None, description="""Optimization method used (e.g., nlsic, SLSQP, Levenberg-Marquardt). Recommended; required at the benchmark tier for estimation runs.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000088'} })
    objective_function: Optional[str] = Field(default=None, description="""Mathematical expression for the objective function being optimized (e.g., \"maximize biomass\" for FBA). May be empty for isotope-based MFA where the objective is implicit (minimize WSSR).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'slot_uri': 'fluxo:FLUXO_0000223'} })
    isotopic_state_space: Optional[IsotopicStateSpaceEnum] = Field(default=None, description="""Isotopic state-space representation used for computation (isotopomer, cumomer, EMU, or auto). A benchmarking-fairness parameter — tools differ in their native representation (13CFLUX2 cumomer, INCA cumomer/EMU, miemu EMU).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'slot_uri': 'fluxo:FLUXO_0000146'} })
    multistart_count: Optional[int] = Field(default=None, description="""Number of optimization restarts (for non-convex problems).""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    monte_carlo_runs: Optional[int] = Field(default=None, description="""Number of Monte Carlo resampling runs (FreeFlux n_runs, INCA montecarlo). Not a multistart count: each run resamples the measurements and re-solves.""", ge=1, json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    random_seed: Optional[int] = Field(default=None, description="""Random seed for reproducibility of stochastic optimizers.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    convergence_tolerance: Optional[float] = Field(default=None, description="""Optimizer convergence tolerance (e.g., 1e-6).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    stop_time: Optional[float] = Field(default=None, description="""Simulation stop time for non-stationary (INST) MFA, in time_unit.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    integration_timespan: Optional[list[float]] = Field(default=None, description="""Time grid the non-stationary simulation is evaluated on (FluxML <group>@times, INCA int_tspan, FreeFlux set_timepoints), in time_unit.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    time_unit: Optional[str] = Field(default=None, description="""Unit of stop_time and integration_timespan.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'SimulationRun'],
         'slot_uri': 'fluxo:FLUXO_0000221'} })
    solver_options: Optional[list[SolverOption]] = Field(default=None, description="""Every other tool setting, as key/value pairs with the tool's own names: influx_si flags (--prefix, --clownr, --zc, --noopt), INCA m.options keys (int_reltol, fit_starts), FreeFlux solve() arguments, FluxML <simulation>@type. Tool-specific knobs live here rather than in slots of their own, so the schema does not change when a tool adds an option.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    variables: Optional[list[VariableSpecification]] = Field(default=None, description="""Input variable specification: which fluxes and pool sizes are free, constrained or dependent, with starting values and bounds (influx_si .tvar; FluxML <simulation><variables>; FreeFlux ini_fluxes). Replaces the earlier initial_values slot, which stored bounds in confidence-interval slots.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    start_time: Optional[str] = Field(default=None, description="""When the run started.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    end_time: Optional[str] = Field(default=None, description="""When the run ended.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    runtime_seconds: Optional[float] = Field(default=None, description="""Wall-clock runtime in seconds. For a timing benchmark this is the result.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    converged: Optional[bool] = Field(default=None, description="""Whether the optimizer reported convergence.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    solver_status: Optional[str] = Field(default=None, description="""Native solver status message or code.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    iteration_count: Optional[int] = Field(default=None, description="""Number of optimizer iterations.""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun']} })
    flux_solution: Optional[FluxSolution] = Field(default=None, description="""Results of the run: estimated (or reference / simulated) flux values, pool sizes, simulated measurements and fit residuals.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'in_subset': ['core']} })
    goodness_of_fit: Optional[GoodnessOfFit] = Field(default=None, description="""Goodness-of-fit statistics for the solution.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'in_subset': ['core']} })
    input_files: Optional[list[str]] = Field(default=None, description="""Native input files used for this simulation run, by id into FluxoDataset.source_files (network, measurements, tracers, constraints, configuration). Referenced, not inlined, so one physical file is recorded once with one checksum.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000266'} })
    output_files: Optional[list[str]] = Field(default=None, description="""Output / results files produced by this simulation run, by id into FluxoDataset.source_files. Provenance for extracted results (NMDC has_output pattern).""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulationRun'], 'slot_uri': 'fluxo:FLUXO_0000284'} })


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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset'],
         'in_subset': ['core']} })
    software_name: MFASoftwareEnum = Field(default=..., description="""Name of the MFA software.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SoftwareInfo'], 'in_subset': ['core']} })
    software_name_other: Optional[str] = Field(default=None, description="""Free-text software name, used when software_name is \"other\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['SoftwareInfo']} })
    version: Optional[str] = Field(default=None, description="""Version of the software. Recommended: input files never record it. Required at the benchmark tier for completed runs.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MetabolicNetworkModel', 'SoftwareInfo'],
         'in_subset': ['core'],
         'recommended': True,
         'slot_uri': 'fluxo:FLUXO_0000243'} })
    url: Optional[str] = Field(default=None, description="""URL to the software repository or documentation.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SoftwareInfo']} })


class SolverOption(ConfiguredBaseModel):
    """
    One named tool or solver setting (a fluxomics parameter).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000210',
         'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    key: str = Field(default=..., description="""Native option name, verbatim (e.g. \"--clownr\", \"int_reltol\", \"solver\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['SolverOption']} })
    value: Optional[str] = Field(default=None, description="""Option value as text; absent for a flag that takes no value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult']} })
    description: Optional[str] = Field(default=None, description="""What the option does, when not obvious.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'MetabolicNetworkModel',
                       'SourceFile',
                       'SolverOption',
                       'FluxoDataset']} })


class VariableSpecification(ConfiguredBaseModel):
    """
    One row of a free/dependent/constrained variable specification: a flux or pool size, its classification, and its starting value and bounds. FLUXO has no term for this yet (new-term request).
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    variable_id: str = Field(default=..., description="""Reaction or metabolite identifier the variable belongs to. Not a typed reference: a specification may name free symbols that are not network entities.""", json_schema_extra = { "linkml_meta": {'domain_of': ['VariableSpecification']} })
    variable_kind: VariableKindEnum = Field(default=..., description="""Net flux, exchange flux, or pool size.""", json_schema_extra = { "linkml_meta": {'domain_of': ['VariableSpecification']} })
    variable_type: Optional[VariableTypeEnum] = Field(default=None, description="""Free, constrained, or dependent.""", json_schema_extra = { "linkml_meta": {'domain_of': ['VariableSpecification', 'FluxResult', 'PoolSizeResult']} })
    value: Optional[float] = Field(default=None, description="""Starting value (free) or fixed value (constrained). For a dependent variable any value is informational only: the tool recomputes it from the free variables (influx_si writes one in .tvar and ignores it).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult']} })
    lower_bound: Optional[float] = Field(default=None, description="""Lower bound of the variable.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint', 'VariableSpecification']} })
    upper_bound: Optional[float] = Field(default=None, description="""Upper bound of the variable.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'PoolSizeConstraint', 'VariableSpecification']} })
    increment: Optional[float] = Field(default=None, description="""Step size for grid or design scans (influx_si / FluxML \"inc\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['VariableSpecification']} })
    ed_weight: Optional[float] = Field(default=None, description="""Weight in experimental design (FluxML edweight).""", json_schema_extra = { "linkml_meta": {'domain_of': ['VariableSpecification']} })
    comment: Optional[str] = Field(default=None, description="""Optional free-text comment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment',
                       'MIDMeasurement',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'VariableSpecification']} })


class FluxSolution(ConfiguredBaseModel):
    """
    The flux values (and optionally pool sizes) that best explain the experimental data, or that were imposed for a forward simulation, together with what the model predicts for each measurement.
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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset'],
         'in_subset': ['core']} })
    solution_role: Optional[SolutionRoleEnum] = Field(default=None, description="""Whether the values were estimated, are known reference values (synthetic benchmark truth, fluxes imposed for a forward simulation), or were simulated.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxSolution']} })
    flux_results: Optional[list[FluxResult]] = Field(default=None, description="""Individual flux values.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxSolution'], 'in_subset': ['core']} })
    pool_size_results: Optional[list[PoolSizeResult]] = Field(default=None, description="""Estimated metabolite pool sizes.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxSolution']} })
    simulated_mids: Optional[list[SimulatedMID]] = Field(default=None, description="""Simulated MID values predicted by the model (measured-vs-fitted plots, WSSR re-derivation, forward-simulation output).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxSolution']} })
    measurement_fits: Optional[list[MeasurementFitResult]] = Field(default=None, description="""Measured-versus-simulated value and residual for each measurement (influx_si .miso.sim / .mflux.sim / .mmet.sim Residual and Pvalue columns).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxSolution']} })
    scale_factors: Optional[list[ScaleFactorResult]] = Field(default=None, description="""Fitted measurement scale factors (one per \"auto\"-scaled group; influx_si .pres.csv). They count towards the number of fitted parameters.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxSolution']} })


class FluxResult(ConfiguredBaseModel):
    """
    An estimated flux value for a single reaction, including uncertainty information.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000123',
         'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    reaction_id: str = Field(default=..., description="""Reference to the reaction in the network model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'FluxMeasurement', 'FluxResult'],
         'in_subset': ['core']} })
    flux_type: FluxTypeEnum = Field(default=..., description="""Type of flux (net, forward, backward, exchange).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxConstraint', 'FluxMeasurement', 'FluxResult'],
         'in_subset': ['core']} })
    value: float = Field(default=..., description="""Estimated flux value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000236'} })
    lower_ci: Optional[float] = Field(default=None, description="""Lower bound of the confidence interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult', 'ScaleFactorResult'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000262'} })
    upper_ci: Optional[float] = Field(default=None, description="""Upper bound of the confidence interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult', 'ScaleFactorResult'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000263'} })
    confidence_level: Optional[float] = Field(default=None, description="""Confidence level of lower_ci / upper_ci (e.g. 0.95). Tools differ (FreeFlux 0.95 for CIs, 0.999 for its chi-square test).""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult'], 'in_subset': ['core']} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation of the flux estimate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    flux_unit: Optional[str] = Field(default=None, description="""Unit of the flux value (e.g., mmol/gDW/h).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxMeasurement', 'FluxResult'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000219'} })
    confidence_interval_method: Optional[ConfidenceIntervalMethodEnum] = Field(default=None, description="""Method used to compute the confidence interval (profile likelihood, linearized, Monte Carlo, bootstrap, grid search).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult'], 'in_subset': ['core']} })
    variable_type: Optional[VariableTypeEnum] = Field(default=None, description="""Output partition: whether the flux was free, constrained or dependent in this fit (influx_si .tvar.sim). A choice of basis — compare solutions by value, not by partition.""", json_schema_extra = { "linkml_meta": {'domain_of': ['VariableSpecification', 'FluxResult', 'PoolSizeResult']} })
    structural_identifiability: Optional[str] = Field(default=None, description="""Native structural-identifiability verdict for the flux (influx_si .tvar.sim Struct_identif).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult']} })
    derivation: Optional[str] = Field(default=None, description="""How value (and its SD / CI) was derived rather than read, as a formula or short note that may quote the native number (e.g. \"xch = xch01 / (1 - xch01) from influx_si xch01 = 0.2; SD by the delta method\", \"xch = min(fwd, bwd)\"). Absent means the tool reported the value directly. The native output file (output_files) keeps the raw numbers.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult']} })


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
                       'PoolSizeResult',
                       'SimulatedMID']} })
    value: float = Field(default=..., description="""Estimated pool size value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000062'} })
    lower_ci: Optional[float] = Field(default=None, description="""Lower bound of the confidence interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult', 'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000262'} })
    upper_ci: Optional[float] = Field(default=None, description="""Upper bound of the confidence interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult', 'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000263'} })
    confidence_level: Optional[float] = Field(default=None, description="""Confidence level of lower_ci / upper_ci (e.g. 0.95).""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult']} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation of the pool size estimate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    pool_size_unit: Optional[str] = Field(default=None, description="""Unit of the pool size (e.g., mmol/gDW).""", json_schema_extra = { "linkml_meta": {'domain_of': ['PoolSizeMeasurement', 'PoolSizeResult'],
         'slot_uri': 'fluxo:FLUXO_0000222'} })
    confidence_interval_method: Optional[ConfidenceIntervalMethodEnum] = Field(default=None, description="""Method used to compute the confidence interval (profile likelihood, linearized, Monte Carlo, bootstrap, grid search).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult']} })
    variable_type: Optional[VariableTypeEnum] = Field(default=None, description="""Output partition: free, constrained or dependent in this fit.""", json_schema_extra = { "linkml_meta": {'domain_of': ['VariableSpecification', 'FluxResult', 'PoolSizeResult']} })
    structural_identifiability: Optional[str] = Field(default=None, description="""Native structural-identifiability verdict.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult']} })
    derivation: Optional[str] = Field(default=None, description="""How value (and its SD / CI) was derived rather than read, as a formula or short note that may quote the native number (e.g. \"xch = xch01 / (1 - xch01) from influx_si xch01 = 0.2; SD by the delta method\", \"xch = min(fwd, bwd)\"). Absent means the tool reported the value directly. The native output file (output_files) keeps the raw numbers.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult']} })


class SimulatedMID(ConfiguredBaseModel):
    """
    A simulated isotopic measurement: the MID the model predicts for one fragment. Carries no standard deviation or analytical method — it was computed, not measured.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000090',
         'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    measurement_id: Optional[str] = Field(default=None, description="""Id of the measured MIDMeasurement this simulates, when there is one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulatedMID', 'MeasurementFitResult', 'ScaleFactorResult']} })
    metabolite_id: Optional[str] = Field(default=None, description="""Reference to the simulated metabolite.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ReactionParticipant',
                       'PoolSizeConstraint',
                       'LabeledSource',
                       'MIDMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'PoolSizeResult',
                       'SimulatedMID'],
         'recommended': True} })
    fragment_name: Optional[str] = Field(default=None, description="""Native fragment name (e.g. INCA \"Ala2\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'SimulatedMID']} })
    measurement_spec: Optional[str] = Field(default=None, description="""Native measurement specification, verbatim.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement', 'SimulatedMID']} })
    atom_positions: Optional[str] = Field(default=None, description="""Atom positions covered by the fragment.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'SimulatedMID']} })
    scaled: Optional[bool] = Field(default=None, description="""Whether the values include the fitted scale factor of an \"auto\"-scaled group (i.e. are comparable to the raw measured values) rather than being normalised model output.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulatedMID']} })
    data_points: Optional[list[SimulatedMIDDataPoint]] = Field(default=None, description="""Simulated values, one per isotopologue (and time).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDMeasurement', 'NMRIsotopomerMeasurement', 'SimulatedMID']} })


class SimulatedMIDDataPoint(ConfiguredBaseModel):
    """
    One simulated isotopologue value.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    isotopologue_index: int = Field(default=..., description="""Isotopologue mass shift index (m+0, m+1, ...).""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint', 'SimulatedMIDDataPoint', 'MeasurementFitResult']} })
    time_point: Optional[float] = Field(default=None, description="""Time of the value (non-stationary simulation).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'SimulatedMIDDataPoint',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000056'} })
    value: float = Field(default=..., description="""Simulated abundance. Not bounded: solvers emit tiny negative values (e.g. -3.75e-09 in influx_si .miso.sim).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult']} })


class MeasurementFitResult(ConfiguredBaseModel):
    """
    How well the fitted model reproduces one measured value: measured and simulated value, SD, residual and its p-value. FLUXO has no per-measurement residual term yet.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    measurement_id: str = Field(default=..., description="""Id of the measurement (MIDMeasurement, FluxMeasurement, ...) or the native measurement name when the measurement is not materialised.""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulatedMID', 'MeasurementFitResult', 'ScaleFactorResult']} })
    isotopologue_index: Optional[int] = Field(default=None, description="""Isotopologue index, for labeling measurements.""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint', 'SimulatedMIDDataPoint', 'MeasurementFitResult']} })
    time_point: Optional[float] = Field(default=None, description="""Sampling time, for non-stationary measurements.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'SimulatedMIDDataPoint',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000056'} })
    measured_value: Optional[float] = Field(default=None, description="""Measured value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementFitResult']} })
    simulated_value: Optional[float] = Field(default=None, description="""Value predicted by the fitted model.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementFitResult']} })
    standard_deviation: Optional[float] = Field(default=None, description="""SD used to weight the residual.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000208'} })
    residual: Optional[float] = Field(default=None, description="""Unweighted residual, simulated minus measured value.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementFitResult']} })
    weighted_residual: Optional[float] = Field(default=None, description="""Residual divided by the SD, (simulated - measured) / SD. This is what influx_si's \"Residual\" column and INCA's res.val report.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementFitResult']} })
    p_value: Optional[float] = Field(default=None, description="""Native p-value of the residual (influx_si Pvalue column; a robust z-test, not a standard test).""", json_schema_extra = { "linkml_meta": {'domain_of': ['MeasurementFitResult']} })
    derivation: Optional[str] = Field(default=None, description="""Which of the values were derived rather than read, and how (e.g. \"measured_value = simulated_value - weighted_residual * SD\" when the input measurement file was unavailable).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult']} })


class ScaleFactorResult(ConfiguredBaseModel):
    """
    A fitted scale factor for one \"auto\"-scaled measurement group.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    measurement_id: str = Field(default=..., description="""Id or native name of the scaled measurement group (influx_si \"1:mass;F;111;108\").""", json_schema_extra = { "linkml_meta": {'domain_of': ['SimulatedMID', 'MeasurementFitResult', 'ScaleFactorResult']} })
    time_point: Optional[float] = Field(default=None, description="""Sampling time, when the factor is time-specific.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerMeasurement',
                       'SimulatedMIDDataPoint',
                       'MeasurementFitResult',
                       'ScaleFactorResult']} })
    value: float = Field(default=..., description="""Fitted scale factor.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'SolverOption',
                       'VariableSpecification',
                       'FluxResult',
                       'PoolSizeResult',
                       'SimulatedMIDDataPoint',
                       'ScaleFactorResult']} })
    standard_deviation: Optional[float] = Field(default=None, description="""Standard deviation of the scale factor.""", json_schema_extra = { "linkml_meta": {'domain_of': ['MIDDataPoint',
                       'FluxMeasurement',
                       'PoolSizeMeasurement',
                       'NMRIsotopomerDataPoint',
                       'FluxRatioMeasurement',
                       'PoolSizeRatioMeasurement',
                       'FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult']} })
    lower_ci: Optional[float] = Field(default=None, description="""Lower bound of the confidence interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult', 'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000262'} })
    upper_ci: Optional[float] = Field(default=None, description="""Upper bound of the confidence interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult', 'PoolSizeResult', 'ScaleFactorResult'],
         'slot_uri': 'fluxo:FLUXO_0000263'} })
    derivation: Optional[str] = Field(default=None, description="""How the factor was obtained when the tool does not report it (e.g. \"scaled / unscaled simulated measurement\" for 13CFLUX v3, which computes scale factors in closed form).""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxResult',
                       'PoolSizeResult',
                       'MeasurementFitResult',
                       'ScaleFactorResult']} })


class GoodnessOfFit(ConfiguredBaseModel):
    """
    Statistical measures of how well the flux solution fits the experimental data.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'fluxo:FLUXO_0000212',
         'from_schema': 'https://w3id.org/fluxolink/simulation_run'})

    wssr: Optional[float] = Field(default=None, description="""Weighted sum of squared residuals (variance-weighted).""", json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000086'} })
    sum_squared_residuals: Optional[float] = Field(default=None, description="""Unweighted sum of squared residuals.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit']} })
    number_of_measurements: Optional[int] = Field(default=None, description="""Number of measured values used in the fit.""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit']} })
    number_of_parameters: Optional[int] = Field(default=None, description="""Number of fitted parameters (free fluxes, free pool sizes and scale factors).""", ge=0, json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit']} })
    degrees_of_freedom: Optional[int] = Field(default=None, description="""Degrees of freedom in the fit.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000030'} })
    degrees_of_freedom_convention: Optional[str] = Field(default=None, description="""How degrees_of_freedom was counted when the tool does not report it (e.g. \"n_measurements - n_free_fluxes - n_auto_scaled_groups\" for 13CFLUX v3). Tools differ, so a comparison across tools needs the convention.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit']} })
    chi_square_p_value: Optional[float] = Field(default=None, description="""Upper-tail p-value of the chi-square goodness-of-fit test, P(X >= chi2); small values reject the fit. Always the upper tail: readers convert tools that report the lower tail (influx_si writes pchisq(chi2, df), so p = 1 - its value).""", json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit'],
         'in_subset': ['core'],
         'slot_uri': 'fluxo:FLUXO_0000213'} })
    chi_square_confidence_level: Optional[float] = Field(default=None, description="""Confidence level of the chi-square acceptance test (e.g. 0.95; FreeFlux uses 0.999).""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit']} })
    fit_accepted: Optional[bool] = Field(default=None, description="""The tool's own verdict on whether the fit passes its chi-square test.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GoodnessOfFit']} })
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
                                   'nest. It is enforced by `fluxolink-validate '
                                   '--benchmark` (src/fluxolink/validate.py) instead, '
                                   'together with every other field-level benchmark '
                                   'requirement.',
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
                       'EquivalenceCheck',
                       'Condition',
                       'SimulationRun',
                       'SoftwareInfo',
                       'FluxSolution',
                       'FluxoDataset'],
         'in_subset': ['core']} })
    name: Optional[str] = Field(default=None, description="""Human-readable name of the dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'Contributor',
                       'MetabolicNetworkModel',
                       'NetworkMetabolite',
                       'NetworkReaction',
                       'FluxConstraint',
                       'PoolSizeConstraint',
                       'LabelingExperiment',
                       'LabeledSource',
                       'TracerIsotopomer',
                       'Condition',
                       'FluxoDataset'],
         'in_subset': ['core']} })
    description: Optional[str] = Field(default=None, description="""Detailed description of the dataset contents.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Investigation',
                       'MetabolicNetworkModel',
                       'SourceFile',
                       'SolverOption',
                       'FluxoDataset']} })
    schema_version: Optional[str] = Field(default=None, description="""Version of the FluxoLink schema this dataset conforms to.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    creation_date: Optional[date] = Field(default=None, description="""Date the dataset was created.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    last_modified: Optional[date] = Field(default=None, description="""Date the dataset was last modified.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    fluxo_ontology_version: Optional[str] = Field(default=None, description="""FLUXO ontology release version used for term mappings (e.g., \"2026-04-08\"). Pins the ontology version for traceability.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    dataset_type: Optional[DatasetTypeEnum] = Field(default=None, description="""Classification of this dataset by curation tier. When \"benchmark\", the materialised network is required (LinkML rule below) and `fluxolink-validate` re-imposes the strict field-level set — tracer fractions and purities, MID values and SDs, software versions, and, for experimental data, the cultivation condition. When \"catalog\" or absent, input content stays in the referenced SourceFiles.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset'], 'in_subset': ['core']} })
    source_files: Optional[list[SourceFile]] = Field(default=None, description="""Native MFA files referenced by this dataset (FluxML, MTF, FTBL, .mat, etc.). Tier-1 provenance layer.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LabelingExperiment', 'FluxoDataset'], 'in_subset': ['core']} })
    conditions: Optional[list[Condition]] = Field(default=None, description="""All cultivation conditions in this dataset, defined once and referenced by LabelingExperiment.condition and SimulationRun.condition. Held at dataset level so one cultivation is described exactly once.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset'], 'in_subset': ['core']} })
    investigations: Optional[list[Investigation]] = Field(default=None, description="""All MFA investigations in this dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset'], 'in_subset': ['core']} })
    networks: Optional[list[MetabolicNetworkModel]] = Field(default=None, description="""All metabolic network models in this dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })
    experiments: Optional[list[LabelingExperiment]] = Field(default=None, description="""All labeling experiments in this dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset'], 'in_subset': ['core']} })
    simulation_runs: Optional[list[SimulationRun]] = Field(default=None, description="""All simulation runs in this dataset.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset'], 'in_subset': ['core']} })
    equivalence_checks: Optional[list[EquivalenceCheck]] = Field(default=None, description="""Results of re-parsing generated (or foreign) native files and comparing them with the content they should encode. This is how a dataset links tool formats: each tool's input files are recorded once, with what they were derived from and whether they still encode the same problem.""", json_schema_extra = { "linkml_meta": {'domain_of': ['FluxoDataset']} })


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
EquivalenceCheck.model_rebuild()
Condition.model_rebuild()
SimulationRun.model_rebuild()
SoftwareInfo.model_rebuild()
SolverOption.model_rebuild()
VariableSpecification.model_rebuild()
FluxSolution.model_rebuild()
FluxResult.model_rebuild()
PoolSizeResult.model_rebuild()
SimulatedMID.model_rebuild()
SimulatedMIDDataPoint.model_rebuild()
MeasurementFitResult.model_rebuild()
ScaleFactorResult.model_rebuild()
GoodnessOfFit.model_rebuild()
FluxoDataset.model_rebuild()
