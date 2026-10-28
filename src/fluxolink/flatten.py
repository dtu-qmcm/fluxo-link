"""Flatten FluxoDataset documents into one row per run, reaction and flux type.

The dataset is the record of truth; this table is the view a database
indexes and most questions need ("every PGI flux measured in E. coli on
[1-13C]glucose, by tool"). Columns are defined by
``src/fluxolink/schema/flux_record.yaml``, which also generates SQL DDL
(``just gen-sql``).

    fluxolink-flatten ds1.yaml ds2.yaml -o fluxes.tsv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

#: Column order of the flat table (FluxRecord in flux_record.yaml).
COLUMNS = [
    "dataset_id",
    "run_id",
    "reaction_id",
    "flux_type",
    "value",
    "standard_deviation",
    "lower_ci",
    "upper_ci",
    "confidence_level",
    "confidence_interval_method",
    "flux_unit",
    "solution_role",
    "fluxomics_method",
    "run_mode",
    "software_name",
    "software_version",
    "investigation_id",
    "investigation_name",
    "publication_doi",
    "organism_name",
    "strain",
    "specific_growth_rate",
    "growth_rate_unit",
    "data_origin",
    "stationary",
    "tracer",
    "wssr",
    "degrees_of_freedom",
    "chi_square_p_value",
]

_RESULT_SLOTS = (
    "reaction_id",
    "flux_type",
    "value",
    "standard_deviation",
    "lower_ci",
    "upper_ci",
    "confidence_level",
    "confidence_interval_method",
    "flux_unit",
)


def _join(values: Iterable[Any]) -> str | None:
    """Join distinct non-empty values with "; " (None when there are none)."""
    seen: list[str] = []
    for value in values:
        if value in (None, ""):
            continue
        text = str(value)
        if text not in seen:
            seen.append(text)
    return "; ".join(seen) or None


def _tracer(experiment: dict[str, Any]) -> str | None:
    """Summarise an experiment's tracer design in one string."""
    if experiment.get("tracer_summary"):
        return str(experiment["tracer_summary"])
    parts = []
    for source in experiment.get("labeled_sources") or []:
        forms = [
            f"{t.get('labeling_pattern')} x {t.get('tracer_fraction')}"
            if t.get("tracer_fraction") is not None
            else str(t.get("labeling_pattern"))
            for t in source.get("tracers") or []
        ]
        parts.append(f"{source.get('metabolite_id')}: {', '.join(forms)}")
    return " | ".join(parts) or None


def flux_records(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten one FluxoDataset document.

    Args:
        doc: The dataset as a plain dict (as loaded from YAML or JSON).

    Returns:
        One dict per flux result, keyed by ``COLUMNS`` (absent values are
        ``None``).
    """
    investigations = {i.get("id"): i for i in doc.get("investigations") or []}
    conditions = {c.get("id"): c for c in doc.get("conditions") or []}
    experiments = {e.get("id"): e for e in doc.get("experiments") or []}
    rows: list[dict[str, Any]] = []
    for run in doc.get("simulation_runs") or []:
        solution = run.get("flux_solution") or {}
        results = solution.get("flux_results") or []
        if not results:
            continue
        exps = [experiments[e] for e in run.get("experiment_id") or [] if e in experiments]
        cond_ids = [run.get("condition")] + [e.get("condition") for e in exps]
        conds = [conditions[c] for c in dict.fromkeys(cond_ids) if c in conditions]
        stationary = {e.get("stationary") for e in exps}
        software = run.get("software") or {}
        name = software.get("software_name")
        if name == "other":
            name = software.get("software_name_other") or name
        investigation = investigations.get(run.get("investigation_id")) or {}
        gof = run.get("goodness_of_fit") or {}
        context = {
            "dataset_id": doc.get("id"),
            "run_id": run.get("id"),
            "solution_role": solution.get("solution_role"),
            "fluxomics_method": run.get("fluxomics_method"),
            "run_mode": _join(run.get("run_mode") or []),
            "software_name": name,
            "software_version": software.get("version"),
            "investigation_id": run.get("investigation_id"),
            "investigation_name": investigation.get("name"),
            "publication_doi": investigation.get("publication_doi"),
            "organism_name": _join(c.get("organism_name") for c in conds),
            "strain": _join(c.get("strain") for c in conds),
            "specific_growth_rate": (
                conds[0].get("specific_growth_rate") if len(conds) == 1 else None
            ),
            "growth_rate_unit": (conds[0].get("growth_rate_unit") if len(conds) == 1 else None),
            "data_origin": _join(e.get("data_origin") for e in exps),
            "stationary": stationary.pop() if len(stationary) == 1 else None,
            "tracer": _join(_tracer(e) for e in exps),
            "wssr": gof.get("wssr"),
            "degrees_of_freedom": gof.get("degrees_of_freedom"),
            "chi_square_p_value": gof.get("chi_square_p_value"),
        }
        for result in results:
            row = {column: None for column in COLUMNS}
            row.update(context)
            row.update({slot: result.get(slot) for slot in _RESULT_SLOTS})
            rows.append(row)
    return rows


def _write(rows: list[dict[str, Any]], out: Path | None) -> None:
    suffix = out.suffix.lower() if out else ".tsv"
    handle = open(out, "w", newline="", encoding="utf-8") if out else sys.stdout  # noqa: SIM115
    try:
        if suffix == ".jsonl":
            for row in rows:
                handle.write(json.dumps(row) + "\n")
        elif suffix in (".yaml", ".yml"):
            handle.write(yaml.safe_dump({"records": rows}, sort_keys=False))
        else:
            writer = csv.DictWriter(
                handle, fieldnames=COLUMNS, delimiter="," if suffix == ".csv" else "\t"
            )
            writer.writeheader()
            writer.writerows(rows)
    finally:
        if out:
            handle.close()


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point for ``fluxolink-flatten``.

    Args:
        argv: Arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(
        prog="fluxolink-flatten",
        description="Flatten FluxoDataset files into one row per run, reaction and flux type.",
    )
    parser.add_argument("files", nargs="+", type=Path, help="dataset YAML/JSON files")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output file; .tsv (default, also stdout), .csv, .jsonl or .yaml",
    )
    args = parser.parse_args(argv)
    rows: list[dict[str, Any]] = []
    for path in args.files:
        with open(path, encoding="utf-8") as handle:
            rows += flux_records(yaml.safe_load(handle) or {})
    _write(rows, args.output)
    if args.output:
        print(f"wrote {len(rows)} rows to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
