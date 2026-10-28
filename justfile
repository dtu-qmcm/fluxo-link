# justfile — common developer tasks.
# Install `just` with: uv tool install rust-just

# Install dependencies (including dev extras)
setup:
    uv sync --extra dev

# Generate the full project artifacts (jsonschema, owl, erdiagram, docs, ...)
gen:
    uv run gen-project -d project/ src/fluxolink/schema/fluxolink.yaml

# Regenerate the Pydantic datamodel from the schema
gen-pydantic:
    uv run gen-pydantic src/fluxolink/schema/fluxolink.yaml > src/fluxolink/datamodel/fluxolink.py

# Validate the example datasets against the schema
validate-examples:
    uv run linkml-validate -s src/fluxolink/schema/fluxolink.yaml examples/valid/*.yaml

# Schema + semantic validation (fluxolink-validate) of every example
check-examples:
    uv run fluxolink-validate examples/valid/*.yaml examples/benchmark/*.yaml

# Regenerate docs/core_profile.md from the `core` subset of the schema
core-profile:
    uv run python scripts/gen_core_profile.py

# SQL DDL for the flat flux table (one row per run x reaction x flux type)
gen-sql:
    uv run gen-sqlddl src/fluxolink/schema/flux_record.yaml > docs/flux_record.sql
    uv run python -c "import pathlib; p = pathlib.Path('docs/flux_record.sql'); p.write_text(p.read_text().rstrip() + '\\n')"

# Run the test suite
test:
    uv run pytest

# Lint and format-check the Python sources
lint:
    uv run ruff check src tests
    uv run ruff format --check src tests

# Lint the LinkML schema itself
schema-lint:
    uv run linkml-lint src/fluxolink/schema/fluxolink.yaml

# Generate HTML documentation
doc:
    uv run gen-doc -d docs/ src/fluxolink/schema/fluxolink.yaml

# Regenerate the draw.io-editable ER diagram from the schema
erd:
    uv run python scripts/gen_erd.py
