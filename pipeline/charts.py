"""Generate simple static SVG previews for README."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_PATH = ROOT / "data" / "processed" / "analysis.json"
OUT_DIR = ROOT / "assets" / "charts"


def _load() -> dict[str, Any]:
    return json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))


def _svg_frame(title: str, body: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360">'
        '<rect width="900" height="360" fill="#f7faf7"/>'
        f'<text x="24" y="36" font-family="Arial" font-size="26" font-weight="700" fill="#152312">{title}</text>'
        f"{body}</svg>"
    )


def _scale(v: float, src_min: float, src_max: float, dst_min: float, dst_max: float) -> float:
    if src_max <= src_min:
        return (dst_min + dst_max) / 2
    ratio = (v - src_min) / (src_max - src_min)
    return dst_min + ratio * (dst_max - dst_min)


def _write(name: str, content: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(content, encoding="utf-8")


def generate() -> None:
    data = _load()

    eff = data.get("efficiency_map", {}).get("points", [])
    if eff:
        xs = [float(p["cost_per_task"]) for p in eff]
        ys = [float(p["score"]) for p in eff]
        circles = []
        for p in eff:
            x = _scale(float(p["cost_per_task"]), min(xs), max(xs), 80, 860)
            y = _scale(float(p["score"]), min(ys), max(ys), 300, 80)
            circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#0f766e" opacity="0.75"/>')
        _write("efficiency-map.svg", _svg_frame("Efficiency Illusion Map", "".join(circles)))

    conf = data.get("confidence_lens", {}).get("points", [])
    if conf:
        xs = [float(p["hle_score"]) for p in conf]
        ys = [float(p["calibration_error"]) for p in conf]
        circles = []
        for p in conf:
            x = _scale(float(p["hle_score"]), min(xs), max(xs), 80, 860)
            y = _scale(float(p["calibration_error"]), min(ys), max(ys), 300, 80)
            circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#b91c1c" opacity="0.75"/>')
        _write("confidence-lens.svg", _svg_frame("Confidence vs Competence", "".join(circles)))

    gap = data.get("transfer_gap", {}).get("points", [])[:12]
    if gap:
        lines = []
        y = 70
        for p in gap:
            x1 = _scale(float(p["hle"]), 0, 100, 120, 860)
            x2 = _scale(float(p["arc_agi_2"]), 0, 100, 120, 860)
            lines.append(f'<line x1="{x1:.1f}" y1="{y}" x2="{x2:.1f}" y2="{y}" stroke="#90a89c" stroke-width="2"/>')
            lines.append(f'<circle cx="{x1:.1f}" cy="{y}" r="4" fill="#b91c1c"/>')
            lines.append(f'<circle cx="{x2:.1f}" cy="{y}" r="4" fill="#0f766e"/>')
            y += 22
        _write("transfer-gap.svg", _svg_frame("Transfer Gap Matrix", "".join(lines)))


if __name__ == "__main__":
    generate()
