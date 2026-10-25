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
