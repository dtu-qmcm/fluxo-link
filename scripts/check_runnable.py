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


def check_run(run: dict[str, Any], dataset: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    sw = run.get("software", {}) or {}
    name = sw.get("software_name", "<unset>")
    spec = TOOLS.get(name)

    print(f"  run {run.get('id')}  ->  tool {name} {sw.get('version', '?')}")
    if spec is None:
        findings.append(f"unknown tool {name!r}: no runnability contract to check")
        print(f"    ! no runnability contract known for {name!r}")
        return findings

    infiles = run.get("input_files") or []
    roles = {f.get("role") for f in infiles}
    paths = [f.get("path") for f in infiles]

    # 1. mandatory roles
    for role in spec["needs_roles"]:
        if role in roles:
            print(f"    ok   mandatory role {role!r} present")
        else:
            print(f"    MISS mandatory role {role!r} absent")
            findings.append(f"missing mandatory role {role!r} for {name}")

    # 2. can the specific mandatory FILE be identified, not just the role?
    if name == "influx_si":
        meas = [f for f in infiles if f.get("role") == "measurements"]
        if len(meas) > 1:
            exts = sorted({Path(f["path"]).suffix for f in meas})
            print(
                f"    AMBIG {len(meas)} files share role 'measurements' {exts};"
                " the .miso cannot be identified from the record"
            )
            findings.append(
                "role 'measurements' is overloaded: .miso / .mflux / .mmet are"
                " indistinguishable, so the mandatory MID file is not resolvable"
                " without parsing filenames"
            )
        prefixes = {Path(p).name.split(".")[0] for p in paths}
        if len(prefixes) == 1:
            print(
                f"    infer --prefix={prefixes.pop()!r} (recovered by string"
                " surgery on paths; not declared anywhere)"
            )
            findings.append(
                "the MTF --prefix is not a declared field; it only happens to be"
                " recoverable because every path shares a stem"
            )
        else:
            print(f"    MISS cannot infer a single --prefix from {sorted(prefixes)}")
            findings.append("cannot determine the MTF --prefix")

    if name == "13CFLUX2":
        same = {f.get("path") for f in infiles}
        if len(same) == 1 and len(infiles) == 1:
            role = infiles[0].get("role")
            if role != "network":
                print(
                    f"    AMBIG the single input file is recorded as role={role!r},"
                    " so the record does not assert that a network is present"
                )
                findings.append(
                    "one .fml plays 5 roles but SourceFile.role is single-valued:"
                    " the run's input_files cannot state that this file carries"
                    " network + tracer + measurements at once"
                )
        cfgs = [f for f in (dataset.get("source_files") or []) if f.get("role") == "configuration"]
        if cfgs and not (dataset.get("experiments") or []):
            print(
                "    MISS no experiment recorded, so the <configuration> to run"
                " is not named and stationarity is unstated"
            )
            findings.append(
                "the FluxML <configuration> to run is not identified (no"
                " experiment, and no configuration-name slot exists)"
            )

    if name == "freeflux":
        if "tracer" not in roles:
            print(
                "    MISS no 'tracer' role: FreeFlux sets the labeling strategy"
                " through set_labeling_strategy() in Python, so the tracer is"
                " absent from the file set entirely -- this dataset CANNOT be run"
            )
            findings.append(
                "FreeFlux file set has no tracer at all (API-only), and the"
                " schema cannot distinguish 'tracer absent' from 'tracer not"
                " recorded'"
            )
        print(
            "    MISS the driver .py that supplies the tracer, bounds and solver"
            " is not referenced; FileRoleEnum has no value for a driver script"
        )
        findings.append(
            "no FileRoleEnum value for the FreeFlux driver script, which carries"
            " the settings the TSVs omit"
        )

    if name == "INCA":
        fmts = {f.get("format") for f in infiles}
        if fmts == {"other"}:
            print(
                "    note the .m script can only be typed as format='other';"
                " InputFormatEnum's INCA_mat is the binary results container"
            )
            findings.append(
                "InputFormatEnum has no value for an INCA .m script (INCA_mat is"
                " the results format), so the input format is untyped"
            )
        print(
            "    AMBIG the script is simultaneously the input AND the program;"
            " nothing records that it calls simulate() rather than estimate()"
        )
        findings.append(
            "INCA's run intent (simulate vs estimate vs continuate vs montecarlo)"
            " is unrecoverable: it lives in the script body and has no slot"
        )

    # 3. the invocation itself
    print(f"    would run: {spec['invocation']}")
    if run.get("optimization_method"):
        print(
            f"    note optimization_method={run['optimization_method']!r} is"
            " recorded, but no format supplies it - see the FABRICATED comments"
        )
    for slot, why in [
        ("command_line", "the actual invocation and its flags"),
        ("run_mode", "whether this was a fit or a forward simulation only"),
        ("solver_options", "solver flags such as --clownr / --zc / --noopt"),
        ("integration_timespan", "the INST time grid"),
    ]:
        if slot not in run:
            print(f"    MISS no {slot!r} slot: {why} is unrecoverable")
            findings.append(f"no slot for {why}")

    if run.get("fluxomics_method") in {"INST_MFA", "dynamic_MFA"} and "stop_time" not in run:
        print("    MISS INST run with no stop_time and no time grid")
        findings.append("INST run without a stop time or integration grid")

    return findings


def main(argv: list[str]) -> int:
    total: list[tuple[str, str]] = []
    for path in argv:
        data = yaml.safe_load(Path(path).read_text())
        runs = data.get("simulation_runs") or []
        print(f"\n=== {Path(path).name}  (dataset_type={data.get('dataset_type')}) ===")
        if not runs:
            print("  no simulation_runs: nothing to run, provenance only")
            continue
        for run in runs:
            for f in check_run(run, data):
                total.append((Path(path).name, f))

    print("\n" + "=" * 72)
    print(f"UNRESOLVABLE ITEMS: {len(total)}")
    for name, f in total:
        print(f"  [{name}] {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
