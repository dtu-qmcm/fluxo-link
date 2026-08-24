# AGENT.md — FluxoLink Project

This file describes the project conventions, tools, and workflow for AI coding agents working on this repository.

## Project Identity

- **Name:** `fluxolink`
- **Description:** LinkML data model for 13C-MFA simulation studies, grounded in the [FLUXO ontology](https://purl.obolibrary.org/obo/fluxo/)
- **Version:** 0.1.0 (Pre-Alpha)
- **License:** Apache 2.0
- **Python:** >=3.11

## Architecture

```
FLUXO Ontology (semantics) -> LinkML Schema (structure) -> fluxomics_converter (computation)
```

This repo is the **LinkML Schema layer**. It defines the data model in YAML; the `datamodel/` directory holds auto-generated Python classes.

## Directory Structure

```
src/fluxolink/
├── __init__.py
├── schema/                  # LinkML YAML schema definitions
│   ├── fluxolink.yaml    # Main schema (imports the rest) + FluxoDataset root container
│   ├── enumerations.yaml    # Semantic enums backed by FLUXO ontology terms
│   ├── investigation.yaml   # Investigation provenance (contributors, conditions, publication)
│   ├── network.yaml         # Metabolic network model (metabolites, reactions, atom transitions)
│   ├── experiment.yaml      # Labeling experiments (tracers, MID/NMR/flux/pool-size measurements)
│   └── simulation_run.yaml  # Simulation runs (software, flux solutions, goodness-of-fit)
└── datamodel/               # Auto-generated Python datamodel from LinkML
tests/                       # Pytest test suite
examples/                    # Example data files (valid + invalid fixtures)
project/                     # Project configuration (gen-project outputs)
```

## Schema Modules

| Module | Description |
|---|---|
| `fluxolink.yaml` | Main schema with imports + `FluxoDataset` root container |
| `enumerations.yaml` | Semantic enums backed by FLUXO ontology terms |
| `investigation.yaml` | Investigation provenance (contributors, conditions, publication) |
| `network.yaml` | Metabolic network model (metabolites, reactions, atom transitions, constraints) |
| `experiment.yaml` | Labeling experiments (tracers, MID/NMR/flux/pool-size measurements) |
| `simulation_run.yaml` | Simulation runs (software, flux solutions, goodness-of-fit) |

## Development Commands

| Command | Purpose |
|---|---|
| `uv sync --extra dev` | Install all dependencies |
| `uv pip install -e ".[dev]"` | Editable install with dev extras |
| `uv run pytest` | Run test suite |
| `uv run ruff check src tests` | Lint Python code |
| `uv run ruff format --check src tests` | Check formatting |
| `uv run mypy src` | Type-check |
| `uv run pre-commit run --all-files` | Run all pre-commit hooks |

## Coding Conventions

- **Line length:** 99 characters
- **Docstring style:** Google convention
- **Linter:** Ruff with pycodestyle + pyflakes + isort + pep8-naming + pyupgrade + flake8-bugbear + flake8-simplify + pydocstyle
- **Type-checker:** Mypy (strict: `disallow_untyped_defs = true`)
- **Formatter:** Ruff format
- **Test framework:** Pytest with markers: `schema`, `unit`, `integration`
- **Package manager:** uv
- **Build system:** Hatchling
- **No docstring enforcement in tests**

## Key Dependencies

- `linkml` >=1.7.0 — Schema definition framework
- `linkml-runtime` >=1.7.0 — Runtime support
- `pydantic` >=2.0 — Data validation

## Agent Workflow

1. **Schema changes:** Edit `.yaml` files in `src/fluxolink/schema/`, then regenerate `datamodel/`
2. **Python changes:** Edit `.py` files in `src/fluxolink/` or `tests/`
3. **After any change:** Run `uv run ruff check src tests && uv run pytest`
4. **Before committing:** Run `uv run pre-commit run --all-files`

## Git Conventions

- Atomic commits with descriptive messages
- Pre-commit hooks enforce lint + format on commit
