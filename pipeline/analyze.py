"""Compute derived datasets for chart modules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import PROCESSED_DIR


def _load_unified() -> list[dict[str, Any]]:
    path = PROCESSED_DIR / "unified_models.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing unified records: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_ratio(score: float | None, cost: float | None) -> float | None:
    if score is None or cost in (None, 0):
        return None
    return score / cost


def _pareto_frontier(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Maximize score, minimize cost.
    ordered = sorted(points, key=lambda x: (x["cost_per_task"], -(x["score"] or 0)))
    frontier: list[dict[str, Any]] = []
    best_score = float("-inf")
    for point in ordered:
        score = point.get("score")
        if score is None:
            continue
        if score > best_score:
            frontier.append(point)
            best_score = score
    return frontier


def build_analysis_payload() -> dict[str, Any]:
    rows = _load_unified()

    efficiency = [
        {
            "model": row["canonical_name"],
            "provider": row.get("provider"),
            "score": row.get("arc_score"),
            "cost_per_task": row.get("arc_cost_per_task"),
            "tasks_evaluated": row.get("arc_tasks_evaluated"),
            "efficiency_ratio": _safe_ratio(row.get("arc_score"), row.get("arc_cost_per_task")),
        }
        for row in rows
        if row.get("arc_score") is not None and row.get("arc_cost_per_task") is not None
    ]

    confidence = [
        {
            "model": row["canonical_name"],
            "provider": row.get("provider"),
            "hle_score": row.get("hle_score"),
            "calibration_error": row.get("calibration_error"),
            "arc_agi_2": row.get("hle_arc_agi_2") or row.get("arc_score"),
        }
        for row in rows
        if row.get("hle_score") is not None and row.get("calibration_error") is not None
    ]

    transfer = []
    for row in rows:
        arc_score = row.get("hle_arc_agi_2") or row.get("arc_score")
        hle_score = row.get("hle_score")
        if arc_score is None or hle_score is None:
            continue
        transfer.append(
            {
                "model": row["canonical_name"],
                "provider": row.get("provider"),
                "arc_agi_2": arc_score,
                "hle": hle_score,
                "gap": arc_score - hle_score,
            }
        )

    timeline = [
        {
            "model": row["canonical_name"],
            "provider": row.get("provider"),
            "release_date": row.get("release_date"),
            "arc_score": row.get("arc_score"),
            "hle_score": row.get("hle_score"),
        }
        for row in rows
        if row.get("release_date") and (row.get("arc_score") is not None or row.get("hle_score") is not None)
    ]

    return {
        "summary": {
            "model_count": len(rows),
            "efficiency_points": len(efficiency),
            "confidence_points": len(confidence),
            "transfer_points": len(transfer),
            "timeline_points": len(timeline),
        },
        "efficiency_map": {
            "points": efficiency,
            "pareto_frontier": _pareto_frontier(efficiency),
            "source": "https://arcprize.org/media/data/leaderboard/evaluations.json",
            "assumption_note": "ARC leaderboard may mix constrained and unconstrained submissions.",
        },
        "confidence_lens": {
            "points": confidence,
            "source": "https://dashboard.safe.ai/api/models",
            "assumption_note": "Lower calibration error is better; API fields can change.",
        },
        "transfer_gap": {
            "points": sorted(transfer, key=lambda x: abs(x["gap"]), reverse=True),
            "source": "https://dashboard.safe.ai/api/models",
            "assumption_note": "ARC and HLE scores are compared as percentages; semantics differ by benchmark.",
        },
        "twin_rivers": {
            "points": sorted(timeline, key=lambda x: x.get("release_date") or ""),
            "source": "https://arcprize.org/media/data/leaderboard/evaluations.json + https://dashboard.safe.ai/api/models",
            "assumption_note": "Release dates may be missing or inferred by source systems.",
        },
    }


def write_analysis(payload: dict[str, Any]) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "analysis.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    path = write_analysis(build_analysis_payload())
    print(f"Wrote analysis -> {path}")
