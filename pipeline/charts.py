"""Generate static SVG chart previews for README."""

from __future__ import annotations

import json
import math
from datetime import date as dt_date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_PATH = ROOT / "data" / "processed" / "analysis.json"
OUT_DIR = ROOT / "assets" / "charts"

W, H = 900, 420
MARGIN = {"top": 60, "right": 30, "bottom": 50, "left": 70}
IW = W - MARGIN["left"] - MARGIN["right"]
IH = H - MARGIN["top"] - MARGIN["bottom"]

ARC_COLOR = "#0f766e"
HLE_COLOR = "#b91c1c"
GRID_COLOR = "#d3dfd4"
TEXT_COLOR = "#1d2a1d"
MUTED_COLOR = "#5a6e58"
BG_COLOR = "#fbfdfb"
FONT = "system-ui, -apple-system, sans-serif"
MONO = "ui-monospace, 'SF Mono', monospace"


def _load() -> dict[str, Any]:
    return json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _scale(v: float, lo: float, hi: float, dst_lo: float, dst_hi: float) -> float:
    if hi <= lo:
        return (dst_lo + dst_hi) / 2
    return dst_lo + (v - lo) / (hi - lo) * (dst_hi - dst_lo)


def _nice_ticks(lo: float, hi: float, count: int = 5) -> list[float]:
    if hi <= lo:
        return [lo]
    raw = (hi - lo) / count
    mag = 10 ** math.floor(math.log10(raw))
    res = raw / mag
    step = mag if res <= 1.5 else 2 * mag if res <= 3 else 5 * mag if res <= 7 else 10 * mag
    start = math.floor(lo / step) * step
    ticks: list[float] = []
    v = start
    while v <= hi + step * 0.01:
        if v >= lo - step * 0.01:
            ticks.append(round(v, 10))
        v += step
    return ticks


def _write(name: str, content: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(content, encoding="utf-8")


def _header(title: str, subtitle: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<rect width="{W}" height="{H}" fill="{BG_COLOR}" rx="8"/>'
        f'<text x="{MARGIN["left"]}" y="30" font-family="{FONT}" font-size="20" font-weight="700" fill="{TEXT_COLOR}">{_esc(title)}</text>'
        f'<text x="{MARGIN["left"]}" y="48" font-family="{FONT}" font-size="12" fill="{MUTED_COLOR}">{_esc(subtitle)}</text>'
    )


def _axes_xy(x_ticks: list[float], y_ticks: list[float],
             x_label: str, y_label: str,
             x_lo: float, x_hi: float, y_lo: float, y_hi: float) -> str:
    ox, oy = MARGIN["left"], MARGIN["top"]
    parts: list[str] = []

    for yv in y_ticks:
        py = oy + _scale(yv, y_lo, y_hi, IH, 0)
        parts.append(f'<line x1="{ox}" y1="{py:.1f}" x2="{ox + IW}" y2="{py:.1f}" stroke="{GRID_COLOR}" stroke-width="0.5"/>')
        parts.append(f'<text x="{ox - 8}" y="{py + 4:.1f}" font-family="{MONO}" font-size="10" fill="{MUTED_COLOR}" text-anchor="end">{yv:g}</text>')

    for xv in x_ticks:
        px = ox + _scale(xv, x_lo, x_hi, 0, IW)
        parts.append(f'<line x1="{px:.1f}" y1="{oy + IH}" x2="{px:.1f}" y2="{oy + IH + 5}" stroke="{GRID_COLOR}"/>')
        parts.append(f'<text x="{px:.1f}" y="{oy + IH + 18}" font-family="{MONO}" font-size="10" fill="{MUTED_COLOR}" text-anchor="middle">{xv:g}</text>')

    parts.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy + IH}" stroke="{GRID_COLOR}"/>')
    parts.append(f'<line x1="{ox}" y1="{oy + IH}" x2="{ox + IW}" y2="{oy + IH}" stroke="{GRID_COLOR}"/>')
    parts.append(f'<text x="{ox + IW / 2}" y="{oy + IH + 38}" font-family="{FONT}" font-size="11" fill="{MUTED_COLOR}" text-anchor="middle">{_esc(x_label)}</text>')
    parts.append(f'<text x="14" y="{oy + IH / 2}" font-family="{FONT}" font-size="11" fill="{MUTED_COLOR}" text-anchor="middle" transform="rotate(-90, 14, {oy + IH / 2})">{_esc(y_label)}</text>')
    return "\n".join(parts)


def _legend(items: list[tuple[str, str]], x: float, y: float) -> str:
    parts: list[str] = []
    cx = x
    for label, color in items:
        parts.append(f'<circle cx="{cx}" cy="{y}" r="4" fill="{color}"/>')
        parts.append(f'<text x="{cx + 8}" y="{y + 3}" font-family="{FONT}" font-size="10" fill="{MUTED_COLOR}">{_esc(label)}</text>')
        cx += len(label) * 6.5 + 24
    return "\n".join(parts)


def _gen_efficiency(data: dict) -> None:
    pts = [p for p in data.get("efficiency_map", {}).get("points", []) if p["cost_per_task"] > 0 and p["score"] > 0]
    pareto = data.get("efficiency_map", {}).get("pareto_frontier", [])
    if not pts:
        return

    ox, oy = MARGIN["left"], MARGIN["top"]
    scores = [p["score"] for p in pts]
    costs = [p["cost_per_task"] for p in pts]
    x_lo, x_hi = min(costs), max(costs)
    y_hi = max(scores)
    x_ticks = _nice_ticks(x_lo, x_hi)
    y_ticks = _nice_ticks(0, y_hi)
    y_hi = max(y_ticks) if y_ticks else y_hi

    out = [_header("Efficiency Illusion Map", f"{len(pts)} models | Cost per task vs ARC score")]
    out.append(_axes_xy(x_ticks, y_ticks, "Cost per task (USD)", "ARC score (%)", x_lo, x_hi, 0, y_hi))
    out.append(_legend([("Models", ARC_COLOR), ("Pareto frontier", HLE_COLOR)], ox, oy - 14))

    for p in pts:
        px = ox + _scale(p["cost_per_task"], x_lo, x_hi, 0, IW)
        py = oy + _scale(p["score"], 0, y_hi, IH, 0)
        out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{ARC_COLOR}" opacity="0.5"/>')

    pareto_ok = [p for p in pareto if p.get("cost_per_task", 0) > 0]
    if len(pareto_ok) >= 2:
        d_parts = []
        for i, p in enumerate(pareto_ok):
            px = ox + _scale(p["cost_per_task"], x_lo, x_hi, 0, IW)
            py = oy + _scale(p["score"], 0, y_hi, IH, 0)
            d_parts.append(f"{'M' if i == 0 else 'L'}{px:.1f},{py:.1f}")
        out.append(f'<path d="{" ".join(d_parts)}" fill="none" stroke="{HLE_COLOR}" stroke-width="2"/>')

    for p in sorted(pts, key=lambda p: p["score"], reverse=True)[:6]:
        px = ox + _scale(p["cost_per_task"], x_lo, x_hi, 0, IW)
        py = oy + _scale(p["score"], 0, y_hi, IH, 0)
        out.append(f'<text x="{px + 6:.1f}" y="{py - 6:.1f}" font-family="{MONO}" font-size="9" fill="{TEXT_COLOR}">{_esc(p["model"][:20])}</text>')

    out.append("</svg>")
    _write("efficiency-map.svg", "\n".join(out))


def _gen_confidence(data: dict) -> None:
    pts = data.get("confidence_lens", {}).get("points", [])
    if not pts:
        return

    ox, oy = MARGIN["left"], MARGIN["top"]
    x_hi = max(p["hle_score"] for p in pts)
    y_hi = max(p["calibration_error"] for p in pts)
    x_ticks = _nice_ticks(0, x_hi)
    y_ticks = _nice_ticks(0, y_hi)
    x_hi = max(x_ticks) if x_ticks else x_hi
    y_hi = max(y_ticks) if y_ticks else y_hi

    out = [_header("Confidence vs Competence", f"{len(pts)} models | HLE accuracy vs calibration error")]
    out.append(_axes_xy(x_ticks, y_ticks, "HLE accuracy (%)", "Calibration error (lower = better)", 0, x_hi, 0, y_hi))
    out.append(_legend([("Model (size = ARC score)", ARC_COLOR)], ox, oy - 14))

    # Quadrant hints
    out.append(f'<text x="{ox + IW - 4}" y="{oy + IH - 8}" font-family="{FONT}" font-size="9" fill="{MUTED_COLOR}" text-anchor="end" opacity="0.6">Ideal: accurate &amp; calibrated</text>')
    out.append(f'<text x="{ox + 4}" y="{oy + 12}" font-family="{FONT}" font-size="9" fill="{MUTED_COLOR}" opacity="0.6">Danger: overconfident</text>')

    for p in pts:
        px = ox + _scale(p["hle_score"], 0, x_hi, 0, IW)
        py = oy + _scale(p["calibration_error"], 0, y_hi, IH, 0)
        arc = p.get("arc_agi_2") or 10
        r = max(3, min(12, math.sqrt(arc) * 1.3))
        out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r:.1f}" fill="{ARC_COLOR}" opacity="0.5"/>')

    for p in sorted(pts, key=lambda p: p["hle_score"], reverse=True)[:6]:
        px = ox + _scale(p["hle_score"], 0, x_hi, 0, IW)
        py = oy + _scale(p["calibration_error"], 0, y_hi, IH, 0)
        out.append(f'<text x="{px + 6:.1f}" y="{py - 6:.1f}" font-family="{MONO}" font-size="9" fill="{TEXT_COLOR}">{_esc(p["model"][:20])}</text>')

    out.append("</svg>")
    _write("confidence-lens.svg", "\n".join(out))


def _gen_transfer_gap(data: dict) -> None:
    pts = data.get("transfer_gap", {}).get("points", [])[:18]
    if not pts:
        return

    all_s = [p["arc_agi_2"] for p in pts] + [p["hle"] for p in pts]
    x_hi = max(all_s) if all_s else 100
    x_ticks = _nice_ticks(0, x_hi)
    x_hi = max(x_ticks) if x_ticks else x_hi

    row_h = 22
    ch = MARGIN["top"] + len(pts) * row_h + MARGIN["bottom"]
    ox = MARGIN["left"] + 90
    iw = W - ox - MARGIN["right"]

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{ch}" viewBox="0 0 {W} {ch}">',
        f'<rect width="{W}" height="{ch}" fill="{BG_COLOR}" rx="8"/>',
        f'<text x="{ox}" y="30" font-family="{FONT}" font-size="20" font-weight="700" fill="{TEXT_COLOR}">Transfer Gap Matrix</text>',
        f'<text x="{ox}" y="48" font-family="{FONT}" font-size="12" fill="{MUTED_COLOR}">{len(pts)} models | ARC-AGI vs HLE score gap</text>',
    ]
    out.append(_legend([("ARC-AGI", ARC_COLOR), ("HLE", HLE_COLOR)], ox, MARGIN["top"] - 14))

    bottom = MARGIN["top"] + len(pts) * row_h
    for xv in x_ticks:
        px = ox + _scale(xv, 0, x_hi, 0, iw)
        out.append(f'<line x1="{px:.1f}" y1="{MARGIN["top"]}" x2="{px:.1f}" y2="{bottom}" stroke="{GRID_COLOR}" stroke-width="0.5"/>')
        out.append(f'<text x="{px:.1f}" y="{bottom + 16}" font-family="{MONO}" font-size="10" fill="{MUTED_COLOR}" text-anchor="middle">{xv:g}</text>')
    out.append(f'<text x="{ox + iw / 2}" y="{bottom + 36}" font-family="{FONT}" font-size="11" fill="{MUTED_COLOR}" text-anchor="middle">Score (%)</text>')

    for i, p in enumerate(pts):
        cy = MARGIN["top"] + i * row_h + row_h / 2
        arc_x = ox + _scale(p["arc_agi_2"], 0, x_hi, 0, iw)
        hle_x = ox + _scale(p["hle"], 0, x_hi, 0, iw)
        x1, x2 = min(arc_x, hle_x), max(arc_x, hle_x)

        out.append(f'<text x="{ox - 6}" y="{cy + 3:.1f}" font-family="{MONO}" font-size="9" fill="{MUTED_COLOR}" text-anchor="end">{_esc(p["model"][:18])}</text>')
        out.append(f'<line x1="{x1:.1f}" y1="{cy:.1f}" x2="{x2:.1f}" y2="{cy:.1f}" stroke="#a8bbb0" stroke-width="2"/>')
        out.append(f'<circle cx="{arc_x:.1f}" cy="{cy:.1f}" r="4" fill="{ARC_COLOR}"/>')
        out.append(f'<circle cx="{hle_x:.1f}" cy="{cy:.1f}" r="4" fill="{HLE_COLOR}"/>')
        out.append(f'<text x="{x2 + 8:.1f}" y="{cy + 3:.1f}" font-family="{MONO}" font-size="9" fill="{TEXT_COLOR}">{p["gap"]:+.1f}</text>')

    out.append("</svg>")
    _write("transfer-gap.svg", "\n".join(out))


def _gen_twin_rivers(data: dict) -> None:
    raw = [p for p in data.get("twin_rivers", {}).get("points", []) if p.get("release_date")]
    dated = []
    for p in raw:
        try:
            y, m, d = p["release_date"].split("-")
            dd = dt_date(int(y), int(m), int(d))
            dated.append({**p, "_ord": dd.toordinal(), "_d": dd})
        except (ValueError, IndexError):
            pass
    if not dated:
        return

    ox, oy = MARGIN["left"], MARGIN["top"]
    ords = [p["_ord"] for p in dated]
    all_s = [p.get("arc_score", 0) or 0 for p in dated] + [p.get("hle_score", 0) or 0 for p in dated]
    x_lo, x_hi = min(ords), max(ords)
    y_hi = max(all_s) if all_s else 100
    y_ticks = _nice_ticks(0, y_hi)
    y_hi = max(y_ticks) if y_ticks else y_hi

    out = [_header("Twin Rivers Timeline", f"{len(dated)} models | ARC-AGI and HLE scores over time")]
    out.append(_legend([("ARC-AGI", ARC_COLOR), ("HLE", HLE_COLOR)], ox, oy - 14))

    # Y grid
    for yv in y_ticks:
        py = oy + _scale(yv, 0, y_hi, IH, 0)
        out.append(f'<line x1="{ox}" y1="{py:.1f}" x2="{ox + IW}" y2="{py:.1f}" stroke="{GRID_COLOR}" stroke-width="0.5"/>')
        out.append(f'<text x="{ox - 8}" y="{py + 4:.1f}" font-family="{MONO}" font-size="10" fill="{MUTED_COLOR}" text-anchor="end">{yv:g}</text>')

    # X labels (unique months)
    seen_months: set[tuple[int, int]] = set()
    for p in sorted(dated, key=lambda x: x["_ord"]):
        ym = (p["_d"].year, p["_d"].month)
        if ym not in seen_months:
            seen_months.add(ym)
            px = ox + _scale(p["_ord"], x_lo, x_hi, 0, IW)
            out.append(f'<text x="{px:.1f}" y="{oy + IH + 16}" font-family="{MONO}" font-size="9" fill="{MUTED_COLOR}" text-anchor="middle">{p["_d"].strftime("%b %Y")}</text>')

    out.append(f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy + IH}" stroke="{GRID_COLOR}"/>')
    out.append(f'<line x1="{ox}" y1="{oy + IH}" x2="{ox + IW}" y2="{oy + IH}" stroke="{GRID_COLOR}"/>')
    out.append(f'<text x="{ox + IW / 2}" y="{oy + IH + 38}" font-family="{FONT}" font-size="11" fill="{MUTED_COLOR}" text-anchor="middle">Release date</text>')
    out.append(f'<text x="14" y="{oy + IH / 2}" font-family="{FONT}" font-size="11" fill="{MUTED_COLOR}" text-anchor="middle" transform="rotate(-90, 14, {oy + IH / 2})">Score (%)</text>')

    # Bridges
    for p in dated:
        if p.get("arc_score") is not None and p.get("hle_score") is not None:
            px = ox + _scale(p["_ord"], x_lo, x_hi, 0, IW)
            out.append(f'<line x1="{px:.1f}" y1="{oy + _scale(p["arc_score"], 0, y_hi, IH, 0):.1f}" x2="{px:.1f}" y2="{oy + _scale(p["hle_score"], 0, y_hi, IH, 0):.1f}" stroke="#cad8cb" stroke-width="1"/>')

    # Dots
    for p in dated:
        px = ox + _scale(p["_ord"], x_lo, x_hi, 0, IW)
        if p.get("arc_score") is not None:
            py = oy + _scale(p["arc_score"], 0, y_hi, IH, 0)
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{ARC_COLOR}"/>')
        if p.get("hle_score") is not None:
            py = oy + _scale(p["hle_score"], 0, y_hi, IH, 0)
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{HLE_COLOR}"/>')

    # Label top-5
    for p in sorted(dated, key=lambda p: p.get("arc_score", 0) or 0, reverse=True)[:5]:
        px = ox + _scale(p["_ord"], x_lo, x_hi, 0, IW)
        py = oy + _scale(p.get("arc_score", 0) or 0, 0, y_hi, IH, 0)
        out.append(f'<text x="{px + 6:.1f}" y="{py - 6:.1f}" font-family="{MONO}" font-size="9" fill="{TEXT_COLOR}">{_esc(p["model"][:18])}</text>')

    out.append("</svg>")
    _write("twin-rivers.svg", "\n".join(out))


def generate() -> None:
    data = _load()
    _gen_efficiency(data)
    _gen_confidence(data)
    _gen_transfer_gap(data)
    _gen_twin_rivers(data)


if __name__ == "__main__":
    generate()
