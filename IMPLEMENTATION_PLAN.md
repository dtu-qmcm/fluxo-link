# FluxoLink — Implementation Plan

**Status:** Phases 1-3 applied (3a-3r); Phase 3s applied; 3t-0 closed and 3t-1 partly applied. This document covers Phases 3t-7.
**Last updated:** 2026-09-18 (3t-0 closed as a scope decision; method/investigation enums re-grounded; `Condition` hoisted to dataset level)

> **Read Phase 3t first if you are about to touch the schema.** The audit of
> every corpus under `fluxomics_data_converter/data/` found that (a) no dataset
> derived from MTF, FreeFlux, or INCA files can currently be made valid and (b)
> `benchmark/FluxML/EC.fml` — the reference dataset of PATH_FORWARD §8 — cannot
> be represented at all. **3t therefore precedes Phase 7**, which depends on it.
>
> Three caveats about the sections below:
> - The audit's third finding — that 3q/3r content was "silently lost" — was
>   **wrong**, and 3t-0 is closed. Those enums and `Condition` slots were
>   removed **deliberately** in `160086d` (2026-08-24), five days after the
>   audit was written. See 3t-0 for the decision and its rationale. Do not
>   restore them.
> - §3h's "no FLUXO term, left unmapped" table is **partly wrong** — terms do
>   exist for several of those fields (3t-12).
> - `SimulationRun.mfa_method` was renamed `fluxomics_method` on 2026-09-18 and
>   `MFAMethodEnum` became `FluxomicsMethodEnum`. Both names are updated
>   throughout this document, including in entries describing earlier phases;
>   `.agent/CHANGELOG.md` holds the history under the original names.

---

## Completed Work (Phases 1-2)

### Phase 1: Prefix-Doubling Fix ✓

- Changed `fluxo:` prefix from `http://purl.obolibrary.org/obo/FLUXO_` → `http://purl.obolibrary.org/obo/` in all 6 schema files
- IRIs now expand correctly (e.g., `fluxo:FLUXO_0000162` → `http://purl.obolibrary.org/obo/FLUXO_0000162`)

### Phase 2: Ontology Mappings & Bug Fixes ✓

- **Critical bug fixed:** `MetabolicNetworkModel.class_uri` `_0000057` → `_0000127`
- **5 classes got `class_uri`:** `SimulationRun`→`_0000057`, `ReactionParticipant`→`_0000185`, `MIDDataPoint`→`_0000143`, `PoolSizeResult`→`_0000062`, `GoodnessOfFit`→`_0000212`
- **6 slots got `slot_uri`:** `n_tracked_atoms`→`_0000183`, `FluxResult.value`→`_0000236`, `optimization_method`→`_0000088`, `degrees_of_freedom`→`_0000030`, `reduced_chi_square`→`_0000237`. ~~`labeling_pattern`→`_0000148`~~ **REMOVED in review pass** — `_0000148` is "isotopomer representation" (a state-space choice), wrong for a tracer's binary label string. Slot left unmapped.
- **CI mappings fixed:** `lower_ci`→`_0000262`, `upper_ci`→`_0000263` (on both `FluxResult` and `PoolSizeResult`)
- Removed `MIDDataPoint.value.slot_uri`; fixed typo "E.g.reactions" → "E.g. reactions"
- 13/13 tests pass, ruff lint passes

### Known Issues (to fix in Phase 3)

- `GoodnessOfFit.assessment` references deleted `GoodnessAssessmentEnum` — dangling
- `ReactionParticipant.role` references `ParticipantRoleEnum` — to be removed
- `MeasurementGroup` still exists — to be replaced
- `ParticipantRoleEnum` has stale `reactant`/`product` values

### Ontology Bug to Flag (fluxo repo, not schema)

- `FLUXO_0000209` (line 1802 in `fluxo-edit.owl`) has duplicate `IAO:0000115` definition ("upper confidence limit is a data item...") that belongs on `FLUXO_0000263`
- **`FLUXO_0000223` (mathematical expression) is overloaded** — used as `slot_uri` for `FluxConstraint.expression`, `PoolSizeConstraint.expression`, AND `SimulationRun.objective_function`. Acceptable as a generic term, but a more specific FLUXO term for "objective function" would improve precision. Flag for ontology review.
- **`FLUXO_0000062` (metabolite pool size) is overloaded** — used as `class_uri` for `PoolSizeResult`, `slot_uri` for `PoolSizeResult.value`, AND `slot_uri` for `PoolSizeMeasurement.value`. Same term used as both class and slot mapping. Acceptable in LinkML but indicates the ontology lacks distinct terms for "pool size as a class" vs "pool size value as a slot". Flag for ontology review.

---

## Phase 3 — Structural Restructure

### 3a. Root Container (`fluxolink.yaml`)

Add `FluxoDataset` class with `tree_root: true`:

```yaml
classes:
  FluxoDataset:
    class_uri: fluxo:FLUXO_0000002
    description: >-
      Root container aggregating all studies, networks, experiments,
      and simulation runs in a fluxomics dataset.
    tree_root: true
    attributes:
      id:
        description: Unique identifier for this dataset.
        identifier: true
        required: true
      name:
        description: Human-readable name of the dataset.
      description:
        description: Detailed description of the dataset contents.
      studies:
        description: All studies in this dataset.
        range: Study
        multivalued: true
        inlined_as_list: true
      networks:
        description: All metabolic network models in this dataset.
        range: MetabolicNetworkModel
        multivalued: true
        inlined_as_list: true
      experiments:
        description: All labeling experiments in this dataset.
        range: LabelingExperiment
        multivalued: true
        inlined_as_list: true
      simulation_runs:
        description: All simulation runs in this dataset.
        range: SimulationRun
        multivalued: true
        inlined_as_list: true
```

**Rationale:** LinkML needs a `tree_root` to serialize/deserialize complete documents. `FluxoDataset` is the file-level container; `Study` is a scientific entity (provenance record). Flat collections with FK references support multi-study files and shared networks across studies/experiments.

---

### 3b. Condition Modeling (`study.yaml` + `experiment.yaml`)

**Rename** `OrganismInfo` → `Condition`, add `class_uri: fluxo:FLUXO_0000218`:

```yaml
Condition:
  class_uri: fluxo:FLUXO_0000218
  description: >-
    Cultivation conditions for the biological system under study,
    including organism, strain, culture medium, and growth rate.
  attributes:
    id:
      description: Unique identifier for the condition record.
      identifier: true
      required: true
    name:
      description: Human-readable name for this condition.
    organism_name:
      description: Name of the organism (e.g., Escherichia coli).
      slot_uri: fluxo:FLUXO_0000181
      required: true
    strain:
      description: Strain designation (e.g., BW25113).
      slot_uri: fluxo:FLUXO_0000182
    culture_medium:
      description: Growth medium used for cultivation.
      slot_uri: fluxo:FLUXO_0000184
    specific_growth_rate:
      description: Measured specific growth rate of the organism.
      slot_uri: fluxo:FLUXO_0000084
      range: float
    growth_rate_unit:
      description: Unit for the growth rate (e.g., 1/h).
      slot_uri: fluxo:FLUXO_0000219
```

**Remove** `Study.organism` slot (biological context now per-experiment).

**Update** `Study.description` (consolidated with Phase 3l change):

> A fluxomics investigation comprising one or more isotope labeling experiments or simulation studies.

**Rationale:** Removes the old "comprising... experimental data, metabolic models, and results" language (Study is now provenance only, not a container — Phase 3b) AND removes the implication of a single method (since `study_type` moves to `SimulationRun` per Phase 3l, enabling multi-method studies).

**Add to `LabelingExperiment`:**

```yaml
study_id:
  description: Reference to the parent study.
  required: true
condition:
  description: Biological sample and cultivation context for this experiment.
  range: Condition
  inlined: true
  required: true
```

**Rationale:** A study with multiple strains/conditions needs each `LabelingExperiment` to carry its own `Condition`. Matches real 13C-MFA workflows where each labeling experiment comes from a specific biological sample.

---

### 3c. Measurement Restructure — Option C (`experiment.yaml`)

**Rename** `MeasurementGroup` → `MIDMeasurement` (scoped to MID only):

```yaml
MIDMeasurement:
  class_uri: fluxo:FLUXO_0000143
  description: >-
    A group of MID (mass isotopologue distribution) measurements for
    one metabolite fragment at a given time point.
  attributes:
    id:
      description: Unique identifier for the measurement group.
      identifier: true
      required: true
    metabolite_id:
      description: Reference to the measured metabolite in the network model.
      required: true
    atom_positions:
      description: Traced atom positions (e.g., "2,3" or "1-5").
      required: true
    analytical_method:
      description: Analytical method for this measurement.
      range: AnalyticalMethodEnum
    time_point:
      description: Measurement time point for non-stationary experiments.
      slot_uri: fluxo:FLUXO_0000056
      range: float
    scale_method:
      description: Scaling method for this measurement group.
      range: ScaleMethodEnum
    error_model_expression:
      description: Mathematical expression for the error model.
      slot_uri: fluxo:FLUXO_0000091
    dataset_id:
      description: Optional run/batch identifier (influx_si "Dataset" column).
    comment:
      description: Optional free-text comment.
    data_points:
      description: Individual MID measurement data points.
      range: MIDDataPoint
      multivalued: true
      inlined_as_list: true
```

**Add** `FluxMeasurement` (flat, scalar):

```yaml
FluxMeasurement:
  description: >-
    A measured external flux value for a single reaction.
  attributes:
    id:
      description: Unique identifier for the flux measurement.
      identifier: true
      required: true
    reaction_id:
      description: Reference to the reaction in the network model.
      required: true
    flux_type:
      description: Type of flux (net, forward, backward, exchange).
      range: FluxTypeEnum
      required: true
    value:
      description: Measured flux value.
      slot_uri: fluxo:FLUXO_0000236
      range: float
      required: true
    standard_deviation:
      description: Standard deviation of the flux measurement.
      slot_uri: fluxo:FLUXO_0000208
      range: float
      minimum_value: 0.0
    time_point:
      description: Measurement time point (for non-stationary experiments).
      slot_uri: fluxo:FLUXO_0000056
      range: float
    comment:
      description: Optional free-text comment.
```

**Add** `PoolSizeMeasurement` (flat, scalar, optional SD):

```yaml
PoolSizeMeasurement:
  description: >-
    A measured metabolite pool size for a single metabolite.
  attributes:
    id:
      description: Unique identifier for the pool size measurement.
      identifier: true
      required: true
    metabolite_id:
      description: Reference to the metabolite in the network model.
      required: true
    value:
      description: Measured pool size value.
      slot_uri: fluxo:FLUXO_0000062
      range: float
      required: true
    standard_deviation:
      description: Standard deviation of the pool size measurement.
      slot_uri: fluxo:FLUXO_0000208
      range: float
      minimum_value: 0.0
    time_point:
      description: Measurement time point (for non-stationary experiments).
      slot_uri: fluxo:FLUXO_0000056
      range: float
    comment:
      description: Optional free-text comment.
```

**Update** `LabelingExperiment`:

- Remove `analytical_method` (now on `MIDMeasurement`)
- Replace `measurement_groups` with:

```yaml
mid_measurements:
  description: MID (mass isotopologue distribution) measurements.
  range: MIDMeasurement
  multivalued: true
  inlined_as_list: true
nmr_measurements:
  description: 13C NMR isotopomer (multiplet) measurements.
  range: NMRIsotopomerMeasurement
  multivalued: true
  inlined_as_list: true
flux_measurements:
  description: Measured external flux values.
  range: FluxMeasurement
  multivalued: true
  inlined_as_list: true
pool_size_measurements:
  description: Measured metabolite pool sizes.
  range: PoolSizeMeasurement
  multivalued: true
  inlined_as_list: true
```

**Update** `MIDDataPoint`:

- Add `weight` slot (optional string — for MS/MS "2,3" notation)
- ~~Add `nmr_multiplet_type` slot~~ — **REMOVED**: NMR data is structurally different (positional vs mass-based indexing). Use `NMRIsotopomerMeasurement` instead (see below).
- **Remove `class_uri: fluxo:FLUXO_0000143` from MIDDataPoint** (added in Phase 2). That term is the *distribution* concept and belongs on `MIDMeasurement` (the group), not on an individual data point. Leave `MIDDataPoint` unmapped — consistent with Phase 3h's handling of no-term fields.

**Delete** `MeasurementTypeEnum` (type implicit in class choice). **Migrate its `meaning`s to `class_uri`s on the new measurement classes:**

- `MID → FLUXO_0000143` → `MIDMeasurement.class_uri` (already in 3c)
- `flux → FLUXO_0000124` → `FluxMeasurement.class_uri: fluxo:FLUXO_0000124` (external flux)
- `pool_size → FLUXO_0000062` → `PoolSizeMeasurement.class_uri: fluxo:FLUXO_0000062`

**Add** `NMRIsotopomerMeasurement` + `NMRIsotopomerDataPoint` (for 13C NMR-based MFA):

```yaml
NMRIsotopomerMeasurement:
  class_uri: fluxo:FLUXO_0000144
  description: >-
    A group of 13C NMR isotopomer measurements for one metabolite,
    providing positional labeling information via multiplet analysis.
  attributes:
    id:
      description: Unique identifier for the NMR measurement group.
      identifier: true
      required: true
    metabolite_id:
      description: Reference to the measured metabolite in the network model.
      required: true
    analytical_method:
      description: NMR method used (e.g., 1D 13C, 2D HSQC, 2D TOCSY).
      range: AnalyticalMethodEnum
    time_point:
      description: Measurement time point for non-stationary experiments.
      slot_uri: fluxo:FLUXO_0000056
      range: float
    comment:
      description: Optional free-text comment.
    data_points:
      description: Individual NMR isotopomer data points.
      range: NMRIsotopomerDataPoint
      multivalued: true
      inlined_as_list: true

NMRIsotopomerDataPoint:
  class_uri: fluxo:FLUXO_0000144
  description: >-
    A single 13C NMR multiplet measurement for one carbon position.
  attributes:
    atom_position:
      description: >-
        Carbon position index (1-based) in the metabolite.
      range: integer
      minimum_value: 1
      required: true
    multiplet_type:
      description: >-
        NMR multiplet type indicating the labeling state of neighboring
        carbons.
      range: NMRMultipletTypeEnum
      required: true
    value:
      description: Measured fractional abundance of this multiplet.
      range: float
      required: true
      minimum_value: 0.0
      maximum_value: 1.0
    standard_deviation:
      description: Standard deviation of the measurement.
      slot_uri: fluxo:FLUXO_0000208
      range: float
      minimum_value: 0.0
      required: true
```

**Rationale:** NMR isotopomer data is fundamentally different from MS MID data — it uses (atom_position, multiplet_type) indexing instead of (mass_shift). Mixing them on one class (via `nmr_multiplet_type` on `MIDDataPoint`) was a design flaw. Separate classes follow the Option C pattern (type-specific classes, no polymorphism). Maps to `FLUXO_0000144` (isotopomer distribution), distinct from `FLUXO_0000143` (isotopologue distribution / MID).

**Add** `NMRMultipletTypeEnum` to `enumerations.yaml` (no FLUXO term — left unmapped per Phase 3h):

```yaml
NMRMultipletTypeEnum:
  description: >-
    13C NMR multiplet types indicating the labeling state of
    neighboring carbon atoms.
  permissible_values:
    S:
      description: Singlet — carbon unlabeled, neighbors unlabeled.
    DL:
      description: Left doublet — carbon labeled, left neighbor unlabeled.
    DR:
      description: Right doublet — carbon labeled, right neighbor unlabeled.
    DD:
      description: Double doublet — carbon labeled, both neighbors unlabeled.
    T:
      description: Triplet — carbon labeled, both neighbors labeled.
```

**Add `class_uri` to `FluxMeasurement` and `PoolSizeMeasurement`** (migrated from deleted `MeasurementTypeEnum`):

```yaml
FluxMeasurement:
  class_uri: fluxo:FLUXO_0000124   # external flux
  ...

PoolSizeMeasurement:
  class_uri: fluxo:FLUXO_0000062   # metabolite pool size
  ...
```

**Rationale:** All 4 tool formats (FluxML, FreeFlux, INCA, influx_si) separate measurement types structurally — none use an in-band type enum. Metadata fields are disjoint across types (`atom_positions`/`weight`/`scale_method` are MID-only; `reaction_id` is flux-only). MID is vector data; flux/pool_size are scalars.

---

### 3d. GoodnessOfFit Cleanup (`simulation_run.yaml` + `enumerations.yaml`)

- **Remove** `GoodnessOfFit.assessment` slot (dangling reference to deleted `GoodnessAssessmentEnum`)
- Fit quality can be derived from `chi_square_p_value` by downstream tools (p > 0.05 = accepted, etc.)
- `ScaleMethodEnum` values (`auto`, `one`) remain unmapped — no FLUXO term, acceptable in LinkML

---

### 3e. ReactionParticipant Simplification (`network.yaml` + `enumerations.yaml`)

- **Remove** `role` slot from `ReactionParticipant` (redundant — role is implicit from `reactants`/`products` list membership on `NetworkReaction`)
- **Delete** `ParticipantRoleEnum` from `enumerations.yaml`

---

### 3f. FluxML Compatibility — Medium-Impact Gaps

| Gap                             | File                    | Change                                                                                                                                                                                                                                     |
| ------------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Time-varying substrate profiles | `experiment.yaml`     | Add`profile` slot on `LabeledSource` (optional string — e.g., `"0.5, 1.0, 1.5"`); add `profile_values` on `TracerIsotopomer` (optional string — textual formula like `"0.5 + 0.5 * sin(t-1.57)"`)                            |
| Initial values                  | `simulation_run.yaml` | Add`initial_values` slot on `SimulationRun` (range: `FluxSolution`, inlined, optional) — for warm-starting optimizers. **Required when `fluxomics_method` is isotope-based** (see cross-slot rule in Phase 3j); optional for FBA. |
| Simulation stop time            | `simulation_run.yaml` | Add`stop_time` slot on `SimulationRun` (optional float — for INST-MFA)                                                                                                                                                                |
| Variant ratio                   | `network.yaml`        | Add`ratio` slot on `AtomTransitionVariant` (optional float, 0.0–1.0 — likelihood of this variant for scrambling reactions)                                                                                                           |
| Pool size constraints           | `network.yaml`        | Add`PoolSizeConstraint` class (parallel to `FluxConstraint` but with `metabolite_id` instead of `reaction_id`); add `pool_size_constraints: [PoolSizeConstraint]` slot on `MetabolicNetworkModel`                              |

**`PoolSizeConstraint` design:**

```yaml
PoolSizeConstraint:
  description: >-
    A constraint on metabolite pool size values in the network model.
  attributes:
    id:
      description: Unique identifier for the constraint.
      identifier: true
      required: true
    metabolite_id:
      description: Reference to the metabolite this constraint applies to.
      required: true
    constraint_type:
      description: The type of constraint.
      range: ConstraintTypeEnum
      required: true
    lower_bound:
      description: Lower bound for the pool size value.
      range: float
    upper_bound:
      description: Upper bound for the pool size value.
      range: float
    fixed_value:
      description: Fixed value for equality constraints.
      range: float
    expression:
      description: Mathematical expression for linear combination constraints.
      slot_uri: fluxo:FLUXO_0000223
```

---

### 3g. FluxML Compatibility — Low-Impact Gaps

| Gap                  | File                | Change                                                                                                                                                                |
| -------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Flux ratios          | `experiment.yaml` | Add`FluxRatioMeasurement` class (id, expression, value, standard_deviation); add `flux_ratio_measurements: [FluxRatioMeasurement]` slot on `LabelingExperiment` |
| Pool size ratios     | `experiment.yaml` | Add`PoolSizeRatioMeasurement` class (same structure); add `pool_size_ratio_measurements` slot                                                                     |
| InChI on metabolites | `network.yaml`    | Verify`NetworkMetabolite.inchi` slot exists with `slot_uri: fluxo:FLUXO_0000239` (already present — confirm)                                                     |
| Tracer cost          | `experiment.yaml` | Add`cost` slot on `TracerIsotopomer` (optional float, `slot_uri: fluxo:FLUXO_0000081`)                                                                          |
| Input type           | `experiment.yaml` | Add`input_type` slot on `LabeledSource` (range: `IsotopicStateSpaceEnum`, optional — isotopomer/cumomer/emu)                                                   |

**`FluxRatioMeasurement` design:**

```yaml
FluxRatioMeasurement:
  description: >-
    A measured flux ratio between two or more reactions.
  attributes:
    id:
      description: Unique identifier for the flux ratio measurement.
      identifier: true
      required: true
    expression:
      description: >-
        Textual formula referencing reaction IDs (e.g.,
        "EMP2_v2/(EMP2_v2 + PPP1_v9)").
      required: true
    value:
      description: Measured ratio value.
      range: float
      required: true
    standard_deviation:
      description: Standard deviation of the ratio.
      slot_uri: fluxo:FLUXO_0000208
      range: float
      minimum_value: 0.0
    comment:
      description: Optional free-text comment.
```

**`PoolSizeRatioMeasurement`:** same structure, expression references metabolite IDs.

---

### 3h. Unmapped Fields (no FLUXO term, left unmapped)

> **⚠️ Partly wrong — corrected in 3t-12.** Terms exist for `ScaleMethodEnum` /
> `scale_method` (FLUXO_0000161 groupscale), `MIDDataPoint.weight`
> (FLUXO_0000054 tandem isotopologue distribution), `FluxRatioMeasurement`
> (FLUXO_0000029 flux ratio), and `ConfidenceIntervalMethodEnum`
> (FLUXO_0000302–0000306). And `PoolSizeConstraint` should **not** reuse
> FLUXO_0000068 — that term's label is "linear *flux* constraint".

| Field                                          | Reason                                               |
| ---------------------------------------------- | ---------------------------------------------------- |
| `ScaleMethodEnum` values (`auto`, `one`) | No FLUXO term for scaling method                     |
| `MIDDataPoint.weight` (MS/MS)                | No FLUXO term for mass shift index                   |
| `NMRIsotopomerDataPoint.multiplet_type`      | No FLUXO term for NMR multiplet types                |
| `MIDMeasurement.dataset_id`                  | No FLUXO term for measurement run identifier         |
| `comment` slots                              | No FLUXO term (could use`rdfs:comment` annotation) |
| `LabeledSource.profile`                      | No FLUXO term for time-varying profile               |
| `PoolSizeConstraint`                         | May reuse`FLUXO_0000068` or leave unmapped         |
| `FluxRatioMeasurement`                       | No dedicated FLUXO term                              |
| `PoolSizeRatioMeasurement`                   | No dedicated FLUXO term                              |

---

### 3i. Update CHANGELOG

Update `.agent/CHANGELOG.md` documenting Phase 3 changes.

---

### 3j. Validation & Reproducibility Requirements

Based on cross-format analysis of minimal core data requirements (see `VALIDATION_REQUIREMENTS.md` for full details), mark critical slots as `required: true` and add cardinality/cross-slot constraints.

**Critical required-field additions (13 slots):**

| Slot                                         | File                    | Change                                                                                                      |
| -------------------------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------- |
| `MetabolicNetworkModel.metabolites`        | `network.yaml`        | `required: true`                                                                                          |
| `MetabolicNetworkModel.reactions`          | `network.yaml`        | `required: true`                                                                                          |
| `NetworkReaction.reactants`                | `network.yaml`        | `required: true`                                                                                          |
| `NetworkReaction.products`                 | `network.yaml`        | `required: true` (except sink reactions — document this)                                                 |
| `NetworkReaction.atom_transition_variants` | `network.yaml`        | `required: true` (for tracked metabolites)                                                                |
| `TracerIsotopomer.tracer_fraction`         | `experiment.yaml`     | `required: true`                                                                                          |
| `TracerIsotopomer.isotopic_purity`         | `experiment.yaml`     | `required: true`                                                                                          |
| `MIDDataPoint.standard_deviation`          | `experiment.yaml`     | `required: true` (explicitly required in influx_si; present in all formats)                               |
| `LabelingExperiment.labeled_sources`       | `experiment.yaml`     | `required: true` (isotope-based experiments only — FBA has no experiment)                                |
| `SimulationRun.fluxomics_method` (Phase 3l)      | `simulation_run.yaml` | `required: true` (was `Study.study_type`)                                                               |
| `SimulationRun.optimization_method`        | `simulation_run.yaml` | `required: true`                                                                                          |
| `SimulationRun.initial_values` (Phase 3f)  | `simulation_run.yaml` | Conditional: required for isotope-based MFA (INCA/influx_si); optional for FBA — see cross-slot rule below |
| `SoftwareInfo.version`                     | `simulation_run.yaml` | `required: true`                                                                                          |

**Reproducibility required-field additions (5 slots):**

| Slot                                         | File                | Change             |
| -------------------------------------------- | ------------------- | ------------------ |
| `Condition.strain`                         | `study.yaml`      | `required: true` |
| `Condition.specific_growth_rate`           | `study.yaml`      | `required: true` |
| `Condition.growth_rate_unit`               | `study.yaml`      | `required: true` |
| `MIDMeasurement.atom_positions` (Phase 3c) | `experiment.yaml` | `required: true` |
| `MIDMeasurement.analytical_method`         | `experiment.yaml` | `required: true` |

**New slot — `stationary` flag (replaces `ExperimentTypeEnum`):**

Add `stationary` (boolean, required) to `LabelingExperiment`. This replaces the existing `experiment_type` slot (range `ExperimentTypeEnum`), which encoded the same concept with more verbose values.

```yaml
stationary:
  description: >-
    Whether the experiment is isotopically stationary (true) or
    non-stationary/INST (false). Determines whether time_point is required.
  range: boolean
  required: true
```

**Also remove:**

- `LabelingExperiment.experiment_type` slot (existing, currently required)
- `ExperimentTypeEnum` from `enumerations.yaml` (values `isotopic_steady_state` / `isotopic_non_stationary`)

**Rationale:** The boolean is simpler, more universal across formats (FluxML `stationary=`, INCA `sim_ss`, FreeFlux `'stationary'` arg, influx_si Time column presence), and avoids an enum with only two values. The existing `ExperimentTypeEnum` and the planned `stationary` boolean encoded the same concept — keeping both would be redundant.

**Cardinality constraints (where supported):**

| Slot                                   | Constraint                               |
| -------------------------------------- | ---------------------------------------- |
| `MetabolicNetworkModel.metabolites`  | `minimum_cardinality: 1`               |
| `MetabolicNetworkModel.reactions`    | `minimum_cardinality: 1`               |
| `NetworkReaction.reactants`          | `minimum_cardinality: 1` (except sink) |
| `LabelingExperiment.labeled_sources` | `minimum_cardinality: 1`               |

**Cross-slot constraints (LinkML `rules` — defer to Phase 5 if complex):**

| Rule                                                                                                                                      | Defer to Phase 5? |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| If`LabelingExperiment.stationary == false`, then `MIDMeasurement.time_point` required                                                 | Yes               |
| **`LabelingExperiment.stationary` must agree with `SimulationRun.fluxomics_method` (`true`↔`IST_MFA`, `false`↔`INST_MFA`)** — added 2026-08-24 per §13.16: stationarity is encoded twice, independently, and a probe asserting `stationary: true` with `fluxomics_method: INST_MFA` validates cleanly                          | Yes               |
| If`LabelingExperiment.stationary == false`, then `SimulationRun.stop_time` required                                                   | Yes               |
| If`NetworkMetabolite.n_tracked_atoms > 0`, then `NetworkReaction.atom_transition_variants` required                                   | Yes               |
| `TracerIsotopomer.tracer_fraction` sums to ≤1.0 per `LabeledSource`                                                                  | Yes               |
| If`SimulationRun.fluxomics_method` is isotope-based (IST/INST/dynamic/13C/I-MFA), then `SimulationRun.experiment_id` is required (Phase 3k) | Yes               |
| If`SimulationRun.fluxomics_method` is isotope-based, then `SimulationRun.initial_values` is required (Phase 3f/3j reconciliation)           | Yes               |

**Rationale:** See `VALIDATION_REQUIREMENTS.md` for full cross-format analysis. Key findings:

- influx_si explicitly requires `SD` column in `.miso` (line 124 of spec) — universally present across all 4 formats
- All 4 formats require atom transitions for carbon-tracked metabolites
- All 4 formats require tracer metabolite, labeling pattern, and fraction
- Stationary vs non-stationary flag is universal (FluxML `stationary=`, INCA `sim_ss`, FreeFlux `'stationary'` arg, influx_si Time column presence)
- Software version is critical for reproducibility but not enforced by any format spec — schema should enforce it

---

### 3k. FBA & Non-Isotope MFA Compatibility

**Problem:** FBA (flux balance analysis) and other stoichiometry-based MFA methods don't use isotope tracers. The current schema requires `SimulationRun.experiment_id` (line 42) and plans to require `LabelingExperiment.labeled_sources` (Phase 3j) — both fail for FBA.

**Changes:**

1. **Make `SimulationRun.experiment_id` optional** (was `required: true`):

   ```yaml
   experiment_id:
     description: >-
       Reference to the labeling experiment used. Optional for
       non-isotope methods (e.g., FBA) that don't use tracers.
   ```

   Remove `required: true` from this slot.
2. **Add `objective_function` slot to `SimulationRun`** (for FBA's maximize biomass, etc.):

   ```yaml
   objective_function:
     description: >-
       Mathematical expression for the objective function being
       optimized (e.g., "maximize biomass" for FBA). May be empty
       for isotope-based MFA where the objective is implicit
       (minimize WSSR).
     slot_uri: fluxo:FLUXO_0000223
   ```

   Optional — not required (isotope-based MFA doesn't need it).
3. **Expand `FluxomicsMethodEnum`** (currently only 3 values; add 6 missing FLUXO terms):

   ```yaml
   FluxomicsMethodEnum:
     description: >-
       Metabolic flux analysis method types from the FLUXO ontology.
     permissible_values:
       # Existing (keep)
       IST_MFA:
         description: Isotopically stationary MFA
         meaning: fluxo:FLUXO_0000043
       INST_MFA:
         description: Isotopically non-stationary MFA
         meaning: fluxo:FLUXO_0000044
       dynamic_MFA:
         description: Dynamic isotope-based MFA
         meaning: fluxo:FLUXO_0000045
       # NEW — add these
       MFA:
         description: Generic metabolic flux analysis
         meaning: fluxo:FLUXO_0000040
       I_MFA:
         description: Isotope-based metabolic flux analysis (parent of 13C-MFA, IST-MFA, INST-MFA)
         meaning: fluxo:FLUXO_0000041
       C13_MFA:
         description: 13C metabolic flux analysis
         meaning: fluxo:FLUXO_0000042
       FBA:
         description: Flux balance analysis (stoichiometry-based, no isotope)
         meaning: fluxo:FLUXO_0000039
       stoichiometry_based_MFA:
         description: Stoichiometry-based MFA (parent of FBA, constraint-based)
         meaning: fluxo:FLUXO_0000018
       constraint_based_MFA:
         description: Constraint-based MFA (FBA variant with additional constraints)
         meaning: fluxo:FLUXO_0000019
   ```

**Scenario walkthrough (your example):**

```
FluxoDataset
├── studies:
│   ├── Study1 (FBA investigation — no tracers, objective_function="maximize biomass")
│   ├── Study2 (IST-MFA — uses tracers, network A)
│   └── Study3 (INST-MFA — modified strain, different tracer, network B)
├── networks:
│   ├── NetworkA (used by Study2)
│   └── NetworkB (modified, used by Study3)
├── experiments:
│   ├── Experiment1 (IST-MFA, Condition1, labeled_sources=[1-13C glucose])
│   └── Experiment2 (INST-MFA, Condition2=modified strain, labeled_sources=[U-13C glucose])
└── simulation_runs:
    ├── Run1 (Study1, NetworkA, experiment_id=null, objective_function="max biomass", method=FBA)
    ├── Run2 (Study2, NetworkA, Experiment1, method=IST_MFA)
    └── Run3 (Study3, NetworkB, Experiment2, method=INST_MFA)
```

All three simulation runs coexist; FBA's `experiment_id` is null; `objective_function` only populated for FBA. `fluxomics_method` (relocated per 3l) distinguishes the approach per run.

---

### 3l. Move `study_type` to `SimulationRun`

**Problem:** `Study.study_type` (single `FluxomicsMethodEnum`) is too rigid — a study using multiple methods (FBA first, then 13C-MFA on the same network) requires multiple `study_type` values or fragmented studies.

**Changes:**

1. **Remove `study_type` slot from `Study`** (in `study.yaml`).
2. **Add `fluxomics_method` slot to `SimulationRun`** (in `simulation_run.yaml`):

   ```yaml
   fluxomics_method:
     description: The MFA method used in this simulation run.
     range: FluxomicsMethodEnum
     required: true
   ```

   Each run declares its own method — a study can mix FBA + IST-MFA + INST-MFA runs without splitting provenance.
3. **Update `Study.description`**: already consolidated in Phase 3b (description no longer mentions a single method; provenance only).

**Rationale:** The method is a property of the simulation, not the study. A study is an investigation; the method is how each run analyzes it. This enables multi-method studies (common in practice — FBA for initial exploration, then 13C-MFA for detailed flux resolution).

---

### 3m. Parallel Labeling Experiments (PLE)

**Problem:** `SimulationRun.experiment_id` is a singular reference, but FLUXO itself defines `FLUXO_0000050` "parallel labeling experiments" as a first-class concept — "different isotopic tracers with distinct labeling patterns or tracer mixtures are supplied to resolve overlapping metabolic routes." PLE design (2–4 tracer experiments on the same biological condition fit jointly to one shared flux solution) is now standard practice for well-resolved 13C-MFA (INCA's multi-experiment fitting, 13CFLUX2/FluxML's multi-configuration jobs). The current one-to-one design can't express this — duplicating the flux solution across separate `SimulationRun`s would be statistically wrong (throws away joint-fitting power).

**Change:** Make `SimulationRun.experiment_id` **multivalued**:

```yaml
experiment_id:
  description: >-
    Reference(s) to the labeling experiment(s) used. Singular for
    single-labeling-experiment MFA; multivalued (2+) for parallel
    labeling experiments (PLE) that are jointly fit to one shared
    flux solution.
  multivalued: true
  required: false  # still optional for FBA per Phase 3k
```

**Rationale:** A multivalued `experiment_id` with 2+ entries signals joint fitting. PLE siblings carry duplicate-but-consistent `Condition` data (per Phase 3b's per-experiment inlining). This doesn't conflict with the inlining decision — it just lets one `SimulationRun` reference multiple experiments. Maps to `FLUXO_0000050` (parallel labeling experiments) at the schema semantics level.

---

### 3n. Natural Isotope Correction & Simulated Values

**Problem 1 — Natural isotope correction:** FLUXO defines `FLUXO_0000275` "corrected isotopologue distribution" ("reflects only the labeling introduced by your isotopic tracer without isotope natural abundance") and `FLUXO_0000131` "tracer isotopologue" ("the output of the natural isotope abundance correction"). Whether an MID dataset is raw or corrected (and by which algorithm — IsoCor, skyline, in-house) changes fitted fluxes substantially. Neither `MIDMeasurement` nor `MIDDataPoint` has a slot for this.

**Change 1:** Add `natural_abundance_corrected` slot to `MIDMeasurement`:

```yaml
natural_abundance_corrected:
  description: >-
    Whether the MID values have been corrected for natural isotope
    abundance. If true, correction_algorithm should be specified.
  range: boolean
correction_algorithm:
  description: >-
    Algorithm used for natural isotope correction (e.g., "IsoCor",
    "skyline", "in-house"). Optional even if corrected (some tools
    apply correction internally without exposing the algorithm).
```

**Problem 2 — Simulated/predicted values:** `GoodnessOfFit` captures WSSR/chi-square/dof but not the model's predicted MID/flux/pool-size values. Without those, nobody can regenerate a measured-vs-fitted plot (standard in every 13C-MFA paper) or independently re-derive the WSSR.

**Change 2:** Add mirrored "simulated" slots on `FluxSolution`:

```yaml
FluxSolution:
  attributes:
    # existing: flux_results, pool_size_results
    simulated_mids:
      description: >-
        Simulated MID values predicted by the model for comparison
        against measured MIDs. Optional — present when the solver
        exposes forward-simulation output.
      range: MIDMeasurement
      multivalued: true
      inlined_as_list: true
```

(Reuses `MIDMeasurement` structure — simulated values have the same shape as measured values, just without `standard_deviation` populated.)

---

### 3o. FK Typing & Referential Integrity

**Problem:** All `_id` slots (`reaction_id`, `metabolite_id`, `study_id`, `network_model_id`, `experiment_id`) inherit `default_range: string` rather than declaring `range: NetworkReaction` / `range: NetworkMetabolophile` / etc. This is the standard LinkML idiom for identifier-based references — makes them self-documenting and lets `gen-doc` render cross-links. Currently nothing signals these are references.

**Change 1 — Type the FK slots:**

| Slot                                                   | Current range    | New range                      |
| ------------------------------------------------------ | ---------------- | ------------------------------ |
| `LabelingExperiment.study_id`                        | string (default) | `Study`                      |
| `LabelingExperiment.condition.metabolite_id` (if FK) | —               | (Condition is inlined, not FK) |
| `LabeledSource.metabolite_id`                        | string (default) | `NetworkMetabolite`          |
| `ReactionParticipant.metabolite_id`                  | string (default) | `NetworkMetabolite`          |
| `MIDMeasurement.metabolite_id`                       | string (default) | `NetworkMetabolite`          |
| `FluxMeasurement.reaction_id`                        | string (default) | `NetworkReaction`            |
| `FluxConstraint.reaction_id`                         | string (default) | `NetworkReaction`            |
| `PoolSizeConstraint.metabolite_id`                   | string (default) | `NetworkMetabolite`          |
| `PoolSizeMeasurement.metabolite_id`                  | string (default) | `NetworkMetabolite`          |
| `SimulationRun.study_id`                             | string (default) | `Study`                      |
| `SimulationRun.network_model_id`                     | string (default) | `MetabolicNetworkModel`      |
| `SimulationRun.experiment_id`                        | string (default) | `LabelingExperiment`         |
| `FluxResult.reaction_id`                             | string (default) | `NetworkReaction`            |
| `PoolSizeResult.metabolite_id`                       | string (default) | `NetworkMetabolite`          |
| `AtomTransition.reactant_metabolite_id`              | string (default) | `NetworkMetabolite`          |
| `AtomTransition.product_metabolite_id`               | string (default) | `NetworkMetabolite`          |

**Note:** In LinkML, `range: SomeClass` on a slot that holds an ID string (not an inlined object) is interpreted as "a reference to an instance of SomeClass, identified by its `identifier` slot." This is the standard pattern for FK-style references.

**Change 2 — Add referential-integrity tests to Phase 5b** (see Phase 5 update below): assert that every `_id` value in a `FluxoDataset` instance resolves to an existing object's `id` elsewhere in the same dataset.

---

### 3p. Critical Fixes from Review

This sub-phase consolidates the concrete defects identified in review that don't fit elsewhere:

**1. Wire `FluxConstraint` into `MetabolicNetworkModel`:**

`FluxConstraint` is currently defined but orphaned — `MetabolicNetworkModel` has no `flux_constraints` slot. Add:

```yaml
# On MetabolicNetworkModel:
flux_constraints:
  description: Flux constraints (bounds, equalities) applied to reactions.
  range: FluxConstraint
  multivalued: true
  inlined_as_list: true
```

**2. Reaction participant naming — keep `reactants`/`products`:**

`NetworkReaction` uses `reactants` (paired with `products`). This matches the FLUXO ontology participant roles (`FLUXO_0000167` "reactant role", `FLUXO_0000169` "product role") and the `fluxomics_data_converter` naming. (An earlier draft of this plan proposed renaming to `substrates`; that was reversed for ontology and cross-tool consistency.) `ReactionParticipant` role is reactant vs product.

**3. Add unit slots to `FluxMeasurement` and `PoolSizeMeasurement`:**

```yaml
# On FluxMeasurement:
flux_unit:
  description: Unit of the measured flux (e.g., "mmol/gDW/h").
  slot_uri: fluxo:FLUXO_0000219

# On PoolSizeMeasurement:
pool_size_unit:
  description: Unit of the measured pool size (e.g., "mmol/gDW").
  slot_uri: fluxo:FLUXO_0000222
```

**4. Resolve `FluxMeasurement.standard_deviation` contradiction:**

`VALIDATION_REQUIREMENTS.md` marks stddev required for all 4 formats; the plan's 3c left it optional. **Make it required** on `FluxMeasurement` and `PoolSizeMeasurement` (consistent with `MIDDataPoint.standard_deviation` being required per 3j). FreeFlux pool sizes are the only exception — handle via cross-slot rule allowing `pool_size_unit` absent → SD optional, or accept that FreeFlux's missing SD is a converter-level gap (converter emits SD=0 or NaN).

**5. Add "at least one measurement" constraint:**

Add to Phase 5 cross-slot rules (LinkML can't express "at least one of N slots" with plain cardinality): a `LabelingExperiment` must have at least one of `mid_measurements` / `nmr_measurements` / `flux_measurements` / `pool_size_measurements` populated (unless `fluxomics_method` is FBA, which has no experiment).

**6. FBA biological context:**

FBA runs have no `LabelingExperiment` (per 3k), so no `Condition` — but FBA needs exchange bounds defined by the growth medium. **Add optional `condition` slot to `SimulationRun`** (range: `Condition`, inlined, optional) so FBA runs can carry biological context without an experiment:

```yaml
# On SimulationRun:
condition:
  description: >-
    Biological context for this run. Required for FBA (no experiment);
    optional for isotope-based MFA (condition is on the experiment).
  range: Condition
  inlined: true
```

---

### 3q. Expanded Metadata & Validation Rules

**Optimization metadata** (Part 4):

Add to `SimulationRun`:

```yaml
multistart_count:
  description: >-
    Number of optimization restarts (for non-convex problems).
  range: integer
  minimum_value: 1
random_seed:
  description: Random seed for reproducibility of stochastic optimizers.
  range: integer
convergence_tolerance:
  description: Solver convergence tolerance (e.g., 1e-6).
  range: float
```

**CI method** (Part 4):

Add to `FluxResult` and `PoolSizeResult`:

```yaml
confidence_interval_method:
  description: >-
    Method used to compute confidence intervals (e.g., "profile_likelihood",
    "parameter_continuation", "bootstrap", "grid_search").
  range: ConfidenceIntervalMethodEnum  # NEW enum
```

Add `ConfidenceIntervalMethodEnum` to `enumerations.yaml` (profile_likelihood/parameter_continuation/bootstrap/grid_search/other). No FLUXO terms.

**NMR analytical method sub-types** (Part 4):

`NMRIsotopomerMeasurement.analytical_method` is typed against `AnalyticalMethodEnum` (one generic NMR value), but its description promises "1D 13C, 2D HSQC, 2D TOCSY". Expand `AnalyticalMethodEnum`:

```yaml
# Add to AnalyticalMethodEnum:
NMR_1D_13C:
  description: 1D 13C NMR spectroscopy
NMR_2D_HSQC:
  description: 2D 1H-13C HSQC NMR
NMR_2D_TOCSY:
  description: 2D TOCSY NMR
```

(Keep existing single `NMR` value for backward compat, or deprecate it.)

**New cross-slot validation rules** (Part 3):

| Rule                                                                                                                   | Justification                                                                                     |
| ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `TracerIsotopomer.labeling_pattern` length must equal referenced metabolite's `n_tracked_atoms`                    | Silent curation error otherwise                                                                   |
| `AtomTransition.reactant_atom_index` / `product_atom_index` must be < `n_tracked_atoms` of respective metabolite | Out-of-bounds check                                                                               |
| `MIDDataPoint.isotopologue_index` must not exceed metabolite's `n_tracked_atoms`                                   | Can't have m+7 for a 6-carbon metabolite                                                          |
| Sum of`MIDDataPoint.value` across one `MIDMeasurement.data_points` should be ≈1.0                                 | Standard MID sanity check                                                                         |
| If`reaction_type` is `sink`/`demand`/`exchange`, then `products` is optional (not required)                  | Resolves the "products required except sink" carve-out — extends to all one-sided reaction types |

All deferred to Phase 5 (LinkML `rules:`).

**Dataset versioning** (Part 4):

Add to `FluxoDataset`:

```yaml
schema_version:
  description: Version of the FLUXO schema this dataset conforms to.
creation_date:
  description: Date the dataset was created.
  range: date
last_modified:
  description: Date the dataset was last modified.
  range: date
fluxo_ontology_version:
  description: >-
    FLUXO ontology release version used for term mappings (e.g.,
    "2026-04-08"). Pins the ontology version for traceability.
```

---

### 3r. Enum Coverage & Scope Expansion

**Problem:** `MFASoftwareEnum`, `InputFormatEnum`, and other closed enums have no "other + free text" escape hatch. For a schema curating diverse published datasets (not just the user's own lab), this will bite quickly — many studies use one-off institutional scripts that will never get a FLUXO term. Also, Phase 3k added FBA support but `MFASoftwareEnum` wasn't expanded for FBA solvers (COBRApy, cameo).

**Changes:**

1. **Add `other` value + `other_specify` pattern to relevant enums:**

For `MFASoftwareEnum`, `InputFormatEnum`, `AnalyticalMethodEnum` — add an `other` permissible value and document that when `other` is selected, a separate free-text slot must be populated. (LinkML doesn't have a built-in "other specify" mechanism, so this is a convention: `software_name: other` + `software_name_other: "MyCustomScript"`.)

3. **Broaden `fluxolink.yaml` description:**

Current: "A LinkML data model for 13C-MFA simulation studies... from tools such as freeflux, 13CFLUX2, influx_si, and INCA."

Updated:

> A LinkML data model for metabolic flux analysis (MFA) investigations, including isotope-based MFA (13C-MFA, IST-MFA, INST-MFA) and stoichiometry-based methods (FBA). Grounded in the FLUXO ontology. Supports data from tools such as freeflux, 13CFLUX2, influx_si, INCA, COBRApy, and others.

---

### Phase 3 Verification

```bash
uv run ruff check src tests
uv run pytest
```

May need to update `tests/test_schema.py` for renamed/added classes. Manual `SchemaView` smoke check:

```python
from linkml_runtime import SchemaView
sv = SchemaView("src/fluxolink/schema/fluxolink.yaml")
assert sv.get_class("FluxoDataset").tree_root is True
assert sv.get_class("Condition") is not None
assert sv.get_class("MIDMeasurement") is not None
assert sv.get_class("FluxMeasurement") is not None
assert sv.get_class("PoolSizeMeasurement") is not None
```

---

## Phase 4 — Project Structure & Generation Pipeline

### 4a. Add `justfile` at repo root

```justfile
# justfile
setup:
    uv sync --extra dev

gen:
    gen-project -d project/ src/fluxolink/schema/fluxolink.yaml

gen-pydantic:
    gen-pydantic src/fluxolink/schema/fluxolink.yaml > src/fluxolink/datamodel/fluxolink.py

test:
    uv run pytest

lint:
    uv run ruff check src tests
    uv run ruff format --check src tests
    uv run mypy src

schema-lint:
    linkml lint src/fluxolink/schema/fluxolink.yaml

testdoc:
    gen-doc -d docs/ src/fluxolink/schema/fluxolink.yaml
```

**Prerequisite:** install `just` (`uv tool install rust-just`).

### 4b. Add `config.yaml` (gen-project config)

```yaml
# config.yaml — generator arguments for gen-project
generator_args:
  pydantic:
    output: src/fluxolink/datamodel/fluxolink.py
  jsonschema:
    output: project/jsonschema/
  owl:
    output: project/owl/
  erdiagram:
    output: project/erdiagram/
  doc:
    output: docs/
```

### 4c. Create `examples/` directory

- `examples/valid/minimal_dataset.yaml` — hand-written `FluxoDataset` with one study, one network, one experiment (with `Condition`), one `SimulationRun`. Doubles as test fixture.
- Optionally `examples/invalid/` for negative validation tests.

### 4d. Add `.yamllint.yaml` + `.editorconfig`

YAML formatting rules and editor consistency (canonical LinkML template includes these).

### 4e. Run generation

- `just gen-pydantic` → populate `src/fluxolink/datamodel/fluxolink.py`
- Verify it imports cleanly
- Optionally `just gen` for full project artifacts (jsonschema, owl, erdiagram, docs)

### 4f. Keep `datamodel/` at `src/fluxolink/datamodel/`

Importable as `from fluxolink.datamodel import ...`. Update `.gitignore` if needed.

### 4g. `.agent/` Markdown conversion ✓ (already done)

The `.agent/` HTML files were converted to Markdown in a prior step:

- `.agent/AGENT.html` → `.agent/AGENTS.md` ✓
- `.agent/CHANGELOG.html` → `.agent/CHANGELOG.md` ✓

Only remaining action in this phase: update `README.md` with `just` targets and document the generation workflow.

### Phase 4 Verification

```bash
just test          # gen + pytest
just gen-pydantic  # produces valid Python module
just lint          # passes
```

---

## Phase 5 — Test Suite Depth

### 5a. Add `tests/conftest.py`

Session-scoped `SchemaView` fixture:

```python
import pytest
from linkml_runtime import SchemaView

@pytest.fixture(scope="session")
def schema_view():
    return SchemaView("src/fluxolink/schema/fluxolink.yaml")
```

### 5b. Add `SchemaView`-based tests

- Every class resolves
- Every enum resolves
- Every `range` reference is valid
- Every `class_uri`/`slot_uri`/`meaning` expands to a non-doubled IRI
- `tree_root` exists on `FluxoDataset`
- No dangling enum references (catch the `GoodnessAssessmentEnum` class of bug)
- **No two classes share the same `class_uri`** (catches the `FLUXO_0000143` collision between `MIDMeasurement` and `MIDDataPoint`)
- **No `slot_uri` is reused as a `class_uri` for a different concept** (catches ontology term overloading)

### 5c. Add example-data validation tests

Use `linkml.validator` against `examples/valid/minimal_dataset.yaml`.

### 5d. Add **negative tests** (NEW — Part 6 finding)

For every constraint added in Phase 3j/3p/3q, write a test that invalid data is correctly rejected:

- `tests/invalid/missing_required_field/` — drop a required field, assert validation fails
- `tests/invalid/empty_collection/` — network with no metabolites, assert fails
- `tests/invalid/dangling_fk/` — `reaction_id` references non-existent reaction, assert fails (requires 5f)
- `tests/invalid/duplicate_class_uri/` — (schema-level, not data-level)
- `tests/invalid/broken_pattern/` — `labeling_pattern` with wrong length, assert fails (requires cross-slot rules)

### 5e. Add **referential-integrity tests** (NEW — Part 2 finding)

Custom validator/test that loads a `FluxoDataset` instance and asserts:

- Every `study_id` resolves to an existing `Study.id` in `dataset.studies`
- Every `network_model_id` resolves to an existing `MetabolicNetworkModel.id`
- Every `experiment_id` resolves to an existing `LabelingExperiment.id`
- Every `metabolite_id` (on participants, measurements, constraints, results) resolves to an existing `NetworkMetabolite.id`
- Every `reaction_id` (on measurements, constraints, results) resolves to an existing `NetworkReaction.id`

This is the most common defect class in multi-entity dataset files — separate from schema-level `range` validation (5b).

### 5f. Apply markers

Tag tests with `@pytest.mark.schema`/`unit`/`integration` (currently all unmarked despite markers being registered).

### 5g. Round-trip serialization test

YAML → Pydantic object → YAML (verify no data loss).

### 5h. Add **real published model example** (NEW — Part 6 finding)

Beyond the minimal hand-written fixture (4c), add `examples/valid/ecoli_core_dataset.yaml` converted from a real published 13C-MFA model (e.g., E. coli core model used in many MFA papers). Stress-tests:

- Symmetric-metabolite `AtomTransitionVariant`s (real scrambling reactions)
- Real biomass stoichiometry (multi-component biomass reaction)
- Multi-tracer mixtures (e.g., 77% [1-13C] + 20.5% [U-13C] + 2.5% [12C] glucose)
- The 3-method scenario from Phase 3k (FBA + IST-MFA + INST-MFA in one dataset) — better validation fixture than the minimal example

### 5i. Tier-1 & results-layer validation tests (NEW — PATH_FORWARD §11-§12)

The Phase 3j/3p/3q rules cover Tier-2 (input content). Add tests for the
Tier-1 (file provenance) and results-layer rules:

- `SourceFile.checksum` matches `"algorithm:hash"` pattern; `role`/`format` present; every `input_files`/`output_files` reference resolves to a declared `SourceFile`
- Exactly one `role=network` file per `SimulationRun.input_files`
- `dataset_type == benchmark` ⇒ `networks` non-empty AND ≥1 experiment with `labeled_sources` + ≥1 measurement collection populated (negative test: benchmark dataset without networks fails)
- CI ordering: `lower_ci ≤ value ≤ upper_ci` on `FluxResult`/`PoolSizeResult` (when all three present)
- Alias format: every `aliases` entry matches `"<tool>:<native_id>"`
- Recommended-present warnings: `flux_unit`, `wssr` + `degrees_of_freedom` on completed runs

### Phase 5 Verification

```bash
uv run pytest  # passes with new tests
```

---

## Phase 6 — Project Hygiene (deferred)

### 6a. `docs/` + `mkdocs.yml`

Documentation generation via `gen-doc`.

### 6b. `.github/workflows/`

CI: test + lint + docs deploy on push.

### 6c. `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`

Standard community files.

### 6d. Public API exports

`src/fluxolink/__init__.py` — expose `SchemaView`, schema path constant, generated classes.

---

## Phase 3s — PATH_FORWARD Alignment (Schema Additions)

Post-Phase-3 additions from the cross-tool benchmarking analysis (see
`PATH_FORWARD.md` §3–§6, §11–§12). Phase 3 built the full input-content model
(**Tier 2**); this sub-phase adds the file-provenance layer and comparison
keys (**Tier 1**) and formalizes the two-tier semantics:

- **Tier 1 — required for all datasets:** `FluxoDataset`, `Investigation`,
  `Condition`, `SourceFile` provenance, `SimulationRun` + results.
- **Tier 2 — input truth (required for benchmark/truth-carrying datasets;
  optional for results-catalog datasets):** network + experiment detail
  classes from Phase 3. Present ⇒ the VALIDATION_REQUIREMENTS ruleset applies.

### 3s-1. `SourceFile` + `FileRoleEnum` (Tier-1 provenance)

Add to `experiment.yaml` (or a new `files.yaml` module):

```yaml
SourceFile:
  description: >-
    Reference to a native MFA file (FluxML, MTF, FTBL, .mat, etc.).
    The schema references the file; Tier-2 classes optionally carry
    its parsed content.
  attributes:
    id:        { identifier: true, required: true }
    path:      { required: true }                    # relative path or URI
    format:    { range: InputFormatEnum, required: true }
    format_other:                                    # free text when format=other
    role:      { range: FileRoleEnum, required: true }
    checksum:
      description: '"algorithm:hash" (e.g., "sha256:abc123...")'
      pattern: "^[a-z0-9]+:[0-9a-f]+$"
    media_type:
    file_size_bytes: { range: integer, minimum_value: 0 }
    description:

FileRoleEnum:   # in enumerations.yaml
  permissible_values: [network, measurements, tracer, constraints,
                       simulation, results, configuration, other]
```

### 3s-2. File slots on dataset and runs

- `FluxoDataset.source_files: [SourceFile]` (multivalued, inlined_as_list)
- `SimulationRun.input_files: [SourceFile]` (multivalued, inlined_as_list)
- `SimulationRun.output_files: [SourceFile]` (multivalued, inlined_as_list) —
  provenance for extracted results; NMDC `has_output` pattern, map output edge
  to `prov:wasGeneratedBy`.

### 3s-3. Comparison keys

- `NetworkReaction.aliases`, `NetworkMetabolite.aliases`: multivalued string,
  **tool-namespaced** (`"influx_si:v5"`, `"freeflux:R1"`). The canonical↔native
  ID mapping is new information present in no native file — it lives in the
  dataset, once per entity (PATH_FORWARD §6).
- `SimulationRun.isotopic_state_space` (range `IsotopicStateSpaceEnum`):
  **re-add** — benchmarking-fairness parameter, like `optimization_method`
  (tools differ: 13CFLUX2 cumomer, INCA cumomer/EMU, miemu EMU).

### 3s-4. Measurement fidelity

- `replicate` (optional integer, `minimum_value: 1`) on `MIDMeasurement`,
  `FluxMeasurement`, `PoolSizeMeasurement` — miemu carries replicates;
  published datasets report them.
- `LabelingExperiment.tracer_summary` (optional string) — human-readable
  tracer description for catalog browsing; machine-readable spec stays in
  `labeled_sources` / native files.

### 3s-5. `dataset_type` — two-tier enforcement mechanism

Add optional `FluxoDataset.dataset_type` (new enum `DatasetTypeEnum`:
`benchmark` | `catalog`). Phase-5 rule: `dataset_type == benchmark` ⇒
`networks` non-empty AND ≥1 experiment with `labeled_sources` and ≥1
measurement collection populated. Absent ⇒ Tier 2 optional (catalog dataset).

---

## Phase 3t — Corpus Compatibility (from PATH_FORWARD §13)

Derived from the 2026-08-19 audit of every corpus and specification under
`fluxomics_data_converter/data/` (five formats, the FluxML XSD, three
solver-output round-trips, the converter's internal model, and the FLUXO
ontology). See `PATH_FORWARD.md` §13 for the evidence behind each item.

**Why this phase blocks others.** Two results reorder the roadmap:

1. **No dataset derived from MTF, FreeFlux, or INCA files can currently be made
   valid** — the required-field set is calibrated to FluxML alone (§13.1).
2. **`benchmark/FluxML/EC.fml` cannot be represented at all** — one network with
   four `<configuration>` blocks has no shape in the schema (§13.4).

Phase 7f ("author EC ground truth as a Tier-2-complete `FluxoDataset`") and
PATH_FORWARD §11 workflow step 1 both depend on 3t-1 … 3t-4. **3t moves ahead of
Phase 7 in the execution order.**

Sub-phases are ordered by blocking severity. 3t-0 first: it is a regression, not
a design change.

---

### 3t-0. ✅ CLOSED — not a regression, a scope decision (2026-09-18)

> **The audit was wrong about this one.** PATH_FORWARD §13.12 and the original
> version of this section claimed 3q/3r content had been "silently lost from
> the working tree". It had not. Every item was removed **deliberately** in
> commit `160086d` (2026-08-24) — five days *after* the audit was written on
> 2026-08-19, when `HEAD` was still `17487dc` and did contain them. The working
> tree matches `HEAD` exactly. **Do not restore these.**

Decisions recorded, with the owner's rationale:

| Removed | Rationale |
|---|---|
| `AerationEnum`, `CultivationModeEnum`, and `Condition.aeration` / `.temperature` / `.ph` / `.cultivation_mode` / `.genotype` | Out of scope — cultivation-process detail, not fluxomics. |
| `AnalyticalMethodEnum`: `NMR_1D_13C`, `NMR_2D_HSQC`, `NMR_2D_TOCSY` | The NMR attribute set is unsettled; the sub-types were removed to avoid committing to a shape that may change. Generic `NMR` remains, as do `NMRIsotopomerMeasurement`, `NMRIsotopomerDataPoint` and `NMRMultipletTypeEnum`. |
| `MFASoftwareEnum`: `COBRApy`, `cameo` | Not MFA software. |
| `FluxomicsMethodEnum`: `MFA` (FLUXO_0000040) | **Correct for a reason nobody wrote down.** FLUXO:0000040 is `is_a` FLUXO:0000162 *fluxomics investigation*, not a method — see the enum rework below. |

**Enum rework applied 2026-09-18.** The removals above exposed that
`FluxomicsMethodEnum` (then `MFAMethodEnum`) had no membership rule, so values
were being added and dropped by feel. It is now defined as *exactly the
`FLUXO:0000021` ("fluxomics method") subtree* — nine values, each a verified
descendant:

| Value | Term | Value | Term |
|---|---|---|---|
| `I_MFA` | 0000041 | `kinetic_flux_profiling` | 0000295 |
| `C13_MFA` | 0000042 | `stoichiometry_based` | 0000018 |
| `IST_MFA` | 0000043 | `constraint_based` | 0000019 |
| `INST_MFA` | 0000044 | `kinetic_modeling` | 0000294 |
| `dynamic_MFA` | 0000045 | | |

Two consequences:

- `C13_MFA` (FLUXO_0000042) was **restored** — it is a true subclass of
  FLUXO:0000041, so its removal in `160086d` was collateral, not intended.
- `FBA → FLUXO_0000039` was a **category error** and is gone. FLUXO:0000039
  (flux balance analysis) and FLUXO:0000040 (metabolic flux analysis) are both
  `is_a` *fluxomics investigation*. They now live in the new
  `InvestigationTypeEnum` on `Investigation.investigation_type`. A run's method
  is the plan it realises (`FLUXO:0000021` `is_a` IAO:0000104 plan
  specification); an investigation is the executed process
  (`FLUXO:0000162` `is_a` COB:0000035). One investigation may realise several
  methods — which is precisely the cross-tool benchmark case — so the method
  stays on `SimulationRun`, not on `Investigation`.

`SimulationRun.mfa_method` → `fluxomics_method` accordingly: the enum now
carries stoichiometry-based, constraint-based and kinetic-modeling values, for
which "MFA" is simply wrong.

**Remaining self-contradiction fixed:**
`NMRIsotopomerMeasurement.analytical_method`'s description named the three
deleted NMR sub-types; it now points at generic `NMR` and states why.

**Guard added:** `TestOntologyScopedEnums` in `tests/test_schema.py` pins both
ontology-scoped enums to their exact value→term mapping and asserts that
FLUXO:0000039/0000040 never reappear as methods. This is the enum-completeness
test the original 3t-0 asked for, scoped to the enums where membership is an
ontology fact rather than a judgement call.

> **Still open from this section:** `VALIDATION_REQUIREMENTS.md` §3 references a
> `fluxomics_method` value `13C`. The correct value is `C13_MFA`. Fold into the
> 3t-13 rewrite.

---

### 3t-1. Tier the required-field set (unblocks MTF / FreeFlux / INCA ingest)

> **◐ PARTLY DONE — 2026-08-24.** The blocking half is implemented and tested;
> the field-level demotions below are not, and one of them turned out to be
> undoable the way this section assumed.
>
> **Landed:**
> - `SimulationRun.network_model_id`: `required` → `recommended`
>   (`simulation_run.yaml`).
> - `FluxoDataset` gains a `rules:` block,
>   `benchmark_tier_requires_input_ground_truth`: `dataset_type == benchmark`
>   ⇒ `networks` and `experiments` required (`fluxolink.yaml`).
> - Placeholder networks **deleted** from all four catalog fixtures.
> - `examples/invalid/benchmark_tier_missing_inputs.yaml` + two tests in
>   `tests/test_examples.py`. 26 tests pass; `check_runnable.py` still reports
>   exactly 27 unresolvable items, i.e. no runnability regression.
>
> **Verified enabling fact:** LinkML `rules` are not merely documentation — they
> compile to JSON Schema `if`/`then` and `linkml-validate` enforces them. The
> whole gated-strictness strategy depends on this and it holds.
>
> **Correction to the plan below:** the line "Phase-5 rule to add:
> `dataset_type == benchmark` ⇒ all of the above present" **is not
> implementable as a LinkML rule.** `slot_conditions` cannot nest, so a rule on
> `FluxoDataset` cannot re-impose a requirement on `Condition.strain` or
> `MIDDataPoint.standard_deviation`; and a rule on `Condition` cannot see
> `dataset_type`, which lives on the root. Field-level tier strictness has to
> be an **external validator** — the `fluxo validate --benchmark` gate already
> planned in Phase 7 — or else the tier field must be duplicated onto every
> nested class, which is not worth it. Update Phase 7d/7e accordingly: the
> gate is Python, not schema.
>
> **Deliberately not done:** every `required` → `recommended` row in the table
> below. Each one is a minimum-information judgement, not housekeeping — e.g.
> `Condition.specific_growth_rate` is required today and supplied by **zero**
> of the four formats, so demoting it is a claim about what a fluxomics record
> may omit. That decision belongs with the MI work, not with a schema fix.

Demote to `recommended` and re-impose the strict set as a Phase-5 rule gated on
`FluxoDataset.dataset_type == benchmark`. `DatasetTypeEnum` already exists (3s-5)
and is currently unused for this.

| Slot | File | Change |
|---|---|---|
| `Condition.strain`, `.specific_growth_rate`, `.growth_rate_unit` | `investigation.yaml` | `required` → `recommended` |
| `Condition.organism_name` | `investigation.yaml` | `required` → `recommended` |
| `LabelingExperiment.condition` | `experiment.yaml` | `required` → `recommended` |
| `TracerIsotopomer.isotopic_purity`, `.tracer_fraction` | `experiment.yaml` | `required` → `recommended` |
| `MIDMeasurement.analytical_method`, `.atom_positions` | `experiment.yaml` | `required` → `recommended` |
| `MIDDataPoint.value`, `.standard_deviation` | `experiment.yaml` | `required` → `recommended` |
| `FluxMeasurement.standard_deviation`, `PoolSizeMeasurement.standard_deviation` | `experiment.yaml` | `required` → `recommended` |
| `SimulationRun.optimization_method` | `simulation_run.yaml` | `required` → `recommended` |
| `SoftwareInfo.version` | `simulation_run.yaml` | `required` → `recommended` |
| `MetabolicNetworkModel.metabolites` | `network.yaml` | keep the slot; drop `required` + `minimum_cardinality: 1` (INCA derives metabolites from reaction strings) |
| `SimulationRun.fluxomics_method`, `.investigation_id`; `LabelingExperiment.investigation_id` | `simulation_run.yaml`, `experiment.yaml` | `required` → `recommended` |

Phase-5 rule to add: `dataset_type == benchmark` ⇒ all of the above present.

Consequence for Phase 7d/7e: `fluxo ingest` succeeds for a catalog dataset with
no `--meta` sidecar; the sidecar is required only under `--benchmark`, and
`fluxo validate --benchmark` is the gate.

---

### 3t-2. Fix outright defects

| Fix | File |
|---|---|
| `NetworkReaction.aliases`, `NetworkMetabolite.aliases` → add **`multivalued: true`** (they are single-valued today — a plain bug against the plural name, the two-example description, and 3s-3's "once per entity" intent) | `network.yaml` |
| Make atom indices **1-based** throughout, matching all five formats and the converter's `AtomAddress`. `AtomTransition.reactant_atom_index`/`.product_atom_index` are documented 0-based while `NMRIsotopomerDataPoint.atom_position` is 1-based — an off-by-one inside one schema | `network.yaml` |
| `MIDDataPoint.value` → drop `maximum_value: 1.0` and allow small negatives (or gate the range on `scale_type`). Rejects real data on three counts: influx_si `.miso.sim` / `toy_calc.miso` negatives, 22 `e-0` literals in `ecoli_model_level_2.fml`, and unscaled `scale="auto"` groups | `experiment.yaml` |
| `SourceFile.role` → `multivalued: true` (or add a `bundle` value): one `.fml` is network + constraints + tracer + measurements + simulation at once | `experiment.yaml`, `enumerations.yaml` |
| `FileRoleEnum` → add a `role_other` companion slot, matching the `*_other` convention | `experiment.yaml`, `enumerations.yaml` |
| `SimulationRun.input_files`/`.output_files` → make them **references** into `FluxoDataset.source_files` rather than `inlined_as_list`, so one physical file is not duplicated with divergent checksums | `simulation_run.yaml` |
| `PoolSizeConstraint` → remove `class_uri: fluxo:FLUXO_0000068` (that term is "**linear flux** constraint"); leave unmapped pending an ontology request | `network.yaml` |
| `IsotopicStateSpaceEnum` → add `auto` (the `<simulation>@method` default; the value in 14 of 15 real `<simulation>` elements) | `enumerations.yaml` |
| Split simulated from measured MIDs: give `FluxSolution.simulated_mids` a dedicated class (`SimulatedMID`, `class_uri: fluxo:FLUXO_0000090` "simulated isotopic measurement") with no SD, analytical method, or atom-positions requirement. Today the slot is **unpopulatable** — its range requires all three while its own description says SD is "left unpopulated" | `experiment.yaml`, `simulation_run.yaml` |

---

### 3t-3. Constraints: permit linear combinations and record the domain

`FluxConstraint.reaction_id` is required + single-valued, which **forbids** the
constraints FluxML `<textual>` and influx_si `.cnstr` routinely contain
(`0.488*R67=bmAla` ×31 in `EC.fml`; `v2<=v1`; `fum___1+fum___2<=100`;
`bmALA - 0.488*v67 == 0` ×31 in `EC.cnstr`).

1. `FluxConstraint.reaction_id` / `PoolSizeConstraint.metabolite_id` →
   optional (or multivalued as a participating-entity list), so `expression` can
   stand alone.
2. Add `constraint_domain` (new `ConstraintDomainEnum`: `net` / `xch` / `psize` /
   `metab`). This axis is **orthogonal** to `ConstraintTypeEnum`'s relational
   form. Without it, `EC.cnstr`'s NET- and XCH-scoped constraints with identical
   formula, operator and value collapse into indistinguishable instances — three
   such collisions exist in one file.
3. Add an operator slot (`==` / `>=` / `<=`), since `inequality` carries no
   direction.
4. Allow an expression-valued right-hand side (all bound slots are `float`
   today), and add a notation flag for MathML vs textual (the converter's
   `is_mathml`).
5. Add `is_auto_generated` (+ `generated_by`, `generator_version`,
   `generation_date` on `SourceFile`): influx_si's `.cnstr.def` files are
   `txt2ftbl`-derived defaults, indistinguishable from user-authored `.cnstr`
   today, and every `.def` preamble carries all three values.

Note that a constraint may legitimately name entities absent from the network —
`toy.mflux` measures `BIOMASS_YIELD`, a free variable that is not a reaction in
`toy.netw`. Referential-integrity checks must permit this.

---

### 3t-4. The `Configuration` concept (unblocks `EC.fml` and Phase 7f)

`EC.fml` = 1 `<reactionnetwork>` + 1 global `<constraints>` + **4
`<configuration>`** (`a_INST`, `b_INST`, `a_STAT`, `b_STAT`), differing in
stationarity, group count (33/1/33/1), netflux id sets, data blocks, and
pool-size variables (56 each for INST, 0 for STAT). `Syn.fml` has 3
configurations each with its **own** `<constraints>` carrying *different* bounds.
`<configuration>@name` is XSD-unique — it is the identity.

1. Add a `Configuration` concept: either a class between `MetabolicNetworkModel`
   and `LabelingExperiment`, or a configuration key plus per-configuration
   containers. It must carry `name` (identifier), `stationary`, `time`,
   `comment`, its own constraints, and its own variable specification.
2. Allow `flux_constraints` / `pool_size_constraints` at configuration / run /
   experiment scope, keeping the network-level slots as the shared default.
   `<constraints>` is legal at both levels in FluxML and both occur in 5 of 11
   real files; influx_si, INCA and the converter all scope them per run too.
3. Add `LabelingExperiment.network_model_id` — its measurement foreign keys
   currently don't say which network they resolve against, so referential
   integrity is undecidable in a multi-network dataset.
4. Add `SourceFile.experiment_id` (or a `SourceFileSet`): benchmark
   file→experiment attribution is carried only by filename convention
   (`_a`/`_b`, `_stat`/`_inst`), and FreeFlux encodes stationarity *solely* in
   which filename was read.

---

### 3t-5. Variable specification: free / dependent / constrained

The concept is absent from the schema **and** from the ontology (a new-term
request). It is influx_si's headline feature and FluxML's
`<simulation><variables>` block.

1. New class (e.g. `VariableSpecification`), one row per variable:
   `name` (reaction or metabolite), `kind` (new `VariableKindEnum`:
   `NET`/`XCH`/`METAB`), `type` (new `VariableTypeEnum`: `free`/`constrained`/
   `dependent`), `value`, `lower_bound`, `upper_bound`, `increment`,
   `ed_weight`, `is_estimated`.
2. **Stop using `FluxSolution` for `SimulationRun.initial_values.`** `FluxResult`
   carries `lower_ci`/`upper_ci`/`confidence_interval_method` — meaningless for a
   starting point — and lacks `lo`/`hi`/`inc`/`edweight`, which is what the
   formats store. Per-variable *bounds* are currently written into
   *confidence-interval* slots. `FluxResult.value` is also `required`, so an
   input `.tvar` with ~90 blank dependent rows cannot be loaded.
3. Store the **input** partition and the **output** partition separately, and add
   `structural_identifiability` to `FluxResult`/`PoolSizeResult` (`.tvar.sim`
   `Struct_identif`).

**Benchmark-fairness note for Phase 7b.** The three `simple_model` round-trips
fit the same model to the same data, agree on every fitted value and SD, and
still partition differently (`MTF_from_mtf`/`MTF_from_freeflux`: `R1/R2/R3`
free; `MTF_from_fml`: `R3/E_out/F_out` free). The partition is a choice of basis,
not a property of the solution — the equivalence diff must normalise it away
rather than compare it.

---

### 3t-6. Results layer: residuals, statistics, and run provenance

1. New `MeasurementFitResult` class on `FluxSolution`: measurement reference,
   measured value, simulated value, SD, `residual`, `weighted_residual`,
   `p_value`. `Residual` + `Pvalue` appear on **three** influx_si output file
   types and have no slot anywhere.
2. Add `FluxSolution.simulated_fluxes` and `.simulated_pool_sizes` to parallel
   `simulated_mids` (`.mflux.sim` and `.mmet.sim` have no home), plus a channel
   for simulated NMR / cumomer rows (influx_si's `LAB_*` / `PEAK_*`).
3. Add fitted **measurement scale factors** as results. `.pres.csv` reports them
   (`1:mass;F;111;108 = 1.0000000002`) and they count toward
   `number_of_parameters`; FluxML `scale="auto"` means "estimate a scale factor"
   and the estimate has nowhere to go.
4. `GoodnessOfFit` → add `sum_squared_residuals` (unweighted),
   `number_of_measurements`, `number_of_parameters`, and a verdict slot. Document
   on `chi_square_p_value` that influx_si reports the **lower** tail
   (`pchisq(chi2, df)`, failing when `p > 0.95`) — the opposite of the
   conventional convention, so an unlabelled import inverts every verdict.
5. Add `confidence_level` to `FluxResult`/`PoolSizeResult` (FreeFlux uses 0.95
   for CIs, 0.999 for its χ² test).
6. Add run provenance to `SimulationRun`: `start_time`, `end_time`,
   `runtime_seconds`, `converged`/solver status, `iteration_count`,
   `command_line`. influx_si's `.log` carries the *actual* command line — which
   differs from `.opt` — and the INCA benchmark scripts' entire output is a
   wall-clock timing, with `dataset_type: benchmark` having nowhere to record it.
7. Add `solver_options`: a multivalued key/value carrier
   (`slot_uri: fluxo:FLUXO_0000210` "fluxomics parameter") plus first-class slots
   for the load-bearing few. `.opt`'s `commandArgs` expands to 33 parameters of
   which **27 are unmapped**, and six of those (`--cupx`, `--cupn`, `--cupp`,
   `--clownr`, `--cinout`, `--clowp`) are implicit bounds on every flux and pool
   that appear in no constraint file. INCA's `m.options` is a flat namespace of
   dozens of keys against 6 scalar slots.
8. Split `SimulationRun.convergence_tolerance`: add
   `integration_rel_tolerance` / `integration_abs_tolerance`. INCA's `int_reltol`
   is an ODE-integrator tolerance, and the three benchmark files disagree on it
   by four orders of magnitude.
9. Add `FluxSolution.solution_role` (`reference` vs `estimated`): synthetic
   benchmarks know the true fluxes and there is nowhere to put them.
10. Do **not** map FreeFlux's `n_runs` to `multistart_count` — it resamples every
    measurement from `N(mean, sd)` and re-solves (a parametric bootstrap). Add a
    separate `monte_carlo_runs` slot.

---

### 3t-7. Measurement identity and notation

1. Add `MIDMeasurement.fragment_id` / `fragment_name` — the MS fragment is a
   named entity in every format (INCA `Ala2`, FreeFlux `Glu_12345`, `model.json`
   `fragment_id`, `toy_model` `ms_id`) and measured↔simulated series cannot be
   matched without it. Do **not** derive `replicate` from INCA's fragment-name
   suffix: `Ser2a`/`Ser2c` are both `Ser @ 2 3` but `Ser2b` is `Ser @ 1 2`.
2. Add expression forms alongside the foreign keys:
   `FluxMeasurement.flux_expression` (FluxML `<netflux>` bodies are expressions —
   `EC.fml:791` is `R63-R63b`), `PoolSizeMeasurement.pool_expression`, and a
   multivalued-or-expression species reference for MID/pool-size measurements so
   pooled signals like `E+B` (in both `toy.miso` and `toy.mmet`) can be held.
   Retain the raw spec formula for round-trip.
3. Widen `MIDDataPoint.isotopologue_index` to hold **tuples**: FluxML v3.0 writes
   `<datum weight="2,1">` (124 occurrences in `ecoli_model_level_3.fml`, 19
   distinct tuple values) for multi-isotope MS specs like
   `Ala[1-4]#M(3,0),(0,0),…`.
4. Make `atom_positions` a multivalued integer (`fragment_positions`) plus a raw
   notation string. Every format parses it to a list, and real specs mix ranges
   with commas (`Cit[1-3,5,6]`, `LEU[1-5,7]`) or omit the bracket entirely.
5. Add an `IsospeciesNotationEnum` (`mass_isotopomer` / `isotopomer_pattern` /
   `cumomer_pattern` / `nmr_peak`) and a home for **cumomer-pattern
   measurements** (`010`, `1xx` with wildcards, `+`-sums). These fit neither
   `MIDDataPoint` (index-based) nor `NMRIsotopomerDataPoint` (position+multiplet)
   — currently a hole. `IsotopicStateSpaceEnum.cumomer` is a *computation*
   setting on the run, not a measurement representation.
6. Add `NMRIsotopomerDataPoint.coupled_positions` and correct the
   `NMRMultipletTypeEnum` descriptions: the schema says `S` = "carbon unlabeled,
   neighbors unlabeled", but FTBL's singlet is the *labeled* carbon with
   unlabeled neighbours. `(position, multiplet_type)` alone is not
   round-trippable — `DD` and `T` emit the same arrow string. Also give
   `NMRIsotopomerMeasurement` the `dataset_id`, `scale_method`,
   `error_model_expression` and `replicate` slots `MIDMeasurement` has (or factor
   a shared parent).
7. Add an error-model slot to `FluxMeasurement`, `PoolSizeMeasurement` and the
   ratio classes: `<errormodel>` is legal on `<netflux>`, `<xchflux>` and
   `<poolsize>` too, and INCA's `f.std = f.val/20` is a model, not a value.
8. Add a `declared_but_unmeasured` marker (or make values optional per 3t-1): a
   measurement file can be a **template** — `toy.miso` has `Value = NA`
   throughout, INCA's `d.idvs = idv` declares fragments with no data, and
   FreeFlux's `set_target_EMUs` selects simulate-only targets.
9. Deepen natural-abundance provenance: per-element correction basis
   (`atom_dict`), NA probability constant, correction strategy, error-propagation
   rule, inoculum fraction, and — separately from the data flag — whether the
   *tool* corrects internally (x3cflux does; freeflux, influx_si, cmfa do not).
   Add a `data_origin` slot (`real` / `synthetic` / `simulated`): the
   compatibility doc establishes that this single bit decides whether a
   conversion is correct. Ontology support: FLUXO_0000275/0000283,
   FLUXO_0000289/0000290/0000291.
10. Split `replicate` into technical and biological (FLUXO_0000292,
    FLUXO_0000293 — the single integer conflates two ontology terms) and add a
    `Sample` layer (FLUXO_0000264) between `Condition` and the measurements.

---

### 3t-8. Multi-element tracing (the schema is silently 13C-only)

FluxML v3.0 is explicitly multi-element and the corpus uses it
(`spirallus_model_level_3.fml`, `CN_network_model_BCG.fml`).

1. Add `TracerElementEnum` (C / H / N / O / S) and an element slot on
   `TracerIsotopomer` (`slot_uri: fluxo:FLUXO_0000132` "tracer element"), plus
   `LabelingExperiment.tracer_elements`.
2. Add `AtomTransition.atom_element` — `cfg="C#1@1 N#2@1"` means C-position-1 and
   N-position-1 currently collide.
3. Make `NetworkMetabolite.n_tracked_atoms` per-element, or add a composition
   slot for `<pool>@cfg` (43 distinct values in the corpus: `C3N1`, `C2N2`,
   `C0N1`, `C15N5`, …). A `C3N1` pool currently collapses to `4`.
4. Make `TracerIsotopomer.isotopic_purity` multivalued: `@purity` is `xs:string`
   in the XSD and space-separated per element in v3.0 (`purity="0.99 0.88"`).
   Add `tracer_chemical_purity` as a distinct slot (FLUXO_0000080 vs the
   FLUXO_0000139 the schema uses).
5. Consider making `n_tracked_atoms` conditionally required when a labeling
   pattern exists — INCA and FreeFlux position lists cannot be converted to the
   required binary string without the atom count.

---

### 3t-9. Atom transitions: level, multiplicity, dangling atoms

1. **Relocate variants to the participant.** FluxML's `<variant>` is an
   alternative `cfg` for one `<reduct>`/`<rproduct>`, not for the reaction.
   `EC.fml:219-226` has 2 educt variants on `Suc` *and* 2 product variants on
   `Fum`, whose Cartesian product is the 4 flux ids in
   `<reaction id="R25___1 R25___2 R25___3 R25___4">`. Recommend
   `ParticipantCfgVariant` under `ReactionParticipant`.
2. Add a home for **space-separated multi-ID reactions** (`"R24___1 R24___2"`,
   `"sdh___1 … sdh___4"`, `"bsDAP___1 … bsDAP___4"`), which `<fluxvalue>`
   references individually.
3. Add an **occurrence/instance index** on `ReactionParticipant` and
   `AtomTransition`. Real cases: `V11: O (abcd) -> M (ab) + M (cd)`, INCA
   `Pyr (abc) + Pyr (def)`, `Ru5P + CO2 -> G3P (cde) + G3P (fba)`. FluxML uses
   `@MoleculeIndex`, the converter `AtomAddress.instance`.
4. Add **metabolite-level symmetry** (`NetworkMetabolite.symmetry`: name +
   position map), mapped to FLUXO_0000064 / FLUXO_0000077. INCA declares it once
   per metabolite; reaction-level variants force re-declaration on every reaction
   the metabolite touches.
5. Record **which scrambling convention** a dataset used: inline `<variant>`,
   pre-expanded reactions plus a tie constraint, or influx_si's duplicate
   reactions plus `NET v24_a - v24_b == 0`. Also drop the "ratio should sum to
   1.0" expectation — FreeFlux, INCA, and FluxML's `EC`/`CN` variants carry no
   ratio.
6. Allow **dangling atoms**: make `AtomTransition.product_metabolite_id` /
   `.product_atom_index` optional. Efflux reactions consume tracked atoms with no
   product (`spirallus_model_level_3.fml:53-56`, `linea.fml:25-27`).
7. Add `NetworkReaction.arrow_type` (or `net_flux_nonnegative`): influx_si has
   four arrow types (`->`, `->>`, `<->`, `<->>`) where the doubled forms mean
   net ≥ 0 and generate every `.cnstr.def` row (78 in `EC`).
8. Add `NetworkMetabolite.is_external` and `.is_balanced`. Both are absent from
   the ontology (new-term requests) and neither is `is_pseudo`. The compatibility
   doc's own conversion function takes `is_external` as a required parameter.
9. Add `NetworkMetabolite.pool_size` for `<pool>@size`, and `is_auto_generated`
   for converter-created drain reactions.

---

### 3t-10. Time

1. Add `time_unit` throughout (`slot_uri: fluxo:FLUXO_0000221`). FluxML supplies
   `<mlabel><timeunit>s</timeunit>` and INCA `m.options.sim_tunit` — both
   currently discarded.
2. Add `integration_timespan` (multivalued float) alongside `stop_time`:
   FluxML `<group>@times` (9 values in `EC.fml`), INCA `int_tspan`, FreeFlux
   `set_timepoints`. Grid points with no datum are unrecoverable today.
3. Move `time_point` to the **data point** (or add a `times` list on the group).
   FluxML repeats `@time` per `<datum>` (1487× in `EC.fml`) and influx_si has
   `Time` per row; a 9-timepoint group currently explodes into 9
   `MIDMeasurement` objects with duplicated metadata. Same on `FluxMeasurement`,
   `PoolSizeMeasurement`, `NMRIsotopomerMeasurement`.
4. Add a configuration-level nominal `time` (`<configuration>@time`).
5. Move units to the measurement-collection level (FluxML declares
   `<fluxunit>`/`<poolsizeunit>`/`<timeunit>` once per `<measurement>`, while the
   schema repeats them per row).

---

### 3t-11. Renames and enum work

Renames (only where the current name misleads — see PATH_FORWARD §13.11 for the
full table with evidence):

- `InputFormatEnum` → `FileFormatEnum`; `freeflux_csv` → `freeflux_tsv`
  (FreeFlux's reader **raises `TypeError` on `.csv`**), add `freeflux_xlsx`,
  `INCA_script`, `vmtf`, `MathML`.
- `MIDDataPoint.weight` → `msms_fragment_positions` and correct its description:
  FluxML/FTBL `WEIGHT` is the isotopologue index, i.e. what
  `isotopologue_index` already holds.
- `MIDMeasurement.scale_method` → `scale_type`, **and map it** to
  `fluxo:FLUXO_0000161` ("groupscale"). Add `none` for influx_si `--noscale`.
- `AtomAnnotationTypeEnum`: split `letter` into `lowercase_letter` /
  `uppercase_letter`; replace the uninformative `FluxML` value with
  `element_position_molecule`; add `comma_variant`, `position_list`,
  `inca_atommap`.
- `FluxTypeEnum`: add `exchange_normalized` for influx_si's xch01 ∈ [0,1) and
  record `xch` as an alias. Today `exchange` is documented as `min(fwd, rev)`
  while `.tvar.sim` reports xch01 and `edge.xchflux.attrs` reports the
  un-normalised exchange — three quantities, one value, so
  `(reaction_id, flux_type)` is not a unique key.

New enums: `SimulationTypeEnum` (`auto`/`explicit`/`full` — `<simulation>@type`
has no slot at all), `ConstraintDomainEnum`, `ConstraintOperatorEnum`,
`VariableTypeEnum`, `VariableKindEnum`, `TracerElementEnum`,
`IsospeciesNotationEnum`, `RunModeEnum`, `OptimizationMethodEnum`
(`nlsic`/`BFGS`/`Nelder-Mead`/`SANN`/`ipopt`/`pso` from influx_si;
`slsqp`/`ralg`/`glpk` from FreeFlux; plus `other`),
`ReactionDirectionalityEnum`.

Extensions: `FluxomicsMethodEnum` — add a **forward-simulation** value (`FLUXO_0000087`
"labeling simulation") and `FVA`; the entire benchmark suite (three INCA scripts,
three FreeFlux drivers) is forward simulation with fixed fluxes and is
untypeable today. `ConfidenceIntervalMethodEnum` — add `linearized`/Fisherian
(the **default** in both FreeFlux and INCA, currently absent) and `monte_carlo`;
and map the enum to FLUXO_0000302–0000306, replacing its "No FLUXO terms"
comment. `MFASoftwareEnum` — add `miemu` (referenced by the schema's own prose
*and* by Phase 7c), `cmfa`, `x3cflux`, `IsoCor`, `Skyline`.
`AnalyticalMethodEnum` — add `not_specified`. `ReactionTypeEnum` — add `drain`,
`biomass_precursor`, `symmetry_variant`, `dummy`. `FileRoleEnum` — add
`initial_values`/`parameters`, `variable_classification`, `batch`, `report`,
`bundle`, and **`driver_script`** (added 2026-08-24 per §13.15: the FreeFlux
`.py` and INCA `.m` that carry the tracer, bounds and solver settings the data
files omit have no role value today, so for FreeFlux the one artefact that makes
a dataset runnable cannot be referenced at all).

Add a `pathway` slot on `NetworkReaction`/`NetworkMetabolite`:
`<annotation name="pathway">` occurs **604×** — the most common annotation in the
corpus — and FreeFlux `reactions.xlsx` carries `#Glycolysis`-style section rows.
Also unmapped: `<annotation name="indexes">` (atom-index mapping into the InChI)
and `name`.

Give `MetabolicNetworkModel` the metadata FluxML `<info>` supplies and the
schema drops: `version`, `date` (with a time component — `FluxoDataset.creation_date`
is `range: date` and dataset-scoped), `description`/`comment` (`Syn.fml:6-19`
embeds three DOIs), `modeler`, `signature`.

---

### 3t-12. Correct the ontology-mapping claims in §3h

The "no FLUXO term, left unmapped" table is partly wrong. Terms exist for:
`ScaleMethodEnum`/`scale_method` → **FLUXO_0000161** groupscale;
`MIDDataPoint.weight` → **FLUXO_0000054** tandem isotopologue distribution;
`FluxRatioMeasurement` → **FLUXO_0000029** flux ratio;
`ConfidenceIntervalMethodEnum` → **FLUXO_0000302–0000306**;
`SourceFile.path`/`.checksum` → **FLUXO_0000297** / **FLUXO_0000288**.

Genuinely absent from the ontology, so these are **new-term requests** to file
against the `mfao` repo: free/dependent/constrained variable classification;
external and unbalanced metabolite; MS fragment as an entity; per-measurement
residual; optimization method / solver; configuration; aeration, temperature, pH,
genotype, cultivation mode; NMR multiplet type; dataset curation tier.

---

### 3t-13. Rewrite `VALIDATION_REQUIREMENTS.md`

The audit leaves that document substantially stale, and it must not be edited
piecemeal — its central premise has changed. Rewrite it alongside 3t-1.

**What is now wrong in it:**

- **§2 "Missing entirely from schema"** lists items that have since landed:
  `SourceFile` + `FileRoleEnum`, `NetworkReaction.aliases` /
  `NetworkMetabolite.aliases`, `replicate`, `FluxoDataset.dataset_type`,
  `SimulationRun.isotopic_state_space`, `MIDMeasurement.natural_abundance_corrected`,
  `FluxMeasurement.flux_unit` / `PoolSizeMeasurement.pool_size_unit`, FK typing,
  `initial_values`, `stop_time`, `MIDMeasurement.atom_positions`, and multivalued
  `experiment_id`.
- **§2 "Should be required but currently optional"** lists slots that are now
  required (`metabolites`, `reactions`, `reactants`, `tracer_fraction`,
  `isotopic_purity`, `MIDDataPoint.standard_deviation`, `labeled_sources`,
  `optimization_method`), while `products` and `atom_transition_variants` are
  `recommended: true` **by deliberate decision** — not a gap.
- **§§1, 3, 4 invert the conclusion.** The document's whole thrust is "make more
  slots `required: true`". §13.1 shows that is precisely what makes MTF,
  FreeFlux, and INCA datasets unrepresentable. The required-field
  recommendations must be re-expressed as **Tier-2 / benchmark-only** rules.
- **§3 references an `fluxomics_method` value `13C`** that does not exist (3t-0).
- **§3's cross-slot rules assume shapes that need to change**: MID sum ≈ 1.0 is
  wrong for `scale="auto"` groups; the `[0,1]` bound on `MIDDataPoint.value`
  rejects real data; `labeling_pattern` length = `n_tracked_atoms` cannot be
  checked when `n_tracked_atoms` is optional and cannot hold a multi-element
  composition; atom-index bounds change with the 1-based fix.
- **§5's Tier-1 rule "exactly one `role=network` file per
  `SimulationRun.input_files`"** is wrong for FluxML, where one `.fml` is
  network + constraints + tracer + measurements + simulation at once (3t-2).

**What to add:** the rules implied by 3t-3 … 3t-10 — constraint-domain
consistency, configuration↔network↔experiment referential integrity,
variable-partition well-formedness (every `NET`/`XCH` variable classified exactly
once; dependent variables not required to carry values), `lower_ci ≤ value ≤
upper_ci` extended to the new result classes, residual/measurement linkage,
time-unit presence when any `time_point` is set, and element consistency between
a tracer's `labeling_pattern`, its element, and the metabolite's per-element
composition.

**Framing to keep:** the two-tier split is right and should become the document's
organising principle rather than a note bolted onto the front — Tier 1 for all
datasets, Tier 2 for `dataset_type: benchmark`, with every rule labelled by tier.

---

### Phase 3t Verification

```bash
uv run ruff check src tests
uv run pytest
```

Beyond the existing suite, 3t must add:

- an **enum-completeness test** per enum (guards against a 3t-0 recurrence);
- a **fixture per corpus** — one dataset each derived from FluxML, MTF, FreeFlux,
  INCA and `toy_model`, all validating without fabricated values. This is the
  real acceptance test for 3t-1;
- `examples/valid/ec_cross_tool_dataset.yaml` exercising four configurations over
  one network (the 3t-4 acceptance test);
- fixtures covering the awkward real values: negative near-zero simulated MIDs,
  tuple weights (`weight="2,1"`), `Value = NA` templates, pooled species
  (`E+B`), multi-element `cfg="C#1@1 N#2@1"`, and space-separated
  multi-ID reactions.

Note that the current `examples/valid/*.yaml` exercise **none** of the Tier-1
provenance layer — no `source_files`, `dataset_type`, `input_files`/`output_files`,
`aliases`, or `replicate` — so 3s is entirely untested by fixtures today.

---

## Phase 7 — Tool Integration & CLI (converter + miemu)

Per PATH_FORWARD §11–§12. Adapter code lives **in each tool repo** with
`fluxomics_linkml` as an optional `[linkml]` dependency importing the
generated pydantic (Phase 4e is a hard prerequisite).

### 7a. Hydration adapter (converter repo, `io/linkml_io.py`)

`FluxoDataset` ↔ `FluxomicsData` in both directions. Normalization contract:
atom indices 1-based ↔ 0-based; converter atom maps product→reactant inverted;
variant `weights` ↔ `AtomTransitionVariant.ratio`; fragment DSL
(`"Ala[2,3]#M0,1,2"`) parsed via converter's `_parse_ms_expression`;
stoichiometry defaults 1.0 (converter doesn't parse coefficients); converter
`Simulation`/setup ↔ `SimulationRun.initial_values`. Round-trip tests per
format (FluxML, MTF, FreeFlux).

### 7b. Equivalence diff (converter repo)

`FluxomicsData` vs `FluxomicsData`, normalized: reaction sets, stoichiometry,
atom transitions, tracer composition, MID values within tolerance. Used to
verify that per-tool files encode the same ground truth before results are
admitted to a benchmark dataset (PATH_FORWARD §11 workflow step 5).

### 7c. Results extraction

| Source                                           | Status                                                                                                                                                                                                                                                              |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| influx_si post-fit`.tvar` (free fluxes, F/D/C) | ✅ existing parser suffices                                                                                                                                                                                                                                         |
| 13CFLUX2 output files                            | ❌ new reader                                                                                                                                                                                                                                                       |
| INCA`.mat` results                             | ❌ new parser (no`.mat` support at all today)                                                                                                                                                                                                                     |
| FreeFlux API results                             | ❌ API-capture shim                                                                                                                                                                                                                                                 |
| miemu`FitResults`                              | ❌ wrapper →`SimulationRun` (`software`=miemu+version, `isotopic_state_space`=EMU, `optimization_method`="SLSQP (null-space)", CIs from `flux_confidence_interval()`, `wssr` from `opt_objective`; `chi_square_p_value` empty — no χ² in miemu) |

Note: full net-flux vectors from free fluxes need the stoichiometric matrix
(the converter's QR-pivot machinery is reusable); store native + `flux_type`,
derivation is downstream.

### 7d. Metadata sidecar + `fluxo meta init`

No native format carries `Investigation`/`Condition` metadata (FluxML `<info>`
is the partial exception: modeler/strain/date). `--meta study.yaml` is
**required** for MTF/FreeFlux/INCA ingest; `fluxo meta init <file>` scaffolds
a template listing exactly the required-but-missing fields. μ may be
*suggested* from measured biomass fluxes but never silently auto-filled.

### 7e. CLI + packaging

`pip install fluxomics_data_converter[linkml]`; commands:
`fluxo ingest <file> [--results dir] [--meta study.yaml] -o dataset.yaml`,
`fluxo validate dataset.yaml [--benchmark]`, `fluxo compare a.yaml b.yaml --by reaction_id`.
CLI first; a UI is premature.

### 7f. End-to-end: `benchmark/EC`

Author EC ground truth as Tier-2-complete `FluxoDataset` → hydrate → generate
FluxML/MTF/FreeFlux (INCA hand-checked via 7b) → run tools (+ miemu re-fit of
stat configs) → extract one `SimulationRun` per tool → validate.

---

## Execution Order

| Pass                     | Phases | Scope                                                                                                                                                                                                                 |
| ------------------------ | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Done**           | 1-2    | Prefix fix + ontology mappings + bug fixes                                                                                                                                                                            |
| **Done**           | 3      | Restructure (3a-3r): root container, Condition, Option C measurements, cleanup, validation, FBA compatibility, parallel labeling experiments, natural isotope correction, FK typing, expanded metadata, enum coverage |
| **Done**           | 3s + 4 | PATH_FORWARD alignment (SourceFile, aliases, replicate, dataset_type, file slots) + project structure + generation pipeline + examples                                                                                |
| **Done**           | 3t-0   | ✅ Closed 2026-09-18 — **not** a regression. Removals confirmed deliberate; `FluxomicsMethodEnum` re-grounded on the FLUXO:0000021 subtree, `InvestigationTypeEnum` added, enum-completeness guard in place            |
| **Pass 2b**        | 3t-1 … 3t-4 | **Blocking compatibility** — tier the required set (unblocks MTF/FreeFlux/INCA ingest), fix the outright defects, permit linear-combination constraints, add the `Configuration` concept (unblocks `EC.fml`)     |
| **Pass 2c**        | 3t-5 … 3t-13 | Remaining compatibility work — variable specification, results layer, measurement identity, multi-element tracing, atom transitions, time, renames/enums, ontology-mapping corrections, and the `VALIDATION_REQUIREMENTS.md` rewrite (3t-13, do alongside 3t-1) |
| **Pass 3**         | 5      | Deep tests (SchemaView, validation, negative tests, referential integrity, Tier-1/results-layer rules (5i), markers, round-trip, real published model example) — **plus the per-corpus fixtures 3t requires**         |
| **Pass 4**         | 7      | Tool integration: hydration adapter, equivalence diff, results extraction, metadata sidecar, CLI, EC benchmark end-to-end. **Depends on 3t-1 … 3t-4**                                                                 |
| **Pass 5** (later) | 6      | Docs, CI, community files, public API                                                                                                                                                                                 |

Phases 3t-5 … 3t-12 can be reordered freely; 3t-0 must come first, 3t-13 tracks
3t-1, and 3t-1 … 3t-4 gate Phase 7. Each 3t sub-phase is independently
shippable — none requires another to land to be useful.

---

## Complete Class Inventory After Phase 3 + 3s

> **⚠️ This table is historical — it records the Phase 3+3s target, not the
> schema on disk.** Since it was written, 3t-0 (2026-09-18) confirmed a set of
> deliberate removals and reworked two enums. The rows below still list
> `Condition.aeration`/`.temperature`/`.ph`/`.cultivation_mode`/`.genotype`,
> which are **gone on purpose** — see 3t-0 before acting on anything here.
>
> Current on-disk state, verified 2026-09-18: **30 classes, 15 enums** (no class was added — `Condition` moved modules; `InvestigationTypeEnum` is the 15th enum).
> Changes not reflected in the rows below:
> - `Condition` moved `investigation.yaml` → `experiment.yaml`, and is now held
>   once at `FluxoDataset.conditions` and referenced by id from
>   `LabelingExperiment.condition` and `SimulationRun.condition` instead of
>   being inlined twice.
> - `Investigation` gained `investigation_type` (`InvestigationTypeEnum`).
> - `SimulationRun.mfa_method` → `fluxomics_method` (`FluxomicsMethodEnum`).
> - `FluxoDataset` gained `conditions`; its benchmark-tier rule no longer
>   requires `experiments` (see 3t-1 and the Phase 7 validator).

| Module                  | Classes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fluxolink.yaml`   | `FluxoDataset` (+ `schema_version`, `creation_date`, `last_modified`, `fluxo_ontology_version`; **3s:** + `source_files`, `dataset_type`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `investigation.yaml`  | `Investigation` (renamed from `Study`; module renamed from `study.yaml`), `Contributor`, `Condition` (renamed from `OrganismInfo`; + `aeration`, `temperature`, `ph`, `cultivation_mode`, `genotype`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `network.yaml`        | `MetabolicNetworkModel` (+ `flux_constraints`, `pool_size_constraints`), `NetworkMetabolite` (**3s:** + `aliases`), `NetworkReaction` (`reactants`/`products`; **3s:** + `aliases`), `ReactionParticipant`, `AtomTransitionVariant` (+ `ratio`), `AtomTransition` (`reactant_metabolite_id`/`reactant_atom_index`), `FluxConstraint` (now wired), `PoolSizeConstraint` (NEW)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `experiment.yaml`     | `LabelingExperiment` (+ `stationary`, `condition`, `investigation_id`, `mid_measurements`, `nmr_measurements`, `flux_measurements`, `pool_size_measurements`, `flux_ratio_measurements`, `pool_size_ratio_measurements`; **3s:** + `tracer_summary`), `LabeledSource` (+ `profile`, `input_type`), `TracerIsotopomer` (+ `cost`, `profile_values`), `MIDMeasurement` (renamed from `MeasurementGroup`; + `atom_positions`, `dataset_id`, `natural_abundance_corrected`, `correction_algorithm`, `comment`; **3s:** + `replicate`), `MIDDataPoint` (+ `weight`; class_uri removed), `NMRIsotopomerMeasurement` (NEW), `NMRIsotopomerDataPoint` (NEW), `FluxMeasurement` (NEW; + `flux_unit`; **3s:** + `replicate`), `PoolSizeMeasurement` (NEW; + `pool_size_unit`; **3s:** + `replicate`), `FluxRatioMeasurement` (NEW), `PoolSizeRatioMeasurement` (NEW), **`SourceFile` (NEW — 3s)** |
| `simulation_run.yaml` | `SimulationRun` (+ `fluxomics_method`, `objective_function`, `stop_time`, `initial_values`, `multistart_count`, `random_seed`, `convergence_tolerance`, `condition`, multivalued `experiment_id`; **3s:** + `input_files`, `output_files`, `isotopic_state_space`), `SoftwareInfo`, `FluxSolution` (+ `simulated_mids`), `FluxResult` (+ `confidence_interval_method`), `PoolSizeResult` (+ `confidence_interval_method`), `GoodnessOfFit` (assessment slot removed)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `enumerations.yaml`   | +`NMRMultipletTypeEnum`, `AerationEnum`, `CultivationModeEnum`, `ConfidenceIntervalMethodEnum`; expanded `FluxomicsMethodEnum` (9 values), `AnalyticalMethodEnum` (NMR sub-types), `MFASoftwareEnum` (FBA tools + `other`); **3s:** + `FileRoleEnum`, `DatasetTypeEnum`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

**Deleted:** `MeasurementGroup` (renamed), `MeasurementTypeEnum`, `ExperimentTypeEnum` (replaced by `stationary` boolean), `GoodnessAssessmentEnum` (already deleted), `ParticipantRoleEnum`, `OrganismInfo` (renamed)

**Schema-level bug fixes applied (Phase 2 corrections):**

- Removed `slot_uri: fluxo:FLUXO_0000148` from `TracerIsotopomer.labeling_pattern` (wrong concept — isotopomer representation is a state-space choice, not a tracer pattern)
- Removed `class_uri: fluxo:FLUXO_0000143` from `MIDDataPoint` (collision with `MIDMeasurement` — the distribution concept belongs on the group, not the data point)
