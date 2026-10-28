#!/usr/bin/env python3
"""Generate a draw.io-editable SVG entity-relationship diagram of the schema.

Two files are written, both native draw.io documents:

  * `<name>.drawio`     — a plain draw.io/mxGraph file. Open it in draw.io,
    diagrams.net or the VS Code Draw.io extension; fully editable shapes.
  * `<name>.drawio.svg` — the same diagram as an SVG that any browser, IDE
    or GitHub preview renders directly, with the mxGraph model carried in
    the root `<svg>` element's `content` attribute so draw.io can open and
    edit that file too.

Everything is read from `src/fluxolink/schema/*.yaml`, so the picture cannot
drift from the schema: re-run after any schema change.

Usage:  python scripts/gen_erd.py [-o docs/diagrams/fluxolink-erd.drawio.svg]
"""

from __future__ import annotations

import argparse
import glob
import os
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import yaml

REPO = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO / "src" / "fluxolink" / "schema"
DEFAULT_OUT = REPO / "docs" / "diagrams" / "fluxolink-erd.drawio.svg"

# ---------------------------------------------------------------- geometry ---

BOX_W = 300  # recomputed from the longest attribute label by fit_box_width()
HDR_H = 30
ROW_H = 17
BOX_GAP = 34
COL_GAP = 150
MARGIN_X = 48
TOP_H = 150  # title band
LEGEND_H = 176

# Per-module palette: (fill, stroke, header fill, header text)
PALETTE = {
    "fluxolink": ("#F2F4FD", "#3B4CA8", "#3B4CA8", "#FFFFFF"),
    "investigation": ("#F1F6F3", "#2F6E52", "#2F6E52", "#FFFFFF"),
    "experiment": ("#FBF4EC", "#9A6512", "#9A6512", "#FFFFFF"),
    "network": ("#F3F1F8", "#5B4A9E", "#5B4A9E", "#FFFFFF"),
    "simulation_run": ("#FAF1F1", "#9C3A32", "#9C3A32", "#FFFFFF"),
    "enums": ("#F4F5F7", "#5A6472", "#5A6472", "#FFFFFF"),
}

INK = "#1D2430"
MUTED = "#68717F"
EDGE_COMPOSE = "#3B4CA8"
EDGE_REF = "#9C3A32"
PAPER = "#FFFFFF"

# Column assignment. Ordered so that most references land between neighbours;
# `experiment` is split in two so column heights stay comparable.
COLUMNS: list[tuple[str, list[str]]] = [
    ("investigation", ["Investigation", "Contributor"]),
    (
        "experiment",
        [
            "LabelingExperiment",
            "Condition",
            "LabeledSource",
            "TracerIsotopomer",
            "SourceFile",
            "EquivalenceCheck",
        ],
    ),
    (
        "experiment",
        [
            "MIDMeasurement",
            "MIDDataPoint",
            "NMRIsotopomerMeasurement",
            "NMRIsotopomerDataPoint",
            "FluxMeasurement",
            "PoolSizeMeasurement",
            "FluxRatioMeasurement",
            "PoolSizeRatioMeasurement",
        ],
    ),
    (
        "network",
        [
            "MetabolicNetworkModel",
            "NetworkMetabolite",
            "NetworkReaction",
            "ReactionParticipant",
            "AtomTransitionVariant",
            "AtomTransition",
            "FluxConstraint",
            "PoolSizeConstraint",
        ],
    ),
    (
        "simulation_run",
        ["SimulationRun", "SoftwareInfo", "SolverOption", "VariableSpecification"],
    ),
    (
        "simulation_run",
        [
            "FluxSolution",
            "FluxResult",
            "PoolSizeResult",
            "SimulatedMID",
            "SimulatedMIDDataPoint",
            "MeasurementFitResult",
            "ScaleFactorResult",
            "GoodnessOfFit",
        ],
    ),
]


# ------------------------------------------------------------------- model ---


@dataclass
class Attr:
    """One LinkML slot, reduced to what the diagram needs."""

    name: str
    range: str
    kind: str  # "prim" | "class" | "enum"
    identifier: bool = False
    required: bool = False
    recommended: bool = False
    multivalued: bool = False
    inlined: bool = False

    @property
    def label(self) -> str:
        """Render the slot as one text row."""
        marker = (
            "PK"
            if self.identifier
            else ("*" if self.required else ("+" if self.recommended else " "))
        )
        rng = f"{self.range}[]" if self.multivalued else self.range
        return f"{marker} {self.name} : {rng}"


@dataclass
class Cls:
    """One LinkML class, plus its computed position on the canvas."""

    name: str
    module: str
    tree_root: bool = False
    class_uri: str | None = None
    attrs: list[Attr] = field(default_factory=list)
    rules: list[dict] = field(default_factory=list)
    # layout
    x: float = 0
    y: float = 0

    @property
    def h(self) -> float:
        """Box height: header plus one row per slot."""
        return HDR_H + ROW_H * len(self.attrs)

    @property
    def cx(self) -> float:
        """Horizontal centre of the box."""
        return self.x + BOX_W / 2

    @property
    def cy(self) -> float:
        """Vertical centre of the box."""
        return self.y + self.h / 2


@dataclass
class Edge:
    """A slot whose range is another class: containment or reference."""

    src: str
    dst: str
    slot: str
    compose: bool
    multi: bool


def load() -> tuple[dict[str, Cls], dict[str, int], str]:
    """Read every schema module and return its classes, enums and version."""
    classes: dict[str, Cls] = {}
    enums: dict[str, int] = {}
    raw: dict[str, dict] = {}
    version = "?"
    for path in sorted(glob.glob(str(SCHEMA_DIR / "*.yaml"))):
        if Path(path).name == "flux_record.yaml":  # a derived view, not the dataset
            continue
        mod = os.path.basename(path)[:-5]
        doc = yaml.safe_load(Path(path).read_text()) or {}
        if doc.get("version"):
            version = doc["version"]
        raw[mod] = doc
        for name, body in (doc.get("enums") or {}).items():
            enums[name] = len(((body or {}).get("permissible_values")) or {})
    for mod, doc in raw.items():
        for name, body in (doc.get("classes") or {}).items():
            body = body or {}
            classes[name] = Cls(
                name=name,
                module=mod,
                tree_root=bool(body.get("tree_root")),
                class_uri=body.get("class_uri"),
                rules=list(body.get("rules") or []),
            )
    for _mod, doc in raw.items():
        for name, body in (doc.get("classes") or {}).items():
            body = body or {}
            for slot, spec in (body.get("attributes") or {}).items():
                spec = spec or {}
                rng = spec.get("range", "string")
                kind = "class" if rng in classes else ("enum" if rng in enums else "prim")
                classes[name].attrs.append(
                    Attr(
                        name=slot,
                        range=rng,
                        kind=kind,
                        identifier=bool(spec.get("identifier")),
                        required=bool(spec.get("required")),
                        recommended=bool(spec.get("recommended")),
                        multivalued=bool(spec.get("multivalued")),
                        inlined=bool(spec.get("inlined_as_list") or spec.get("inlined")),
                    )
                )
    return classes, enums, version


def _kind_colour(kind: str) -> str:
    """Colour an attribute's type by what it points at."""
    if kind == "class":
        return EDGE_COMPOSE
    if kind == "enum":
        return "#5A6472"
    return INK


ATTR_X = 28  # left inset of the attribute text
CHAR_W = 6.35  # advance width of the 10.5px monospace face
PAD_R = 14


def fit_box_width(classes: dict[str, Cls], enums: dict[str, int]) -> int:
    """Widen the boxes until the longest label fits, then round to a 10px grid.

    Sized from data rather than guessed: `confidence_interval_method :
    ConfidenceIntervalMethodEnum` is 56 characters and silently overflowed a
    300px box.
    """
    longest = 0
    for cls in classes.values():
        for a in cls.attrs:
            longest = max(longest, len(f"{a.name} : {a.range}" + ("[]" if a.multivalued else "")))
    for name, n in enums.items():
        longest = max(longest, len(f"{name}  ({n})"))
    need = ATTR_X + longest * CHAR_W + PAD_R
    return max(300, int(-(-need // 10) * 10))


def rule_lines(classes: dict[str, Cls]) -> list[str]:
    """Describe every class rule in the schema, read from the schema itself.

    Hardcoding this went stale the moment the tier rule stopped requiring
    `experiments` -- exactly the drift this generator exists to prevent.
    """
    lines: list[str] = []
    for cls in sorted(classes.values(), key=lambda c: c.name):
        for rule in cls.rules:
            title = rule.get("title") or "(untitled)"
            pre = " and ".join(_conditions(rule.get("preconditions"))) or "always"
            post = " and ".join(f"{c} required" for c in _conditions(rule.get("postconditions")))
            lines.append(f"{cls.name} · {title}")
            lines += _wrap(f"{pre}  ⇒  {post or '(nothing)'}", 52, indent="   ")
    if not lines:
        lines = ["(the schema declares no class rules)"]
    lines.append("")
    lines += _wrap(
        "Enforced, not decorative: rules compile to JSON Schema "
        "if/then and linkml-validate rejects violations.",
        50,
    )
    return lines


def _conditions(block: dict | None) -> list[str]:
    """Flatten one rule pre/postcondition block into readable clauses."""
    out: list[str] = []
    for slot, cond in ((block or {}).get("slot_conditions") or {}).items():
        cond = cond or {}
        if "equals_string" in cond:
            out.append(f"{slot} == {cond['equals_string']}")
        else:
            out.append(slot)
    return out


def _wrap(text: str, width: int, indent: str = "") -> list[str]:
    """Greedy word wrap; SVG has no text layout of its own."""
    line, out = "", []
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if len(candidate) > width and line:
            out.append(indent + line if out else line)
            line = word
        else:
            line = candidate
    if line:
        out.append(indent + line if out else line)
    return out


def build_edges(classes: dict[str, Cls]) -> list[Edge]:
    """Derive one edge per slot whose range is a class."""
    edges: list[Edge] = []
    for cls in classes.values():
        for a in cls.attrs:
            if a.kind != "class":
                continue
            edges.append(
                Edge(
                    src=cls.name,
                    dst=a.range,
                    slot=a.name,
                    compose=a.inlined,
                    multi=a.multivalued,
                )
            )
    return edges


def layout(classes: dict[str, Cls], enums: dict[str, int]) -> tuple[float, float, dict]:
    """Place the root, the module columns, and the enum panel."""
    placed: set[str] = set()
    x = MARGIN_X
    body_top = TOP_H + 40
    max_bottom = body_top

    # The root is placed after the columns so it can be centred over them.
    root = classes["FluxoDataset"]
    root.y = body_top
    placed.add(root.name)

    col_top = root.y + root.h + 64
    for _module, names in COLUMNS:
        y = col_top
        for name in names:
            cls = classes[name]
            cls.x = x
            cls.y = y
            placed.add(name)
            y += cls.h + BOX_GAP
        max_bottom = max(max_bottom, y)
        x += BOX_W + COL_GAP

    missing = set(classes) - placed
    if missing:  # safety net: a class was added to the schema but not to COLUMNS
        y = col_top
        for name in sorted(missing):
            cls = classes[name]
            cls.x = x
            cls.y = y
            y += cls.h + BOX_GAP
        max_bottom = max(max_bottom, y)
        x += BOX_W + COL_GAP

    enum_panel = {
        "x": x,
        "y": col_top,
        "w": BOX_W,
        "h": HDR_H + ROW_H * len(enums) + 8,
    }
    max_bottom = max(max_bottom, enum_panel["y"] + enum_panel["h"])
    width = x + BOX_W + MARGIN_X

    # Centre the root over everything now that the full span is known.
    root.x = (width - BOX_W) / 2

    height = max_bottom + LEGEND_H

    # Self-check: nothing may fall outside the declared canvas, or the SVG
    # silently clips and the draw.io page size is wrong too.
    right = max([c.x + BOX_W for c in classes.values()] + [enum_panel["x"] + enum_panel["w"]])
    bottom = max([c.y + c.h for c in classes.values()] + [enum_panel["y"] + enum_panel["h"]])
    assert right <= width - MARGIN_X + 1, (
        f"content overflows right edge: {right} > {width - MARGIN_X}"
    )
    assert bottom <= height - LEGEND_H + 1, (
        f"content overflows into legend: {bottom} > {height - LEGEND_H}"
    )

    return (
        width,
        height,
        {
            "enum_panel": enum_panel,
            "missing": sorted(missing),
            "rule_lines": rule_lines(classes),
        },
    )


# ------------------------------------------------------------- edge routing ---


def route(src: Cls, dst: Cls) -> tuple[str, tuple[float, float]]:
    """An orthogonal-ish cubic path between two boxes, plus its arrow anchor.

    Edges are painted before the boxes, so a path passing under a box reads as
    going behind it. Self-references are drawn as a small loop on the right.
    """
    if src.name == dst.name:
        x, y = src.x + BOX_W, src.cy
        d = f"M {x} {y - 14} C {x + 54} {y - 24}, {x + 54} {y + 24}, {x} {y + 14}"
        return d, (x + 2, y + 14)

    if abs(src.cx - dst.cx) < 1:  # same column: run down the gutter to its left
        down = src.y < dst.y
        gx = src.x - 30
        y0 = src.y + src.h if down else src.y
        y1 = dst.y if down else dst.y + dst.h
        sx = src.x + 34
        d = (
            f"M {sx} {y0} C {sx} {y0 + (20 if down else -20)}, {gx} {y0}, {gx} {(y0 + y1) / 2} "
            f"C {gx} {y1}, {sx} {y1 + (-20 if down else 20)}, {sx} {y1}"
        )
        return d, (sx, y1)

    if src.cx < dst.cx:
        x0, x1 = src.x + BOX_W, dst.x
        anchor = (x1, dst.cy)
    else:
        x0, x1 = src.x, dst.x + BOX_W
        anchor = (x1, dst.cy)
    y0, y1 = src.cy, dst.cy
    mid = (x0 + x1) / 2
    d = f"M {x0} {y0} C {mid} {y0}, {mid} {y1}, {x1} {y1}"
    return d, anchor


# --------------------------------------------------------------- mxGraph ----


def mxgraph(
    classes: dict[str, Cls],
    enums: dict[str, int],
    edges: list[Edge],
    meta: dict,
    w: float,
    h: float,
) -> str:
    """Build the mxGraph model that draw.io will open for editing."""
    cells: list[str] = []

    def cid(name: str) -> str:
        return f"cls_{name}"

    for cls in classes.values():
        fill, stroke, hdr, hdr_txt = PALETTE[cls.module]
        title = cls.name + ("  «root»" if cls.tree_root else "")
        style = (
            "swimlane;html=1;whiteSpace=wrap;childLayout=stackLayout;horizontal=1;"
            f"startSize={HDR_H};horizontalStack=false;resizeParent=1;resizeParentMax=0;"
            f"fontStyle=1;fontSize=13;fillColor={fill};strokeColor={stroke};"
            f"swimlaneFillColor={fill};fontColor={hdr_txt};swimlaneLine=1;"
            f"rounded=1;arcSize=6;shadow=0;strokeWidth=1.5;"
            f"swimlaneHead=1;fillStyle=solid;gradientColor=none;"
            f"labelBackgroundColor={hdr};"
        )
        cells.append(
            f'<mxCell id="{cid(cls.name)}" value={quoteattr(title)} style={quoteattr(style)} '
            f'vertex="1" parent="1"><mxGeometry x="{cls.x}" y="{cls.y}" width="{BOX_W}" '
            f'height="{cls.h}" as="geometry"/></mxCell>'
        )
        for i, a in enumerate(cls.attrs):
            colour = _kind_colour(a.kind)
            weight = "fontStyle=1;" if (a.identifier or a.required) else ""
            rstyle = (
                "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;"
                f"spacingLeft=8;spacingRight=6;overflow=hidden;rotatable=0;fontSize=11;"
                f"fontColor={colour};{weight}points=[[0,0.5],[1,0.5]];portConstraint=eastwest;"
            )
            cells.append(
                f'<mxCell id="{cid(cls.name)}_a{i}" value={quoteattr(a.label)} '
                f'style={quoteattr(rstyle)} vertex="1" parent="{cid(cls.name)}">'
                f'<mxGeometry y="{HDR_H + i * ROW_H}" width="{BOX_W}" height="{ROW_H}" '
                f'as="geometry"/></mxCell>'
            )

    # Enum panel
    panel = meta["enum_panel"]
    fill, stroke, _hdr, hdr_txt = PALETTE["enums"]
    pstyle = (
        "swimlane;html=1;childLayout=stackLayout;horizontal=1;"
        f"startSize={HDR_H};horizontalStack=false;resizeParent=1;resizeParentMax=0;"
        f"fontStyle=1;fontSize=13;fillColor={fill};strokeColor={stroke};fontColor={hdr_txt};"
        "rounded=1;arcSize=6;strokeWidth=1.5;"
    )
    cells.append(
        f'<mxCell id="enums" value="Enumerations ({len(enums)})" style={quoteattr(pstyle)} vertex="1" '
        f'parent="1"><mxGeometry x="{panel["x"]}" y="{panel["y"]}" width="{panel["w"]}" '
        f'height="{panel["h"]}" as="geometry"/></mxCell>'
    )
    for i, (name, n) in enumerate(sorted(enums.items())):
        rstyle = (
            "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;"
            f"spacingLeft=8;overflow=hidden;rotatable=0;fontSize=11;fontColor={INK};"
        )
        cells.append(
            f'<mxCell id="enum_{i}" value={quoteattr(f"{name}  ({n})")} style={quoteattr(rstyle)} '
            f'vertex="1" parent="enums"><mxGeometry y="{HDR_H + i * ROW_H}" width="{panel["w"]}" '
            f'height="{ROW_H}" as="geometry"/></mxCell>'
        )

    for i, e in enumerate(edges):
        if e.compose:
            style = (
                "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;jettySize=auto;orthogonalLoop=1;"
                f"startArrow=diamondThin;startFill=1;startSize=10;endArrow=none;"
                f"strokeColor={EDGE_COMPOSE};strokeWidth=1.4;"
            )
        else:
            style = (
                "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;jettySize=auto;orthogonalLoop=1;"
                f"dashed=1;dashPattern=6 4;endArrow=open;endFill=0;endSize=8;"
                f"strokeColor={EDGE_REF};strokeWidth=1.2;"
            )
        card = "1..*" if (e.multi and e.compose) else ("*" if e.multi else "")
        label = f"{e.slot}{'  ' + card if card else ''}"
        cells.append(
            f'<mxCell id="edge_{i}" value={quoteattr(label)} style={quoteattr(style)} edge="1" '
            f'parent="1" source="{cid(e.src)}" target="{cid(e.dst)}">'
            f'<mxGeometry relative="1" as="geometry"/></mxCell>'
        )

    body = "".join(cells)
    return (
        '<mxfile host="app.diagrams.net" agent="fluxolink scripts/gen_erd.py" type="device">'
        '<diagram id="fluxolink-erd" name="FluxoLink data model">'
        f'<mxGraphModel dx="0" dy="0" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
        f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="{int(w)}" pageHeight="{int(h)}" '
        f'math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}'
        "</root></mxGraphModel></diagram></mxfile>"
    )


# ------------------------------------------------------------------- SVG ----

MONO = "'IBM Plex Mono','SFMono-Regular',Menlo,Consolas,monospace"
SANS = "'Public Sans','Helvetica Neue',Helvetica,Arial,sans-serif"


def svg_body(
    classes: dict[str, Cls],
    enums: dict[str, int],
    edges: list[Edge],
    meta: dict,
    w: float,
    h: float,
    version: str,
) -> str:
    """Draw the same model as plain SVG, so the file renders without draw.io."""
    o: list[str] = []
    a = o.append

    a(
        "<defs>"
        f'<marker id="ref" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="{EDGE_REF}" '
        'stroke-width="1.4"/></marker>'
        f'<marker id="dia" viewBox="0 0 12 12" refX="1" refY="6" markerWidth="9" markerHeight="9" '
        f'orient="auto"><path d="M 1 6 L 6 3 L 11 6 L 6 9 z" fill="{EDGE_COMPOSE}" '
        f'stroke="{EDGE_COMPOSE}"/></marker>'
        "</defs>"
    )
    a(f'<rect x="0" y="0" width="{w}" height="{h}" fill="{PAPER}"/>')

    # ---- title band
    a(
        f'<text x="{MARGIN_X}" y="58" font-family="{SANS}" font-size="30" font-weight="700" '
        f'fill="{INK}">FluxoLink data model</text>'
    )
    a(
        f'<text x="{MARGIN_X}" y="86" font-family="{SANS}" font-size="14" fill="{MUTED}">'
        f"LinkML schema v{escape(version)} &#183; {len(classes)} classes &#183; {len(enums)} enumerations "
        f"&#183; {sum(len(c.attrs) for c in classes.values())} slots &#183; {len(edges)} relationships</text>"
    )
    a(
        f'<text x="{MARGIN_X}" y="108" font-family="{SANS}" font-size="12.5" fill="{MUTED}">'
        "Generated from src/fluxolink/schema/*.yaml by scripts/gen_erd.py &#8212; editable in "
        "draw.io (the mxGraph model is embedded in this file).</text>"
    )
    a(
        f'<line x1="{MARGIN_X}" y1="{TOP_H - 22}" x2="{w - MARGIN_X}" y2="{TOP_H - 22}" stroke="#DDE1E8" stroke-width="1"/>'
    )

    # ---- edges first, so boxes occlude them
    for e in edges:
        src, dst = classes[e.src], classes[e.dst]
        d, anchor = route(src, dst)
        if e.compose:
            a(
                f'<path d="{d}" fill="none" stroke="{EDGE_COMPOSE}" stroke-width="1.4" '
                f'opacity="0.7" marker-start="url(#dia)"/>'
            )
        else:
            a(
                f'<path d="{d}" fill="none" stroke="{EDGE_REF}" stroke-width="1.2" '
                f'stroke-dasharray="6 4" opacity="0.5" marker-end="url(#ref)"/>'
            )
        _ = anchor

    # ---- class boxes
    for cls in classes.values():
        fill, stroke, hdr, hdr_txt = PALETTE[cls.module]
        a(
            f'<g><rect x="{cls.x}" y="{cls.y}" width="{BOX_W}" height="{cls.h}" rx="6" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        )
        a(
            f'<path d="M {cls.x} {cls.y + HDR_H} L {cls.x} {cls.y + 6} '
            f"Q {cls.x} {cls.y} {cls.x + 6} {cls.y} L {cls.x + BOX_W - 6} {cls.y} "
            f"Q {cls.x + BOX_W} {cls.y} {cls.x + BOX_W} {cls.y + 6} "
            f'L {cls.x + BOX_W} {cls.y + HDR_H} z" fill="{hdr}"/>'
        )
        title = escape(cls.name)
        a(
            f'<text x="{cls.x + 10}" y="{cls.y + 20}" font-family="{SANS}" font-size="13.5" '
            f'font-weight="700" fill="{hdr_txt}">{title}</text>'
        )
        badge = []
        if cls.tree_root:
            badge.append("root")
        if cls.rules:
            badge.append(f"{len(cls.rules)} rule" + ("s" if len(cls.rules) > 1 else ""))
        if badge:
            a(
                f'<text x="{cls.x + BOX_W - 10}" y="{cls.y + 20}" text-anchor="end" '
                f'font-family="{SANS}" font-size="10.5" font-weight="600" fill="{hdr_txt}" '
                f'opacity="0.85">{escape(" · ".join(badge))}</text>'
            )
        for i, at in enumerate(cls.attrs):
            ty = cls.y + HDR_H + i * ROW_H + 12
            if i % 2 == 1:
                a(
                    f'<rect x="{cls.x + 1}" y="{cls.y + HDR_H + i * ROW_H}" width="{BOX_W - 2}" '
                    f'height="{ROW_H}" fill="{stroke}" opacity="0.035"/>'
                )
            mark = (
                "PK"
                if at.identifier
                else ("*" if at.required else ("+" if at.recommended else ""))
            )
            if mark:
                a(
                    f'<text x="{cls.x + 8}" y="{ty}" font-family="{MONO}" font-size="9" '
                    f'font-weight="700" fill="{stroke}">{mark}</text>'
                )
            colour = _kind_colour(at.kind)
            rng = escape(at.range + ("[]" if at.multivalued else ""))
            bold = ' font-weight="600"' if at.kind != "prim" else ""
            a(
                f'<text x="{cls.x + ATTR_X}" y="{ty}" font-family="{MONO}" font-size="10.5" '
                f'fill="{INK}">{escape(at.name)}'
                f'<tspan fill="{MUTED}"> : </tspan>'
                f'<tspan fill="{colour}"{bold}>{rng}</tspan></text>'
            )
        a("</g>")

    # ---- enum panel
    panel = meta["enum_panel"]
    fill, stroke, hdr, hdr_txt = PALETTE["enums"]
    px, py, pw, ph = panel["x"], panel["y"], panel["w"], panel["h"]
    a(
        f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
    )
    a(
        f'<path d="M {px} {py + HDR_H} L {px} {py + 6} Q {px} {py} {px + 6} {py} '
        f'L {px + pw - 6} {py} Q {px + pw} {py} {px + pw} {py + 6} L {px + pw} {py + HDR_H} z" fill="{hdr}"/>'
    )
    a(
        f'<text x="{px + 10}" y="{py + 20}" font-family="{SANS}" font-size="13.5" font-weight="700" '
        f'fill="{hdr_txt}">Enumerations ({len(enums)})</text>'
    )
    for i, (name, n) in enumerate(sorted(enums.items())):
        ty = py + HDR_H + i * ROW_H + 12
        if i % 2 == 1:
            a(
                f'<rect x="{px + 1}" y="{py + HDR_H + i * ROW_H}" width="{pw - 2}" height="{ROW_H}" fill="{stroke}" opacity="0.035"/>'
            )
        a(
            f'<text x="{px + 10}" y="{ty}" font-family="{MONO}" font-size="10.5" fill="{INK}">'
            f'{escape(name)}<tspan fill="{MUTED}">  ({n})</tspan></text>'
        )

    # ---- legend
    ly = h - LEGEND_H + 26
    a(
        f'<line x1="{MARGIN_X}" y1="{ly - 26}" x2="{w - MARGIN_X}" y2="{ly - 26}" stroke="#DDE1E8" stroke-width="1"/>'
    )
    a(
        f'<text x="{MARGIN_X}" y="{ly}" font-family="{SANS}" font-size="13" font-weight="700" fill="{INK}">Legend</text>'
    )

    lx = MARGIN_X
    a(
        f'<path d="M {lx} {ly + 24} L {lx + 46} {ly + 24}" stroke="{EDGE_COMPOSE}" stroke-width="1.4" marker-start="url(#dia)"/>'
    )
    a(
        f'<text x="{lx + 56}" y="{ly + 28}" font-family="{SANS}" font-size="11.5" fill="{INK}">'
        'containment (<tspan font-family="' + MONO + '" font-size="10.5">inlined_as_list</tspan>) '
        "&#8212; child lives inside the parent document</text>"
    )
    a(
        f'<path d="M {lx} {ly + 48} L {lx + 46} {ly + 48}" stroke="{EDGE_REF}" stroke-width="1.2" stroke-dasharray="6 4" marker-end="url(#ref)"/>'
    )
    a(
        f'<text x="{lx + 56}" y="{ly + 52}" font-family="{SANS}" font-size="11.5" fill="{INK}">'
        "reference &#8212; the slot holds an identifier; LinkML does "
        '<tspan font-weight="700">not</tspan> check that the target exists</text>'
    )

    lx2 = MARGIN_X + 720
    for i, (mark, text) in enumerate(
        [
            ("PK", "identifier slot"),
            ("*", "required"),
            ("+", "recommended"),
            ("[]", "multivalued"),
        ]
    ):
        a(
            f'<text x="{lx2}" y="{ly + 24 + i * 18}" font-family="{MONO}" font-size="10" '
            f'font-weight="700" fill="{MUTED}">{escape(mark)}</text>'
        )
        a(
            f'<text x="{lx2 + 30}" y="{ly + 24 + i * 18}" font-family="{SANS}" font-size="11.5" '
            f'fill="{INK}">{escape(text)}</text>'
        )

    lx3 = MARGIN_X + 980
    a(
        f'<text x="{lx3}" y="{ly}" font-family="{SANS}" font-size="13" font-weight="700" fill="{INK}">Modules</text>'
    )
    for i, (mod, label) in enumerate(
        [
            ("fluxolink", "fluxolink.yaml (root)"),
            ("investigation", "investigation.yaml"),
            ("experiment", "experiment.yaml"),
            ("network", "network.yaml"),
            ("simulation_run", "simulation_run.yaml"),
            ("enums", "enumerations.yaml"),
        ]
    ):
        fill, stroke, _h, _t = PALETTE[mod]
        yy = ly + 18 + i * 17
        a(
            f'<rect x="{lx3}" y="{yy - 9}" width="13" height="13" rx="3" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
        )
        a(
            f'<text x="{lx3 + 22}" y="{yy + 2}" font-family="{MONO}" font-size="10.5" fill="{INK}">{escape(label)}</text>'
        )

    note_x = MARGIN_X + 1340
    a(
        f'<text x="{note_x}" y="{ly}" font-family="{SANS}" font-size="13" font-weight="700" '
        f'fill="{INK}">Conditional requirements</text>'
    )
    for i, line in enumerate(meta["rule_lines"]):
        a(
            f'<text x="{note_x}" y="{ly + 18 + i * 15}" font-family="{SANS}" font-size="11" '
            f'fill="{MUTED}">{escape(line)}</text>'
        )
    return "".join(o)


def main() -> int:
    """Generate the diagram and write it to disk."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default=str(DEFAULT_OUT), type=Path)
    args = ap.parse_args()

    classes, enums, version = load()

    global BOX_W
    BOX_W = fit_box_width(classes, enums)

    edges = build_edges(classes)
    w, h, meta = layout(classes, enums)
    if meta["missing"]:
        print(f"note: classes not in COLUMNS, appended in a spare column: {meta['missing']}")

    model = mxgraph(classes, enums, edges, meta, w, h)
    body = svg_body(classes, enums, edges, meta, w, h, version)

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{int(w)}" height="{int(h)}" viewBox="0 0 {int(w)} {int(h)}" '
        f"content={quoteattr(model)}>\n{body}\n</svg>\n"
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg)

    # The native draw.io file: the same model, no SVG wrapper.
    drawio = args.out.with_suffix("") if args.out.name.endswith(".drawio.svg") else None
    if drawio is None:
        drawio = args.out.with_suffix(".drawio")
    drawio.write_text(model + "\n")

    print(
        f"wrote {drawio}  (draw.io, {len(classes)} classes, {len(edges)} edges, "
        f"{len(model) // 1024} KB)"
    )
    print(
        f"wrote {args.out}  ({int(w)}x{int(h)} SVG + embedded draw.io model, "
        f"{len(svg) // 1024} KB)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
