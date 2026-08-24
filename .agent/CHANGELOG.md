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

_This changelog is maintained by the AI agent. Entries are appended as changes are made._
