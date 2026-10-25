#!/usr/bin/env bash
# Fail if the generated Pydantic datamodel is out of sync with the LinkML schema.
# Run `just gen-pydantic` to regenerate, then re-stage.
set -euo pipefail

SCHEMA="src/fluxolink/schema/fluxolink.yaml"
COMMITTED="src/fluxolink/datamodel/fluxolink.py"

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

uv run gen-pydantic "$SCHEMA" > "$tmp"

if ! diff -q "$COMMITTED" "$tmp" >/dev/null 2>&1; then
  echo "ERROR: $COMMITTED is out of sync with $SCHEMA." >&2
  echo "Run: just gen-pydantic" >&2
  echo "" >&2
  diff -u "$COMMITTED" "$tmp" | head -50 >&2
  exit 1
fi
