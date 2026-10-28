#!/usr/bin/env python3
"""Ask of a FluxoDataset: is the recorded data enough to re-run the tool?

This is the Way-2 acceptance test. A catalog-tier dataset references native
files instead of re-describing them, so its value depends entirely on whether a
consumer can reconstruct a runnable invocation from the record alone.

For each SimulationRun the checker resolves the tool from `software.software_name`,
compares the recorded `input_files` against that tool's mandatory inputs, and
reports which parts of the invocation it can and cannot determine.

Usage:  python scripts/check_runnable.py examples/valid/<dataset>.yaml ...
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

# Mandatory inputs per tool, expressed as the FileRoleEnum values a consumer
# would have to find. Sources: specifications/influx_si_spec.md (.netw/.linp/
# .miso are the three "Required: Yes" rows) and specifications/fluxml_spec.md
# (<reactionnetwork> plus a <configuration> carrying input + measurement).
TOOLS: dict[str, dict[str, Any]] = {
    "influx_si": {
        "needs_roles": ["network", "tracer", "measurements"],
        "invocation": "influx_s.py [flags] --prefix <PREFIX>",
        "notes": [
            "all input files must share one --prefix and sit in one directory",
            "the MID file must be the .miso specifically, not any measurements file",
        ],
    },
    "13CFLUX2": {
        "needs_roles": ["network"],
        "invocation": "fitfluxes / fwdsim <MODEL>.fml",
        "notes": [
            "one .fml must carry <reactionnetwork> AND a <configuration> with"
            " <input> and <measurement>",
            "with several <configuration> blocks the run must name which one",
        ],
    },
    # FreeFlux's own spec is explicit that files alone are insufficient:
    # reactions.tsv is the only required file, and the tracer, bounds and solver
    # settings are all supplied through the Python API at runtime.
    "freeflux": {
        "needs_roles": ["network"],
        "invocation": "python <driver>.py  (Model + Simulator/Fitter API calls)",
        "notes": [
            "reactions.tsv is the ONLY mandatory file",
            "the tracer is set by set_labeling_strategy() in code, not a file",
            "flux/concentration bounds, n_runs, solver and tol are API arguments",
        ],
    },
    # An INCA .m file is not data read by a program -- it IS the program.
    "INCA": {
        "needs_roles": [],
        "invocation": "matlab -batch \"run('<MODEL>.m')\"",
        "notes": [
            "the .m script builds the model, attaches data and calls the solver",
            "nothing outside the script is needed, and nothing in the record"
            " describes what the script does",
        ],
    },
}


def _source_files(run: dict[str, Any], dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve the run's input_files ids against FluxoDataset.source_files."""
    by_id = {f.get("id"): f for f in dataset.get("source_files") or []}
    files = []
    for ref in run.get("input_files") or []:
        if isinstance(ref, dict):  # pre-2026-10 inlined form
            files.append(ref)
        elif ref in by_id:
            files.append(by_id[ref])
    return files


def _roles(f: dict[str, Any]) -> set[str]:
    role = f.get("role")
    return set(role) if isinstance(role, list) else {role}


def _prefix(run: dict[str, Any]) -> str | None:
    """Return influx_si's --prefix from solver_options or the command line."""
    for option in run.get("solver_options") or []:
        if option.get("key") == "--prefix":
            return option.get("value")
    words = (run.get("command_line") or "").replace('"', " ").split()
    if "--prefix" in words and words.index("--prefix") + 1 < len(words):
        return words[words.index("--prefix") + 1]
    return None


def _experiments(run: dict[str, Any], dataset: dict[str, Any]) -> list[dict[str, Any]]:
    wanted = set(run.get("experiment_id") or [])
    return [e for e in dataset.get("experiments") or [] if e.get("id") in wanted]


def check_run(run: dict[str, Any], dataset: dict[str, Any]) -> list[str] | None:
    """Return what a consumer cannot determine, or None when no contract exists."""
    findings: list[str] = []
    sw = run.get("software", {}) or {}
    name = sw.get("software_name", "<unset>")
    spec = TOOLS.get("13CFLUX2" if name == "13CFLUX3" else name)

    print(f"  run {run.get('id')}  ->  tool {name} {sw.get('version', '?')}")
    if spec is None:
        print(f"    skip no runnability contract known for {name!r}")
        return None

    infiles = _source_files(run, dataset)
    roles = set().union(*(_roles(f) for f in infiles)) if infiles else set()
    experiments = _experiments(run, dataset)

    # 1. mandatory roles. A run whose network (and, for isotope methods, its
    # experiments) is materialised can have every input regenerated from the
    # record with `fluxo export`, so it does not depend on native files.
    materialised = bool(run.get("network_model_id")) and (
        bool(experiments) or not run.get("experiment_id")
    )
    if materialised:
        print("    ok   inputs regenerable from materialised content (fluxo export)")
    for role in [] if materialised else spec["needs_roles"]:
        alternatives = {role}
        if role == "measurements":
            alternatives |= {"mid_measurements"}
        if roles & alternatives:
            print(f"    ok   mandatory role {role!r} present")
        else:
            print(f"    MISS mandatory role {role!r} absent")
            findings.append(f"missing mandatory role {role!r} for {name}")

    # 2. can the specific mandatory FILE be identified, not just the role?
    if name == "influx_si":
        mids = [f for f in infiles if "mid_measurements" in _roles(f)]
        generic = [f for f in infiles if "measurements" in _roles(f)]
        if len(mids) == 1:
            print(f"    ok   MID file is {mids[0]['path']!r}")
        elif len(generic) > 1 and not mids:
            print("    AMBIG several generic 'measurements' files; the .miso is not identified")
            findings.append(
                "several files carry the generic 'measurements' role, so the mandatory"
                " MID file is not identified (use mid_measurements)"
            )
        prefix = _prefix(run)
        if materialised:
            pass  # `fluxo export --to mtf` chooses the prefix
        elif prefix:
            print(f"    ok   --prefix {prefix!r} is recorded")
        else:
            print("    MISS --prefix not recorded (command_line / solver_options)")
            findings.append("the MTF --prefix is not recorded (command_line or solver_options)")

    if name in {"13CFLUX2", "13CFLUX3"}:
        fml = [f for f in infiles if f.get("format") == "FluxML"]
        if fml and not {"network"} <= _roles(fml[0]):
            findings.append("the .fml input does not declare role 'network'")
        named = run.get("configuration_name") or next(
            (e.get("configuration_name") for e in experiments if e.get("configuration_name")),
            None,
        )
        if named:
            print(f"    ok   configuration {named!r} is named")
        else:
            print("    MISS the FluxML <configuration> to run is not named")
            findings.append("the FluxML <configuration> to run is not named (configuration_name)")

    if name == "freeflux":
        driver = [f for f in infiles if "driver_script" in _roles(f)]
        tracer_in_record = any(e.get("labeled_sources") for e in experiments)
        if driver:
            print(f"    ok   driver script {driver[0]['path']!r} carries the API settings")
        elif tracer_in_record:
            print("    ok   tracer materialised in the experiment (no driver script recorded)")
        else:
            print("    MISS neither a driver script nor a materialised tracer is recorded")
            findings.append(
                "FreeFlux sets the tracer in code: record the driver script"
                " (role driver_script) or materialise labeled_sources"
            )

    if name == "INCA":
        scripts = [f for f in infiles if f.get("format") == "INCA_script"]
        if not scripts:
            findings.append("the INCA .m script is not recorded as format INCA_script")

    # 3. the invocation itself
    if run.get("command_line"):
        print(f"    would run: {run['command_line']}")
    else:
        print(f"    would run: {spec['invocation']}")
    if not run.get("run_mode") and run.get("run_status") != "planned":
        print("    MISS run_mode not recorded: fit vs forward simulation is unknown")
        findings.append("run_mode not recorded (fit vs forward simulation)")
    if name in {"influx_si", "INCA", "freeflux"} and not (
        run.get("command_line") or run.get("solver_options")
    ):
        print("    MISS neither command_line nor solver_options is recorded")
        findings.append("invocation flags not recorded (command_line / solver_options)")

    nonstationary = any(e.get("stationary") is False for e in experiments) or run.get(
        "fluxomics_method"
    ) in {"INST_MFA", "dynamic_MFA"}
    has_grid = run.get("stop_time") is not None or run.get("integration_timespan")
    has_grid = has_grid or any(
        m.get("time_points") for e in experiments for m in e.get("mid_measurements") or []
    )
    if nonstationary and not has_grid:
        print("    MISS INST run with no stop_time and no time grid")
        findings.append("INST run without a stop time or integration grid")

    return findings


def main(argv: list[str]) -> int:
    """Check every run in the given dataset files and print the findings."""
    total: list[tuple[str, str]] = []
    skipped = 0
    for path in argv:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        runs = data.get("simulation_runs") or []
        print(f"\n=== {Path(path).name}  (dataset_type={data.get('dataset_type')}) ===")
        if not runs:
            print("  no simulation_runs: nothing to run, provenance only")
            continue
        for run in runs:
            found = check_run(run, data)
            if found is None:
                skipped += 1
                continue
            for f in found:
                total.append((Path(path).name, f))

    print("\n" + "=" * 72)
    print(f"UNRESOLVABLE ITEMS: {len(total)}   (runs without a tool contract: {skipped})")
    for name, f in total:
        print(f"  [{name}] {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
