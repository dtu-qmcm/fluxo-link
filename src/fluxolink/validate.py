"""Semantic and tier validation for FluxoDataset documents.

LinkML validation checks structure: types, required slots, enums, patterns,
and the one tier rule a LinkML ``rules:`` block can express. It cannot check
what a fluxomics dataset needs beyond that:

* references between objects (``LabelingExperiment.condition`` must name a
  declared condition; JSON-Schema validation does not check foreign keys);
* cross-slot consistency (``stationary`` versus ``fluxomics_method``, tracer
  fractions summing above 1, labeling patterns longer than the molecule,
  one atom mapped to two places);
* the benchmark tier. LinkML ``slot_conditions`` cannot nest, so a rule on
  ``FluxoDataset`` cannot re-impose ``TracerIsotopomer.isotopic_purity`` or
  ``MIDDataPoint.standard_deviation``. Those fields are ``recommended`` in the
  schema, and this module requires them when ``dataset_type`` is
  ``benchmark`` (or when ``--benchmark`` is passed).

Every issue is an error or a warning. Errors make ``fluxolink-validate`` exit
non-zero; warnings flag things a curator should look at.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

SCHEMA_PATH = Path(__file__).parent / "schema" / "fluxolink.yaml"

ERROR = "error"
WARNING = "warning"

# Methods that use isotope labeling and therefore need a labeling experiment.
ISOTOPE_METHODS = frozenset(
    {"I_MFA", "C13_MFA", "IST_MFA", "INST_MFA", "dynamic_MFA", "kinetic_flux_profiling"}
)
STATIONARY_METHODS = frozenset({"IST_MFA"})
NONSTATIONARY_METHODS = frozenset({"INST_MFA", "dynamic_MFA", "kinetic_flux_profiling"})
SAMPLED_CI_METHODS = frozenset({"monte_carlo", "bootstrap"})

# Tolerance for sums of fractions and for MID values that should lie in [0, 1].
FRACTION_TOL = 1e-6
MID_RANGE_TOL = 0.01

# `<enum slot>` -> `<free-text companion slot>` pairs that must be filled when
# the enum value is "other".
OTHER_COMPANIONS = {
    "software_name": "software_name_other",
    "format": "format_other",
    "input_format": "input_format_other",
    "analytical_method": "analytical_method_other",
}


@dataclass(frozen=True)
class Issue:
    """One validation finding.

    Attributes:
        severity: ``"error"`` or ``"warning"``.
        rule: Short identifier of the rule that fired (e.g. ``ci-order``).
        path: JSON-pointer-like location of the offending object.
        message: Human-readable explanation.
    """

    severity: str
    rule: str
    path: str
    message: str

    def __str__(self) -> str:
        """Render the issue as one log line."""
        return f"[{self.severity.upper()}] {self.rule} at {self.path}: {self.message}"


def _items(obj: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Return a multivalued slot as a list of dicts (absent -> empty list)."""
    value = obj.get(key) or []
    return [v for v in value if isinstance(v, dict)]


def _ids(value: Any) -> list[str]:
    """Normalise a single- or multivalued reference slot to a list of ids."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def _num(value: Any) -> float | None:
    """Return value as a finite float, or None when absent or not numeric."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def parse_positions(spec: Any) -> list[int] | None:
    """Parse an atom-position string such as ``"2,3"`` or ``"1-3,5"``.

    Args:
        spec: The position string (or an int / list of ints).

    Returns:
        The positions in order, or None when the string cannot be parsed.
    """
    if spec is None:
        return None
    if isinstance(spec, int) and not isinstance(spec, bool):
        return [spec]
    if isinstance(spec, list):
        return [int(p) for p in spec] if all(isinstance(p, int) for p in spec) else None
    positions: list[int] = []
    for part in str(spec).replace(" ", "").split(","):
        if not part:
            continue
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
        if not match:
            return None
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if end < start:
            return None
        positions.extend(range(start, end + 1))
    return positions or None


class _Network:
    """Lookup tables for one MetabolicNetworkModel."""

    def __init__(self, net: dict[str, Any]) -> None:
        self.id = str(net.get("id"))
        self.metabolites = {str(m.get("id")): m for m in _items(net, "metabolites")}
        self.reactions = {str(r.get("id")): r for r in _items(net, "reactions")}
        self.variant_ids = {
            str(v.get("variant_id"))
            for r in self.reactions.values()
            for v in _items(r, "atom_transition_variants")
        }
        self.has_metabolites = bool(self.metabolites)

    def n_atoms(self, metabolite_id: Any) -> int | None:
        met = self.metabolites.get(str(metabolite_id))
        if met is None:
            return None
        n = met.get("n_tracked_atoms")
        return n if isinstance(n, int) and not isinstance(n, bool) else None

    def knows_reaction(self, reaction_id: Any) -> bool:
        rid = str(reaction_id)
        return rid in self.reactions or rid in self.variant_ids


class DatasetValidator:
    """Collects semantic and tier issues for one FluxoDataset document.

    Args:
        doc: The dataset as loaded from YAML or JSON (a plain dict).
        benchmark: Force benchmark-tier checks on (True) or off (False).
            None means "follow the document's ``dataset_type``".
    """

    def __init__(self, doc: dict[str, Any], *, benchmark: bool | None = None) -> None:
        """Index the document's top-level collections for reference checks."""
        self.doc = doc
        self.benchmark = doc.get("dataset_type") == "benchmark" if benchmark is None else benchmark
        self.issues: list[Issue] = []
        self.networks = {n.id: n for n in (_Network(x) for x in _items(doc, "networks"))}
        self.ids: dict[str, set[str]] = {
            key: {str(x.get("id")) for x in _items(doc, key)}
            for key in (
                "investigations",
                "conditions",
                "networks",
                "experiments",
                "source_files",
                "simulation_runs",
                "equivalence_checks",
            )
        }
        self.experiments = {str(e.get("id")): e for e in _items(doc, "experiments")}
        self.conditions = {str(c.get("id")): c for c in _items(doc, "conditions")}
        self.source_files = {str(f.get("id")): f for f in _items(doc, "source_files")}

    # -- reporting ---------------------------------------------------------

    def _add(self, severity: str, rule: str, path: str, message: str) -> None:
        self.issues.append(Issue(severity, rule, path, message))

    def _error(self, rule: str, path: str, message: str) -> None:
        self._add(ERROR, rule, path, message)

    def _warn(self, rule: str, path: str, message: str) -> None:
        self._add(WARNING, rule, path, message)

    def _tier(self, rule: str, path: str, message: str) -> None:
        """Report a benchmark-tier requirement: an error at that tier only."""
        if self.benchmark:
            self._error(rule, path, message)

    def _require(self, obj: dict[str, Any], slots: Iterable[str], path: str, why: str) -> None:
        for slot in slots:
            if obj.get(slot) in (None, "", []):
                self._tier("benchmark-required", path, f"'{slot}' is required {why}")

    def _ref(self, value: Any, kind: str, path: str, slot: str) -> None:
        for ref in _ids(value):
            if ref not in self.ids[kind]:
                self._error(
                    "reference-integrity",
                    path,
                    f"{slot} '{ref}' does not match any id in {kind}",
                )

    # -- entry point -------------------------------------------------------

    def run(self) -> list[Issue]:
        """Run every check and return the issues found."""
        self._check_duplicate_ids()
        self._check_other_companions(self.doc, "")
        for i, cond in enumerate(_items(self.doc, "conditions")):
            self._check_condition(cond, f"/conditions/{i}")
        for i, src in enumerate(_items(self.doc, "source_files")):
            if "other" in _ids(src.get("role")) and not src.get("role_other"):
                self._error(
                    "other-companion", f"/source_files/{i}", "role 'other' needs role_other"
                )
            path = f"/source_files/{i}"
            self._ref(src.get("derived_from"), "source_files", path, "derived_from")
            if str(src.get("id")) in _ids(src.get("derived_from")):
                self._error("reference-integrity", path, "a file cannot be derived from itself")
        for i, check in enumerate(_items(self.doc, "equivalence_checks")):
            self._check_equivalence(check, f"/equivalence_checks/{i}")
        for i, net in enumerate(_items(self.doc, "networks")):
            self._check_network(net, f"/networks/{i}")
        for i, exp in enumerate(_items(self.doc, "experiments")):
            self._check_experiment(exp, f"/experiments/{i}")
        for i, run in enumerate(_items(self.doc, "simulation_runs")):
            self._check_run(run, f"/simulation_runs/{i}")
        if self.benchmark and not self.networks:
            self._error(
                "benchmark-required", "", "a benchmark dataset must materialise its network"
            )
        return self.issues

    # -- dataset level -----------------------------------------------------

    def _check_duplicate_ids(self) -> None:
        for key in self.ids:
            counts = Counter(str(x.get("id")) for x in _items(self.doc, key))
            for ident, n in counts.items():
                if n > 1:
                    self._error("duplicate-id", f"/{key}", f"id '{ident}' is used {n} times")

    def _check_other_companions(self, obj: Any, path: str) -> None:
        """Walk the document: every enum value "other" needs its free text."""
        if isinstance(obj, dict):
            for slot, companion in OTHER_COMPANIONS.items():
                if obj.get(slot) == "other" and not obj.get(companion):
                    self._error("other-companion", path, f"{slot} 'other' needs {companion}")
            for key, value in obj.items():
                self._check_other_companions(value, f"{path}/{key}")
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                self._check_other_companions(value, f"{path}/{i}")

    def _check_condition(self, cond: dict[str, Any], path: str) -> None:
        if cond.get("specific_growth_rate") is not None and not cond.get("growth_rate_unit"):
            self._error("growth-rate-unit", path, "specific_growth_rate needs growth_rate_unit")

    def _check_equivalence(self, check: dict[str, Any], path: str) -> None:
        self._ref(check.get("files"), "source_files", path, "files")
        self._ref(check.get("compared_with"), "source_files", path, "compared_with")
        self._ref(check.get("network_model_id"), "networks", path, "network_model_id")
        self._ref(check.get("experiment_id"), "experiments", path, "experiment_id")
        differences = check.get("differences") or []
        if check.get("equivalent") is True and differences:
            self._error(
                "equivalence-consistency",
                path,
                f"equivalent is true but {len(differences)} unexpected difference(s) are listed",
            )
        elif check.get("equivalent") is False and not differences:
            self._warn(
                "equivalence-consistency",
                path,
                "equivalent is false but no difference is listed",
            )
        if not check.get("compared_with") and not self.networks:
            self._warn(
                "equivalence-target",
                path,
                "no compared_with files and no materialised network: the check names nothing "
                "it was compared against",
            )

    # -- network -----------------------------------------------------------

    def _check_network(self, net: dict[str, Any], path: str) -> None:
        model = self.networks[str(net.get("id"))]
        if not model.has_metabolites:
            self._tier(
                "benchmark-required",
                path,
                "'metabolites' is required at the benchmark tier (the network must be "
                "materialised, not derived from reaction strings)",
            )
        for i, rxn in enumerate(_items(net, "reactions")):
            self._check_reaction(model, rxn, f"{path}/reactions/{i}")
        for i, con in enumerate(_items(net, "flux_constraints")):
            self._check_flux_constraint(model, con, f"{path}/flux_constraints/{i}")
        for i, con in enumerate(_items(net, "pool_size_constraints")):
            self._check_pool_constraint(model, con, f"{path}/pool_size_constraints/{i}")

    def _check_reaction(self, model: _Network, rxn: dict[str, Any], path: str) -> None:
        sides: dict[str, set[tuple[str, int]]] = {}
        for side in ("reactants", "products"):
            seen: set[tuple[str, int]] = set()
            for j, part in enumerate(_items(rxn, side)):
                met = str(part.get("metabolite_id"))
                key = (met, int(part.get("instance") or 1))
                if key in seen:
                    self._error(
                        "participant-instance",
                        f"{path}/{side}/{j}",
                        f"'{met}' appears twice on the {side} side with the same instance "
                        "index; give each occurrence its own instance",
                    )
                seen.add(key)
                if model.has_metabolites and met not in model.metabolites:
                    self._error(
                        "reference-integrity",
                        f"{path}/{side}/{j}",
                        f"metabolite_id '{met}' is not a metabolite of network '{model.id}'",
                    )
            sides[side] = seen
        if not sides["reactants"] and not sides["products"]:
            self._error(
                "reaction-participants", path, "a reaction needs at least one reactant or product"
            )

        variants = _items(rxn, "atom_transition_variants")
        ratios = [_num(v.get("ratio")) for v in variants]
        if variants and all(r is not None for r in ratios):
            total = sum(r for r in ratios if r is not None)
            if abs(total - 1.0) > FRACTION_TOL:
                self._warn(
                    "variant-ratio-sum",
                    path,
                    f"atom transition variant ratios sum to {total:g}, not 1",
                )
        for k, variant in enumerate(variants):
            self._check_variant(model, variant, sides, f"{path}/atom_transition_variants/{k}")

        if self.benchmark and not variants and model.has_metabolites:
            parts = _items(rxn, "reactants") + _items(rxn, "products")
            if any((model.n_atoms(p.get("metabolite_id")) or 0) > 0 for p in parts):
                self._warn(
                    "atom-transitions-missing",
                    path,
                    "reaction involves tracked metabolites but has no atom transitions",
                )

    def _check_variant(
        self,
        model: _Network,
        variant: dict[str, Any],
        sides: dict[str, set[tuple[str, int]]],
        path: str,
    ) -> None:
        sources: Counter[tuple[str, int, int]] = Counter()
        targets: Counter[tuple[str, int, int]] = Counter()
        for t, tr in enumerate(_items(variant, "transitions")):
            tpath = f"{path}/transitions/{t}"
            ends = (
                ("reactant", "reactants", sources),
                ("product", "products", targets),
            )
            for end, side, counter in ends:
                met = tr.get(f"{end}_metabolite_id")
                index = tr.get(f"{end}_atom_index")
                if met is None or index is None:
                    if end == "reactant" or (met is None) != (index is None):
                        self._error(
                            "atom-transition-incomplete",
                            tpath,
                            f"{end}_metabolite_id and {end}_atom_index must be given together",
                        )
                    continue
                instance = int(tr.get(f"{end}_instance") or 1)
                counter[(str(met), instance, int(index))] += 1
                if sides[side] and (str(met), instance) not in sides[side]:
                    self._error(
                        "atom-transition-participant",
                        tpath,
                        f"{end} '{met}' (instance {instance}) is not among the reaction's {side}",
                    )
                n_atoms = model.n_atoms(met)
                if n_atoms is not None and int(index) > n_atoms:
                    self._error(
                        "atom-index-range",
                        tpath,
                        f"{end}_atom_index {index} exceeds n_tracked_atoms {n_atoms} of '{met}'",
                    )
        for counter, what in ((sources, "reactant"), (targets, "product")):
            for (met, instance, index), n in counter.items():
                if n > 1:
                    self._error(
                        "atom-mapped-twice",
                        path,
                        f"{what} atom {met}#{index} (instance {instance}) appears in {n} "
                        "transitions of one variant; one atom cannot map to two places",
                    )

    def _check_flux_constraint(self, model: _Network, con: dict[str, Any], path: str) -> None:
        if not con.get("reaction_id") and not con.get("expression"):
            self._error("constraint-target", path, "give reaction_id or expression")
        rid = con.get("reaction_id")
        if rid and model.reactions and not model.knows_reaction(rid):
            self._error(
                "reference-integrity",
                path,
                f"reaction_id '{rid}' is not a reaction of network '{model.id}'",
            )

    def _check_pool_constraint(self, model: _Network, con: dict[str, Any], path: str) -> None:
        if not con.get("metabolite_id") and not con.get("expression"):
            self._error("constraint-target", path, "give metabolite_id or expression")
        met = con.get("metabolite_id")
        if met and model.has_metabolites and str(met) not in model.metabolites:
            self._error(
                "reference-integrity",
                path,
                f"metabolite_id '{met}' is not a metabolite of network '{model.id}'",
            )

    # -- experiments -------------------------------------------------------

    def _network_for(self, network_id: Any) -> _Network | None:
        """Resolve the network an object's references resolve against."""
        if network_id is not None:
            return self.networks.get(str(network_id))
        if len(self.networks) == 1:
            return next(iter(self.networks.values()))
        return None

    def _check_met_ref(self, model: _Network | None, met: Any, path: str) -> None:
        if met is None or model is None or not model.has_metabolites:
            return
        if str(met) not in model.metabolites:
            self._error(
                "reference-integrity",
                path,
                f"metabolite_id '{met}' is not a metabolite of network '{model.id}'",
            )

    def _check_rxn_ref(self, model: _Network | None, rid: Any, path: str) -> None:
        if rid is None or model is None or not model.reactions:
            return
        if not model.knows_reaction(rid):
            self._error(
                "reference-integrity",
                path,
                f"reaction_id '{rid}' is not a reaction of network '{model.id}'",
            )

    def _check_experiment(self, exp: dict[str, Any], path: str) -> None:
        self._ref(exp.get("investigation_id"), "investigations", path, "investigation_id")
        self._ref(exp.get("condition"), "conditions", path, "condition")
        self._ref(exp.get("network_model_id"), "networks", path, "network_model_id")
        self._ref(exp.get("source_files"), "source_files", path, "source_files")
        if len(self.networks) > 1 and not exp.get("network_model_id"):
            self._warn(
                "network-binding",
                path,
                "dataset has several networks; set network_model_id so references resolve",
            )
        model = self._network_for(exp.get("network_model_id"))
        experimental = exp.get("data_origin") == "experimental"

        self._require(exp, ["investigation_id", "labeled_sources"], path, "at the benchmark tier")
        if self.benchmark and exp.get("data_origin") is None:
            self._warn(
                "data-origin",
                path,
                "set data_origin; a benchmark with experimental data must also carry its "
                "cultivation condition",
            )
        if experimental:
            self._require(exp, ["condition"], path, "for experimental data at the benchmark tier")
            cond = self.conditions.get(str(exp.get("condition")))
            if cond is not None:
                self._require(
                    cond,
                    ["organism_name", "strain", "specific_growth_rate", "growth_rate_unit"],
                    f"{path} -> condition {cond.get('id')}",
                    "for experimental data at the benchmark tier",
                )

        for i, src in enumerate(_items(exp, "labeled_sources")):
            self._check_labeled_source(model, src, f"{path}/labeled_sources/{i}")

        stationary = exp.get("stationary")
        for i, mid in enumerate(_items(exp, "mid_measurements")):
            self._check_mid(model, mid, stationary, experimental, f"{path}/mid_measurements/{i}")
        for i, nmr in enumerate(_items(exp, "nmr_measurements")):
            self._check_met_ref(model, nmr.get("metabolite_id"), f"{path}/nmr_measurements/{i}")
        for i, flux in enumerate(_items(exp, "flux_measurements")):
            fpath = f"{path}/flux_measurements/{i}"
            if not flux.get("reaction_id") and not flux.get("flux_expression"):
                self._error("measurement-target", fpath, "give reaction_id or flux_expression")
            self._check_rxn_ref(model, flux.get("reaction_id"), fpath)
            self._check_measurement_sd(flux, fpath)
        for i, pool in enumerate(_items(exp, "pool_size_measurements")):
            ppath = f"{path}/pool_size_measurements/{i}"
            if not pool.get("metabolite_id") and not pool.get("pool_expression"):
                self._error("measurement-target", ppath, "give metabolite_id or pool_expression")
            self._check_met_ref(model, pool.get("metabolite_id"), ppath)
            self._check_measurement_sd(pool, ppath)
        if model is not None:
            for i, con in enumerate(_items(exp, "flux_constraints")):
                self._check_flux_constraint(model, con, f"{path}/flux_constraints/{i}")
            for i, con in enumerate(_items(exp, "pool_size_constraints")):
                self._check_pool_constraint(model, con, f"{path}/pool_size_constraints/{i}")

    def _check_measurement_sd(self, meas: dict[str, Any], path: str) -> None:
        self._require(meas, ["value"], path, "at the benchmark tier")
        if meas.get("standard_deviation") is None and not meas.get("error_model_expression"):
            self._tier(
                "benchmark-required",
                path,
                "'standard_deviation' (or error_model_expression) is required at the "
                "benchmark tier",
            )

    def _check_labeled_source(
        self, model: _Network | None, src: dict[str, Any], path: str
    ) -> None:
        self._check_met_ref(model, src.get("metabolite_id"), path)
        n_atoms = model.n_atoms(src.get("metabolite_id")) if model else None
        fractions: list[float | None] = []
        for j, tracer in enumerate(_items(src, "tracers")):
            tpath = f"{path}/tracers/{j}"
            self._require(
                tracer, ["tracer_fraction", "isotopic_purity"], tpath, "at the benchmark tier"
            )
            fractions.append(_num(tracer.get("tracer_fraction")))
            pattern = tracer.get("labeling_pattern")
            if n_atoms is not None and pattern is not None and len(str(pattern)) != n_atoms:
                self._error(
                    "labeling-pattern-length",
                    tpath,
                    f"labeling_pattern '{pattern}' has {len(str(pattern))} positions but "
                    f"'{src.get('metabolite_id')}' tracks {n_atoms} atoms",
                )
        known = [f for f in fractions if f is not None]
        total = sum(known)
        if total > 1.0 + FRACTION_TOL:
            self._error(
                "tracer-fraction-sum",
                path,
                f"tracer fractions sum to {total:g}, above 1",
            )
        elif known and len(known) == len(fractions) and total < 1.0 - FRACTION_TOL:
            self._warn(
                "tracer-fraction-sum",
                path,
                f"tracer fractions sum to {total:g}; the remainder is read as natural abundance",
            )

    def _check_mid(
        self,
        model: _Network | None,
        mid: dict[str, Any],
        stationary: Any,
        experimental: bool,
        path: str,
    ) -> None:
        self._check_met_ref(model, mid.get("metabolite_id"), path)
        if self.benchmark and not mid.get("atom_positions") and not mid.get("measurement_spec"):
            self._error(
                "benchmark-required",
                path,
                "'atom_positions' (or measurement_spec) is required at the benchmark tier",
            )
        if experimental:
            self._require(
                mid, ["analytical_method"], path, "for experimental data at the benchmark tier"
            )
        if mid.get("natural_abundance_corrected") and not mid.get("correction_algorithm"):
            self._warn(
                "natural-abundance",
                path,
                "natural_abundance_corrected is true but correction_algorithm is not given",
            )
        positions = parse_positions(mid.get("atom_positions"))
        n_atoms = model.n_atoms(mid.get("metabolite_id")) if model else None
        if positions and n_atoms is not None and max(positions) > n_atoms:
            self._error(
                "atom-index-range",
                path,
                f"atom_positions reach {max(positions)} but '{mid.get('metabolite_id')}' tracks "
                f"{n_atoms} atoms",
            )
        max_index = len(positions) if positions else n_atoms
        scaled = mid.get("scale_method") == "auto"
        if stationary is True and mid.get("time_points"):
            self._warn("stationary-time", path, "stationary experiment with time_points")
        values = [_num(p.get("value")) for p in _items(mid, "data_points")]
        if len(values) > 1 and all(v == 0.0 for v in values):
            self._warn(
                "mid-placeholder",
                path,
                f"all {len(values)} values are 0.0; placeholder data rather than a measurement?",
            )
        for k, point in enumerate(_items(mid, "data_points")):
            ppath = f"{path}/data_points/{k}"
            value = _num(point.get("value"))
            self._require(point, ["value", "standard_deviation"], ppath, "at the benchmark tier")
            if stationary is False and value is not None and point.get("time_point") is None:
                self._error(
                    "inst-time",
                    ppath,
                    "non-stationary experiment: every measured value needs a time_point",
                )
            index = point.get("isotopologue_index")
            if isinstance(index, int) and max_index is not None and index > max_index:
                self._warn(
                    "isotopologue-range",
                    ppath,
                    f"isotopologue_index {index} exceeds the {max_index} traced positions",
                )
            if (
                value is not None
                and not scaled
                and not (-MID_RANGE_TOL <= value <= 1.0 + MID_RANGE_TOL)
            ):
                self._warn(
                    "mid-range",
                    ppath,
                    f"MID value {value:g} lies outside [0, 1] in a group not scaled 'auto'",
                )

    # -- simulation runs ---------------------------------------------------

    def _check_run(self, run: dict[str, Any], path: str) -> None:
        self._ref(run.get("investigation_id"), "investigations", path, "investigation_id")
        self._ref(run.get("network_model_id"), "networks", path, "network_model_id")
        self._ref(run.get("experiment_id"), "experiments", path, "experiment_id")
        self._ref(run.get("condition"), "conditions", path, "condition")
        self._ref(run.get("input_files"), "source_files", path, "input_files")
        self._ref(run.get("output_files"), "source_files", path, "output_files")

        method = run.get("fluxomics_method")
        status = run.get("run_status")
        modes = set(_ids(run.get("run_mode")))
        software = run.get("software") or {}
        self._require(run, ["fluxomics_method", "investigation_id"], path, "at the benchmark tier")
        if status not in ("planned", None) or (status is None and run.get("flux_solution")):
            self._require(
                software,
                ["version"],
                f"{path}/software",
                "for an executed run at the benchmark tier",
            )
        if "estimation" in modes:
            self._require(
                run, ["optimization_method"], path, "for an estimation run at the benchmark tier"
            )

        experiment_ids = _ids(run.get("experiment_id"))
        if method in ISOTOPE_METHODS and not experiment_ids:
            message = f"{method} is isotope-based but the run names no labeling experiment"
            if self.benchmark:
                self._error("isotope-method-experiment", path, message)
            else:
                self._warn("isotope-method-experiment", path, message)

        any_nonstationary = False
        for eid in experiment_ids:
            exp = self.experiments.get(eid)
            if exp is None:
                continue
            stationary = exp.get("stationary")
            any_nonstationary |= stationary is False
            if method in STATIONARY_METHODS and stationary is False:
                self._error(
                    "stationarity-method",
                    path,
                    f"fluxomics_method {method} but experiment '{eid}' is non-stationary",
                )
            if method in NONSTATIONARY_METHODS and stationary is True:
                self._error(
                    "stationarity-method",
                    path,
                    f"fluxomics_method {method} but experiment '{eid}' is stationary",
                )
        if (
            any_nonstationary
            and run.get("stop_time") is None
            and not run.get("integration_timespan")
        ):
            has_grid = any(
                mid.get("time_points")
                for eid in experiment_ids
                for mid in _items(self.experiments.get(eid) or {}, "mid_measurements")
            )
            if not has_grid:
                self._warn(
                    "inst-run-time",
                    path,
                    "non-stationary run without stop_time, integration_timespan or a "
                    "measurement time grid",
                )

        if run.get("input_files"):
            roles = {
                role
                for fid in _ids(run.get("input_files"))
                for role in _ids((self.source_files.get(fid) or {}).get("role"))
            }
            if not roles & {"network", "driver_script"}:
                self._warn(
                    "run-network-file",
                    path,
                    "input_files declare no file with role network (or driver_script)",
                )

        self._check_variables(run, path)
        self._check_results(run, modes, status, path)

    def _check_variables(self, run: dict[str, Any], path: str) -> None:
        seen: Counter[tuple[str, str]] = Counter()
        for i, var in enumerate(_items(run, "variables")):
            seen[(str(var.get("variable_id")), str(var.get("variable_kind")))] += 1
            lo, hi = _num(var.get("lower_bound")), _num(var.get("upper_bound"))
            if lo is not None and hi is not None and lo > hi:
                self._error(
                    "variable-spec", f"{path}/variables/{i}", "lower_bound exceeds upper_bound"
                )
        for (vid, kind), n in seen.items():
            if n > 1:
                self._error(
                    "variable-spec", f"{path}/variables", f"{kind} '{vid}' is specified {n} times"
                )

    def _check_results(self, run: dict[str, Any], modes: set[str], status: Any, path: str) -> None:
        solution = run.get("flux_solution")
        model = self._network_for(run.get("network_model_id"))
        if status == "completed" and not solution and modes != {"forward_simulation"}:
            self._warn(
                "results-extracted",
                path,
                "run_status is completed but no flux_solution was recorded (results not "
                "extracted?)",
            )
        if status == "planned" and solution and solution.get("solution_role") == "estimated":
            self._error("results-extracted", path, "a planned run cannot carry estimated results")
        if not solution:
            return
        spath = f"{path}/flux_solution"
        missing_unit = 0
        for i, res in enumerate(_items(solution, "flux_results")):
            rpath = f"{spath}/flux_results/{i}"
            self._check_ci(res, rpath)
            if run.get("network_model_id"):
                self._check_rxn_ref(model, res.get("reaction_id"), rpath)
            if not res.get("flux_unit"):
                missing_unit += 1
        if missing_unit:
            self._warn(
                "flux-unit",
                spath,
                f"{missing_unit} flux result(s) have no flux_unit; cross-run comparison needs it",
            )
        for i, res in enumerate(_items(solution, "pool_size_results")):
            rpath = f"{spath}/pool_size_results/{i}"
            self._check_ci(res, rpath)
            if run.get("network_model_id"):
                self._check_met_ref(model, res.get("metabolite_id"), rpath)
        gof = run.get("goodness_of_fit") or {}
        estimated = solution.get("solution_role") in (None, "estimated")
        isotope = run.get("fluxomics_method") in ISOTOPE_METHODS
        if (
            "estimation" in modes
            and estimated
            and isotope
            and (gof.get("wssr") is None or gof.get("degrees_of_freedom") is None)
        ):
            self._warn(
                "gof-expected",
                path,
                "estimation run without wssr and degrees_of_freedom; fit acceptance cannot "
                "be assessed",
            )

    def _check_ci(self, res: dict[str, Any], path: str) -> None:
        value = _num(res.get("value"))
        lo, hi = _num(res.get("lower_ci")), _num(res.get("upper_ci"))
        if value is None:
            return
        if lo is not None and hi is not None and lo > hi:
            self._error("ci-order", path, f"lower_ci {lo:g} exceeds upper_ci {hi:g}")
        elif (lo is not None and lo > value) or (hi is not None and hi < value):
            message = (
                f"confidence interval [{res.get('lower_ci')}, {res.get('upper_ci')}] does not "
                f"contain the value {res.get('value')}"
            )
            # Sampling-based intervals are quantiles of re-fits and can
            # legitimately exclude the point estimate; analytic ones cannot.
            if res.get("confidence_interval_method") in SAMPLED_CI_METHODS:
                self._warn("ci-order", path, message)
            else:
                self._error("ci-order", path, message)


def validate_dataset(doc: dict[str, Any], *, benchmark: bool | None = None) -> list[Issue]:
    """Run the semantic and tier checks on one dataset document.

    Args:
        doc: The FluxoDataset as a plain dict.
        benchmark: Force benchmark-tier checks on or off; None follows the
            document's ``dataset_type``.

    Returns:
        All issues found, errors and warnings.
    """
    return DatasetValidator(doc, benchmark=benchmark).run()


def schema_issues(doc: dict[str, Any], schema_path: Path = SCHEMA_PATH) -> list[Issue]:
    """Validate a document against the LinkML schema.

    Imports are merged up front so validation does not depend on the working
    directory.

    Args:
        doc: The FluxoDataset as a plain dict.
        schema_path: Path to the root schema file.

    Returns:
        One error per LinkML validation result.
    """
    from linkml.validator import Validator
    from linkml.validator.plugins import JsonschemaValidationPlugin
    from linkml_runtime.utils.schemaview import SchemaView

    view = SchemaView(str(schema_path), merge_imports=True)
    plugins = [JsonschemaValidationPlugin(closed=True)]
    validator = Validator(view.schema, validation_plugins=plugins)
    report = validator.validate(doc, "FluxoDataset")
    return [Issue(ERROR, "schema", "", result.message) for result in report.results]


def validate_file(
    path: str | Path, *, benchmark: bool | None = None, schema: bool = True
) -> list[Issue]:
    """Load a YAML/JSON dataset file and run schema plus semantic validation.

    Args:
        path: The dataset file.
        benchmark: Force benchmark-tier checks on or off; None follows the
            document's ``dataset_type``.
        schema: Also run LinkML schema validation.

    Returns:
        All issues found. Semantic checks are skipped when the schema check
        fails, because they assume a structurally valid document.
    """
    with open(path) as handle:
        doc = yaml.safe_load(handle)
    if not isinstance(doc, dict):
        return [Issue(ERROR, "schema", "", "document is not a mapping")]
    if schema:
        issues = schema_issues(doc)
        if issues:
            return issues
    return validate_dataset(doc, benchmark=benchmark)


def _format_report(path: str, issues: Sequence[Issue], quiet: bool) -> Iterator[str]:
    errors = sum(1 for i in issues if i.severity == ERROR)
    warnings = len(issues) - errors
    for issue in issues:
        if quiet and issue.severity != ERROR:
            continue
        yield f"{path}: {issue}"
    yield f"{path}: {errors} error(s), {warnings} warning(s)"


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point for ``fluxolink-validate``.

    Args:
        argv: Arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code: 0 when no file has errors, 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        prog="fluxolink-validate",
        description=(
            "Validate FluxoDataset files: LinkML schema, references, cross-slot "
            "consistency, and benchmark-tier requirements."
        ),
    )
    parser.add_argument("files", nargs="+", type=Path, help="dataset YAML/JSON files")
    tier = parser.add_mutually_exclusive_group()
    tier.add_argument(
        "--benchmark",
        dest="benchmark",
        action="store_true",
        default=None,
        help="apply benchmark-tier requirements whatever dataset_type says",
    )
    tier.add_argument(
        "--no-benchmark",
        dest="benchmark",
        action="store_false",
        help="skip benchmark-tier requirements whatever dataset_type says",
    )
    parser.add_argument("--no-schema", action="store_true", help="skip LinkML validation")
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as errors for the exit code"
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="print errors only")
    args = parser.parse_args(argv)

    failed = False
    for path in args.files:
        issues = validate_file(path, benchmark=args.benchmark, schema=not args.no_schema)
        for line in _format_report(str(path), issues, args.quiet):
            print(line)
        if any(i.severity == ERROR or args.strict for i in issues):
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
