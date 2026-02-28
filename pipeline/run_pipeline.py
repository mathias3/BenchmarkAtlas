"""Single-command pipeline runner."""

from __future__ import annotations

from pathlib import Path

from .analyze import build_analysis_payload, write_analysis
from .charts import generate as generate_chart_previews
from .export import export_site_data
from .ingest import fetch_all
from .transform import normalize_sources, write_unified

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_DIR = ROOT / "data" / "bootstrap"
SOURCES_DIR = ROOT / "data" / "sources"


def _has_chart_data(payload: dict) -> bool:
    summary = payload.get("summary", {})
    return any(
        summary.get(key, 0) > 0
        for key in ("efficiency_points", "confidence_points", "transfer_points", "timeline_points")
    )


def _restore_bootstrap_sources() -> None:
    for file in BOOTSTRAP_DIR.glob("*.json"):
        target = SOURCES_DIR / file.name
        target.write_text(file.read_text(encoding="utf-8"), encoding="utf-8")


def run() -> None:
    print("1/5 Fetching source data...")
    fetch_all()

    print("2/5 Normalizing records...")
    records = normalize_sources()
    write_unified(records)

    print("3/5 Computing derived datasets...")
    payload = build_analysis_payload()
    if not _has_chart_data(payload):
        print("No chart data parsed from live sources, restoring bootstrap data...")
        _restore_bootstrap_sources()
        records = normalize_sources()
        write_unified(records)
        payload = build_analysis_payload()
    write_analysis(payload)

    print("4/5 Exporting site/data.json...")
    path = export_site_data()

    print("5/5 Rendering static chart previews...")
    generate_chart_previews()
    print(f"Done: {path}")


if __name__ == "__main__":
    run()
