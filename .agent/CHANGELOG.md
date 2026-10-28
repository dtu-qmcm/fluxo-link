# CHANGELOG — FluxoLink

Project change log. Updated by the AI agent as changes are made.

---

## v0.1.0 — Initial Setup

### Initial Project Setup (2026-05-12)

`added` `schema` `dev-tooling`

- Established project repository with LinkML schema backbone
- Created 6 schema modules totaling 974 lines:
  - `fluxolink.yaml` — Main schema (30 lines)
  - `enumerations.yaml` — FLUXO ontology-backed enums (240 lines)
  - `study.yaml` — Study provenance (104 lines)
  - `network.yaml` — Metabolic network model (244 lines)
  - `experiment.yaml` — Labeling experiments (165 lines)
  - `simulation_run.yaml` — Simulation runs (191 lines)
- Set up Python package with `pyproject.toml` (hatchling build, uv package manager)
- Configured dev tooling: pytest, ruff, mypy, pre-commit
- Added `.pre-commit-config.yaml` with lint + format hooks

---

## Phase 1-2 — Prefix Fix & Ontology Mappings (2026-07-17)

`changed` `schema` `ontology`

### Phase 1: Prefix-Doubling Fix

- Changed `fluxo:` prefix from `http://purl.obolibrary.org/obo/FLUXO_` to `http://purl.obolibrary.org/obo/` in all 6 schema files
- IRIs now expand correctly (e.g., `fluxo:FLUXO_0000162` -> `http://purl.obolibrary.org/obo/FLUXO_0000162`)

### Phase 2: Ontology Mappings & Bug Fixes

- **Critical bug fixed:** `MetabolicNetworkModel.class_uri` `FLUXO_0000057` -> `FLUXO_0000127` (was mapped to "fluxomics simulation")
- **5 classes got `class_uri`:**
  - `SimulationRun` -> `FLUXO_0000057` (fluxomics simulation)
  - `ReactionParticipant` -> `FLUXO_0000185` (reaction participant)
  - `MIDDataPoint` -> `FLUXO_0000143` (isotopologue distribution)
  - `PoolSizeResult` -> `FLUXO_0000062` (metabolite pool size)
  - `GoodnessOfFit` -> `FLUXO_0000212` (goodness of fit statistical test)
- **6 slots got `slot_uri`:**
  - `NetworkMetabolite.n_tracked_atoms` -> `FLUXO_0000183` (number of traced atoms)
  - `TracerIsotopomer.labeling_pattern` -> `FLUXO_0000148` (isotopomer representation)
  - `FluxResult.value` -> `FLUXO_0000236` (reaction rate)
  - `SimulationRun.optimization_method` -> `FLUXO_0000088` (flux estimation method)
  - `GoodnessOfFit.degrees_of_freedom` -> `FLUXO_0000030` (degrees of freedom)
  - `GoodnessOfFit.reduced_chi_square` -> `FLUXO_0000237` (residual mean square)
- **CI mappings fixed:** `lower_ci` -> `FLUXO_0000262`, `upper_ci` -> `FLUXO_0000263` (on both `FluxResult` and `PoolSizeResult`); added `standard_deviation` slot_uri to `PoolSizeResult`
- Removed `MIDDataPoint.value.slot_uri` (class-level mapping suffices)
- Fixed typo: "E.g.reactions" -> "E.g. reactions"
- 13/13 tests pass, ruff lint passes

### Known Issues (deferred to Phase 3)

- `GoodnessOfFit.assessment` references deleted `GoodnessAssessmentEnum` — dangling
- `ReactionParticipant.role` references `ParticipantRoleEnum` — to be removed
- `MeasurementGroup` still exists — to be replaced by type-specific classes

### Ontology Bug to Flag (fluxo repo)

- `FLUXO_0000209` (line 1802 in `fluxo-edit.owl`) has duplicate `IAO:0000115` definition ("upper confidence limit is a data item...") that belongs on `FLUXO_0000263`

---

## Git History

| Commit | Message |
|---|---|
| `25b8581` | fix definitions and add ontology links |
| `8b020b8` | update agent files |
| `78b0410` | Remove no-commit-to-branch hook from pre-commit |
| `e4cae2d` | Initial project setup with LinkML schema backbone |
| `e954a43` | Initial commit |

---

## Linking Tool Formats: `derived_from` + `EquivalenceCheck` (2026-10-27)

`added` `schema` `validation` — requested by the converter session for `fluxo convert --link`

FluxoLink links tool formats rather than being one more format. A dataset now
records, for every converter-generated tool input, what it was generated from
and whether it still encodes the same problem.

- **`SourceFile.derived_from`:** multivalued reference into `source_files`,
  `slot_uri: prov:wasDerivedFrom`. Multivalued because a FluxML file can be
  derived from a whole MTF set.
- **New `EquivalenceCheck` class, held at `FluxoDataset.equivalence_checks`:**
  - one check per encoding: `files` lists all files of the set (e.g. the seven
    MTF files);
  - `compared_with`: other files. When absent, `network_model_id` /
    `experiment_id` name the dataset's own Tier-2 content;
  - `equivalent`, `differences`, `expected_differences` (one
    "[kind] key: detail" line each);
  - `checked_by`, `checker_version`, `check_date`.

  It sits at dataset level rather than inlined on one "representative" file,
  so a multi-file encoding needs no convention about which file carries the
  check.
- **Validator:**
  - reference integrity for `derived_from` (never the file itself) and for
    every check reference;
  - `equivalence-consistency`: `equivalent: true` with unexpected differences
    is an error;
  - `equivalence-target` warning.
- **Verified:** 37 classes; 94 tests pass; ER diagram and core profile
  regenerated.

---

## Simplification: Format Mechanics Out, Core Profile + Flat Table In (2026-10-26)

`removed` `added` `schema` `docs` — breaking for documents that used the removed slots

### Why

The 2026-10-25 pass aimed for lossless round-trips of five file formats, and
that pulled format mechanics into the standard: 218 → 347 slots, 66 → 132
enum values. Lossless round-tripping is the converter's job. The checksummed
native files already preserve everything, so the record should hold only
normalised, tool-neutral facts.

### Removed (moved into `solver_options`, the converter, or the native files)

- **5 enums:** `SimulationTypeEnum`, `ExpressionNotationEnum`,
  `ConstraintOperatorEnum`, `ChiSquareTailEnum`, `MeasurementKindEnum`.
- **Constraints:** `FluxConstraint` / `PoolSizeConstraint` lose `operator`
  (it is in `expression`) and `expression_notation` (a MathML expression is
  kept verbatim and is recognisable by its leading `<`).
- **`SimulationRun`:**
  - `simulation_type`, `integration_rel_tolerance` and
    `integration_abs_tolerance` move to `solver_options`.
  - `file_prefix` moves to `solver_options` as `--prefix`; it is also in
    `command_line`.
- **`FluxResult` / `PoolSizeResult`:** `native_value` and
  `native_standard_deviation` are gone. `derivation` now quotes the native
  number (e.g. "… from influx_si xch01 = 0.2").
- **`MeasurementFitResult.measurement_kind`:** derivable from the measurement
  it points to.
- **`GoodnessOfFit.chi_square_tail`:** `chi_square_p_value` is now *always*
  the upper tail. Readers convert influx_si's lower tail (1 − p), and the
  `chi-square-tail` validator rule is gone.

**Result:** 21 enums / 113 values (was 26 / 132), 333 slots (was 347), 35
`SimulationRun` fields (was 39). Fixtures, the EC benchmark (regenerated) and
the converter's adapter, results readers and tests are updated.

### Added

- **`core` subset** (`in_subset: [core]`): 59 fields in 12 classes — the
  minimal record most datasets should fill and a database should index.
  - `docs/core_profile.md` is generated from it (`just core-profile`;
    `tests/test_flatten.py` fails if the page is stale).
  - `examples/valid/minimal_core_record.yaml` is a complete core record, with
    illustrative values.
- **Flat table for databases:**
  - `src/fluxolink/schema/flux_record.yaml` defines one row per run ×
    reaction × flux type, with the study context denormalised.
  - `fluxolink-flatten` (`src/fluxolink/flatten.py`) writes it as TSV, CSV,
    JSONL or YAML.
  - `just gen-sql` writes SQL DDL (`docs/flux_record.sql`).
  - The dataset documents stay the record of truth; the table is rebuilt from
    them.
- **Convention, recorded in AGENTS.md:** tool-specific knobs go to
  `solver_options`, never new slots or enums.

### Verified

- fluxolink: 92 tests pass. All 12 valid fixtures and the EC benchmark give
  0 errors.
- converter: 445 pass. 2 FluxML-writer round-trip tests fail because of the
  uncommitted `io/fluxml_writer.py` / `io/fluxml_parser.py` changes (purity
  is no longer written by default). With the committed versions of those
  files they pass.

---

## Phase 3t Compatibility Pass + `fluxolink-validate` (2026-10-25)

`added` `changed` `fixed` `schema` `validation` `examples` — 3t-1 … 3t-6 and 3t-13 done; 3t-7 … 3t-12 partly

### Why

The 2026-10-25 project review listed what still did not work:
- the schema bugs of 3t-2;
- `EC.fml` could not be represented;
- the fixtures carried invented values;
- a catalog record could not say how to re-run its tool (63 gaps in
  `check_runnable.py`).

This pass fixes the schema side of all four. The converter-side work
(adapter, equivalence diff, results readers, `fluxo` CLI) lives in the
converter repo; since 2026-10-27 it sits in the converter's `io/` layout (see
the converter-side list below).

### Required set tiered; benchmark gate in Python (3t-1)

Every `required` → `recommended` row of 3t-1 is applied. The strict set comes
back at the benchmark tier in **`src/fluxolink/validate.py`**, exposed as the
`fluxolink-validate` console script (rule `benchmark-required`). LinkML cannot
do this itself because `slot_conditions` cannot nest.

Refinement: the cultivation fields are required at the benchmark tier only for
`LabelingExperiment.data_origin: experimental` (new `DataOriginEnum`). A
synthetic benchmark has no culture.

### Semantic validation (new)

`fluxolink-validate` runs LinkML first, then checks:
- references (JSON Schema does not check foreign keys);
- `stationary` vs `fluxomics_method`;
- tracer-fraction sums and labeling-pattern length;
- one atom mapped twice, which is the INCA v51 contradiction;
- participant instance uniqueness and atom-index range;
- CI order, INST time points and the chi-square tail;
- `*_other` companions.

All rules are listed in `VALIDATION_REQUIREMENTS.md` (rewritten, 3t-13).
`schema_issues()` merges imports up front, so in-process validation no longer
depends on the working directory.

### Schema

- **3t-2:**
  - `aliases` are multivalued with a `tool:native_id` pattern.
  - Atom indices are 1-based.
  - `MIDDataPoint.value` is unbounded.
  - `SourceFile.role` is multivalued, plus `role_other`.
  - `input_files` / `output_files` are references.
  - `PoolSizeConstraint` is unmapped.
  - `IsotopicStateSpaceEnum.auto` is added.
  - New `SimulatedMID` / `SimulatedMIDDataPoint` classes.
- **3t-3:**
  - Constraint targets are optional, with expressions able to stand alone.
  - New slots: `flux_type` (the domain), `operator`, `expression_notation`,
    `is_auto_generated`.
  - `SourceFile.generated_by` / `generator_version` / `generation_date`.
- **3t-4:** One FluxML `<configuration>` = one `LabelingExperiment`.
  - New experiment slots: `configuration_name`, `nominal_time`, `comment`,
    `time_unit`, `network_model_id`, `source_files`.
  - Constraints can be scoped to one configuration.
  - The `<simulation>` block becomes a `planned` `SimulationRun`.
  - New `SimulationRun.configuration_name`.
- **3t-5:**
  - New `VariableSpecification` on `SimulationRun.variables`, which replaces
    `initial_values`.
  - `variable_type` and `structural_identifiability` on results.
- **3t-6:** New result classes:
  - `MeasurementFitResult` and `ScaleFactorResult`.
  - GoodnessOfFit gains `sum_squared_residuals`, `number_of_measurements`,
    `number_of_parameters`, `chi_square_tail`, `chi_square_confidence_level`,
    `fit_accepted`.
  - `confidence_level` on results.
  - New run slots:
    - invocation: `run_mode`, `run_status`, `command_line`, `file_prefix`,
      `solver_options` (`SolverOption`);
    - integration: tolerances, `integration_timespan`, `time_unit`;
    - provenance: start/end/runtime, `converged`, `solver_status`,
      `iteration_count`;
    - other: `monte_carlo_runs`, `solution_role`.
- **3t-7 / 3t-9 / 3t-10, partly:**
  - Measurement identity: `fragment_name`, `measurement_spec`,
    `flux_expression`, `pool_expression`, error models on flux and pool
    measurements.
  - Atom transitions: `ReactionParticipant.instance` with
    reactant/product instances, dangling atoms (product side optional),
    `AtomTransition.element`.
  - Metabolites: `NetworkMetabolite.is_external` / `is_balanced` /
    `symmetry`; `NetworkReaction.pathway` / `is_auto_generated`.
  - Time: `MIDDataPoint.time_point` with the `MIDMeasurement.time_points`
    grid (the group-level `time_point` is removed).
  - Network metadata: `description`, `version`, `modeler`, `model_date`,
    default flux bounds.
- **Types and enums:**
  - New `IsoDateTime` type: an ISO 8601 date-time with an optional time zone.
    FluxML `<info><date>` has no zone, and JSON Schema `date-time` would force
    one to be invented.
  - New enums: `RunModeEnum`, `RunStatusEnum`, `SimulationTypeEnum`,
    `VariableKindEnum`, `VariableTypeEnum`, `ConstraintOperatorEnum`,
    `ExpressionNotationEnum`, `SolutionRoleEnum`, `ChiSquareTailEnum`,
    `MeasurementKindEnum`, `DataOriginEnum`.
  - New values on existing enums: `13CFLUX3`, `miemu`, `freeflux_tsv`,
    `freeflux_xlsx`, `INCA_script`, `python_script`, `jupyter_notebook`,
    `plain_text`; specific measurement / variable-specification /
    driver-script / log file roles; `linearized` and `monte_carlo` CI
    methods.
- **New FLUXO mappings:** FLUXO_0000161, 0000029, 0000297, 0000288, 0000215,
  0000106, 0000232, 0000233, 0000090, 0000210, 0000064, 0000132, 0000221.
  FLUXO_0000302–0000306, cited by the plan for CI methods, do not exist in the
  2026-09-04 release.
- **Counts:** 36 classes, 26 enums (was 30 / 15).

### Examples

- **All 11 valid fixtures migrated**, and every `FABRICATED` value deleted. Most
  `LOST` markers are now data; the remaining ones are listed in each file
  header.
- **Reclassified as `catalog`:** the four "materialised" corpus encodings. They
  hold Tier-2 content, but their sources are not benchmark-complete:
  - no tracer purity in `.linp` / `linea.fml` / `EC.m`;
  - INCA's AKG5 has no values;
  - no FreeFlux version recorded.

  `fluxolink-validate --benchmark` lists exactly what is missing.
- **Illustrative fixtures:** organism, strain and growth-rate values that no
  source supports were removed. `data_origin: synthetic` is set.
- **`missing_required_fields.yaml`** now fails on slots that stay
  schema-required.

### Scripts and docs

- **`scripts/check_runnable.py`** resolves `input_files` ids, multivalued roles,
  `file_prefix`, `configuration_name`, driver scripts and `run_mode`. It treats
  a run whose inputs are materialised as regenerable. Unresolvable items went
  from 63 to 2, both in illustrative fixtures that record no invocation.
- **`scripts/query_tracers.py`** reads data-point time points, and its
  "unchecked" claims now point at the validator rules.
- **ER diagram** regenerated (`just erd`). The simulation module is split over
  two columns.
- **Plan docs:** `IMPLEMENTATION_PLAN.md` sections 3t-1 … 3t-13 carry status
  blocks, and `PATH_FORWARD.md` has a status note.

### Second round, driven by the converter adapter and results readers

The converter work turned up more schema gaps, closed the same day:

- **More fields demoted to `recommended`, re-imposed at the benchmark tier:**
  - `NetworkReaction.reactants`: pure influx reactions. The new rule
    `reaction-participants` still requires at least one participant.
  - `LabelingExperiment.labeled_sources`: FreeFlux keeps the tracer in its
    driver script.
  - `FluxMeasurement.value` / `PoolSizeMeasurement.value`: templates.
- **New slots:**
  - `NMRIsotopomerMeasurement.measurement_spec`.
  - On flux and pool size results: `native_value`,
    `native_standard_deviation`, `derivation`. These hold influx_si's raw
    xch01 next to the absolute exchange flux, and mark FreeFlux's
    `min(fwd, bwd)` exchange as derived.
  - `MeasurementFitResult.derivation`.
  - `ScaleFactorResult.lower_ci` / `upper_ci` / `derivation`.
  - `GoodnessOfFit.degrees_of_freedom_convention`.
  - `SimulatedMID.scaled`.
  - `MetabolicNetworkModel.default_flux_lower_bound` /
    `default_flux_upper_bound`.
- **New enum values:** `VariableKindEnum` `forward_flux` / `backward_flux`
  (INCA), and `InputFormatEnum.jupyter_notebook`.
- **`MeasurementFitResult.residual`** is now documented as unweighted. influx_si's
  "Residual" column and INCA's `res.val` are `weighted_residual`.
- **Validator:**
  - `ci-order` errors on `lower_ci > upper_ci`. An interval that excludes its
    value is now only a warning for Monte Carlo and bootstrap intervals.
  - New `mid-placeholder` warning for a group whose values are all 0.0.
  - The benchmark tier also requires `labeled_sources` and flux/pool
    measurement values.

### EC benchmark dataset

`examples/benchmark/ec_fluxml_benchmark.yaml` (370 KB) is generated from
`EC.fml` by the converter's `to_fluxo_dataset`. It holds:
- 62 metabolites, 100 reactions, 31 constraints;
- 4 configurations (68 MID groups);
- 4 planned 13CFLUX2 runs;
- an investigation from a sidecar, and no Condition (synthetic data).

It passes `fluxolink-validate --benchmark` with 0 errors and 103 warnings:
- **68 `mid-placeholder`:** every MID datum in EC.fml is 0.0 with SD 0.1;
- **35 `atom-transitions-missing`:** the FluxML parser keeps no atom data for
  efflux reactions.

`tests/test_examples.py` checks it end to end.

### Converter side (fluxomics_data_converter, uncommitted)

Paths as of 2026-10-27: the converter's `link/` package (branch `link-layer`,
commit 9e06c73; FluxoLink is a link between tool formats, not one more
`io/` format):

- **`link/record_from_model.py` / `link/model_from_record.py`:** dataset ↔
  converter model (`to_fluxo_dataset`, `from_fluxo_dataset`).
  `link/record.py` holds `save_record` / `record_text` / `load_record`.
- **`link/equivalence.py`:** the normalised equivalence diff (`compare`).
- **`link/tool_inputs.py`, `link/files.py`, `link/aliases.py`,
  `link/runs.py`:** write, check and record tool inputs. These fill
  `derived_from` and `equivalence_checks`, infer aliases and attach results.
- **`link/results/`:** readers for influx_si `<prefix>_res/` and INCA `.mat`
  files, and for FreeFlux and 13CFLUX v3 live result objects.
- **`cli.py`:** the `fluxo` command — `ingest`, `convert --link`,
  `add-input`, `add-results`, `validate`, `compare [--inputs]`, `export`,
  `meta init`.
- **Packaging:** optional extra `linkml = ["fluxolink"]` with a uv path source
  to this repo.
- **Tests:** 432 converter tests pass, 2 xfailed (376 before).

### Verified

- 84 tests pass (was 32): `tests/test_validate.py` has 51, and
  `tests/test_examples.py` now also checks the benchmark dataset.
- `ruff check`, `ruff format --check` and `mypy src` are clean; `linkml-lint`
  shows only the pre-existing `canonical_prefixes` warning; yamllint reports no
  errors on schema and examples.
- `fluxolink-validate` reports 0 errors on all 11 valid fixtures and on the EC
  benchmark (with `--benchmark`).

---

## Ontology-Grounded Method Enums, `Condition` Hoist, Tier-Rule Fix (2026-09-18)

`fixed` `changed` `schema` `ontology` `validation` — Phase 3t-0 closed; 3t-1 advanced

### 3t-0 was not a regression

PATH_FORWARD §13.12 and IMPLEMENTATION_PLAN §3t-0 both claimed Phase 3q/3r
content had been "silently lost from the working tree" and told the next reader
to restore it. **Wrong, and now withdrawn.** The audit was written 2026-08-19
against `HEAD` = `17487dc`; commit `160086d` (2026-08-24) removed that content
**deliberately**, and the working tree has matched `HEAD` ever since
(`git diff HEAD` on both files is empty). The instruction would have re-added
material the owner had just decided to drop.

Decisions now recorded rather than flagged as defects:

- `AerationEnum`, `CultivationModeEnum`, `Condition.aeration`/`.temperature`/
  `.ph`/`.cultivation_mode`/`.genotype` — cultivation-process detail, out of
  scope for fluxomics.
- `AnalyticalMethodEnum` NMR sub-types — the NMR attribute set is unsettled.
  Generic `NMR` and the NMR classes stay.
- `MFASoftwareEnum`: `COBRApy`, `cameo` — not MFA software.

### Enums re-grounded on the ontology

The removals exposed that the method enum had **no membership rule**, so values
drifted in and out by feel. Both enums are now defined as exactly one FLUXO
subtree, verified against `Fluxomics_ontology/mfao/fluxo.obo`:

- **`MFAMethodEnum` → `FluxomicsMethodEnum`** — exactly the `FLUXO:0000021`
  ("fluxomics method") subtree, 9 values: `I_MFA` (0000041), `C13_MFA`
  (0000042), `IST_MFA` (0000043), `INST_MFA` (0000044), `dynamic_MFA` (0000045),
  `kinetic_flux_profiling` (0000295), `stoichiometry_based` (0000018),
  `constraint_based` (0000019), `kinetic_modeling` (0000294).
- **`InvestigationTypeEnum` (NEW)** — exactly the `FLUXO:0000162` subtree:
  `MFA` (0000040), `FBA` (0000039). Surfaced as
  `Investigation.investigation_type`.

Two corrections fell out of this:

- **`C13_MFA` restored.** FLUXO:0000042 *is* a subclass of FLUXO:0000041, so its
  removal in `160086d` was collateral, not intended.
- **`FBA → FLUXO_0000039` was a category error, removed.** FLUXO:0000039 and
  FLUXO:0000040 are `is_a` FLUXO:0000162 *fluxomics investigation*, not methods.
  A method is a plan specification (`FLUXO:0000021` `is_a` IAO:0000104); an
  investigation is a completely executed planned process (`FLUXO:0000162` `is_a`
  COB:0000035). One investigation may realise several methods — the cross-tool
  benchmark case — so the method stays per-run on `SimulationRun` and the
  investigation type sits on `Investigation`.

**`SimulationRun.mfa_method` → `fluxomics_method`** accordingly: the enum now
covers stoichiometry-based, constraint-based and kinetic-modeling methods, for
which "MFA" is wrong. Renamed across schema, all fixtures, `scripts/` and the
three planning documents.

### Benchmark tier no longer requires `experiments`

`benchmark_tier_requires_input_ground_truth` required both `networks` and
`experiments` when `dataset_type == benchmark`. A stoichiometry-based run has no
tracer, so an FBA benchmark could only validate by fabricating a
`LabelingExperiment` plus a `TracerIsotopomer` with invented `tracer_fraction`
and `isotopic_purity` — the same defect as the placeholder networks removed on
2026-08-24. `networks` stays required; `experiments` is dropped from the
postconditions.

The real rule — *isotope-based method implies a labeling experiment* — **cannot
be written in LinkML**: `fluxomics_method` lives on `SimulationRun`, nested, and
`slot_conditions` cannot nest. It joins field-level tier strictness in the Phase
7 `fluxo validate --benchmark` gate. Moving the method onto `Investigation`
would not have helped: `Investigation` is nested under `FluxoDataset` exactly as
`SimulationRun` is, so the wall is nesting depth, not slot placement.

### `Condition` hoisted to dataset level, moved to `experiment.yaml`

`LabelingExperiment.condition` and `SimulationRun.condition` each **inlined**
their own copy, so one cultivation could be described twice with no shared
identity and no way to detect divergence — the same shape as the
`input_files`/`output_files` duplication logged in 3t-2.

- New `FluxoDataset.conditions` (multivalued, inlined) holds each condition once.
- Both slots are now **references by id**, not inlined objects.
- `Condition` moved `investigation.yaml` → `experiment.yaml`. `Investigation`
  never referenced it; both real consumers are `LabelingExperiment` and
  `SimulationRun`, and `simulation_run.yaml` already imports `experiment.yaml`,
  so no import changes were needed. `FLUXO:0000218` is `is_a` IAO:0000030
  information content entity, so the ontology does not pin it to either module.

### Also fixed

- `NMRIsotopomerMeasurement.analytical_method`'s description named the three
  deleted NMR sub-types; it now points at generic `NMR` and says why.
- `fluxolink.yaml`'s `dataset_type` description no longer promises an
  `experiments` requirement it does not impose.

### Tests & fixtures

- **`TestOntologyScopedEnums`** (`tests/test_schema.py`) — pins both enums to
  their exact value→term mapping and asserts FLUXO:0000039/0000040 never
  reappear as methods. This is the enum-completeness guard 3t-0 asked for,
  scoped to enums whose membership is an ontology fact.
- **`examples/valid/fba_benchmark_no_experiment.yaml` (NEW)** — a benchmark-tier
  dataset with a materialised network, a `constraint_based` run, and
  deliberately no experiments, tracer or atom transitions. Unrepresentable
  before this change.
- `test_stoichiometric_benchmark_needs_no_labeling_experiment`,
  `test_conditions_are_referenced_not_inlined` added;
  `test_benchmark_tier_requires_input_ground_truth` renamed to
  `..._requires_materialised_network` and its `experiments` assertion dropped.

### Verified

32 tests pass (was 26); `ruff check src tests` and `ruff format --check` clean;
all **11** valid fixtures validate; Pydantic datamodel regenerated.
`check_runnable.py` reports 63 unresolvable items against 62 for the same
fixture set before this change — the single new item is the new FBA fixture's
`unknown tool 'other'`, so runnability did not regress. (Note: the 2026-08-24
entry's figure of 27 does not reproduce against the current fixture set; the
62-item baseline was measured immediately before this change.)

### Still open

`VALIDATION_REQUIREMENTS.md` §3 references a `fluxomics_method` value `13C`.
The correct value is `C13_MFA`. Folded into the 3t-13 rewrite.

---

_This changelog is maintained by the AI agent. Entries are appended as changes are made._

---

## Validation Analysis (2026-07-17)

`analysis` `validation` `reproducibility`

### Cross-Format Minimal Requirements Analysis

Added `VALIDATION_REQUIREMENTS.md` with full cross-format analysis of minimal core data requirements for 13C-MFA across FluxML, FreeFlux, INCA, and influx_si.

Key findings:

- **influx_si is the strictest format** — explicitly requires `.netw`, `.linp`, `.miso` files, with `SD` column marked required (line 124 of spec)
- **FreeFlux is the most permissive** — only `reactions.tsv` is file-required; everything else via Python API
- **All 4 formats require**: `reaction.id`, `substrates`, `products`, `reversibility`, `atom_transitions` (for tracked metabolites); `tracer.metabolite`, `labeling_pattern`, `fraction`; `measurement.value`, `stddev`
- **No format requires metadata** for reproducibility — only FluxML has structured `<info>` block (optional)

### Schema Validation Gaps Identified

- **~12 fields** should be `required: true` but aren't (e.g., `MIDDataPoint.standard_deviation`, `TracerIsotopomer.tracer_fraction`/`isotopic_purity`, `NetworkReaction.substrates`/`products`, `LabelingExperiment.labeled_sources`, `SimulationRun.optimization_method`, `SoftwareInfo.version`)
- **Missing slot**: `LabelingExperiment.stationary` (boolean flag — universal across all 4 formats)
- **Cardinality constraints missing**: 5 (e.g., network needs >=1 metabolite/reaction)
- **Cross-slot rules missing**: 4 (e.g., INST-MFA requires time_point; tracked metabolites require atom transitions)

### Implementation Plan Updated

Added Phase 3j to `IMPLEMENTATION_PLAN.md` covering validation requirements. Critical changes:
- Mark 12 slots as `required: true`
- Add `LabelingExperiment.stationary` slot (new, required)
- Add cardinality constraints (`minimum_cardinality: 1`)
- Cross-slot rules deferred to Phase 5

---

## Multi-Method Investigation Analysis (2026-07-20)

`analysis` `schema` `fba-compatibility`

### Scenario Validated

User scenario: one investigation with FBA, then IST-MFA, then INST-MFA on a modified strain with different tracer — all in one dataset.

### Gaps Identified

- **`MFAMethodEnum` incomplete**: only 3 values (IST/INST/dynamic). Missing FBA (`FLUXO_0000039`), 13C-MFA (`FLUXO_0000042`), I-MFA (`FLUXO_0000041`), MFA (`FLUXO_0000040`), stoichiometry-based (`FLUXO_0000018`), constraint-based (`FLUXO_0000019`).
- **FBA has no labeling experiment**: `SimulationRun.experiment_id` is `required: true` — FBA can't satisfy this. `LabelingExperiment.class_uri` is "fluxomics isotope labeling experiment" — wrong for FBA.
- **FBA needs objective function**: no `objective_function` slot anywhere. FBA maximizes/minimizes biomass.
- **`study_type` on Study too rigid**: single method per study fails for multi-method investigations.

### Plan Updated (Phase 3k + 3l)

**Phase 3k — FBA compatibility:**
- Make `SimulationRun.experiment_id` optional (FBA has no experiment)
- Add `objective_function` slot to `SimulationRun` (for FBA's maximize biomass)
- Expand `MFAMethodEnum` with 6 new values from FLUXO ontology

**Phase 3l — Move study_type to SimulationRun:**
- Remove `Study.study_type` slot
- Add `mfa_method` slot to `SimulationRun` (required) — each run declares its method
- Enables multi-method studies (FBA + IST-MFA + INST-MFA in one study)

### Result

The schema now supports the full scenario: 3 studies (or one multi-method study), 2 networks, 2 experiments (IST-MFA + INST-MFA), 3 simulation runs (FBA with no experiment, IST-MFA, INST-MFA). All coexist in one `FluxoDataset`.

---

## Plan Review Response (2026-07-20)

`review` `plan` `conflicts` `ontology-bugs` `structural-gaps`

### Two comprehensive reviews received and accepted

Both reviews identified genuine defects, structural gaps, and missing validation rules. All critical and moderate findings were applied to `IMPLEMENTATION_PLAN.md` and `VALIDATION_REQUIREMENTS.md`.

### Schema-level bug fixes applied immediately

1. **Removed `slot_uri: fluxo:FLUXO_0000148` from `TracerIsotopomer.labeling_pattern`** — `_0000148` is "isotopomer representation" (a state-space choice), wrong for a tracer's binary label string. Slot left unmapped. (Phase 2 correction.)

2. **Removed `class_uri: fluxo:FLUXO_0000143` from `MIDDataPoint`** — that term is the *distribution* concept and belongs on `MIDMeasurement` (the group), not on an individual data point. Avoids collision when `MIDMeasurement` claims the same term in Phase 3c. (Phase 2 correction.)

3. **13/13 tests pass, ruff lint passes** after both fixes.

### New sub-phases added to plan (3m-3r)

| Phase | Finding addressed |
|---|---|
| **3m** — Parallel labeling experiments | `SimulationRun.experiment_id` made multivalued for PLE (FLUXO_0000050) — joint fitting of 2+ experiments to one flux solution |
| **3n** — Natural isotope correction + simulated values | Added `natural_abundance_corrected`/`correction_algorithm` slots on `MIDMeasurement`; added `simulated_mids` slot on `FluxSolution` for measured-vs-fitted plots |
| **3o** — FK typing & referential integrity | All `_id` slots now declare `range: SomeClass` (self-documenting FKs); referential-integrity tests added to Phase 5e |
| **3p** — Critical fixes | Wired `FluxConstraint` into `MetabolicNetworkModel`; rename `reactants`→`substrates`; add unit slots to `FluxMeasurement`/`PoolSizeMeasurement`; resolve SD contradiction (now required); ≥1 measurement constraint; FBA `condition` slot |
| **3q** — Expanded metadata & validation rules | Condition gains `aeration`/`temperature`/`ph`/`cultivation_mode`/`genotype`; SimulationRun gains `multistart_count`/`random_seed`/`convergence_tolerance`; CI method enum; NMR sub-method types; 5 new cross-slot rules; dataset versioning |
| **3r** — Enum coverage & scope | Add `other` escape hatch to closed enums; expand `MFASoftwareEnum` for FBA (COBRApy, cameo); broaden schema description |

### Phase 5 expanded (testing gaps)

- **5d** — Negative tests (invalid data must be rejected)
- **5e** — Referential-integrity tests (every `_id` resolves to existing object)
- **5h** — Real published model example (E. coli core + 3-method FBA/IST/INST scenario)

### VALIDATION_REQUIREMENTS.md synced

Fixed stale references:
- `LabelingExperiment.experiment_type` → marked as removed (replaced by `stationary`)
- `Study.study_type` → marked as removed (replaced by `SimulationRun.mfa_method`)
- `LabelingExperiment.stationary` → marked as added (was "new gap")
- Added new cross-slot rules (pattern length, atom index bounds, MID sum, sink carve-out, ≥1 measurement, referential integrity)

### Ontology TODOs flagged

- `FLUXO_0000223` (mathematical expression) overloaded on 3 slots — needs more specific term for "objective function"
- `FLUXO_0000062` (metabolite pool size) overloaded as both class_uri and slot_uri — needs distinct terms for "pool size class" vs "pool size value"
- No FLUXO term for natural isotope correction algorithm, CI method, or NMR multiplet types

### Scope decisions made explicit

- **Raw file provenance** (FTBL/.miso/FluxML/mzML paths, checksums): out of scope for now (parsed-content-only). Revisit if community curation goal emerges.
- **Replicate structure** (biological/technical replicate linkage): deferred — `dataset_id` slot hints at it but no formal replicate grouping.
- **Compartment class with volume**: deferred — flat string list adequate for prokaryotic models; revisit if eukaryotic compartmental INST-MFA in scope.
- **External repository accession** (FAIRDOMHub/MetabolomicsWorkbench): deferred.

---

`review` `plan` `conflicts`

### Conflicts Found and Resolved

1. **`SimulationRun.initial_values` optional vs required** — Phase 3f said optional, Phase 3j said required. **Resolved**: kept optional in the slot definition; requirement is now conditional via cross-slot rule (required only for isotope-based MFA; optional for FBA).

2. **`LabelingExperiment.stationary` (Phase 3j) vs `experiment_type` (existing)** — both encoded the same concept (stationary vs non-stationary). **Resolved**: added `stationary` boolean (simpler, matches all 4 format flags); delete `experiment_type` slot and `ExperimentTypeEnum`. Updated deleted list.

3. **Phase 4g HTML conversion already done** — the HTML files were converted to Markdown in a prior step but Phase 4g still listed the action. **Resolved**: marked Phase 4g as done; only README update remains.

### Redundancies Cleaned

4. **`Study.description` updated in two phases** (3b and 3l) — both touched the same field with overlapping changes. **Resolved**: consolidated into a single update in Phase 3b; Phase 3l now references it instead of duplicating.

5. **`ReactionParticipant.role` removal mentioned 3 times** — Known Issues, Phase 3e, and deleted list. Acceptable redundancy (cross-references), kept as-is for traceability.

### Missing Items Added

6. **FBA cross-slot rule missing from Phase 3j** — the rule "if `mfa_method` is isotope-based, `experiment_id` required" existed in `VALIDATION_REQUIREMENTS.md` but not in the plan's cross-slot table. **Resolved**: added to Phase 3j table along with the `initial_values` conditional rule.

7. **Slot_uri reuse flagged for ontology review** — `FLUXO_0000223` (mathematical expression) is used on 3 slots; `FLUXO_0000062` (metabolite pool size) is used as both class_uri and slot_uri. **Resolved**: documented as ontology TODOs in the "Ontology Bug to Flag" section. No schema changes needed.

---

## Phase 3 Implemented (2026-07-20)

`changed` `schema` `restructure` `validation` `fba` `rename`

Full Phase 3 (3a–3r) implemented across all schema modules. **13/13 tests pass, ruff clean, SchemaView smoke check passes** (29 classes, 13 enums; every range resolves, every class_uri/slot_uri/meaning expands without prefix doubling).

### Structural (3a–3e)

- **3a — Root container:** added `FluxoDataset` (`tree_root: true`, `class_uri FLUXO_0000002`) with flat collections (`investigations`, `networks`, `experiments`, `simulation_runs`).
- **3b — Condition:** renamed `OrganismInfo` → `Condition` (`class_uri FLUXO_0000218` "cultivation condition"); added `name`; moved biological context per-experiment (`LabelingExperiment.condition`, inlined, required); removed `Study.organism`.
- **3c — Option C measurements:** renamed `MeasurementGroup` → `MIDMeasurement`; added `FluxMeasurement`, `PoolSizeMeasurement`, `NMRIsotopomerMeasurement`, `NMRIsotopomerDataPoint`; split `LabelingExperiment.measurement_groups` into `mid_/nmr_/flux_/pool_size_measurements`; added `MIDDataPoint.weight`; deleted `MeasurementTypeEnum`.
- **3d — GoodnessOfFit:** removed dangling `assessment` slot (referenced deleted `GoodnessAssessmentEnum`).
- **3e — ReactionParticipant:** removed `role` slot (role now implicit from `substrates`/`products` list membership); deleted `ParticipantRoleEnum`.

### Compatibility & validation (3f–3l)

- **3f/3g:** added `LabeledSource.profile`/`input_type`, `TracerIsotopomer.profile_values`/`cost`, `SimulationRun.stop_time`/`initial_values`, `AtomTransitionVariant.ratio`, `PoolSizeConstraint`, `FluxRatioMeasurement`, `PoolSizeRatioMeasurement`.
- **3j — required fields:** marked unconditionally-required slots `required: true` (network `metabolites`/`reactions`, `substrates`, tracer `tracer_fraction`/`isotopic_purity`, `MIDDataPoint.standard_deviation`, `labeled_sources`, `optimization_method`, `SoftwareInfo.version`, `Condition.strain`/`specific_growth_rate`/`growth_rate_unit`, `MIDMeasurement.atom_positions`/`analytical_method`) + `minimum_cardinality: 1`. Added `stationary` boolean (required), deleted `ExperimentTypeEnum`. Conditional requirements (`products`, `atom_transition_variants`) marked `recommended: true` rather than hard-required, because unconditional requirement would break FBA / boundary reactions — the true conditional rules are deferred to Phase 5.
- **3k — FBA:** `experiment_id` made optional; added `objective_function`; expanded `MFAMethodEnum` (+MFA, I_MFA, C13_MFA, FBA, stoichiometry_based_MFA, constraint_based_MFA).
- **3l:** removed `Study.study_type`; added `SimulationRun.mfa_method` (required).

### Review-driven additions (3m–3r)

- **3m — PLE:** `SimulationRun.experiment_id` made multivalued (parallel labeling experiments jointly fit; maps to `FLUXO_0000050`).
- **3n:** added `MIDMeasurement.natural_abundance_corrected`/`correction_algorithm`; `FluxSolution.simulated_mids` (measured-vs-fitted).
- **3o — FK typing:** all `_id` reference slots now declare `range:` the referenced class (`Investigation`/`NetworkMetabolite`/`NetworkReaction`/`MetabolicNetworkModel`/`LabelingExperiment`). Required cross-module imports added (`experiment`→`network`; `simulation_run`→`investigation`+`network`+`experiment`).
- **3p:** wired orphaned `FluxConstraint` into `MetabolicNetworkModel` (+ `pool_size_constraints`); renamed `NetworkReaction.reactants` → `substrates`; added `flux_unit`/`pool_size_unit` + made `standard_deviation` required on `FluxMeasurement`/`PoolSizeMeasurement`; added optional `SimulationRun.condition` (FBA biological context).
- **3q:** `Condition` gained `aeration`/`temperature`/`ph`/`cultivation_mode`/`genotype`; `SimulationRun` gained `multistart_count`/`random_seed`/`convergence_tolerance`; `FluxResult`/`PoolSizeResult` gained `confidence_interval_method`; `AnalyticalMethodEnum` gained NMR sub-types; `FluxoDataset` gained `schema_version`/`creation_date`/`last_modified`/`fluxo_ontology_version`; new enums `AerationEnum`, `CultivationModeEnum`, `ConfidenceIntervalMethodEnum`.
- **3r:** `other` escape-hatch value + companion `*_other` free-text slots on `MFASoftwareEnum`/`InputFormatEnum`/`AnalyticalMethodEnum`; added `COBRApy`/`cameo`; broadened top-level schema description to cover FBA.

### Ontology-verified bug fixes (folded in)

- `TracerIsotopomer.labeling_pattern` — removed incorrect `slot_uri FLUXO_0000148` ("isotopomer representation" is a state-space concept, not a tracer label string). Left unmapped.
- `MIDDataPoint` / `NMRIsotopomerDataPoint` — no `class_uri`; the distribution terms `FLUXO_0000143`/`FLUXO_0000144` belong on the group classes (`MIDMeasurement`/`NMRIsotopomerMeasurement`), avoiding duplicate class_uri collisions.
- `MIDMeasurement.analytical_method` → `slot_uri FLUXO_0000190` ("mass spectrometry method"); deliberately NOT applied to the NMR class (NMR is not MS).

### Naming decision

- **`Study` → `Investigation`** (file `study.yaml` → `investigation.yaml`, module title, class, FK slots `study_id` → `investigation_id`, `FluxoDataset.studies` → `investigations`). Matches the exact ontology label of `FLUXO_0000162` ("fluxomics investigation"). User-approved full-rename scope.

### Deferred to Phase 5 (cross-slot rules)

INST-MFA time-point/stop-time requirements; atom-transition-required-when-tracked; tracer-fraction-sum ≤ 1.0; labeling-pattern-length = n_tracked_atoms; atom-index bounds; MID-sum ≈ 1.0; "at least one measurement type"; boundary-reaction product carve-out; isotope-method → experiment_id/initial_values required; referential integrity of `_id` values.

---

## Reactant/Product Naming Correction (2026-07-21)

`changed` `schema` `naming`

Reversed the Phase 3p `reactants` → `substrates` rename, and extended `substrate` → `reactant` to the atom-transition slots, so the schema uses the **reactant/product** pairing throughout:

- `NetworkReaction.substrates` → `NetworkReaction.reactants` (pairs with `products`).
- `AtomTransition.substrate_metabolite_id` → `reactant_metabolite_id`; `AtomTransition.substrate_atom_index` → `reactant_atom_index`.

**Rationale:** the FLUXO ontology's own participant roles are `FLUXO_0000167` **"reactant role"** and `FLUXO_0000169` **"product role"** (reactant/product, not substrate/product); the pairing is linguistically symmetric with `products`; and it matches the `reactants`/`products` naming already used by the `fluxomics_data_converter`, removing a field-name mismatch at the interchange boundary.

`LabeledSource`'s "labeled substrate (tracer mixture)" description was intentionally left unchanged — there "substrate" means the labeled feedstock fed to the cell, not a stoichiometric reaction participant. Examples and the generated datamodel were updated; 16/16 tests pass, both example datasets still validate.

---

## PATH_FORWARD — Architecture & Ground-Truth Decisions (2026-07-22)

`analysis` `plan` `architecture` `integration` `benchmarking`

Extended discussion on cross-tool benchmarking produced `PATH_FORWARD.md` and synced plan changes. **No schema (YAML) changes — planning documents only.**

### Architecture question: how deep should the schema go?

- Analyzed three paths: **A** (full parsed model, 29 classes), **B** (investigation catalog + results, ~10 classes), **C** (hybrid: parsed results, file references for inputs).
- Initially chose Path C, then **amended it**: a benchmark's *input* ground truth must be declared and validated — a file reference asserts provenance, not equivalence across the 4 tools' files.
- **Final decision — two-tier schema:** Tier 1 (provenance + results) required for all datasets; Tier 2 (input content — the Phase-3 classes) required for `benchmark` datasets, optional for `catalog` datasets. Optionality, not deletion, keeps catalog datasets light.

### Ground-truth holder: the LinkML dataset, not the converter

- Three-layer framing adopted: FLUXO ontology = *semantic* truth; LinkML schema = *information* truth; converter = *application* truth. A ground truth is an information artifact → the `FluxoDataset` holds it; the converter translates and validates (hydration adapter + equivalence diff + file generation).
- External precedents checked: ISA-JSON (pure manifest), SED-ML (reference + patch, stores no results), NMDC `DataObject` (LinkML-native file reference + `has_input`/`has_output`). Tier-1 design follows them; storing parsed results is the deliberate divergence — no stable cross-tool results format exists.
- Comparison-location decision: input-side structural comparison lives in the converter; results benchmarking is a query over `FluxResult`s by canonical `reaction_id`, not a converter responsibility.

### New planning actions (IMPLEMENTATION_PLAN.md)

- **Phase 3s** (schema additions): `SourceFile` + `FileRoleEnum`; `source_files` on `FluxoDataset`; `input_files`/`output_files` on `SimulationRun`; `aliases` (tool-namespaced, e.g. `"influx_si:v5"`) on `NetworkReaction`/`NetworkMetabolite` — canonical↔native ID mapping is new information present in no native file; `isotopic_state_space` re-added (benchmarking-fairness parameter); `replicate` on the 3 measurement classes; `tracer_summary`; `dataset_type` (benchmark/catalog) for two-tier enforcement.
- **Phase 5i** (validation): Tier-1 rules (checksum pattern, exactly one `role=network` file per run, benchmark⇒Tier-2 rule) + results-layer rules (CI ordering, alias format).
- **Phase 7** (integration): hydration adapter (`FluxoDataset` ↔ `FluxomicsData`), equivalence diff, results extraction (only influx_si `.tvar` exists today — 13CFLUX2/INCA/FreeFlux/miemu all new), metadata sidecar (`--meta` required for MTF/FreeFlux/INCA — no native format carries `Condition`/`Investigation` metadata; FluxML `<info>` partially excepted), CLI (`fluxo ingest`/`validate`/`compare`), EC benchmark end-to-end.
- **VALIDATION_REQUIREMENTS.md** synced: tier framing + new §5 (Tier-1/results-layer rules); stale `Study`→`Investigation` references fixed.

### Scope-decision reversals (vs. 2026-07-20 entry)

- **Replicate structure**: previously deferred → now **planned** (`replicate` slot, Phase 3s) — miemu and published datasets carry replicates.
- **Raw file provenance**: previously out of scope → now **in scope** as the `SourceFile` Tier-1 layer (provenance, not content duplication).
- **Dataset as simulation input**: deprioritized — simulators read native files via the converter; the dataset is not a solver input format.
- **miemu integration**: reframed as results *producer* (`FitResults` → `SimulationRun`); stationary-only; no χ² yet (`chi_square_p_value` left empty).

---

## Project Renamed: fluxo-schema → FluxoLink (2026-08-18)

`changed` `rename` `project-identity`

The project was renamed from **fluxo-schema** to **FluxoLink** — "fluxomics data model" is more representative of the work than "fluxo schema".

### What changed

- **Package/dist name:** `fluxo-schema` → `fluxolink` (`pyproject.toml`, `uv.lock` refreshed).
- **Python package:** `src/fluxo_schema/` → `src/fluxolink/` (`from fluxolink.datamodel.fluxolink import ...`).
- **Main schema file:** `fluxo_schema.yaml` → `fluxolink.yaml`; schema `name: fluxo-schema` → `fluxolink`; `title: FLUXO Schema` → `FluxoLink`.
- **Schema namespace URIs:** `https://w3id.org/fluxo/schema*` → `https://w3id.org/fluxolink*` (all 6 modules); submodule `name:` fields `fluxo-*` → `fluxolink-*`.
- **Tooling/docs:** justfile, config.yaml, pre-commit hooks, yamllint, CI workflow, freshness script, tests, README, AGENTS.md updated; Pydantic datamodel regenerated.

### What did NOT change

- LinkML template directory structure (`src/<pkg>/schema/`, `src/<pkg>/datamodel/`).
- **FLUXO ontology grounding:** the `fluxo:` prefix (`http://purl.obolibrary.org/obo/`), all `class_uri`/`slot_uri`/`meaning` mappings, `fluxo_ontology_version`, and the `FluxoDataset` class name.

---

## Dataset Tiering: `catalog` Made Expressible (2026-08-24)

`fixed` `schema` `validation` — Phase 3t-1 (partial)

`dataset_type: catalog` was decorative. `SimulationRun.network_model_id` was
`required: true` with range `MetabolicNetworkModel`, which requires >=1
metabolite and >=1 reaction with >=1 reactant — so a dataset that referenced its
native files instead of re-describing them could not carry a `SimulationRun` at
all, which is the only reason the tier exists. All four catalog fixtures held a
fabricated placeholder network purely to satisfy that slot.

### What changed

- `SimulationRun.network_model_id`: `required: true` -> `recommended: true`.
- `FluxoDataset` gains a `rules:` block,
  `benchmark_tier_requires_input_ground_truth`: when
  `dataset_type == benchmark`, `networks` and `experiments` are required. The
  requirement moved from an unconditional slot to the tier where materialised
  input content actually belongs.
- Placeholder networks **deleted** from `simple_model_mtf_catalog.yaml`,
  `linea_fluxml_catalog.yaml`, `simple_model_freeflux_catalog.yaml` and
  `ec_inca_catalog.yaml`, along with their now-dangling `network_model_id`
  references. Fixture comments updated — they documented the blocker.
- New negative fixture `examples/invalid/benchmark_tier_missing_inputs.yaml`
  plus two tests in `tests/test_examples.py`: one that a benchmark-tier
  document without input content is rejected, one that a catalog-tier document
  with no `networks` and no `experiments` validates.
- Pydantic datamodel regenerated.

Verified: 26 tests pass; all 10 valid fixtures validate; `check_runnable.py`
still reports exactly 27 unresolvable items (runnability is a separate defect
class and did not regress).

### Enabling fact, verified

LinkML `rules` are enforced, not decorative: they compile to JSON Schema
`if`/`then` and `linkml-validate` rejects violations. The gated-strictness
strategy in Phase 3t-1 depends on this.

### Correction to Phase 3t-1's design

`slot_conditions` **cannot nest** — `gen-json-schema` fails with
`SlotDefinition.__init__() got an unexpected keyword argument
'slot_conditions'`. So a rule on `FluxoDataset` can require the *presence of
blocks* but cannot re-impose `Condition.specific_growth_rate` or
`TracerIsotopomer.isotopic_purity`, and a rule on those classes cannot see
`dataset_type`. Field-level tier strictness must be an external validator (the
Phase 7 `fluxo validate --benchmark` gate), not a LinkML rule.

### Deliberately not done

The `required` -> `recommended` demotions in the 3t-1 table. Each is a
minimum-information judgement rather than housekeeping —
`Condition.specific_growth_rate` is required today and supplied by **zero** of
the four tool formats, so demoting it asserts what a fluxomics record may
legitimately omit. That belongs with the MI work.

---

_This changelog is maintained by the AI agent. Entries are appended as changes are made._
