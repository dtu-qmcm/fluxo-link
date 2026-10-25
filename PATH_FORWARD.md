# PATH_FORWARD — Cross-Tool Comparison & Unified Representation

**Status:** Phase 3 + 3s applied to the schema. §§0–10 are the historical
architecture debate; **§11 is the operative decision** (two-tier schema) and
§§0–10 must be read through it. **§13 supersedes §§1–10 on what the schema must
represent** — it records the 2026-08-19 compatibility re-evaluation against the
five real format corpora.
**Last updated:** 2026-08-19 (§13: dataset/specification compatibility re-evaluation)

> **Reading order for anyone picking this up:** §11 (who holds the truth) →
> §13 (what the formats actually require) → §12 (end-user workflow) → §§0–10
> (why Path C was chosen, and which of its deletions were reversed).

---

## 0. Architecture decision: how deep should the schema go?

### The tension

The current schema (29 classes) re-describes in YAML what FluxML, MTF, and
FTBL already encode natively. That is **redundant** if (a) the simulation
software reads its own files, (b) the converter translates between formats
directly, and (c) the main goal is to *catalog* studies and *compare results*.

The question: **what does the schema uniquely provide that the native files
don't?** Three answers define three paths.

### Path A — Detailed internal model (current, 29 classes)

Model everything: metabolites, reactions, atom transitions, tracers, raw MID
data points, constraints, flux results, GOF.

| When it's worth it                                                                 | When it's redundant                                                                      |
| ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Query across studies at the data level ("all E. coli studies with [1-13C]glucose") | Simulation software reads its native file directly                                       |
| Validate internal consistency (referential integrity, MID sum ≈ 1.0)              | Converter translates between formats without an intermediate schema                      |
| Build a queryable database where data from different formats is truly harmonized   | Main need is to catalog*which file belongs to which study* + *what the results were* |

FluxML already IS a universal format — re-describing it in YAML duplicates
that effort. The converter can go directly (FluxML → MTF).

### Path B — Investigation catalog + results (lightweight, ~10 classes)

Model only what's **not already in the native files**:

```
FluxoDataset
├── investigations: [Investigation]       # contributors, publication, DOI
│   └── conditions: [Condition]           # organism, strain, medium, growth, aeration
├── source_files: [SourceFile]            # paths to FluxML/MTF/FTBL/.mat
│   ├── path, format (enum), checksum
│   └── role (network | measurements | tracer | simulation | results)
├── simulation_runs: [SimulationRun]      # software, version, parameters
│   ├── input_files: [SourceFile refs]
│   └── flux_solution: FluxSolution → FluxResult[]
│       └── goodness_of_fit: GoodnessOfFit
```

Network, atom transitions, tracers, raw measurements stay in native files —
the schema just references them. Much less maintenance, no converter needed
for internal data, complements FluxML rather than duplicating it.

**Loss:** can't validate internal structure (e.g., "does this metabolite ID
referenced in a measurement exist in the network?") without parsing the
native file.

### Path C — Hybrid: detailed results, file references for inputs (chosen)

**Extract what's comparable; reference what's not.**

The comparable outputs of MFA — flux solutions, confidence intervals,
goodness-of-fit, pool sizes — are the entire point of cross-study and
cross-tool comparison. These must be structured. The inputs — network
topology, atom transitions, raw measurements, tracers — are already well-
specified by native formats (FluxML, MTF) and are not the unit of
comparison. These become `FileReference`s.

**~17 classes** (down from 29), keeping the comparable core fully structured
while eliminating redundant re-description of native-file content.

### Comparison table

| Criterion                                       | Path A (detailed)                                                      | Path B (catalog)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | **Path C (hybrid)**                                      |
| ----------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Cross-tool flux comparison                      | ✅ direct                                                              | ✅ direct                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | ✅ direct                                                      |
| Cross-study meta-analysis                       | ✅ direct                                                              | ✅ direct                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | ✅ direct                                                      |
| Validate input consistency                      | ✅ full                                                                | ❌ needs file parse                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | ⚠️ results only                                              |
| Query tracer/MID across studies                 | ✅ direct                                                              | ❌ needs file parse                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | ❌ needs file parse                                            |
| Maintenance burden                              | High (29 classes, converter must parse every format into schema shape) | Low (~10 classes, no converter for                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    inputs) | **Medium (~17 classes, converter only parses results)**  |
| Redundancy with FluxML                          | High (re-describes network/measurements)                               | None                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | **Low (only results, which FluxML doesn't standardize)** |
| Converter complexity                            | High (full format → schema)                                           | None (just file paths)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | **Medium (format → results extraction)**                |
| Provenance (which native file)                  | ✅ via`FileReference`                                                | ✅ core feature                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | ✅ via`FileReference`                                        |
| Fairness metadata (seed, multistart, CI method) | ✅ on`SimulationRun`                                                 | ✅ on`SimulationRun`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | ✅ on`SimulationRun`                                         |

### Decision: **Path C (hybrid)** — amended by §11

The schema's job is to be **the comparable results layer**, not a universal
MFA file format. Inputs are referenced, not re-described. This complements
FluxML (which handles inputs) rather than duplicating it, and keeps the
converter's job tractable (extract results, not re-serialize whole models).

> **Amendment (2026-07-22, §11):** the input-class deletions are reversed to
> an **optional tier**. A benchmark's input ground truth must be declared and
> validated — file references assert provenance, not equivalence. The LinkML
> dataset, not the converter, holds the ground truth.

---

## 1. Goal

Store **one study analyzed by multiple MFA tools** as a single, tool-independent
representation so the results can be compared directly.

The primary consumer is **cross-tool benchmarking**: the same network and
experiment are given to several tools (freeflux, 13CFLUX2, influx_si, INCA),
and their fitted fluxes / confidence intervals / goodness-of-fit are compared.

**Why Path C (hybrid, not just links to files):** heterogeneous tool files
(FluxML XML, influx_si MTF, INCA `.mat`) report results in incompatible
shapes — influx_si puts free fluxes in `.tvar`, INCA in `m.rates.flx.val`,
FluxML in `<simulation><variables>`. A "link to the raw file" catalog cannot
answer "compare the fitted flux of reaction PGI across four tools" without
parsing each format. So the **results** must be structured. The **inputs**
(network, measurements, tracers) are already well-specified by the native
formats and are referenced, not re-described.

---

## 2. Target representation (Path C)

One `FluxoDataset` per study. The network and experiment(s) are **referenced
as files**; each tool run is a separate `SimulationRun` with structured results:

```
FluxoDataset  (= one study)
├─ investigations:  [INV1]
│   └─ contributors, publication_doi, conditions: [Condition]
├─ source_files:    [SourceFile]                 ← native files (FluxML, MTF, .mat, ...)
│   ├─ SF_netw      (role=network,     format=FluxML,  path=EC.fml)
│   ├─ SF_meas      (role=measurements, format=MTF,    path=EC_stat.miso)
│   └─ SF_tracer    (role=tracer,      format=MTF,     path=EC.linp)
├─ experiments:     [EXP_a_stat]                  # lightweight: stationarity, tracer summary, file refs
└─ simulation_runs:
   ├─ RUN_freeflux   (software=freeflux,  input_files=[SF_netw, SF_meas, SF_tracer])
   │   └─ flux_solution → FluxResult[] (reaction_id, value, lower_ci, upper_ci, ...)
   │   └─ goodness_of_fit (wssr, dof, chi_square_p, reduced_chi_square)
   ├─ RUN_13cflux2   (software=13CFLUX2,  ...)
   ├─ RUN_influx_si  (software=influx_si, ...)
   └─ RUN_inca       (software=INCA,      ...)
```

**Comparison** = align `FluxResult`s by (canonical) `reaction_id` across runs.

---

## 3. Class classification: survive, reference, or drop

### KEEP (detailed — the comparable results layer)

These classes carry the structured data that cross-tool/cross-study comparison
needs. They survive Path C unchanged.

| Class                  | Why it stays detailed                                                                                                                                 |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FluxoDataset`       | Root container — unchanged                                                                                                                           |
| `Investigation`      | Provenance (contributors, DOI) — unchanged                                                                                                           |
| `Contributor`        | Provenance — unchanged                                                                                                                               |
| `Condition`          | Biological context (organism, strain, medium, growth rate, aeration, temp, pH, mode, genotype) — needed for reproducibility and cross-study grouping |
| `SimulationRun`      | The unit of comparison — software, version, parameters, method.**Gains `input_files` slot**                                                  |
| `SoftwareInfo`       | Software + version — critical for reproducibility                                                                                                    |
| `FluxSolution`       | Container for results — unchanged                                                                                                                    |
| `FluxResult`         | **The core comparable datum** — reaction_id, flux_type, value, CI, SD, unit, CI method                                                         |
| `PoolSizeResult`     | Comparable output (if solver reports pool sizes)                                                                                                      |
| `GoodnessOfFit`      | Fit quality — the pass/fail criterion for cross-tool comparison                                                                                      |
| `LabelingExperiment` | Lightweight experiment metadata (stationary flag, condition) + file references.**Loses detailed measurement slots; gains `source_files`**     |

### ADD (new — file reference layer)

| Class          | Purpose                                                                                                                      |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `SourceFile` | References a native file (path, format, checksum, role). Replaces detailed network/measurement/tracer classes for input data |

### REFERENCE-ONLY (drop detailed classes; replace with `SourceFile`)

> **⛔ SUPERSEDED by §11.** This table was the Path C deletion list. It was
> **reversed**: none of these classes were deleted, and all of them exist in the
> schema today as the optional **Tier 2**. The table is kept only as the record
> of the argument. Do not execute it. §13 shows why reversing it was right —
> a `SourceFile` reference cannot express the input ground truth that four
> tools must be shown to agree on.

These classes re-describe content that native formats already handle. In Path C,
they are **replaced by `SourceFile` references** pointing at the native files.

| Class (current)              | Replaced by                       | Why                                                                                                                                                                                                             |
| ---------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MetabolicNetworkModel`    | `SourceFile(role=network)`      | Network topology, metabolites, reactions, atom transitions are fully specified by FluxML`<reactionnetwork>` / MTF `.netw` / INCA reaction strings. Re-describing them in YAML duplicates the native format. |
| `NetworkMetabolite`        | (inside network file)             | Metabolite IDs, formulas, compartments, atom counts — all in the native network file.                                                                                                                          |
| `NetworkReaction`          | (inside network file)             | Reaction IDs, stoichiometry, reversibility, atom transitions — all in the native file.                                                                                                                         |
| `ReactionParticipant`      | (inside network file)             | Stoichiometry — in the native file.                                                                                                                                                                            |
| `AtomTransitionVariant`    | (inside network file)             | Atom mappings — in the native file.                                                                                                                                                                            |
| `AtomTransition`           | (inside network file)             | Atom-to-atom mappings — in the native file.                                                                                                                                                                    |
| `FluxConstraint`           | (inside network file)             | Flux bounds — in FluxML`<constraints>` / MTF `.cnstr` / INCA `m.rates.flx.lb/ub`.                                                                                                                        |
| `PoolSizeConstraint`       | (inside network file)             | Pool size bounds — in FluxML`<psize>`.                                                                                                                                                                       |
| `MIDMeasurement`           | `SourceFile(role=measurements)` | Raw MID data — in FluxML`<labelingmeasurement>` / MTF `.miso` / FreeFlux `measured_MDVs.tsv`. Not the unit of comparison (results are).                                                                  |
| `MIDDataPoint`             | (inside measurements file)        | Individual m+i values — in the native measurement file.                                                                                                                                                        |
| `NMRIsotopomerMeasurement` | `SourceFile(role=measurements)` | NMR multiplet data — in the native measurement file.                                                                                                                                                           |
| `NMRIsotopomerDataPoint`   | (inside measurements file)        | Individual multiplet values — in the native file.                                                                                                                                                              |
| `FluxMeasurement`          | `SourceFile(role=measurements)` | Measured external fluxes — in the native measurement file.                                                                                                                                                     |
| `PoolSizeMeasurement`      | `SourceFile(role=measurements)` | Measured pool sizes — in the native file.                                                                                                                                                                      |
| `FluxRatioMeasurement`     | `SourceFile(role=measurements)` | Flux ratios — in FluxML`<fluxratios>`.                                                                                                                                                                       |
| `PoolSizeRatioMeasurement` | `SourceFile(role=measurements)` | Pool size ratios — in FluxML`<poolsizeratios>`.                                                                                                                                                              |
| `LabeledSource`            | `SourceFile(role=tracer)`       | Tracer mixture specs — in FluxML`<input>` / MTF `.linp` / INCA `tracer()`.                                                                                                                               |
| `TracerIsotopomer`         | (inside tracer file)              | Labeling patterns, fractions, purity — in the native tracer file.                                                                                                                                              |

### Summary count

> **⛔ SUPERSEDED by §11.** The Path C column below never happened. Verified
> counts in the schema today: **30 classes** (1 root + 3 investigation +
> 8 network + 12 experiment + 6 simulation_run) and **14 enums** — no enum was
> dropped. §11 traded Path C's promised savings for correctness; optionality,
> not deletion, is what keeps results-catalog datasets light.

|         | Path A (current) | Path C (hybrid)                                                                                                                                 |
| ------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Classes | 29               | **17** (11 kept + 1 new + 5 enums retained)                                                                                               |
| Enums   | 14               | **11** (drop `ReactionTypeEnum`, `AtomAnnotationTypeEnum`, `ConstraintTypeEnum`, `ScaleMethodEnum` — only used by input classes) |

---

## 4. The `SourceFile` class

```yaml
SourceFile:
  description: >-
    A reference to a native MFA file (FluxML, MTF, FTBL, .mat, etc.)
    containing network, measurement, tracer, or simulation data.
    The schema references the file rather than re-describing its contents.
  attributes:
    id:
      description: Unique identifier for this source file record.
      identifier: true
      required: true
    path:
      description: >-
        File path or URI to the native file. May be relative to the
        dataset file or an absolute/remote URI.
      required: true
    format:
      description: Native file format.
      range: InputFormatEnum
      required: true
    format_other:
      description: Free-text format, used when format is "other".
    role:
      description: What kind of data this file contains.
      range: FileRoleEnum
      required: true
    checksum:
      description: >-
        Content hash (e.g., SHA-256) for verifying file integrity.
        Format: "algorithm:hash" (e.g., "sha256:abc123...").
    media_type:
      description: >-
        MIME type of the file (e.g., "application/xml" for FluxML,
        "text/tab-separated-values" for MTF).
    description:
      description: Optional free-text description of the file's contents.

FileRoleEnum:
  description: Role of a source file in the MFA workflow.
  permissible_values:
    network:
      description: Metabolic network model (reactions, metabolites, atom transitions).
    measurements:
      description: Measurement data (MID, flux, pool size, NMR).
    tracer:
      description: Tracer / labeled source specifications.
    constraints:
      description: Flux or pool size constraints.
    simulation:
      description: Simulation parameters / solver configuration.
    results:
      description: Simulation results (fitted fluxes, GOF).
    configuration:
      description: >-
        Composite file containing multiple data types (e.g., a FluxML
        file with network + configuration + measurement + simulation).
```

---

## 5. Hybrid schema structure (Path C)

> **⛔ SUPERSEDED by §11.** `network.yaml` was **not** deleted, no enums were
> dropped, and `LabelingExperiment` kept its measurement slots. The layout below
> is the Path C proposal, not the schema. The **actual** layout is:
>
> ```
> src/fluxolink/schema/
> ├── fluxolink.yaml       # FluxoDataset root + imports
> ├── enumerations.yaml    # 14 enums
> ├── investigation.yaml   # Investigation, Contributor, Condition
> ├── network.yaml         # MetabolicNetworkModel, NetworkMetabolite,
> │                        # NetworkReaction, ReactionParticipant,
> │                        # AtomTransitionVariant, AtomTransition,
> │                        # FluxConstraint, PoolSizeConstraint
> ├── experiment.yaml      # LabelingExperiment, LabeledSource,
> │                        # TracerIsotopomer, MID/NMR/flux/pool-size
> │                        # measurements, ratio measurements, SourceFile
> └── simulation_run.yaml  # SimulationRun, SoftwareInfo, FluxSolution,
>                          # FluxResult, PoolSizeResult, GoodnessOfFit
> ```

```
src/fluxolink/schema/
├── fluxolink.yaml      # FluxoDataset root + imports
├── enumerations.yaml      # Retained enums (dropped 4 input-only enums)
├── investigation.yaml     # Investigation, Contributor, Condition
├── experiment.yaml        # LabelingExperiment (slimmed) + SourceFile (NEW)
├── simulation_run.yaml    # SimulationRun, SoftwareInfo, FluxSolution,
│                          # FluxResult, PoolSizeResult, GoodnessOfFit
└── [network.yaml DELETED] # Replaced by SourceFile(role=network)
```

### `LabelingExperiment` (slimmed)

> **⛔ SUPERSEDED by §11.** `LabelingExperiment` was **not** slimmed: it keeps
> `labeled_sources` and all seven measurement collections, and it never gained
> `source_files`. §13.4 records the opposite problem with the live class — it is
> missing a `network_model_id`, so its measurement foreign keys don't say which
> network they resolve against.

```yaml
LabelingExperiment:
  class_uri: fluxo:FLUXO_0000049
  description: >-
    An isotope labeling experiment. Lightweight metadata + references
    to native files containing tracer, measurement, and network data.
  attributes:
    id: { identifier: true, required: true }
    name:
    investigation_id: { range: Investigation, required: true }
    condition: { range: Condition, inlined: true, required: true }
    stationary: { range: boolean, required: true }
    source_files:                          # NEW — replaces labeled_sources, mid_measurements, etc.
      description: References to native files for this experiment.
      range: SourceFile
      multivalued: true
      inlined_as_list: true
      required: true
      minimum_cardinality: 1
    # DROPPED: labeled_sources, mid_measurements, nmr_measurements,
    #         flux_measurements, pool_size_measurements,
    #         flux_ratio_measurements, pool_size_ratio_measurements
```

### `SimulationRun` (gains `input_files`)

```yaml
SimulationRun:
  attributes:
    # ... existing: id, investigation_id, experiment_id (multivalued),
    #     fluxomics_method, condition, software, optimization_method,
    #     objective_function, multistart_count, random_seed,
    #     convergence_tolerance, stop_time, initial_values,
    #     flux_solution, goodness_of_fit
    input_files:                           # NEW
      description: >-
        References to native input files used for this run
        (network, measurements, tracer, solver config).
      range: SourceFile
      multivalued: true
      inlined_as_list: true
    # DROPPED: network_model_id (network is now a file reference,
    #          not a structured MetabolicNetworkModel)
```

### `FluxoDataset` (gains `source_files`)

```yaml
FluxoDataset:
  attributes:
    # ... existing: id, name, description, schema_version, creation_date,
    #     last_modified, fluxo_ontology_version, investigations,
    #     experiments, simulation_runs
    source_files:                          # NEW
      description: All native source files referenced by this dataset.
      range: SourceFile
      multivalued: true
      inlined_as_list: true
    # DROPPED: networks (replaced by source_files with role=network)
```

### `FluxResult` (unchanged — the core comparable datum)

```yaml
FluxResult:
  class_uri: fluxo:FLUXO_0000123
  attributes:
    reaction_id: { required: true }        # now a plain string (no NetworkReaction class to range against)
    flux_type: { range: FluxTypeEnum, required: true }
    value: { range: float, required: true }
    lower_ci: { range: float }
    upper_ci: { range: float }
    standard_deviation: { range: float }
    flux_unit:
    confidence_interval_method: { range: ConfidenceIntervalMethodEnum }
    aliases:                               # NEW — for cross-tool ID mapping
      description: >-
        Native reaction IDs from different tools that map to this
        canonical reaction (e.g., ["v5", "R_PGI", "PGI"]).
      multivalued: true
```

> **⛔ SUPERSEDED by §11.** `aliases` does **not** live on `FluxResult`. Because
> the input classes were restored, the canonical↔native mapping belongs on
> `NetworkReaction` / `NetworkMetabolite` — once per entity rather than
> denormalised onto every result row — and that is where the schema puts it.
> Note the live slots are currently **missing `multivalued: true`**, so they hold
> only one alias each; see §13.2.

---

## 6. Reaction ID alignment (the cross-tool comparison key)

**This is the critical design problem for Path C.**

Without a structured `NetworkReaction` class, `FluxResult.reaction_id` is a
plain string. Different tools name reactions differently (influx_si: `v1..vN`;
FluxML: arbitrary IDs; INCA: from reaction strings; FreeFlux: from TSV). To
compare fluxes across tools, the converter must establish a **canonical
reaction ID** per reaction and record each tool's native ID as an alias.

### Approach

1. **Converter establishes canonical IDs** when building the `FluxoDataset`.
   The canonical ID is typically the FluxML reaction `id` (most descriptive)
   or a normalized form (`R_PGI` not `v5`).
2. **`FluxResult.reaction_id`** stores the canonical ID.
3. **`FluxResult.aliases`** (new multivalued string slot) records the native
   IDs from each tool: `["v5", "R_PGI", "PGI"]`.
4. **`FluxResult.reaction_id` is required** — every flux result must map to
   the canonical ID space. The converter enforces this.
5. **Cross-tool comparison query** = group `FluxResult`s by `reaction_id`
   across `SimulationRun`s, align by `flux_type` (net/forward/backward/exchange).

### What this replaces

The current `aliases`/`native_id` slots planned on `NetworkReaction` (§4 of
the original PATH_FORWARD) move to `FluxResult` — because in Path C there is
no `NetworkReaction` class. The alias mapping lives where it's needed: on the
comparable result.

---

## 7. What the converter does (Path C scope)

The converter's job shrinks dramatically — it no longer needs to re-serialize
whole network models into the schema shape.

| Task                    | Path A (current)                                                                 | Path C (hybrid)                                                              |
| ----------------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Parse network file      | Full parse →`NetworkMetabolite`, `NetworkReaction`, `AtomTransition`, ... | **Skip** — just record file path as `SourceFile(role=network)`      |
| Parse measurements      | Full parse →`MIDMeasurement`, `MIDDataPoint`, `FluxMeasurement`, ...      | **Skip** — just record file path as `SourceFile(role=measurements)` |
| Parse tracers           | Full parse →`LabeledSource`, `TracerIsotopomer`                             | **Skip** — just record file path as `SourceFile(role=tracer)`       |
| Parse constraints       | Full parse →`FluxConstraint`, `PoolSizeConstraint`                          | **Skip** — inside network file                                        |
| **Parse results** | Full parse →`FluxSolution`, `FluxResult`, `GoodnessOfFit`                 | **Full parse** — this is the only structured extraction needed        |
| Establish canonical IDs | Map all native IDs onto canonical`NetworkReaction`/`NetworkMetabolite` IDs   | Map only**reaction IDs** for `FluxResult.reaction_id` + `aliases`  |
| Emit`FluxoDataset`    | 29 classes populated                                                             | ~17 classes populated (mostly results + file refs)                           |

**Converter complexity reduction:** the converter only needs to parse
**results** from each tool format, not the full input model. Results extraction
is far simpler than full model serialization.

---

## 8. Reference dataset: `benchmark/EC`

`fluxomics_data_converter/data/benchmark` has the **same E. coli model** in four
tools — ideal for validating the concept end-to-end:

- `FluxML/EC.fml` — one network, four configurations (a/b × STAT/INST).
- `influx_si/` — `EC.netw`, `EC.linp`, `EC_*_stat.miso` / `EC_*_inst.miso`,
  `EC_stat.tvar` / `EC_inst.tvar`, constraints.
- `INCA/EC.m` (+ `EC_poolsizes.m`) — simulation script.
- `FreeFlux/EC/` — `sim_stat_EC.py`, `sim_inst_EC.py`, `reactions.xlsx`,
  `measured_inst_MDVs.xlsx`.

**Results availability (important):**

- influx_si `EC_stat.tvar` **does** carry fitted free fluxes (e.g. `v5 = 55.59`,
  `v8 = 38.47`; dependent fluxes derive from these).
- FreeFlux and INCA ship as **simulation scripts + measured data**, not fitted
  results — their fitted fluxes require **running the tools**.

So a full four-tool numeric comparison needs a result-extraction step. The
shared structure (file refs + experiments + run records) can be built now and
influx_si populated with real numbers; the other tools' runs are stubs until
their outputs exist.

---

## 9. Migration plan: Path A → Path C

### Phase M1: Add `SourceFile` + `FileRoleEnum` + `input_files` slot

Add the new class and enum to `experiment.yaml`. Add `input_files` slot to
`SimulationRun` and `source_files` to `FluxoDataset` and `LabelingExperiment`.
**No classes deleted yet** — both representations coexist during migration.

### Phase M2: Add `aliases` to `FluxResult` + `PoolSizeResult`

Add the multivalued `aliases` string slot to both result classes. Change
`reaction_id` / `metabolite_id` ranges from `NetworkReaction` / `NetworkMetabolite`
back to plain `string` (since those classes will be dropped).

### Phase M3: Delete input-only classes + `network.yaml`

> **⛔ CANCELLED by §11 — do not execute.** Nothing in this phase was carried
> out and nothing in it should be. All 18 classes, `network.yaml`, the `networks`
> slot, `network_model_id`, the `LabelingExperiment` measurement slots, and all
> four enums remain in the schema and are load-bearing for benchmark datasets.

Remove the 18 classes classified as "reference-only" (§3). Delete
`network.yaml` entirely. Remove `networks` slot from `FluxoDataset`. Remove
`network_model_id` from `SimulationRun`. Remove detailed measurement/tracer
slots from `LabelingExperiment`. Drop the 4 input-only enums
(`ReactionTypeEnum`, `AtomAnnotationTypeEnum`, `ConstraintTypeEnum`,
`ScaleMethodEnum`).

### Phase M4: Update examples + tests

- Update `examples/valid/simple_model_dataset.yaml` — replace structured
  network/measurements/tracers with `SourceFile` references.
- Update `examples/valid/nmr_dataset.yaml` — same.
- Update `examples/invalid/missing_required_fields.yaml` — adjust for new
  required fields.
- Add `examples/valid/ec_cross_tool_dataset.yaml` — the benchmark example
  (influx_si results populated, other runs stubbed).
- Update `tests/test_schema.py` — remove references to deleted classes.
- Update `tests/test_examples.py` — validate new example structure.

### Phase M5: Update docs

- Update `IMPLEMENTATION_PLAN.md` — mark Path C migration as complete.
- Update `VALIDATION_REQUIREMENTS.md` — remove input-validation rules (MID
  sum, atom index bounds, pattern length) that no longer apply.
- Update `.agent/AGENTS.md` — reflect new schema structure.
- Update `.agent/CHANGELOG.md` — document the migration.

### Migration risk

The main risk is **losing validation power** for input data. Mitigations:

- The converter still validates inputs when it parses them (just doesn't
  serialize them into the schema).
- `SourceFile.checksum` provides file-integrity verification.
- The schema's required-field constraints still apply to results and metadata.
- If input-level validation is needed later, a separate "input validation"
  schema (or LinkML import of the native format) can be added without
  restructuring the results layer.

---

## 10. Plan & next steps

1. **Schema migration (Phase M1-M3):** add `SourceFile`, add `aliases`, delete
   18 input-only classes + `network.yaml`, slim `LabelingExperiment` and
   `FluxoDataset`. Regenerate Pydantic datamodel; keep tests green.
2. **Unified example (Phase M4):** build `examples/valid/ec_cross_tool_dataset.yaml`
   — one experiment with `SourceFile` refs, an influx_si `SimulationRun` with
   real fitted fluxes, and stub runs for freeflux / 13CFLUX2 / INCA. Validate it.
3. **Converter integration (separate repo):** the `to_fluxo` adapter that
   extracts results from each tool and emits one `SimulationRun` per tool
   (see the layering already documented in the README:
   ontology → schema → converter).

### Open decisions

- **Experiment ↔ network binding:** with no `NetworkModel` class, experiments
  and runs reference network files via `SourceFile`. If multiple network
  variants exist, each run's `input_files` includes the correct network file.
  Sufficient for benchmarking; no `network_model_id` FK needed.
- **Missing tool results:** run FreeFlux/INCA to obtain fitted fluxes, or ship
  the example with influx_si populated and the other runs stubbed?
- **Result extraction:** does the converter compute the full net-flux vector
  from each tool's free fluxes + stoichiometry, or store only what each tool
  reports natively?
- **`reactants` vs `substrates` naming:** moot in Path C — `NetworkReaction`
  is deleted; reaction participants live in native files.
- **Ground-truth holder:** resolved by §11 — the LinkML dataset holds the
  ground truth; the converter translates and validates. Input classes return
  as a two-tier structure (required for benchmark datasets, optional otherwise).

---

## 11. Who holds the ground truth? (decision, 2026-07-22)

### The three-layer framing

| Layer | Artifact | Kind of understanding | Role |
|---|---|---|---|
| Ontology | FLUXO | **Semantic** — what terms mean | Defines the vocabulary (flux, MID, CI, simulation run) |
| Schema | LinkML (this repo) | **Information** — how valid data is structured | Declares structure + constraints; binds terms to the ontology |
| Converter | fluxomics_data_converter | **Application** — how each tool encodes the same information | Translates between formats; normalizes conventions |

The benchmark goal maps onto the layers: (1) **one ground-truth input**
(network, measurements, tracers), (2) **faithful translation** into 4–5 tools,
(3) **comparable outputs**. Path C solves (3). It does not solve (1) and (2):
a `SourceFile` reference asserts **provenance, not equivalence** — `EC.fml`,
`EC.netw`, `reactions.xlsx`, `EC.m` could silently encode different networks
or tracers, and the benchmark would compare four different problems.
Cross-file equivalence requires parsing and comparing; there is no shortcut
(§0's own comparison table admitted this: "Validate input consistency ❌ needs
file parse").

A ground truth is by definition an *information* artifact — a declared,
authoritative statement of what the benchmark input IS. The ontology cannot
hold instance data (it defines classes of things, not this network); the
converter's job is translation fidelity, not declaration. By the layering
itself: **the LinkML model holds the ground truth.**

### Decision

**The `FluxoDataset` holds the ground truth. The converter is its faithful
translator and validator — never the owner.**

- **FluxoDataset (LinkML)** = declared truth: canonical network (IDs +
  aliases + atom transitions), tracers, measurements, conditions. Archivable,
  validated (VALIDATION_REQUIREMENTS applies only to materialized data),
  ontology-grounded, citable.
- **Converter** = fidelity engine: `FluxoDataset` → `FluxomicsData` → per-tool
  files (writers: FluxML ✅, MTF ✅, FreeFlux ✅, INCA ✗ — no writer), and the
  inverse: parse any foreign/tool-edited file and diff it against the
  declared truth (equivalence check) before its results are admitted.
- **FLUXO ontology** = the meaning of every term in the truth.

The converter's `FluxomicsData` remains the *working form* — computation
(stoichiometric matrices, isotopomer propagation) and file generation happen
there — but **authority lives in the document**.

(One exception where converter-held truth is acceptable: a purely local,
throwaway experiment rig that is never archived, cited, or shared. A benchmark
dataset is by definition a shared reference — its input IS the deliverable —
so the exception does not apply here.)

### Consequence: Path C deletions reversed to a two-tier schema

§0–§9's deletion of the input-content classes was right about one thing —
the **results layer** is the unique contribution for comparison — but wrong
to delete inputs unconditionally. The schema becomes **two-tier**:

- **Tier 1 — required (all datasets):** `FluxoDataset`, `Investigation`,
  `Condition`, `SourceFile` provenance, `SimulationRun` + results
  (the Path C core — unchanged).
- **Tier 2 — input truth (required for benchmark/truth-carrying datasets;
  optional for results-catalog datasets):** `MetabolicNetworkModel` +
  metabolites + reactions + atom transitions + constraints, and
  `LabelingExperiment` detail (tracers, MID/NMR/flux/pool measurements).
  Present ⇒ must satisfy the VALIDATION_REQUIREMENTS ruleset (tracer sums,
  MID SDs, atom transitions for tracked metabolites, referential integrity).

Class count returns to ~31 (29 + `SourceFile` + `FileRoleEnum`, plus
`aliases` / `replicate` slots). The savings Path C promised are abandoned in
favor of correctness; **optionality — not deletion — is what keeps
results-catalog datasets light.**

`aliases` live on the restored `NetworkReaction` / `NetworkMetabolite` as
tool-namespaced strings (`"influx_si:v5"`): the canonical↔native ID mapping
is *new information* present in no native file, so it belongs in the dataset
— once per reaction, not denormalized per result row.

### Updated benchmark workflow

1. Author the EC ground truth **once** as a Tier-2-complete `FluxoDataset`.
2. Hydrate via the converter (`FluxoDataset` → `FluxomicsData`) and
   **generate** FluxML / MTF / FreeFlux inputs (INCA hand-maintained + checked
   via the equivalence diff).
3. Run the four tools (+ optional miemu re-fit of the stationary configs).
4. Extract results into one `SimulationRun` per tool; validate the dataset.
5. Any tool-edited file is parsed and diffed against the declared truth
   before its results are admitted.

### What this requires building

- **The hydration adapter** (`FluxoDataset` → `FluxomicsData`) — the
  load-bearing piece Path C tried to avoid. Plus round-trip tests.
- **The equivalence diff** (`FluxomicsData` vs `FluxomicsData`, normalized:
  reaction sets, stoichiometry, atom transitions, tracer composition, MID
  values within tolerance).
- **miemu results wrapper** (`FitResults` → `SimulationRun`), unchanged.

---

## 12. End-user workflow: the FluxML-native researcher (2026-07-22)

**Persona:** ran 13CFLUX2 natively; has `EC.fml` + 13CFLUX2 output files;
wants to archive the run and later compare it against other runs/tools.

### Journey (files-first path — distinct from the curator's author-once path in §11)

| Step | What happens | Status |
|---|---|---|
| 1. Ingest input | `converter.parse("EC.fml")` → `FluxomicsData` | ✅ exists |
| 2. Hydrate Tier 2 | `FluxomicsData` → `FluxoDataset` (network, tracers, MIDs materialized + validated) | 🔨 hydration adapter (§11) |
| 3. Add metadata | `Investigation` / `Contributor` / `Condition` — organism, medium, growth rate are in **no** FluxML file; `<info>` pre-fills modeler/strain/date; rest via small sidecar YAML (or prompts) | 🔨 sidecar pattern |
| 4. Results | 13CFLUX2 output → `FluxSolution` + `GoodnessOfFit` | ❌ no 13CFLUX2 results reader. Fallbacks: influx_si `.tvar` parseable today (different tool); or re-fit the stationary case with miemu from the hydrated dataset — doubles as a cross-check of the native run |
| 5. Validate + store | `linkml-validate` (schema + Tier-2 rules + referential integrity); save YAML/JSON | 🔨 Phase 5 |
| 6. Compare | ingest a second run identically; group `FluxResult`s by canonical `reaction_id` | 🔨 trivial query once 2+ runs exist. Single-tool user: native IDs *are* the canonical IDs — aliases only matter when a second tool enters |

### Metadata availability by format (why the sidecar is mandatory)

Native formats were never designed to carry investigation metadata — so the
converter alone cannot produce a *valid* dataset:

| Format | Metadata carried | Pre-fillable schema fields |
|---|---|---|
| FluxML `<info>` | name, version, date, modeler, strain, comment | `Condition.strain`; `Contributor.name`; dataset `creation_date`; `Investigation.name`/`description` (partial) |
| MTF (`.netw`/`.linp`/`.miso`/…) | none | nothing |
| FreeFlux TSVs | none | nothing |
| INCA `.m`/`.mat` | none (code) | nothing |

vs. schema-required fields the files cannot give: `Condition.organism_name`,
`strain`, `specific_growth_rate`, `growth_rate_unit` (all `required: true`),
`Investigation.id`/`name`.

Nuances: μ is sometimes *indirectly* recoverable (measured biomass flux in
`.mflux`/FluxML, or a free symbol in constraint expressions) — the tool may
*suggest* it for confirmation but must never silently auto-fill; medium
composition is inference, not data.

Consequences for the CLI:
- MTF / FreeFlux / INCA: `--meta` sidecar **required**; `fluxo ingest` fails
  with a precise missing-fields list otherwise.
- FluxML: pre-fill from `<info>`, then confirm/complete.
- `fluxo meta init <file>` scaffolds a sidecar template listing exactly the
  required-but-missing fields.

(This mirrors ISA's design: investigation metadata is a separate authoring
act, never recoverable from assay files.)

### Reproducibility contract (what's recorded)

Network + atom transitions ✅ (Tier 2 *and* checksummed `SourceFile`),
constraints ✅, tracers ✅, measurements ✅, solver setup ✅
(`optimization_method`, `random_seed`, `multistart_count`,
`convergence_tolerance`, `isotopic_state_space`, `initial_values`),
software **+ version** ✅ (required), original files with SHA-256 ✅.

**Not recorded:** results from tool outputs we can't parse yet (step 4), and
vendor-specific solver knobs beyond our parameter slots. Acceptable by
design: the checksummed original input + the recorded parameters *is* the
reproducibility contract — anyone can re-run the exact bytes.

### Packaging answer: CLI, not UI

One install (`pip install fluxomics_data_converter[linkml]`), three commands:

```bash
fluxo ingest EC.fml --results 13cflux2_out/ --meta study.yaml -o ec_run1.yaml
fluxo validate ec_run1.yaml
fluxo compare ec_run1.yaml ec_run2.yaml --by reaction_id
```

Target users (13CFLUX2/INCA/miemu practitioners) live in terminals and
scripts; a web UI is premature until the CLI proves the workflow.

---

## 13. Dataset & specification compatibility re-evaluation (2026-08-19)

### 13.0 What was checked, and the verdict

Every corpus and specification under `fluxomics_data_converter/data/` was audited
against the live schema (30 classes, 14 enums), plus the converter's own internal
model — which is the de-facto union of the five formats — plus the FLUXO ontology.

| Source | What it is |
|---|---|
| `specifications/format_compatibility.md` (1785 lines) | the cross-format master analysis, incl. its §13 natural-abundance findings |
| `specifications/{fluxml,influx_si,inca,freeflux}_spec.md` | per-format specs |
| `FluxML_tests/format/fluxml.xml` | **the authoritative FluxML XSD** (705 lines, v1.0→v3.0) |
| `benchmark/{FluxML,influx_si,INCA,FreeFlux}` | the EC + Syn cross-tool benchmark |
| `MTF_tests/toy_test` | the only complete MTF file set (all 9 suffixes) |
| `simple_model/roundtrip_test/MTF_from_{mtf,fml,freeflux}` | three round-trips **with solver output** (`.tvar.sim`, `.miso.sim`, `.mflux.sim`, `.stat`, `.log`, `.pres.csv`) |
| `FluxML_tests/fluxml-model/models` | 7 further FluxML models (ecoli 1–3, spirallus 1–3, CN) |
| `toy_model/` | a neutral JSON/CSV representation — the closest existing analogue to this schema |
| `fluxomics_data_converter/src` | `FluxomicsData`, `Constraints`, `Group`, `FluxValue`, `Datum`, `Tracers`, `AtomAddress` |

Excluded by decision: `Sergi_master/` and `FluxML_tests/obsolete/`.

**Verdict: the architecture holds; the schema is not yet compatible with the
corpora.** Tier 1 / Tier 2, the results layer, and the provenance layer all
survive scrutiny. But **no dataset derived from MTF, FreeFlux, or INCA files can
currently be made valid**, **`benchmark/FluxML/EC.fml` — the reference dataset of
§8 — cannot be represented at all**, and several concepts the benchmark depends
on have no home. Findings are grouped below in priority order.
`IMPLEMENTATION_PLAN.md` **Phase 3t** carries the actionable version; this
section records the decisions and the evidence.

Two corrections to `fluxml_spec.md` that the XSD settles, so they are not
propagated: `<variant>` is a child of `<reduct>`/`<rproduct>`, **not** of
`<reaction>`; and there is no `<mgroup>` element and no `<timepoints>` element
anywhere in FluxML.

### 13.1 Blocking: the required-field set is calibrated to FluxML alone

The largest finding, reached independently by all five audits. The schema marks
slots `required: true` that **no format supplies**:

| Required slot | Who can actually supply it |
|---|---|
| `Condition.organism_name`, `.strain`, `.specific_growth_rate`, `.growth_rate_unit` — and `LabelingExperiment.condition` itself | strain: FluxML `<info><strain>`, present in **1 of 11** FluxML files. **Growth rate and its unit: no format, anywhere.** |
| `TracerIsotopomer.isotopic_purity` | FluxML `@purity` — and it is *optional* there too, absent from `linea.fml`, `CN`, `mixture.fml`. MTF `.linp` has no such column; INCA `tracer()` never supplies it; FreeFlux leaves it implicit |
| `TracerIsotopomer.tracer_fraction` | present everywhere, but FreeFlux's remainder is *implicitly* natural substrate and INCA's `t.frac` spans several input metabolites (observed summing to 3.0) |
| `MIDMeasurement.analytical_method` | **no format carries it.** FluxML `<group>` has no analytical field; MTF's `Dataset` column holds `stat`, `inst`, `MS-1`, `F_123` — none is a method |
| `MIDMeasurement.atom_positions` | absent whenever a FluxML spec omits the bracket (`AKG#M0,1,2,3,4,5` = whole molecule), and MTF's empty `Fragment` means the same |
| `MIDDataPoint.value`, `.standard_deviation` | INCA's `d.idvs = idv` declares fragments with **no values at all**; `toy.miso` has `Value = NA` throughout; FreeFlux preset files have no `sd` column |
| `FluxMeasurement.standard_deviation`, `PoolSizeMeasurement.standard_deviation` | FreeFlux `fluxes.tsv` / `concentrations.tsv` are value-only; INCA has no SD |
| `SimulationRun.optimization_method` | recorded by no format — FluxML has no optimizer field at all — and *meaningless* for the forward-simulation runs that make up the entire benchmark suite |
| `SoftwareInfo.version` | no native input file records it |
| `MetabolicNetworkModel.metabolites` (min 1) | INCA never declares metabolites; the list must be derived from reaction strings |
| `SimulationRun.investigation_id`, `LabelingExperiment.investigation_id`, `SimulationRun.fluxomics_method` | no format carries investigation identity; `fluxomics_method` is at best inferable from `@stationary` |

**Decision.** Required-ness must be *tiered*, not global. `DatasetTypeEnum`
already exists for exactly this and is currently unused for it. The strict set
becomes a Phase-5 rule conditioned on `dataset_type: benchmark`; the slots
themselves drop to `recommended`. This applies to fields the mechanism §11
already established for classes: optionality, not deletion.

Corollary for §12: the metadata sidecar stays **mandatory for a benchmark
dataset** and becomes **optional for a catalog dataset**. A researcher archiving
an INCA run must not be blocked on a growth rate they never measured.

### 13.2 Outright defects (fix regardless of any design decision)

| Defect | Evidence |
|---|---|
| `NetworkReaction.aliases` and `NetworkMetabolite.aliases` are **missing `multivalued: true`** | plural name, a description giving two examples, and §11's "once per reaction" intent — yet each holds a single string. This is the designated home for the canonical↔native mapping; INCA alone needs `R61`↔`v61` |
| `FluxSolution.simulated_mids` is **unpopulatable** | its range is `MIDMeasurement`, whose `MIDDataPoint.standard_deviation` is `required: true` (the generated Pydantic emits `Field(default=...)`), plus required `analytical_method` and `atom_positions` — while its own description says SD is "left unpopulated". A simulated value has no instrument and no measurement error |
| `MIDDataPoint.value` bounded `[0.0, 1.0]` rejects real data, on three independent counts | (a) influx_si's own `.miso.sim` and `toy_calc.miso` contain `-5.55e-17`, `-1.11e-16`, `-3.75e-09`; (b) 22 `<datum>` rows in `ecoli_model_level_2.fml` carry `e-0` literals that parse above 1.0; (c) FluxML `scale="auto"` groups are deliberately unscaled and raw MS intensities are not fractions. NA-correction by matrix inversion also produces small negatives |
| Atom indices are **0-based** on `AtomTransition` but **1-based** on `NMRIsotopomerDataPoint.atom_position` | all five formats are 1-based (`C#1@1`, `Ala[2,3]`, `@ 1 2 3`, `atommap('1:4 2:3')`, `2->1,3`), as is the converter's `AtomAddress.index`. A silent off-by-one here corrupts atom transitions — the highest-severity quiet failure in the schema |
| `SourceFile.role` is single-valued and required | one `.fml` is simultaneously network, constraints, tracer, measurements **and** simulation. Needs `multivalued: true` or a `bundle` value |
| `PoolSizeConstraint` reuses `class_uri: fluxo:FLUXO_0000068` | that term's label is "**linear flux** constraint" — wrong for a pool size. Leave unmapped or request a term |
| `FileRoleEnum.other` has no `role_other` companion | breaks the `*_other` convention used by `format_other`, `analytical_method_other`, `software_name_other`, `input_format_other` |
| `SourceFile` is **duplicated rather than referenced** | `inlined_as_list` in both `FluxoDataset.source_files` and `SimulationRun.input_files`/`output_files`, despite `SourceFile` having an identifier. Two copies of one file can then disagree on checksum |
| `IsotopicStateSpaceEnum` is missing `auto` | `auto` is the `<simulation>@method` default and the value in **14 of 15** real `<simulation>` elements |

### 13.3 The schema forbids constraints that FluxML and influx_si routinely contain

`FluxConstraint.reaction_id` is `required: true` and single-valued, and
`constraint_type` is required too. But a linear constraint is *about a
combination*, not about one reaction:

```
EC.cnstr:                    NET  bmALA - 0.488*v67   ==  0     (× 31 biomass couplings)
                             NET  v24_a - v24_b       ==  0
                             XCH  v24_a - v24_b       ==  0
EC.fml:631:                  0.488*R67=bmAla                    (31 statements in one <textual>)
Syn.fml:426:                 bmR5P=0.715*biom                   (16 statements in one <textual>)
Syn.fml:481:                 fum___1+fum___2<=100
spirallus_1.fml:63:          v2<=v1                             (no numeric bound at all)
ecoli_3.fml:1005:            TCA8_v27___1/0.5=TCA8_v27___2/0.5  (division)
ecoli_1.fml:1005:            0=488*mu2_v70___1-Ala_bm___1
```

There is no non-arbitrary `reaction_id` for any of these, and `v2<=v1` has no
numeric bound to put in `lower_bound`/`upper_bound`. The converter's own model
agrees: `ConstraintFormula` is `{name, expression, is_mathml}` with **no reaction
reference at all**. So does the ontology — FLUXO_0000068 is *linear* flux
constraint.

Four further constraint gaps, all confirmed in real files:

- **Domain and relational form are orthogonal axes, and only one is modelled.**
  FluxML's `<net>` / `<xch>` / `<psize>` and influx_si's `Kind` column (`NET` /
  `XCH` / `METAB`) are the *domain* the expression is evaluated in.
  `ConstraintTypeEnum` (`equality` / `inequality` / `bound`) is the *relational
  form*. The schema encodes only the latter, so `EC.cnstr`'s NET-scoped and
  XCH-scoped constraints with byte-identical `Formula`, `Operator`, and `Value`
  (three such pairs) collapse into indistinguishable instances — silent data
  loss. The converter splits `Constraints` into `.net` / `.xch` /
  `.metabolitesize` for precisely this reason.
- **No operator.** `inequality` carries no direction, while the files carry `==`,
  `>=`, `<=` explicitly.
- **One `<textual>` is N constraints** (`;`-separated). Splitting into N
  `FluxConstraint` rows dissolves the grouping and forces N synthetic ids; not
  splitting leaves `reaction_id` meaningless.
- **No expression-valued right-hand side** (the influx_si spec permits one; all
  bound slots are `range: float`), and **no notation flag** — MathML is legal
  wherever `<textual>` is, and the converter carries `is_mathml`.

**Decision.** `reaction_id` / `metabolite_id` become optional (or multivalued as
a participating-entity list) so `expression` can stand alone; add a
`constraint_domain` slot and an operator. A constraint naming entities absent
from the network is not an error — `toy.mflux` measures `BIOMASS_YIELD`, a free
variable that is not a reaction in `toy.netw` at all.

### 13.4 The missing `Configuration` class — why `EC.fml` cannot be represented

This is the concrete blocker for §8's reference dataset. `benchmark/FluxML/EC.fml`
is **one** `<reactionnetwork>` plus **one** global `<constraints>` plus **four**
`<configuration>` blocks:

```
EC.fml:664   name="a_INST"  stationary="false" time="0.0"
EC.fml:2377  name="b_INST"  stationary="false" time="0.0"
EC.fml:2563  name="a_STAT"
EC.fml:2924  name="b_STAT"
```

What actually differs between them: stationarity and nominal time; the number of
labeling measurement groups (33 / 1 / 33 / 1); the netflux measurement id sets
(`fp_0…fp_6` for INST, from `fp_7` for STAT); four separate `<data>` blocks
(1678 `<datum>` total); and the simulation variables — all four carry 35
`<fluxvalue>`, but the two INST configs carry **56 `<poolsizevalue>`** each and
the STAT configs carry none. `Syn.fml` goes further: three configurations (`a`,
`b`, `bayes`), each with its **own nested `<constraints>`** with *different bound
sets*, and `bayes` alone carrying `<poolsizemeasurement>`.

`<configuration>@name` is XSD-unique — it is the configuration's identity. The
schema has no `Configuration` class, no per-configuration constraint container,
no per-configuration simulation container, and `LabelingExperiment.name` is an
optional free-text slot. So converting `EC.fml` means fabricating four
`LabelingExperiment` and four `SimulationRun` ids with no shared key, after
which `a_INST` ↔ its variables ↔ its data cannot be re-associated.

`<constraints>` is legal at **both** levels, and both occur:

| File | Global `<constraints>` | Per-configuration |
|---|---|---|
| `EC.fml` | :629 (`net` only) | — |
| `Syn.fml` | :424 | :460, :1441, :1683 (each `net`+`xch`+`psize`) |
| `ecoli_model_level_1/2/3.fml` | :970 / :964 / :996 | :1003 / :999 (+`psize`@1088) / :1035 |
| `CN_network_model_BCG.fml` | :958 | :1098 |
| `spirallus_model_level_1/2/3.fml` | :54 / :56 / :60 | — |

Merging per-configuration constraints into the network is semantically wrong.
Every other format agrees on the scoping: influx_si has one `.tvar`/`.cnstr` per
file set (`EC_a_stat` / `EC_a_inst` / `EC_b_stat` / `EC_b_inst` over a shared
`EC.netw`), INCA sets `m.rates.flx.lb/ub` on the model instance, and the
converter's `LabelingExperiments` owns its own `constraints` *and* its own
`simulation`.

Two related binding gaps:

- **`LabelingExperiment` has no `network_model_id`.** Its measurement foreign
  keys resolve into *a* network, but the experiment never says which. In a
  multi-network dataset — the benchmark case — referential integrity is not
  decidable at the experiment level.
- **`SourceFile` has no experiment back-reference.** File→experiment attribution
  in the benchmark is carried purely by filename convention (`_a`/`_b`,
  `_stat`/`_inst`), and for FreeFlux a dataset's stationarity is encoded *only*
  in which filename was read (`measured_MDVs.tsv` vs `measured_inst_MDVs.tsv`).

**Decision.** Add a `Configuration` concept — either a class between network and
experiment, or a configuration key plus per-configuration constraint and
variable containers on `LabelingExperiment` / `SimulationRun`. Add the
experiment→network reference and the file→experiment reference. This is a
prerequisite for §8 and for §11's workflow step 1, not a follow-up.

### 13.5 The missing layer: variable specification (free / dependent / constrained)

influx_si's `.tvar` is built on a three-way classification with no schema
counterpart anywhere:

| Column | Meaning |
|---|---|
| `Kind` | `NET` / `XCH` / `METAB` — which parameter family the row addresses |
| `Type` | `F` free (fitted, a degree of freedom) · `C` constrained (fixed, never fitted) · `D` dependent (algebraically determined) |
| `Value` | for `F` the optimizer's **starting point**; for `C` the **fixed value**; for `D` blank on input and **filled on output** |

The same concept appears as FluxML `<fluxvalue>` / `<poolsizevalue>` with
`@lo` / `@hi` / `@inc` / `@edweight` (XSD:675-702) and `@ed`, as FTBL's `FCD` /
`ED_WEIGHT` / `LOW(F)` / `INC(F)` / `UP(F)`, as INCA's `m.rates.flx.fix`, and in
the converter as `FluxValue{flux, type, value, lo, hi, inc, edweight}` and
`MetaboliteSizeValue{..., type: "F=Free, D=Dependent, C=Constrained"}`. It is
**absent from the ontology too** — a genuinely new term request.

Two consequences the schema currently mis-handles:

1. **`SimulationRun.initial_values: FluxSolution` is the wrong shape.**
   `FluxResult` carries `lower_ci` / `upper_ci` / `confidence_interval_method`,
   which are meaningless for a starting point, and lacks `lo` / `hi` / `inc` /
   `edweight`, which are what the formats actually store. Per-variable *bounds*
   are being written into *confidence-interval* slots. And `FluxResult.value` is
   `required`, so an input `.tvar` with ~90 blank dependent rows cannot be loaded
   at all.
2. **The partition is a choice of basis, not a property of the solution.** The
   three `simple_model` round-trips fit the *same model to the same data* and
   agree on every fitted value and SD — but partition differently:
   `MTF_from_mtf` and `MTF_from_freeflux` give `R1/R2/R3` free with
   `E_out/F_out` dependent, while `MTF_from_fml` gives `R3/E_out/F_out` free with
   `R1/R2` dependent. influx_si's `--ffguess` re-derives it.

**Decision.** Add a first-class variable-specification structure, and store the
**input** partition and the **output** partition separately. They are not
comparable across tools, and a benchmark that treats them as comparable measures
the solver's basis choice rather than its answer.

### 13.6 The results layer is thinner than the tools' actual output

The schema's own contribution is meant to be the comparable results layer, so
these gaps matter most. All are present in real output files:

| Missing | Where it appears |
|---|---|
| **Per-measurement residuals and p-values** | `Residual` + `Pvalue` columns on `.miso.sim`, `.mflux.sim`, `.mmet.sim`, and on the recycled `toy.mflux` / `toy_calc.miso`. Measured-vs-fitted agreement per measurement is *the* benchmarking artifact, and no class has a slot for it |
| **`simulated_fluxes` / `simulated_pool_sizes`** | `FluxSolution` has `simulated_mids` but no flux or pool-size counterpart, so `.mflux.sim` and `.mmet.sim` have no home. Nor is there a simulated-NMR or simulated-cumomer channel for influx_si's `LAB_*` / `PEAK_*` rows |
| **Fitted measurement scale factors** | `.pres.csv` row `1:mass;F;111;108 = 1.0000000002`. These are genuine fitted parameters that count toward `number_of_parameters`; `MIDMeasurement.scale_method` records only the *method*. FluxML `scale="auto"` means "estimate a common scaling factor" — the estimate has nowhere to go |
| **Structural identifiability** | `.tvar.sim` `Struct_identif` (`yes`/`no`) |
| **`number_of_measurements`, `number_of_parameters`, fit verdict** | `.stat` carries all three plus a `conclusion` sentence; `GoodnessOfFit` has none. FreeFlux exposes `n_meas` / `n_params` / `dof` and an `is_success` flag |
| **Unweighted SSR** | `GoodnessOfFit` has WSSR, reduced χ², χ² p-value — no plain SSR ("MID loss") |
| **Confidence level** | CIs exist with no α. FreeFlux defaults to 0.95 for CIs and 0.999 for its χ² test |
| **Covariance / correlation, relative SD, MC ensemble** | influx_si's `.kvh` writes net-xch01, fwd-rev, and free-pool covariance matrices, `rsd` for every flux and pool, and a full Monte-Carlo block. FreeFlux exposes `hessian`, `null_space`, contribution and sensitivity matrices |
| **Run provenance: start/end time, runtime, convergence status, iteration count** | influx_si's `.log` carries the *actual* command line (which differs from `.opt`), timestamps, and a redundant-constraint elimination report. The INCA benchmark scripts' entire output is a wall-clock timing — and `dataset_type: benchmark` exists with nowhere to record it |
| **Reference / ground-truth solution** | for synthetic benchmarks the true fluxes are known; `FluxSolution` has no role distinguishing reference from estimated |
| **Solver options as a whole** | `.opt`'s `commandArgs` expands to 33 run parameters of which **27 have no mapping**. Six of them — `--cupx`, `--cupn`, `--cupp`, `--clownr`, `--cinout`, `--clowp` — are implicit bounds on *every* flux and pool and appear in no constraint file. INCA's `m.options` is a flat namespace of dozens of keys against 6 scalar slots. A generic key/value carrier is needed alongside first-class slots for the load-bearing few |

Two cautions surfaced by the audits, both of which invert a result if missed:

- influx_si's `.stat` `p-value` is `pchisq(chi2, df)` — a **lower**-tail
  probability, with the failure test `p > 0.95`. The conventional
  goodness-of-fit p-value is upper-tail. The slot description must state the
  convention.
- FreeFlux's `n_runs` is **not** `multistart_count`. Each run resamples every
  measurement from `N(mean, sd)` and re-solves — a parametric bootstrap, not a
  restart from a new initial point.

### 13.7 Measurement identity is under-specified

- **Measurements are expressions, not foreign keys.** FluxML `<group>` carries a
  formula (`Ala[2,3]#M0,1,2`), and `<netflux>` bodies are expressions over
  fluxes — `EC.fml:791` is literally `R63-R63b`. `<poolsize>` bodies may be
  expressions too. The schema forces a single metabolite or reaction reference,
  so `FluxMeasurement.reaction_id` cannot hold `R63-R63b`. The converter models
  all of these as `Group.expression`, `NetFlux.expression`,
  `MetaboliteSize.expression`. The original formula is also not retained
  anywhere, so two groups with the same spec under different ids
  (`EC.fml:696` / `:699`) round-trip only if the ids are preserved.
- **The MS fragment is a named entity.** INCA `Ala2: Ala @ 2 3`, FreeFlux
  `Glu_12345`, `model.json` `fragment_id`, `toy_model` `ms_id`. The schema has
  `metabolite_id` + `atom_positions` and no fragment identifier, so measured and
  simulated series cannot be matched by name. INCA's fragment suffixes are also
  *not* reliably replicate markers: `Ser2a`/`Ser2c` are both `Ser @ 2 3` but
  `Ser2b` is `Ser @ 1 2`. Deriving `replicate` from the suffix would silently
  corrupt that group.
- **Multi-isotope MS specs need tuple weights.** FluxML v3.0 writes
  `Ala[1-4]#M(3,0),(0,0),(1,0),…` and `<datum weight="2,1">` — 124 tuple-weight
  datums in `ecoli_model_level_3.fml`, 8 in `spirallus_model_level_3.fml`,
  19 distinct tuple values. `MIDDataPoint.isotopologue_index` is `range: integer`
  and **cannot hold `2,1`**. Position lists also mix ranges and commas
  (`Cit[1-3,5,6]`, `LEU[1-5,7]`), and weight lists need not start at 0
  (`Met#M1,2,3,4,5`).
- **A measured species can be a sum.** `toy.miso` and `toy.mmet` both carry
  `E+B` — the signal of a co-eluting or otherwise indistinguishable pool.
  `metabolite_id` is a single reference. This is ordinary analytical reality
  (isobaric overlap, pooled compartments), not an edge case.
- **`Isospecies` holds three notation families, and one fits no class.** Mass
  isotopomer (`M0`…`M9`) → `MIDDataPoint.isotopologue_index` ✓; NMR peak
  (`2->1,3`) → `NMRIsotopomerDataPoint` partially; but **isotopomer / cumomer
  patterns** (`010`, `1xx` with wildcards, and `+`-sums of patterns) belong to
  neither `MIDDataPoint` (index-based) nor `NMRIsotopomerDataPoint`
  (position+multiplet). `IsotopicStateSpaceEnum` has `cumomer`, but only as a
  *computation* setting on `SimulationRun`, never as a measurement representation.
- **The NMR multiplet descriptions are wrong for influx_si.** The schema says
  `S` = "carbon unlabeled, neighbors unlabeled"; FTBL's singlet is the *labeled*
  carbon with unlabeled neighbours. And `(position, multiplet_type)` is not
  round-trippable — the compatibility spec's own converter emits the same arrow
  string for `DD` and `T`, so coupled positions must be explicit. The five
  `NMRMultipletTypeEnum` values do match FluxML `<datum>@type` exactly.
- **A measurement file can be a template with no data.** `toy.miso` has
  `Value = NA` on every row: it declares *which observables exist* and their SDs,
  for forward simulation and identifiability analysis. INCA's `d.idvs = idv` and
  FreeFlux's `set_target_EMUs` do the same. There is no way to say "this
  observable is declared but unmeasured".
- **Error models are only on MID.** `<errormodel>` is legal on `<group>`,
  `<netflux>`, `<xchflux>` and `<poolsize>`; only `MIDMeasurement` has
  `error_model_expression`. INCA's `f.std = f.val/20` is likewise a *model*, not
  a value.
- **Natural-abundance correction is one boolean and one string.** The
  compatibility doc's §13 establishes that the correction's probability
  constant, strategy, error propagation, and — critically — whether the *tool*
  corrects internally (x3cflux does; freeflux, influx_si, cmfa do not) all change
  fitted fluxes; and that whether data is synthetic (no NA) or a real MS signal
  (NA included) decides whether a conversion is correct at all. FreeFlux's
  per-element `correct_for_natural_abundance(atom_dict)` and
  `correct_for_inoculum(fraction)` are likewise unrepresentable.

### 13.8 The schema is silently 13C-only

Nothing anywhere names the tracer element, yet FluxML v3.0 is explicitly
multi-element and ships models that use it:

- `<pool>@cfg` gives **per-element atom composition** — 43 distinct values across
  the corpus (`C3N1`, `C2N2`, `C0N1`, `N1`, `C6N4`, `C15N5`). There is no slot,
  and `n_tracked_atoms` lossily collapses `C3N1` to `4`.
- `cfg` on participants uses `Element#Position@MoleculeIndex`
  (`spirallus_model_level_3.fml:19` `cfg="C#1@1 N#2@1"`), so
  `AtomTransition` — which has indices but **no element** — collides C-position-1
  with N-position-1.
- `@purity` is `xs:string` and space-separated per element in v3.0
  (`purity="0.99 0.88"`). `TracerIsotopomer.isotopic_purity` is a single required
  float and cannot hold it.
- FreeFlux takes `set_labeling_strategy(..., label_atom='C')` with H/C/N
  supported; `MDV.base_atom` defaults to `'C'`; the converter's `AtomAddress`
  carries an `element` field. `FluxML_tests` ships `CN_network_model_BCG.fml`.

A 15N dataset is currently indistinguishable from a 13C one. The ontology
already has **FLUXO_0000132 "tracer element"**. Note also that
`n_tracked_atoms` is *optional* while `TracerIsotopomer.labeling_pattern` is
required with pattern `^[01xX]+$` — and that pattern cannot be derived from
INCA's or FreeFlux's position lists without the atom count.

### 13.9 Atom transitions: level, multiplicity, and dangling atoms

- **`AtomTransitionVariant` is at the wrong level.** In FluxML a `<variant>` is
  an alternative `cfg` **for one participant** (`<reduct>`/`<rproduct>`), not a
  variant of the reaction's whole transition set. `EC.fml:219-226` declares 2
  educt variants on `Suc` *and* 2 product variants on `Fum`, whose Cartesian
  product is the four flux ids in `<reaction id="R25___1 R25___2 R25___3
  R25___4">`. The schema is one level too shallow on the participant axis, and
  cannot express the product at all. Recommend a participant-scoped variant
  (`ParticipantCfgVariant` under `ReactionParticipant`).
- **Space-separated multi-ID reactions have no home.** `NetworkReaction.id` is a
  single identifier, but real files declare several fluxes in one element —
  `"R24___1 R24___2"`, `"R25___1 R25___2 R25___3 R25___4"`, `"sdh___1 … sdh___4"`,
  `"bsDAP___1 … bsDAP___4"` — and `<fluxvalue flux="R25___1" type="xch">`
  references them individually.
- **Three different conventions for the same scrambling.** FluxML inline
  `<variant>`; pre-expanded reactions plus a tie constraint (the `ecoli_model_*`
  files, `TCA8_v27___1/0.5=TCA8_v27___2/0.5`); and influx_si's duplicate
  reactions plus `NET v24_a - v24_b == 0` *and* its XCH twin. Round-tripping
  requires recording which convention was authoritative. Note also that
  `AtomTransitionVariant.ratio`'s documented "should sum to 1.0" is unmeetable
  for FreeFlux and INCA, and for FluxML's `EC`/`CN` variants, which carry no
  ratio at all.
- **Symmetry belongs on the metabolite.** INCA declares it once —
  `m.mets{'Suc'}.sym = list('rotate180', atommap('1:4 2:3 3:2 4:1'))` — and it
  applies everywhere Suc appears; FreeFlux uses comma notation `Suc(abcd,dcba)`.
  Reaction-level variants force re-declaration on every reaction the metabolite
  touches with no single source of truth; the compatibility spec devotes its §12
  to recommending exactly the metabolite-level structure the schema lacks.
  Ontology terms exist: **FLUXO_0000064 molecular symmetry**, **FLUXO_0000077
  symmetric atom transition**.
- **Repeated participants are ambiguous.** `V11: O (abcd) -> M (ab) + M (cd)`;
  INCA `Pyr (abc) + Pyr (def) -> ...`; `Ru5P + CO2 -> G3P (cde) + G3P (fba)`;
  `model.json`'s `{"E":{"a":1.0,"e":1.0}}`. FluxML encodes this as `@MoleculeIndex`
  (`C#1@2`) and the converter as `AtomAddress.instance`. `AtomTransition` keys
  its endpoints by metabolite reference only, so when a metabolite appears twice
  on one side there is no way to say which occurrence.
- **Dangling atoms cannot be expressed.** `AtomTransition` requires *both*
  `product_metabolite_id` and `product_atom_index`, but efflux reactions consume
  tracked atoms with no product at all — `spirallus_model_level_3.fml:53-56`
  (`f_out`, `<reduct cfg="N#1@1" id="F"/>`, no `<rproduct>`),
  `spirallus_model_level_1.fml:44-52`, `linea.fml:25-27`.
- **Stoichiometry has no FluxML source.** FluxML encodes multiplicity by
  repeating participants plus `@MoleculeIndex`; `ReactionParticipant.stoichiometry`
  defaults to 1.0 and the molecule index has no slot, so
  `spirallus_model_level_1.fml:30-34` cannot be reconstructed.
- **Reversibility is a boolean but influx_si has four arrow types.** `->`,
  `->>`, `<->`, `<->>`, where the doubled forms mean "net flux ≥ 0" and generate
  every `.cnstr.def` row (78 of them in `EC`).
- **No external/boundary flag, no unbalanced flag.** `<pool external="true"/>`,
  `_ext`/`.ext`/`.ex` suffixes, INCA `m.states{}.bal = false`, FreeFlux
  `set_unbalanced_metabolites` — all unrepresentable (`is_pseudo` is a different
  claim). The compatibility doc's own conversion function takes `is_external` as
  a required parameter, so the schema cannot supply an input its documented
  conversion needs. Neither concept has an ontology term.
- **`<pool>@size`** (default pool size) has no slot either.

### 13.10 Time is under-modelled in four ways

1. **No time unit — and FluxML supplies one that is being discarded.**
   `<mlabel><timeunit>s</timeunit>` (`EC.fml:682`, `Syn.fml:574`) and INCA's
   `m.options.sim_tunit = 'h'` are both dropped on the floor; FreeFlux uses
   seconds and its benchmark header is literally `time(s)`. (`Syn.m` even sets
   `int_tspan` in seconds while labelling `sim_tunit = 'h'` — the kind of error a
   typed slot would surface.) Ontology: **FLUXO_0000221 "time unit"**.
2. **A scalar `stop_time` cannot hold a time grid.** FluxML declares
   `<group>@times="0,0.5,…"` (9 values in `EC.fml:686`, 8 in `Syn.fml:611`,
   10 in `ecoli_model_level_2.fml:1195`), INCA `m.options.int_tspan`, FreeFlux
   `set_timepoints(...)` (which auto-prepends `t=0`). The grid is a model
   property, not derivable from measurement rows — and grid points with no datum
   are unrecoverable today.
3. **`time_point` sits on the measurement group, but the data is per-row.**
   FluxML repeats `@time` on each `<datum>` (1487× in `EC.fml`); one `.miso`
   `Dataset` spans nine time points; `EC_a_inst.miso` is 136 rows × 9 times. A
   9-timepoint × 6-weight FluxML group must explode into 9 `MIDMeasurement`
   objects with duplicated metabolite, positions, and scale — destroying group
   identity. The same defect applies to `FluxMeasurement.time_point`,
   `PoolSizeMeasurement.time_point`, and `NMRIsotopomerMeasurement.time_point`.
4. **`<configuration>@time`** (the nominal time point of a whole configuration)
   has no slot.

Unit placement is a related mismatch: FluxML declares `<fluxunit>`,
`<poolsizeunit>` and `<timeunit>` **once per `<measurement>`**, while the schema
repeats `flux_unit` and `pool_size_unit` on every measurement row.

### 13.11 Renames and enum changes — only where the current name misleads

| Current | Change | Why |
|---|---|---|
| `InputFormatEnum.freeflux_csv` | → `freeflux_tsv`, add `freeflux_xlsx` | FreeFlux's reader **raises `TypeError` on `.csv`**; it accepts only `.tsv` and Excel. The benchmark corpus is xlsx, the test corpus tsv |
| `InputFormatEnum` (the enum name) | → `FileFormatEnum` | it already types `SimulationRun.output_files` and `SourceFile.format` for outputs |
| `InputFormatEnum` — missing value | add `INCA_script` | every real INCA input is a `.m` MATLAB script; `INCA_mat` is the *results* container, so INCA models can only be `other` today |
| `AtomTransitionVariant` | → participant-scoped `ParticipantCfgVariant` | FluxML's `<variant>` belongs to a participant, not to the reaction (§13.9) |
| `FluxMeasurement.reaction_id` | add `flux_expression` (and keep `reaction_id` for the resolved single-reaction case) | the FluxML body is an expression: `R63-R63b` |
| `MIDDataPoint.weight` | → `msms_fragment_positions`, and correct the description | FluxML/FTBL `WEIGHT` **is** the isotopologue index — what `isotopologue_index` already holds — while the description points at a position list, which is what `atom_positions` holds. An importer following the docstring populates it wrongly |
| `MIDDataPoint.isotopologue_index` | widen to hold tuples | `weight="2,1"` (§13.7) |
| `SimulationRun.stop_time` | add `integration_timespan` (multivalued) | §13.10 |
| `SimulationRun.convergence_tolerance` | split out `integration_rel_tolerance` | INCA `int_reltol` is an ODE-integrator tolerance, not an optimizer tolerance. The three INCA benchmark files disagree on it by four orders of magnitude — a fairness parameter with nowhere to live |
| `MIDMeasurement.atom_positions` | → `fragment_positions`, multivalued integer, plus `fragment_id` | "atom positions" is not the community term for an MS fragment; every format parses it to a list |
| `MIDMeasurement.scale_method` | → `scale_type`, and **map it** | FluxML's attribute is `scale`; the ontology has **FLUXO_0000161 "groupscale"**, contradicting the plan's "no FLUXO term" claim. The `auto`/`one` values themselves match FluxML exactly — add `none` for influx_si `--noscale` |
| `AtomAnnotationTypeEnum.letter` / `.FluxML` | split `lowercase_letter` / `uppercase_letter`; replace `FluxML` with `element_position_molecule`; add `comma_variant`, `position_list`, `inca_atommap` | case is the only thing distinguishing influx_si's notation from everyone else's, and a value named after a format distinguishes nothing — FluxML uses letter notation in 1 file and `Element#Position@MoleculeIndex` in the other 10 |
| `FluxTypeEnum.exchange` | add `exchange_normalized`, and record `xch` as an alias | influx_si's `XCH` is **xch01 ∈ [0,1)** (proved by the generator's `clamp(vfl, 0, 1)`), while `edge.xchflux.attrs` holds the *un-normalized* exchange for the same reactions, and the schema documents `exchange` as `min(fwd, rev)`. Three quantities, one enum value — so `(reaction_id, flux_type)` is not a unique key. FluxML writes the literal `xch` 265 times |
| `IsotopicStateSpaceEnum` | add `auto` | the `<simulation>@method` default and the value in 14 of 15 real `<simulation>` elements |
| — | new `SimulationTypeEnum` = `auto` / `explicit` / `full` | `<simulation>@type` has no slot and no enum (`auto` 12×, `full` 2×) |
| — | new `ConstraintDomainEnum` = `net` / `xch` / `psize`/`METAB` | the domain axis of §13.3, orthogonal to `ConstraintTypeEnum` |
| — | new `TracerElementEnum`, `OptimizationMethodEnum`, `RunModeEnum`, `VariableTypeEnum` (F/C/D), `VariableKindEnum` (NET/XCH/METAB) | §13.5, §13.8; observed optimizers are `nlsic`, `BFGS`, `Nelder-Mead`, `SANN`, `ipopt`, `pso` (influx_si) and `slsqp`, `ralg`, `glpk` (FreeFlux) |
| `FluxomicsMethodEnum` | add a forward-simulation value, and `FVA` | the **entire benchmark suite** — all three INCA scripts and all three FreeFlux drivers — is forward simulation with fixed fluxes, and is untypeable today. Ontology: **FLUXO_0000087 labeling simulation** |
| `ConfidenceIntervalMethodEnum` | add `linearized`/Fisherian and `monte_carlo` | the linearised covariance method is the **default** in both FreeFlux and INCA and has no value at all; influx_si's `--sens mc` is neither `bootstrap` nor `profile_likelihood` |
| `AnalyticalMethodEnum` | add `not_specified` | see §13.1 — no format supplies one |
| `ReactionTypeEnum` | add `drain`, `biomass_precursor`, `symmetry_variant`, `dummy` | converter-generated `{met}_out`, influx_si `bs_*`, split `fum_a`/`fum_b`, INCA `Dummy -> Dummy.ext` |
| `FileRoleEnum` | add `initial_values`/`parameters`, `variable_classification`, `batch`, `report`, `bundle`, `role_other` | FreeFlux `fluxes.tsv`/`concentrations.tsv` are preset parameter values, not constraints; `.tvar` is a classification; `.vmtf` is a batch; a `.fml` is a bundle |
| — | add a `pathway` slot on `NetworkReaction`/`NetworkMetabolite` | `<annotation name="pathway">` occurs **604×** — the most common annotation in the corpus — and FreeFlux `reactions.xlsx` carries `#Glycolysis`-style section rows. Also unmapped: `<annotation name="indexes">` (atom-index mapping into the InChI) and `name` |

**Keep, with aliases documented:** `reactants` (vs FreeFlux/FluxML "substrates" —
the benchmark's own two `reactions.xlsx` files disagree with each other),
`pool_size` (vs "concentration"), `MID` (vs FreeFlux "MDV"), `tracer_fraction`
(vs `percentage` / `ratio` / `tracer_enrichments`), `LabeledSource` (vs
"labeling input"), `n_tracked_atoms` (vs FluxML `atoms`), `reversibility` (vs
`bidirectional`), `AtomTransitionVariant.ratio` (matches FluxML's attribute,
which outranks the compatibility doc's draft `probability`).

Also unmapped and worth a home: FluxML `<info><version>`, `<date>` (with its
time component — `FluxoDataset.creation_date` is `range: date` and
dataset-scoped), `<comment>` (`Syn.fml:6-19` embeds three DOIs;
`MetabolicNetworkModel` has no description slot at all), and `<signature>`; the
`<mixture>` alternate root (`mixture.fml` is a complete valid document with two
`<input>` elements for the *same* pool, which would collide on
`LabeledSource.metabolite_id`); and `<mlabel>`/`<dlabel>` provenance blocks.

### 13.12 ~~Regression~~ — **withdrawn 2026-09-18: this finding was wrong**

This section originally reported that the working tree had "silently dropped"
Phase 3q/3r content still present in `HEAD`, and instructed: *"Restore all of it
before adding anything new."* That instruction was wrong and has been followed
by nobody; it is withdrawn.

**What actually happened.** The audit was written 2026-08-19, when `HEAD` was
`17487dc` (2026-07-22), which did contain the listed content. On 2026-08-24,
commit `160086d` removed it **deliberately**. The working tree has matched
`HEAD` ever since — `git diff HEAD -- enumerations.yaml investigation.yaml` is
empty. There was never a working-tree-versus-`HEAD` divergence; the audit simply
predated the decision.

**The removals, and why.** Recorded in IMPLEMENTATION_PLAN.md §3t-0:

- `AerationEnum`, `CultivationModeEnum`, and the five `Condition` slots —
  cultivation-process detail, out of scope for fluxomics.
- The three `AnalyticalMethodEnum` NMR sub-types — the NMR attribute set is
  unsettled; generic `NMR` and the NMR classes remain.
- `MFASoftwareEnum`: `COBRApy`, `cameo` — not MFA software.
- `FluxomicsMethodEnum`: `MFA` (FLUXO_0000040) — correct, though not for the
  reason given at the time: FLUXO:0000040 is `is_a` *fluxomics investigation*,
  not a method.

**What the finding got right.** Two of the three self-contradictions it named
were real and are now fixed (2026-09-18): the `fluxolink.yaml` COBRApy claim,
and `NMRIsotopomerMeasurement.analytical_method` promising sub-types the enum
does not carry. The third — `VALIDATION_REQUIREMENTS.md` referring to a
`fluxomics_method` value `13C` — is still open; the correct value is `C13_MFA`,
and it folds into the §13.13/3t-13 rewrite.

**The lesson worth keeping.** An enum with no membership rule drifts silently.
`FluxomicsMethodEnum` is now defined as exactly the `FLUXO:0000021` subtree and
pinned by `TestOntologyScopedEnums`, so the next drift fails a test rather than
producing a phantom regression report.

### 13.13 Several proposed additions already have FLUXO terms

The plan's §3h "no FLUXO term, left unmapped" list is partly wrong, and much of
what §13 proposes can be grounded immediately (321 FLUXO classes checked):

- **Corrections to "unmapped" claims:** `ConfidenceIntervalMethodEnum` →
  FLUXO_0000302 (parent), 0000305 profile likelihood, 0000304 parametric
  bootstrap, 0000303 Fisherian, 0000306 MCMC — and 0000303 is precisely the
  linearised method §13.11 adds; `scale_method` → FLUXO_0000161 groupscale;
  `FluxRatioMeasurement` → FLUXO_0000029 flux ratio; `MIDDataPoint.weight` →
  FLUXO_0000054 tandem isotopologue distribution.
- **Terms available for new slots:** FLUXO_0000132 tracer element ·
  FLUXO_0000221 time unit · FLUXO_0000064 molecular symmetry + 0000077 symmetric
  atom transition · FLUXO_0000264 sample · FLUXO_0000292 technical replicate and
  FLUXO_0000293 biological replicate (the schema's single `replicate` integer
  conflates two distinct terms, and `NMRIsotopomerMeasurement` lacks it
  entirely) · FLUXO_0000080 tracer chemical purity (distinct from 0000139
  isotopic purity, which is what the schema uses) · FLUXO_0000090 **simulated
  isotopic measurement** — an exact term for the dedicated simulated-MID class
  §13.2 calls for · FLUXO_0000087 labeling simulation vs 0000088 flux estimation
  for a run-mode slot · FLUXO_0000297 file path, 0000296 file name, 0000288
  checksum for the unmapped `SourceFile` slots · FLUXO_0000289/0000290/0000291
  data-file quality (raw vs processed) · FLUXO_0000275/0000283 corrected vs
  uncorrected isotopologue distribution · FLUXO_0000082/0000160/0000210
  fluxomics parameter, for the solver-option carrier · FLUXO_0000046/0000047/
  0000097 experiment design, for the OED activity and FluxML's `edweight` ·
  FLUXO_0000130 relative exchange flux, for the xch01 distinction.
- **Genuinely absent, so new-term requests:** free/dependent/constrained
  variable classification; external/boundary metabolite; unbalanced metabolite;
  MS fragment as an entity; per-measurement residual; optimization method /
  solver; aeration, temperature, pH, genotype, cultivation mode; NMR multiplet
  types; dataset curation tier; configuration.

### 13.14 Consequence for the benchmark workflow (§11) and the CLI (§12)

§11's five-step workflow survives, with two amendments.

- **Step 1 ("author the EC ground truth once as a Tier-2-complete
  `FluxoDataset`") is not yet possible.** `EC.fml`'s four configurations over one
  network need the `Configuration` concept and per-configuration constraints and
  variables (§13.4, §13.5); its biomass and scrambling couplings need standalone
  linear constraints (§13.3); its participant-level `<variant>` sets and
  multi-ID reactions need §13.9; and its `<datum weight>`/`@times`/`<timeunit>`
  content needs §13.7 and §13.10. **Phase 3t is a prerequisite for the EC
  dataset, not a follow-up to it.**
- **Step 5 ("parse any tool-edited file and diff it against the declared
  truth") is weaker than it looks.** The three `simple_model` round-trips show
  that the free/dependent partition — and therefore `.tvar`'s entire `Type`
  column — changes with the *upstream format* while the fitted solution does not.
  The equivalence diff must normalise the partition away rather than compare it.
  And influx_si's six global default-bound flags are implicit constraints on
  every flux and pool that appear in **no** constraint file: two runs differing
  only in those flags are solving different problems while looking identical in
  the dataset.

For §12's CLI, the tiering decision in §13.1 changes one thing: `fluxo ingest`
should succeed for a catalog dataset without a `--meta` sidecar, and require it
only under `--benchmark`. `fluxo validate --benchmark` becomes the gate where the
strict rules apply.

### 13.15 Empirical check: eight encodings of four formats (2026-08-24)

§§13.1–13.14 were derived by reading. This section records what happened when
four corpora — one per format — were each actually encoded as a `FluxoDataset`
**two ways**: Tier-2 "materialise the content" and Tier-1 "record the dataset".
All eight validate cleanly. The fixtures are in `examples/valid/` and carry
inline `LOST` / `FABRICATED` markers at every point of information loss.

| Format | Encoding | Source | Lines | LOST | FABRIC |
|---|---|---|---|---|---|
| influx_si MTF | `simple_model_mtf_roundtrip.yaml` | 11 files, inputs + solver output | 517 | 13 | 7 |
| influx_si MTF | `simple_model_mtf_catalog.yaml` | same, references only | 266 | 5 | 3 |
| FluxML | `linea_fluxml_materialised.yaml` | `benchmark/FluxML/linea.fml` (56 lines) | 172 | 9 | 5 |
| FluxML | `linea_fluxml_catalog.yaml` | same, references only | 143 | 3 | 3 |
| FreeFlux | `simple_model_freeflux_materialised.yaml` | 4 TSVs, same model as the MTF set | 338 | 6 | 5 |
| FreeFlux | `simple_model_freeflux_catalog.yaml` | same, references only | 108 | 1 | 1 |
| INCA | `ec_inca_materialised_slice.yaml` | slice of `benchmark/INCA/EC.m` | 267 | 13 | 6 |
| INCA | `ec_inca_catalog.yaml` | same, references only | 104 | 8 | 3 |

The INCA Tier-2 fixture is a deliberate **slice** — EC.m has 68 reactions, ~66
derived metabolites and 33 fragments, and hand-encoding all of it adds bulk
without adding findings. The slice keeps exactly the constructs that stress the
schema; every marker in it applies to the full model equally.

**All four formats round-trip at Tier 2, with the predicted losses.** The
predictions in §13.2, §13.3, §13.5, §13.7, §13.9 and §13.10 all reproduced.
Three were confirmed by direct probe against the generated Pydantic model rather
than by inspection: `aliases=["influx_si:R1","freeflux:R1"]` is **rejected**
(single-valued); `MIDDataPoint` without a standard deviation is **rejected**; and
the real `.miso.sim` value `-3.75106667415865e-09` is **rejected** by
`minimum_value: 0.0`, as is a raw MS intensity above 1.0.

#### The repeated-participant defect, in ascending severity

§13.9 predicted that participants have no occurrence index. Encoding all four
formats shows this is not one defect but three, and the third is the worst:

1. **MTF `R5`** (`B (dab) + C (ce) ->> D (abc) + E (d) + E (e)`) and **FreeFlux
   `R5`** (`B(abc)+C(de) -> D(bcd)+E(a)+E(e)`) — `E` appears twice as a
   *product*. Two of the five atom transitions become byte-identical rows,
   `(E, 0)` and `(E, 0)`. Verified live: 5 transitions, 1 distinct product key
   among the two E rows. Lossy but detectable.
2. **FluxML `linea.fml` v3** (`<reduct id="B" cfg="a"/>` with no `<rproduct>`)
   and **FreeFlux `E_out`/`F_out`** (empty product column) — a tracked atom
   leaves the system. `AtomTransition` requires *both* product fields, so the
   transition cannot be written at all; the variant must be omitted, silently
   dropping the only atom-level fact about the reaction.
3. **INCA `v51`** (`Pyr (abc) + Pyr (def) + Glu (ghijk) -> Val (abcef) + CO2 (d)
   + AKG (ghijk)`) — `Pyr` appears twice as a *reactant*, and here the encoding
   is **not merely lossy but internally contradictory**. Molecule 1 contributes
   `abc`, molecule 2 contributes `def`; collapsing both to "Pyr" makes the
   document assert that Pyr atom 1 maps to **both** `Val` atom 1 **and** `CO2`
   atom 1 — impossible for a single molecule. A consumer can neither recover the
   true mapping nor detect that what it read is inconsistent. This is the
   strongest argument in the whole audit for the occurrence index in 3t-9.

#### Two new findings the reading pass missed

**A. `dataset_type: catalog` is not expressible — the Tier-1 tier is decorative.**
`SimulationRun.network_model_id` is `required: true` with range
`MetabolicNetworkModel`, and `MetabolicNetworkModel` requires ≥1 metabolite and
≥1 reaction with ≥1 reactant. So a dataset that references native files instead
of re-describing them **cannot carry a `SimulationRun` at all** — the only
reason the tier exists. Verified: the minimal catalog probe fails with
`'network_model_id' is a required property`. All four catalog fixtures therefore
contain a **fabricated placeholder network** whose sole purpose is to satisfy
that slot. This belongs with 3t-1, and it means `DatasetTypeEnum` cannot serve
as the two-tier enforcement mechanism (3s-5) until it is fixed.

> **✅ FIXED — 2026-08-24.** `SimulationRun.network_model_id` is now
> `recommended: true`, and `FluxoDataset` carries a `rules:` block
> (`benchmark_tier_requires_input_ground_truth`) that requires `networks` and
> `experiments` when `dataset_type == benchmark`. The four catalog fixtures no
> longer contain a placeholder network — the stubs are deleted, not merely
> annotated. Two regression tests guard it in `tests/test_examples.py`, and
> `examples/invalid/benchmark_tier_missing_inputs.yaml` is the negative case.
> `DatasetTypeEnum` is now load-bearing rather than decorative.
>
> **However — a design assumption behind 3t-1 turned out to be wrong.** LinkML
> `slot_conditions` **cannot nest**: a `SlotDefinition` inside a rule's
> `slot_conditions` has no `slot_conditions` of its own (`gen-json-schema`
> fails with `SlotDefinition.__init__() got an unexpected keyword argument
> 'slot_conditions'`). A rule on `FluxoDataset` can therefore only require the
> *presence of blocks* — it cannot reach down and re-impose
> `Condition.specific_growth_rate` or `TracerIsotopomer.isotopic_purity`,
> because `dataset_type` is not visible from those classes. Field-level tier
> strictness must be an **external validator** (the `fluxo validate
> --benchmark` gate of Phase 7), not a LinkML rule. See 3t-1.

**B. At the catalog tier every `FluxResult` is a dangling reference.**
`FluxResult.reaction_id` has range `NetworkReaction`, so results can only name
reactions in a materialised network. Naming the real ids against a placeholder
network **validates today** — LinkML's JSON-Schema validation does not check
referential integrity — but it is exactly what the planned Phase 5
referential-integrity rule (§5, VALIDATION_REQUIREMENTS §3) is specified to
reject. The comparable results layer and the catalog tier are on a collision
course: satisfying one breaks the other.

#### Runnability: can a catalog record re-invoke the tool?

`scripts/check_runnable.py` resolves the tool from `software.software_name`,
compares `input_files` against that tool's mandatory inputs, and reports what it
cannot determine. **27 unresolvable items** across the four catalog fixtures.
The pattern differs sharply by format, and the ranking is the opposite of what
Path B assumed:

- **influx_si — closest to runnable.** All three mandatory roles are present.
  But `role: measurements` is claimed by both `.miso` and `.mflux`, so the
  mandatory MID file cannot be identified without parsing extensions; and the
  `--prefix` the tool is invoked with is not a declared field, recoverable here
  only because every path happens to share a stem.
- **FluxML — one file, five roles.** `SourceFile.role` is single-valued.
  Declaring `linea.fml` once leaves the run unable to assert a network is
  present; declaring it five times (as `source_files` does) presents one
  1920-byte file as five files sharing a checksum. Neither states the actual
  fact. With no experiment recorded there is also nothing to name *which*
  `<configuration>` to run, nor to carry `stationary="false"`.
- **FreeFlux — the file set is genuinely unrunnable, and the schema cannot say
  so.** There is no tracer file at all: FreeFlux sets the labeling strategy via
  `set_labeling_strategy()` in Python. `role: tracer` is simply *absent*, which
  is indistinguishable from "not recorded". The driver `.py` that supplies the
  tracer, bounds, `n_runs`, solver and tolerance has no `FileRoleEnum` value, so
  the one artefact that would make the dataset runnable cannot be referenced.
  This is the format where Tier-1 recording fails hardest — precisely because
  Path B assumed native files are self-sufficient, and for FreeFlux they never
  are.
- **INCA — the "dataset" is executable code.** One `.m` file is network, tracer,
  measurements, flux data, solver options *and* the invocation. It can only be
  typed `format: other` (`INCA_mat` is the binary results container). Referencing
  it records that it exists and nothing about what it does — in particular
  nothing records that `EC.m` calls `simulate()` nine times in a timing loop and
  never calls `estimate()`, so `optimization_method` is not merely fabricated but
  **contradicted by the source**. The same is true of the MTF fixture, whose
  `.log` shows `--noopt`.
- **All four.** No slot holds the invocation (`command_line`), the run mode, the
  solver flags, or the INST time grid.
- **A run that never ran is indistinguishable from one whose results were never
  extracted.** Three of the four corpora (FluxML, FreeFlux, INCA) contain no
  results at all, and the schema accepts a `SimulationRun` with an empty solution
  without comment.

#### What this changes in the plan

Nothing in Phase 3t is invalidated and its ordering is confirmed. The blockers
that stopped these encodings being faithful are exactly 3t-1 (required-field
tiering — the source of every `FABRICATED` value), 3t-2 (role multiplicity,
`aliases` multiplicity, value ranges), 3t-4 (the `Configuration` concept) and
3t-9 (the occurrence index). Fold finding **A** into 3t-1 and finding **B** into
3t-2. Three items gain concrete backing they previously lacked: 3t-6's
`command_line` / `run_mode` / `solver_options` are now demonstrated runnability
failures rather than inferred ones; 3t-9's occurrence index is now known to
produce *contradictory* output, not just lossy output; and `FileRoleEnum` needs a
**driver-script** value (FreeFlux `.py`, INCA `.m`) that 3t-11 did not list.

### 13.16 Query check: stationarity and tracer design (2026-08-24)

Two questions asked of the eight §13.15 fixtures, answered with
`scripts/query_tracers.py` plus six deliberately-broken probes.

#### Q1 — "is this experiment stationary or instationary?" Recordable, **not validatable**

`LabelingExperiment.stationary` is a required boolean, so the fact is always
*present* at Tier 2 and the query is trivially answerable. But nothing checks it,
and the root cause is that **stationarity is encoded twice, independently**:
`LabelingExperiment.stationary` and `SimulationRun.fluxomics_method`
(`IST_MFA` / `INST_MFA`). There is no consistency rule between them.

All of the following validate cleanly (`No issues found`):

| Probe | What it asserts |
|---|---|
| P1 | `stationary: true` **and** `fluxomics_method: INST_MFA` — a direct contradiction |
| P2 | `stationary: false` with no `time_point` on any measurement and no `stop_time` |
| P3 | `stationary: true` while every measurement carries `time_point: 1.0` |

So the schema will happily state that one experiment is both stationary and
instationary, and will accept an INST experiment with no time dimension at all.
The rules that would catch this are the Phase-5 cross-slot rules deferred in 3j
("if `stationary == false` then `time_point` required", "… then `stop_time`
required"), and they do not yet include the one that matters most here: a
**consistency rule between `stationary` and `fluxomics_method`**. That rule is new —
neither 3j nor 3t listed it.

The redundancy is worth resolving rather than policing. `fluxomics_method` is required
on the run and `stationary` is required on the experiment, so every isotope
dataset states the same fact twice in two places that can drift. Either derive
one from the other, or keep both and add the rule.

At the **catalog tier the question is simply unanswerable** — with no
`LabelingExperiment` there is nowhere to record stationarity, and for FreeFlux
the fact lives only in *which filename was read* (`measured_MDVs.tsv` vs
`measured_inst_MDVs.tsv`), which `SourceFile` cannot express.

#### Q2 — "are there multiple tracers, and at what positions?" Largely **yes**

This is the schema working as intended. Three genuinely different senses of
"multiple tracers" are structurally distinct and all three round-trip:

| Sense | Encoding | Exercised by |
|---|---|---|
| **mixture** — one substrate, several labelled forms | several `TracerIsotopomer` in one `LabeledSource` | `linea.fml` (0.1 unlabelled / 0.9 [1-13C]); INCA `t.frac = [0.75, 0.25]` |
| **sources** — several labelled substrates | several `LabeledSource` in one experiment | available; not used by these corpora |
| **parallel** — several experiments jointly fitted | multivalued `SimulationRun.experiment_id` (FLUXO_0000050) | probe P6, validates |

Positions are recoverable: `labeling_pattern` is a 1-based positional string, so
`"100000"` decodes to position 1 and `"111111"` to positions 1–6. The query tool
reports them directly, including INCA's two-form glucose mixture.

Four limits, in descending importance:

1. **The labelled element is unrecorded.** `"100000"` says *which position* but
   never *which isotope*. A ¹⁵N experiment is indistinguishable from a ¹³C one —
   §13.8, and the reason `TracerElementEnum` is in 3t-8.
2. **Pattern length is not checked against `n_tracked_atoms`.** Probe P4 puts a
   4-character pattern on a 1-atom metabolite and validates cleanly, so the
   decoded positions 2 and 3 are meaningless. The check is trivially
   computable — the query tool performs it — but the schema declines to.
3. **Fractions are not summed.** Probe P5 has two forms summing to **1.6** and
   validates. `tracer_fraction` bounds each value to [0, 1] individually and
   nothing constrains the total, even though the slot description says it should
   be ≤ 1.0 and influx_si requires exactly 1.0.
4. **Tracer names are unrecorded.** INCA's `1-13C_Gluc` / `U-13C_Gluc` and
   `toy_model`'s `[2-13C]A` have nowhere to go, so a tracer cannot be referred to
   by the label its own tool uses, nor reused across experiments (3t-7).

At the catalog tier this question is also unanswerable — the tracer design lives
entirely in the referenced files.

#### Consequence for the plan

One new Phase-5 rule: **`stationary` must agree with `fluxomics_method`**. Two existing
3t items gain a cheap, high-value validation each, both demonstrated by a
validating probe rather than argued: pattern-length-vs-`n_tracked_atoms` (3t-8
item 5) and tracer-fraction-sum (already in 3j's deferred list, now shown to be
silently violable). Nothing here changes the 3t ordering.
