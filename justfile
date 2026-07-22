# justfile — common developer tasks.
# Install `just` with: uv tool install rust-just

# Install dependencies (including dev extras)
setup:
    uv sync --extra dev

# Generate the full project artifacts (jsonschema, owl, erdiagram, docs, ...)
gen:
    uv run gen-project -d project/ src/fluxo_schema/schema/fluxo_schema.yaml

# Regenerate the Pydantic datamodel from the schema
gen-pydantic:
    uv run gen-pydantic src/fluxo_schema/schema/fluxo_schema.yaml > src/fluxo_schema/datamodel/fluxo_schema.py

# Validate the example datasets against the schema
validate-examples:
    uv run linkml-validate -s src/fluxo_schema/schema/fluxo_schema.yaml examples/valid/*.yaml

# Run the test suite
test:
    uv run pytest

# Lint and format-check the Python sources
lint:
    uv run ruff check src tests
    uv run ruff format --check src tests

# Lint the LinkML schema itself
schema-lint:
    uv run linkml-lint src/fluxo_schema/schema/fluxo_schema.yaml

# Generate HTML documentation
doc:
    uv run gen-doc -d docs/ src/fluxo_schema/schema/fluxo_schema.yaml
