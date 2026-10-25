# FluxoLink

A LinkML data model for metabolic flux analysis (MFA) investigations, grounded in the [FLUXO ontology](https://purl.obolibrary.org/obo/fluxo/).

## Overview

FluxoLink provides a structured, ontology-compliant schema for curating experimental data, metabolic network models, simulation parameters, and flux solutions. It covers **isotope-based MFA** (13C-MFA, IST-MFA, INST-MFA) and **stoichiometry-based methods** (FBA), and supports data from tools such as **freeflux**, **13CFLUX2**, **influx_si**, **INCA**, and **COBRApy**.

## Architecture

```
FLUXO Ontology (semantics) → LinkML Schema (structure) → fluxomics_converter (translation)
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
| `simulation_run.yaml` | Simulation runs (software, flux solutions, goodness-of-fit)                                    |

A `FluxoDataset` aggregates flat collections of `investigations`, `networks`, `experiments`, and `simulation_runs`, cross-linked by identifier references. A single dataset can hold multiple methods — e.g., an FBA run and a 13C-MFA run over the same network.

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

Hand-authored datasets (which double as validation fixtures) live under `examples/`:

- `examples/valid/simple_model_dataset.yaml` — the `simple_model` benchmark (6-metabolite network) with a 13C-MFA run and an FBA run on the same network.
- `examples/valid/nmr_dataset.yaml` — a 13C NMR isotopomer (multiplet) measurement dataset.
- `examples/invalid/missing_required_fields.yaml` — a deliberately-broken dataset used for negative validation tests.

`tests/test_examples.py` validates all of these via the `linkml-validate` CLI.

### Pre-commit hooks

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## License

Apache 2.0
