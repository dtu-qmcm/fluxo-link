# FluxoLink

A LinkML data model for metabolic flux analysis (MFA) investigations, grounded in the [FLUXO ontology](https://github.com/dtu-qmcm/fluxo).

## Overview

FluxoLink provides a structured, ontology-compliant schema for curating experimental data, metabolic network models, simulation parameters, and flux solutions. It covers **isotope-based MFA** (13C-MFA, IST-MFA, INST-MFA) and **stoichiometry-based methods** (FBA), and supports data from tools such as **freeflux**, **13CFLUX2**, **influx_si**, **INCA**, and **COBRApy**.

## Architecture

```
FLUXO Ontology (semantics) → LinkML Schema (structure) → fluxomics_data_converter (translation) → fluxomics software (computation)
```

The LinkML schema serves as the interface layer between the ontology (what concepts mean) and the computation library (what data does).

## Schema Modules

| Module                  | Description                                                                                    |
| ----------------------- | ---------------------------------------------------------------------------------------------- |
| `fluxolink.yaml`      | Main schema with imports; defines the `FluxoDataset` root container (`tree_root`)          |
| `enumerations.yaml`   | Semantic enums backed by FLUXO ontology terms                                                  |
| `investigation.yaml`  | Investigation provenance (contributors, investigation type, publication)                       |
| `network.yaml`        | Metabolic network model (metabolites, reactions, atom transitions, flux/pool-size constraints) |
| `experiment.yaml`     | Labeling experiments (tracers, MID / NMR / flux / pool-size measurements)                      |
| `simulation_run.yaml` | Simulation runs (software, settings, variable specification, results, residuals, goodness-of-fit) |

A `FluxoDataset` aggregates flat collections of `source_files`, `conditions`, `investigations`, `networks`, `experiments`, and `simulation_runs`, cross-linked by identifier references. A single dataset can hold multiple methods — e.g., an FBA run and a 13C-MFA run over the same network — and multiple tools run on the same problem.

One FluxML `<configuration>` is one `LabelingExperiment` (`configuration_name`), so a file such as `EC.fml` with four configurations becomes four experiments over one network. A configuration's `<simulation>` block becomes a `SimulationRun` with `run_status: planned`. A run records what the tool did (`run_mode`), how it was invoked (`command_line`, `solver_options`), its variable specification (free/dependent/constrained), and its results: fluxes, pool sizes, simulated MIDs, per-measurement residuals, scale factors and goodness of fit.

## Tiers

| `dataset_type` | What it promises |
|---|---|
| `catalog` (or absent) | Results plus file-level provenance. Input content may stay in the referenced native files, and network/experiment detail is optional. |
| `benchmark` | Input ground truth complete enough to regenerate every tool's input: materialised network, tracer fractions and purities, MID values with SDs, software versions, and the cultivation condition when the data are experimental (`data_origin`). |

The schema keeps the strict fields `recommended`, so files from any tool can be represented. `fluxolink-validate` re-imposes them at the benchmark tier. See [VALIDATION_REQUIREMENTS.md](VALIDATION_REQUIREMENTS.md).

## Validation

```bash
uv run fluxolink-validate dataset.yaml              # schema + references + consistency
uv run fluxolink-validate dataset.yaml --benchmark  # also the benchmark-tier requirements
```

`fluxolink-validate` runs LinkML schema validation first, then checks what LinkML cannot:
- references between objects resolve;
- `stationary` agrees with `fluxomics_method`;
- tracer fractions do not sum above 1;
- labeling patterns match the molecule's size;
- no atom is mapped to two places;
- confidence intervals contain their value;
- the tier rules hold.

It exits non-zero on errors and can be called from Python (`fluxolink.validate.validate_dataset`).

## Linking tool formats

A dataset records each tool's native input files once, as `source_files`. A file generated
from another one says so in `derived_from`. `equivalence_checks` record the result of
re-parsing an encoding and comparing it with the dataset's network and experiments, or with
other files. It lists the unexpected differences and the ones the generator introduces by
design, so you can see whether the MTF, FreeFlux and FluxML inputs given to different tools
still describe the same problem. The converter's `fluxo convert` writes these records.

## Core profile and database table

Most of the schema is optional detail. The **core profile**, 59 fields in 12 classes, is the
minimal record most datasets should fill and a database should index. It covers the study,
cultivation, tracer design, method and software, flux results with uncertainty, and source
files. [docs/core_profile.md](docs/core_profile.md) is generated from the schema's `core`
subset and ends with a complete minimal record
(`examples/valid/minimal_core_record.yaml`).

For a database, keep the dataset documents as they are (JSON/YAML) and index a flat table
with one row per run × reaction × flux type, plus its study context:

```bash
uv run fluxolink-flatten datasets/*.yaml -o fluxes.tsv   # or .csv / .jsonl
just gen-sql                                             # SQL DDL -> docs/flux_record.sql
```

The columns are defined by `src/fluxolink/schema/flux_record.yaml`. The table is rebuilt
from the documents, which stay the record of truth.

## Installation

```bash
uv sync --extra dev
```

## Development

The repository ships a `justfile` with common tasks (install `just` with `uv tool install rust-just`):

| Target                     | Action                                                             |
| -------------------------- | ------------------------------------------------------------------ |
| `just gen-pydantic`      | Regenerate the Pydantic datamodel from the schema                  |
| `just validate-examples` | Validate `examples/valid/*.yaml` against the schema              |
| `just check-examples`    | Schema + semantic checks (`fluxolink-validate`) on every example   |
| `just core-profile`      | Regenerate `docs/core_profile.md` from the `core` subset           |
| `just gen-sql`           | SQL DDL for the flat flux table (`docs/flux_record.sql`)           |
| `just erd`               | Regenerate the draw.io ER diagram in `docs/diagrams/`              |
| `just test`              | Run the test suite                                                 |
| `just lint`              | Ruff check + format-check                                          |
| `just schema-lint`       | Lint the LinkML schema itself                                      |
| `just gen`               | Generate full project artifacts (jsonschema, owl, erdiagram, docs) |
| `just doc`               | Generate HTML documentation                                        |

Equivalent commands without `just`:

```bash
uv run pytest                                                   # tests
uv run ruff check src tests && uv run ruff format --check src tests   # lint
uv run gen-pydantic src/fluxolink/schema/fluxolink.yaml > src/fluxolink/datamodel/fluxolink.py
uv run linkml-validate -s src/fluxolink/schema/fluxolink.yaml examples/valid/simple_model_dataset.yaml
```

### Generated datamodel

The Pydantic classes live at `src/fluxolink/datamodel/fluxolink.py` and are importable:

```python
from fluxolink.datamodel.fluxolink import FluxoDataset, Investigation, SimulationRun
```

Regenerate them with `just gen-pydantic` whenever the schema changes.

## Examples

Datasets under `examples/` double as validation fixtures:

- **Encodings of real corpus files**, each made two ways: materialising the content, and cataloguing the files. Inline `LOST` comments mark what the schema still cannot hold.
  - `simple_model_mtf_roundtrip.yaml` / `simple_model_mtf_catalog.yaml` — influx_si inputs plus solver output (forward simulation, residuals, goodness of fit).
  - `simple_model_freeflux_materialised.yaml` / `_catalog.yaml` — FreeFlux tables plus the driver notebook.
  - `linea_fluxml_materialised.yaml` / `_catalog.yaml` — a FluxML v3 file with a dangling atom.
  - `ec_inca_materialised_slice.yaml` / `ec_inca_catalog.yaml` — the INCA EC benchmark script: repeated participants, metabolite symmetry, tracer names.
- **Illustrative datasets**: `simple_model_dataset.yaml` (a 13C-MFA run and an FBA run on one network), `nmr_dataset.yaml` (NMR multiplets) and `fba_benchmark_no_experiment.yaml` (a benchmark with no labeling experiment).
- **Benchmark**: `examples/benchmark/ec_fluxml_benchmark.yaml` — the complete EC model generated from `EC.fml` by the converter: four configurations, every reaction, tracer and measurement.
- **Negative cases**: `examples/invalid/*.yaml`.

`tests/test_examples.py` runs `linkml-validate` on all of these, and `tests/test_validate.py` runs the semantic checks.

### Pre-commit hooks

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## License

Apache 2.0
