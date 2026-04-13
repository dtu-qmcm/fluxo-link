# FLUXO Schema

A LinkML data model for 13C-Metabolic Flux Analysis (13C-MFA) simulation studies, grounded in the [FLUXO ontology](https://purl.obolibrary.org/obo/fluxo/).

## Overview

FLUXO Schema provides a structured, ontology-compliant schema for curating experimental data, metabolic network models, simulation parameters, and flux solutions from tools such as **freeflux**, **13CFLUX2**, **influx_si**, and **INCA**.

## Architecture

```
FLUXO Ontology (semantics) → LinkML Schema (structure) → fluxomics_converter (computation)
```

The LinkML schema serves as the interface layer between the ontology (what concepts mean) and the computation library (what data does).

## Schema Modules

| Module | Description |
|---|---|
| `fluxo_schema.yaml` | Main schema with imports |
| `enumerations.yaml` | Semantic enums backed by FLUXO ontology terms |
| `study.yaml` | Study provenance (contributors, organism, publication) |
| `network.yaml` | Metabolic network model (metabolites, reactions, atom transitions) |
| `experiment.yaml` | Labeling experiments (tracers, MID measurements) |
| `simulation_run.yaml` | Simulation runs (software, flux solutions, goodness-of-fit) |

## Installation

```bash
uv pip install -e ".[dev]"
```

## Development

### Install dependencies

```bash
uv sync --extra dev
```

### Run tests

```bash
uv run pytest
```

### Lint

```bash
uv run ruff check src tests
uv run ruff format --check src tests
```

### Pre-commit hooks

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## License

Apache 2.0
