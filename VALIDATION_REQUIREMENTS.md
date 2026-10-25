# Validation & Reproducibility Requirements

**Cross-format analysis** of minimal core data requirements for 13C-MFA across FluxML, FreeFlux, INCA, and influx_si, mapped to the current FLUXO schema.

> **Tier framing (2026-07-22, PATH_FORWARD §11):** §§1–4 of this document are
> the **Tier-2 (input-content) rules** — they apply when parsed input content
> is present, and are *mandatory* for `dataset_type: benchmark` datasets.
> **Tier-1 (file provenance) and results-layer rules live in §5.**

---

## 1. Minimal Core Requirements by Format

### Strictest → most permissive

| Format | Mandatory files/elements | Strictness |
|---|---|---|
| **influx_si** | `.netw` (network), `.linp` (tracer), `.miso` (MID measurements with `SD` column explicitly required) | **Strictest** — only format that explicitly requires measurement data and stddev |
| **FluxML** | `<reactionnetwork>` only; `<info>`, `<constraints>`, `<configuration>` (containing tracer, measurement, simulation) all optional | Strict at network level, lax elsewhere |
| **INCA** | `reaction({...})` block; `tracer()` and `experiment()` constructed in code; measurements attached but not strictly "required" by syntax | Lax — code-driven |
| **FreeFlux** | `reactions.tsv` only; tracers, measurements, bounds, simulation params all set via Python API | **Most permissive** — files alone are insufficient |

### Cross-cutting intersection (required by ALL 4 formats)

| Category | Required fields |
|---|---|
| **Network** | `reaction.id`, `reaction.reactants`, `reaction.products`, `reaction.reversibility` (expressible), `reaction.atom_transitions` (for carbon-tracked metabolites) |
| **Tracer** | `tracer.metabolite`, `tracer.labeling_pattern`, `tracer.fraction` (must sum to ≤1.0) |
| **Measurement** | At least one measurement; `measurement.value`, `measurement.stddev` (present in every example in all 4 formats; explicitly required in influx_si) |
| **Simulation** | Stationary vs non-stationary flag; for INST-MFA: time points |

### Union of optional-but-important fields

| Category | Field | Format(s) |
|---|---|---|
| **Network** | `metabolite.formula`, `metabolite.charge`, `metabolite.compartment`, `metabolite.n_tracked_atoms` | FluxML has `atoms`/`cfg`; others derive from atom transitions |
| **Tracer** | `tracer.isotopic_purity` | FluxML explicit; others implicit in fractions |
| **Measurement** | `measurement.atom_positions`, `measurement.time_point`, `measurement.scale_method`, `measurement.error_model` | FluxML only for scale/error; atom positions in all 4 |
| **Simulation** | `simulation.initial_flux_values`, `simulation.flux_bounds`, `simulation.stop_time` | INCA + influx_si require initial values; FluxML + INCA require bounds; stop time for INST only |
| **Metadata** | `model.name`, `model.strain`, `modeler`, `date`, `format_version` | FluxML `<info>` only; absent elsewhere |

---

## 2. Current Schema vs. Minimal Requirements

### ✅ Currently required (correct)

| Field | Required via |
|---|---|
| `*.id` (identifier) on all primary classes | `identifier: true`, `required: true` |
| `Investigation.name` | `required: true` |
| ~~`LabelingExperiment.experiment_type`~~ | **Removed in Phase 3j** — replaced by `stationary: boolean` (simpler, matches all 4 format flags) |
| `NetworkReaction.reversibility` | `required: true`, `ifabsent: true` |
| `NetworkReaction.reaction_type` | **Now `required: true` (Phase 3p)** — load-bearing for "products optional if sink/demand/exchange" rule |
| `TracerIsotopomer.labeling_pattern` | `required: true` (note: `slot_uri: FLUXO_0000148` removed — wrong concept) |
| `MIDDataPoint.isotopologue_index`, `.value` | `required: true` |
| `FluxResult.reaction_id`, `.flux_type`, `.value` | `required: true` |
| `SimulationRun.investigation_id`, `.software` | `required: true` (note: `experiment_id` now optional for FBA — Phase 3k) |
| `SimulationRun.network_model_id` | **`recommended` since 2026-08-24 (Phase 3t-1)** — was `required`, which made `dataset_type: catalog` inexpressible. A benchmark-tier dataset must still carry a materialised network, now enforced by the `FluxoDataset` rule `benchmark_tier_requires_input_ground_truth` rather than by this slot |
| `SoftwareInfo.software_name`, `.version` | `required: true` (version added in Phase 3j) |
| `AtomTransition.reactant_metabolite_id`, `.reactant_atom_index`, `.product_metabolite_id`, `.product_atom_index` | `required: true` |
| `LabeledSource.metabolite_id` | `required: true` |

### ❌ Should be required but currently optional (validation gaps)

| Field | Reason | All 4 formats require? |
|---|---|---|
| `MetabolicNetworkModel.metabolites` | Network needs at least one metabolite | ✅ Yes |
| `MetabolicNetworkModel.reactions` | Network needs at least one reaction | ✅ Yes |
| `NetworkReaction.reactants` | A reaction without reactants is meaningless | ✅ Yes |
| `NetworkReaction.products` | Required unless it's an efflux (sink) — but currently no way to express this | ✅ Yes (except sink reactions) |
| `NetworkReaction.atom_transition_variants` | Required for 13C-MFA — atom transitions are universally needed for carbon-tracked metabolites | ✅ Yes (for tracked metabolites) |
| `ReactionParticipant.metabolite_id` | Currently required ✓, but `stoichiometry` has `ifabsent: float(1.0)` (acceptable) | ✅ Yes |
| `TracerIsotopomer.tracer_fraction` | Required — without fraction, tracer composition is undefined | ✅ Yes |
| `TracerIsotopomer.isotopic_purity` | Required for reproducibility — purity affects MID simulation. FluxML always includes it; implicit in others | ⚠️ FluxML yes; others implicit |
| `MIDDataPoint.standard_deviation` | **Explicitly required in influx_si (line 124)**; present in every example across all 4 formats | ✅ Yes |
| `FluxMeasurement.value`, `.standard_deviation` (planned Phase 3) | Required for flux fitting | ✅ Yes |
| `PoolSizeMeasurement.value` (planned Phase 3) | Required if pool size data present | ✅ Yes |
| `SimulationRun.flux_solution` | Required for reproducibility — without it, results can't be verified | ⚠️ Not in input, but in output |
| `LabelingExperiment.labeled_sources` | A labeling experiment without tracer info is meaningless | ✅ Yes |
| `LabelingExperiment.mid_measurements` (planned Phase 3) | At least one measurement is needed to fit fluxes (influx_si requires `.miso`) | ✅ Yes (at least one measurement type) |
| `SimulationRun.optimization_method` | Required for reproducibility — different methods give different results | ⚠️ Tool-specific |
| `Investigation.contributors` | Provenance — at least one contributor for reproducibility | ⚠️ Best practice |

### ❌ Missing entirely from schema

| Field | Reason | Source |
|---|---|---|
| `SimulationRun.initial_flux_values` | Required by INCA (`m.rates.flx.val`) and influx_si (`.tvar` Value for F/C types) for solver warm-starting | Phase 3f — planned (conditional: required for isotope-based MFA; optional for FBA) |
| `SimulationRun.stop_time` | Required for INST-MFA in all 4 formats | Phase 3f — planned |
| ~~`LabelingExperiment.stationary` (flag)~~ | **Added in Phase 3j** — replaces `ExperimentTypeEnum` |
| `MIDMeasurement.atom_positions` | Required in all 4 formats (FluxML `[2,3]`, FreeFlux `_23` suffix, INCA `@ 2 3`, influx_si `Fragment` col) | Phase 3c — planned |
| `NetworkMetabolite.is_tracked` (or `n_tracked_atoms` enforce) | Determines whether atom transitions are required for this metabolite | `n_tracked_atoms` exists; cross-slot rule deferred to Phase 5 |
| Flux/reaction bound defaults | FluxML/INCA require bounds for solver; FreeFlux/influx_si don't | Phase 3p — `FluxConstraint` now wired to `MetabolicNetworkModel.flux_constraints` |
| **`SimulationRun.experiment_id` (multivalued)** | Required for parallel labeling experiments (PLE) — FLUXO_0000050 | Phase 3m — planned |
| **`MIDMeasurement.natural_abundance_corrected`** | Whether MID is raw or corrected affects fluxes substantially | Phase 3n — planned |
| **`FluxMeasurement.flux_unit` / `PoolSizeMeasurement.pool_size_unit`** | Measured values without units aren't reproducible | Phase 3p — planned |
| **FK slots typed as class references** | `reaction_id`, `metabolite_id`, etc. should declare `range: NetworkReaction` etc. | Phase 3o — planned |
| **`SourceFile` + `FileRoleEnum`** | Tier-1 file provenance (path, format, role, checksum) for native input/output files | Phase 3s — planned |
| **`NetworkReaction.aliases` / `NetworkMetabolite.aliases`** | Canonical↔native ID mapping for cross-tool comparison — new information present in no native file | Phase 3s — planned |
| **`replicate`** (on the three measurement classes) | miemu and published datasets carry replicate indices | Phase 3s — planned |
| **`FluxoDataset.dataset_type`** | Two-tier enforcement: `benchmark` ⇒ Tier-2 content required | Phase 3s — planned |
| **`SimulationRun.isotopic_state_space`** | Benchmarking-fairness parameter (was present pre-restructure; tools differ: cumomer vs EMU) | Phase 3s — re-added |

---

## 3. Recommended Validation Rules for Reproducibility

### Critical (must validate for reproducibility)

| Slot | Validation rule | Justification |
|---|---|---|
| `MetabolicNetworkModel.metabolites` | `required: true`, `minimum_cardinality: 1` | Network needs ≥1 metabolite |
| `MetabolicNetworkModel.reactions` | `required: true`, `minimum_cardinality: 1` | Network needs ≥1 reaction |
| `NetworkReaction.reactants` | `required: true`, `minimum_cardinality: 1` | Reaction needs ≥1 reactant (except sink) |
| `NetworkReaction.products` | `required: true` (with sink exception) | Reaction needs ≥1 product (except efflux) |
| `NetworkReaction.atom_transition_variants` | `required: true` for reactions involving tracked metabolites | 13C-MFA requires atom transitions |
| `NetworkReaction.reversibility` | `required: true` (already is) | Universal — affects flux parametrization |
| `TracerIsotopomer.tracer_fraction` | `required: true`, `minimum_value: 0.0`, `maximum_value: 1.0` | Tracer composition must be specified |
| `TracerIsotopomer.isotopic_purity` | `required: true`, `minimum_value: 0.0`, `maximum_value: 1.0` | Purity affects MID simulation; FluxML always includes |
| `MIDDataPoint.standard_deviation` | `required: true`, `minimum_value: 0.0` | Explicitly required in influx_si; present in all examples |
| `LabelingExperiment.labeled_sources` | `required: true`, `minimum_cardinality: 1` | Experiment needs tracer info |
| `LabelingExperiment.stationary` | `required: true` (boolean, new) | Determines INST vs stationary — affects all solver behavior |
| `SimulationRun.optimization_method` | `required: true` | Reproducibility — different methods give different results |
| `SimulationRun.initial_flux_values` | `required: true` (conditional — isotope-based MFA only; FBA optional) | Solver warm-starting |
| `SoftwareInfo.version` | `required: true` | Software version critical for reproducibility |
| `Investigation.publication_doi` | (recommend `required: true` for published studies) | Provenance |
| `Condition.organism_name` | `required: true` (already is) | Reproducibility |
| `Condition.strain` | `required: true` (currently optional) | Reproducibility — strain affects metabolism |
| `Condition.specific_growth_rate` | `required: true` (currently optional) | Critical — growth rate directly affects flux scaling |
| `Condition.growth_rate_unit` | `required: true` (currently optional) | Without unit, growth rate is ambiguous |
| `MIDMeasurement.atom_positions` | `required: true` (planned Phase 3) | Required in all 4 formats |
| `SimulationRun.fluxomics_method` | `required: true` (Phase 3l — moved from Investigation) | Determines simulation approach |
| `NetworkReaction.reaction_type` | `required: true` (Phase 3p) | Load-bearing for "products optional if sink/demand/exchange" rule |
| `FluxMeasurement.standard_deviation` | `required: true` (Phase 3p — contradiction resolved) | Required in all 4 formats |
| `PoolSizeMeasurement.standard_deviation` | `required: true` (Phase 3p) | Required in influx_si; FreeFlux exception handled by converter |

### Important (recommended for reproducibility)

| Slot | Validation rule | Justification |
|---|---|---|
| `NetworkMetabolite.formula` | `required: true` for tracked metabolites | Allows deriving `n_tracked_atoms`; InChI computation |
| `NetworkMetabolite.compartment` | `required: true` | Flux compartmentalization |
| `NetworkMetabolite.n_tracked_atoms` | `required: true` for tracked metabolites | MID dimensionality; already has `slot_uri` |
| `MIDMeasurement.analytical_method` | `required: true` | GC-MS vs LC-MS vs NMR affects MID interpretation |
| `MIDMeasurement.scale_method` | `required: true` | Affects fit — auto vs one changes optimization |
| `SimulationRun.input_format` | `required: true` | Reproducibility — format affects parsing |
| `SimulationRun.isotopic_state_space` | `required: true` | Affects computation (isotopomer vs cumomer vs EMU) |
| `FluxResult.flux_unit` | `required: true` | Without unit, flux value is ambiguous |
| `PoolSizeResult.pool_size_unit` | `required: true` | Same |
| `Investigation.contributors` | `required: true`, `minimum_cardinality: 1` | Provenance |
| ~~`Investigation.study_type`~~ | **Removed in Phase 3l** — replaced by `SimulationRun.fluxomics_method` (per-run, not per-study) |

### Cardinality constraints (LinkML `minimum_cardinality`)

| Slot | Rule |
|---|---|
| `MetabolicNetworkModel.metabolites` | `minimum_cardinality: 1` |
| `MetabolicNetworkModel.reactions` | `minimum_cardinality: 1` |
| `NetworkReaction.reactants` | `minimum_cardinality: 1` (except sink reactions) |
| `LabelingExperiment.labeled_sources` | `minimum_cardinality: 1` |
| At least one of `mid_measurements` / `flux_measurements` / `pool_size_measurements` on `LabelingExperiment` | `minimum_cardinality: 1` (any one) |

### Cross-slot constraints (LinkML `rules` or `expression`)

| Rule | Justification |
|---|---|
| If `LabelingExperiment.stationary == false`, then `SimulationRun.stop_time` is required | INST-MFA needs stop time |
| If `LabelingExperiment.stationary == false`, then `MIDMeasurement.time_point` is required | INST-MFA needs time points |
| If `NetworkMetabolite.n_tracked_atoms > 0`, then `NetworkReaction.atom_transition_variants` is required | 13C-MFA requires atom transitions for tracked metabolites |
| `TracerIsotopomer.tracer_fraction` must sum to ≤1.0 per `LabeledSource` | influx_si enforces this |
| `MIDDataPoint.value` must be in [0, 1] (already enforced via `minimum_value`/`maximum_value`) | MID is fractional abundance |
| If `SimulationRun.fluxomics_method` is isotope-based (IST/INST/dynamic/13C/I-MFA), then `SimulationRun.experiment_id` is required | Isotope MFA needs an experiment; FBA doesn't |
| **`TracerIsotopomer.labeling_pattern` length must equal referenced metabolite's `n_tracked_atoms`** | Silent curation error otherwise (e.g., 6-carbon glucose with 4-char pattern) |
| **`AtomTransition.reactant_atom_index` / `product_atom_index` must be < `n_tracked_atoms` of respective metabolite** | Out-of-bounds check |
| **`MIDDataPoint.isotopologue_index` must not exceed metabolite's `n_tracked_atoms`** | Can't have m+7 for a 6-carbon metabolite |
| **Sum of `MIDDataPoint.value` across one `MIDMeasurement.data_points` should be ≈1.0** | Standard MID sanity check every format's tooling performs |
| **If `NetworkReaction.reaction_type` is `sink`/`demand`/`exchange`, then `products` is optional (not required)** | Extends the "products required except sink" carve-out to all one-sided reaction types |
| **`LabelingExperiment` must have ≥1 of `mid_measurements`/`nmr_measurements`/`flux_measurements`/`pool_size_measurements` populated** (unless `fluxomics_method` is FBA) | influx_si requires `.miso`; all formats need ≥1 measurement to fit |
| **Referential integrity:** every `_id` value must resolve to an existing object's `id` elsewhere in the same `FluxoDataset` | Most common defect in multi-entity dataset files |

---

## 4. Summary of Schema-Validation Gaps

| Gap type | Count | Impact |
|---|---|---|
| Fields should be `required: true` but aren't | ~12 | Critical — affects reproducibility |
| Fields missing entirely from schema | 2 (`stationary`, `initial_flux_values` already planned) + 6 Tier-1/comparison items (§2, Phase 3s) | High — needed for INST-MFA + solver warm-start + provenance/comparison |
| Cardinality constraints missing | 5 | Medium — empty collections pass validation |
| Cross-slot rules missing | 4 | Medium — INST-MFA / atom transition enforcement |
| Tier-1 / results-layer rules missing | 6 + 5 (§5) | High — provenance & comparison integrity |

### Highest-priority validation additions

1. **`MIDDataPoint.standard_deviation` → required: true** (influx_si explicitly requires; all formats include)
2. **`TracerIsotopomer.tracer_fraction`, `.isotopic_purity` → required: true** (tracer composition)
3. **`NetworkReaction.reactants`, `.products` → required: true** (meaningful reactions)
4. **`LabelingExperiment.labeled_sources` → required: true** (experiment needs tracer)
5. **Add `LabelingExperiment.stationary` (boolean, required)** (universal INST/stationary flag)
6. **`SimulationRun.optimization_method`, `.initial_flux_values` → required: true** (reproducibility)
7. **`SoftwareInfo.version` → required: true** (reproducibility)
8. **`Condition.strain`, `.specific_growth_rate`, `.growth_rate_unit` → required: true** (reproducibility)
9. **`MetabolicNetworkModel.metabolites`, `.reactions` → required: true** with cardinality constraints

---

## 5. Tier Structure — Tier-1 & Results-Layer Rules (2026-07-22)

PATH_FORWARD §11 established the two-tier schema: **Tier 1** (file provenance
+ results) is required for all datasets; **Tier 2** (input content — the
subject of §§1–4) is required for benchmark/truth-carrying datasets and
optional for results-catalog datasets. The rules below complete the picture.

### Tier-1 rules (all datasets)

| Rule | Justification |
|---|---|
| `SourceFile.path` resolvable; `format` known; `role` present | Provenance requires the file to be locatable and typed |
| `SourceFile.checksum` matches `"algorithm:hash"` (e.g. `"sha256:…"`) | Integrity check must name its algorithm (NMDC lesson: don't bake it into the slot name) |
| Every `input_files` / `output_files` reference resolves to a declared `SourceFile` | Same defect class as dangling FKs — most common error in multi-entity datasets |
| Exactly one `role=network` file per `SimulationRun.input_files` | A run must bind unambiguously to one network variant |
| `Investigation` present with `name`; `SoftwareInfo.version` (already required) | Provenance + reproducibility |
| `dataset_type == benchmark` ⇒ `networks` non-empty AND ≥1 experiment with `labeled_sources` + ≥1 measurement collection populated | A benchmark dataset without its input ground truth is not a benchmark |

### Results-layer rules (all datasets)

| Rule | Justification |
|---|---|
| `lower_ci ≤ value ≤ upper_ci` on `FluxResult` / `PoolSizeResult` (when all three present) | Trivially checkable; catches transposed or garbled CI extraction |
| `aliases` entries match `"<tool>:<native_id>"` (e.g. `"influx_si:v5"`) | Keeps the canonical↔native mapping usable; bare strings lose provenance |
| `wssr` + `degrees_of_freedom` expected on `GoodnessOfFit` for completed fits (warn) | Fit acceptance can't be assessed without them |
| `flux_unit` expected on `FluxResult` (warn); unit mismatches across runs flagged at comparison time | Cross-tool comparison is meaningless across units |
| `replicate` ≥ 1 when present | Schema-enforced (`minimum_value: 1`) |

### Metadata-sidecar rule (ingest-time)

`Condition.organism_name`, `.strain`, `.specific_growth_rate`,
`.growth_rate_unit` are required but present in **no** native format (FluxML
`<info>` partially excepted: modeler/strain/date). For MTF / FreeFlux / INCA
ingest a metadata sidecar is **mandatory**; the ingester must fail with a
precise missing-fields list otherwise. μ may be *suggested* from measured
biomass fluxes but never silently auto-filled (PATH_FORWARD §12).
