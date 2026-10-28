#!/usr/bin/env python3
"""Query a FluxoDataset for its labeling design: stationarity and tracers.

Answers two questions against real fixtures, and reports where the schema can
only answer them partially:

  Q1  Is each experiment isotopically stationary or instationary?
  Q2  How many tracers are there, and at which atom positions?

"Multiple tracers" is three different things, and the schema does distinguish
them structurally, so they are reported separately:

  mixture  - several TracerIsotopomers inside one LabeledSource
             (one substrate, several labelled forms; e.g. INCA t.frac)
  sources  - several LabeledSources in one experiment
             (several labelled substrates fed together)
  parallel - several LabelingExperiments joined by one SimulationRun
             (parallel labeling experiments, FLUXO_0000050)

Usage:  python scripts/query_tracers.py examples/valid/*.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml


def decode_positions(pattern: str) -> tuple[list[int], list[int]]:
    """Return (labelled 1-based positions, positions left unspecified)."""
    labelled = [i + 1 for i, c in enumerate(pattern) if c == "1"]
    unknown = [i + 1 for i, c in enumerate(pattern) if c in "xX"]
    return labelled, unknown


def atom_counts(doc: dict[str, Any]) -> dict[str, int | None]:
    """Map every metabolite id to its n_tracked_atoms."""
    counts: dict[str, int | None] = {}
    for net in doc.get("networks") or []:
        for met in net.get("metabolites") or []:
            counts[met["id"]] = met.get("n_tracked_atoms")
    return counts


def report(path: Path) -> list[str]:
    """Print Q1/Q2 answers for one dataset and return the caveats."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    caveats: list[str] = []
    counts = atom_counts(doc)
    experiments = doc.get("experiments") or []
    runs = doc.get("simulation_runs") or []

    print(f"\n=== {path.name}  (dataset_type={doc.get('dataset_type')}) ===")

    # ---- Q1: stationarity -------------------------------------------------
    if not experiments:
        print("  Q1 stationarity: UNANSWERABLE - no experiments recorded")
        caveats.append("stationarity unrecorded (no LabelingExperiment)")
    for exp in experiments:
        stat = exp.get("stationary")
        label = "stationary" if stat else "INSTATIONARY (INST)"
        print(f"  Q1 {exp['id']}: {label}   (stationary={stat})")

        # the same fact is also encoded on the run; fluxolink-validate checks
        # that the two agree (rule stationarity-method)
        for run in runs:
            if exp["id"] in (run.get("experiment_id") or []):
                method = run.get("fluxomics_method")
                expected = {True: "IST_MFA", False: "INST_MFA"}.get(stat)
                mark = "consistent" if method == expected else "*** CONTRADICTS ***"
                print(f"       run {run['id']} fluxomics_method={method}  -> {mark}")
                if method != expected:
                    caveats.append(
                        f"stationary={stat} but fluxomics_method={method}: the two"
                        " encodings of stationarity disagree (fluxolink-validate"
                        " rejects IST/INST contradictions)"
                    )
                if (
                    stat is False
                    and run.get("stop_time") is None
                    and not run.get("integration_timespan")
                ):
                    print("       INST run has no stop_time and no integration_timespan")
                    caveats.append("INST run without stop_time or integration_timespan")

        # is the flag corroborated by the data?
        times: list[Any] = []
        for key in ("flux_measurements", "pool_size_measurements", "nmr_measurements"):
            times += [m.get("time_point") for m in (exp.get(key) or [])]
        for mid in exp.get("mid_measurements") or []:
            times += list(mid.get("time_points") or [])
            times += [d.get("time_point") for d in (mid.get("data_points") or [])]
        present = [t for t in times if t is not None]
        if stat is False and not present:
            print("       no measurement carries a time_point -> flag uncorroborated")
            caveats.append("INST declared but no time points recorded")
        elif stat is True and present:
            distinct = sorted(set(present))
            print(f"       stationary but {len(present)} time_point(s) present: {distinct}")
            caveats.append("stationary declared while time points are present")

    # ---- Q2: tracers ------------------------------------------------------
    if not experiments:
        print("  Q2 tracers: UNANSWERABLE - tracer content is in the native files")
        caveats.append("tracer design unrecorded (no LabelingExperiment)")
        return caveats

    for exp in experiments:
        sources = exp.get("labeled_sources") or []
        n_tracers = sum(len(s.get("tracers") or []) for s in sources)
        print(
            f"  Q2 {exp['id']}: {len(sources)} labelled substrate(s), {n_tracers} tracer form(s)"
        )
        for src in sources:
            met = src.get("metabolite_id")
            n_atoms = counts.get(met)
            tracers = src.get("tracers") or []
            kind = "mixture" if len(tracers) > 1 else "single"
            print(
                f"       source {src['id']}: substrate {met}"
                f" (n_tracked_atoms={n_atoms}) - {kind}, {len(tracers)} form(s)"
            )
            for tr in tracers:
                pat = tr.get("labeling_pattern", "")
                labelled, unknown = decode_positions(pat)
                frac = tr.get("tracer_fraction")
                pos = ",".join(map(str, labelled)) if labelled else "none"
                line = f"         pattern {pat!r}  fraction {frac}  -> labelled position(s): {pos}"
                if unknown:
                    line += f"; UNSPECIFIED at {unknown}"
                print(line)
                # rejected by fluxolink-validate (rule labeling-pattern-length)
                if n_atoms is not None and len(pat) != n_atoms:
                    print(
                        f"           !! pattern length {len(pat)} != n_tracked_atoms"
                        f" {n_atoms} - positions are meaningless"
                    )
                    caveats.append(
                        f"{exp['id']}/{src['id']}: pattern length {len(pat)} !="
                        f" n_tracked_atoms {n_atoms}"
                    )
                if n_atoms is None:
                    caveats.append(
                        f"{exp['id']}/{src['id']}: n_tracked_atoms unknown for"
                        f" {met}, so positions cannot be bounds-checked"
                    )
                # element identity
                caveats.append(
                    f"{exp['id']}/{src['id']}: labelled ELEMENT unrecorded"
                    " (13C vs 15N vs 2H) - no tracer-element slot"
                )
                if "name" not in tr and "name" not in src:
                    caveats.append(
                        f"{exp['id']}/{src['id']}: tracer name not recorded"
                        " (TracerIsotopomer.name / LabeledSource.name)"
                    )
            total = sum(t.get("tracer_fraction") or 0 for t in tracers)
            flag = "" if total <= 1.0 + 1e-9 else "   *** EXCEEDS 1.0 ***"
            print(f"         fraction sum = {round(total, 6)}{flag}")
            if total > 1.0 + 1e-9:
                caveats.append(f"{exp['id']}/{src['id']}: fractions sum to {total}")

    # parallel labeling
    for run in runs:
        exp_ids = run.get("experiment_id") or []
        if len(exp_ids) > 1:
            print(
                f"  Q2 {run['id']}: PARALLEL labeling - {len(exp_ids)} experiments"
                f" jointly fitted {exp_ids}"
            )
    return caveats


def main(argv: list[str]) -> int:
    """Report on every dataset file given and list the caveats."""
    all_caveats: list[tuple[str, str]] = []
    for arg in argv:
        for c in report(Path(arg)):
            all_caveats.append((Path(arg).name, c))
    # collapse repeats
    seen: set[tuple[str, str]] = set()
    uniq = [c for c in all_caveats if not (c in seen or seen.add(c))]
    print("\n" + "=" * 74)
    print(f"THINGS THE SCHEMA CANNOT ANSWER OR CANNOT CHECK: {len(uniq)}")
    for name, c in uniq:
        print(f"  [{name}] {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
