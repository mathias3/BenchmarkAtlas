"""Single-command pipeline runner."""

from __future__ import annotations

from .analyze import build_analysis_payload, write_analysis
from .export import export_site_data
from .ingest import fetch_all
from .transform import normalize_sources, write_unified


def run() -> None:
    print("1/4 Fetching source data...")
    fetch_all()

    print("2/4 Normalizing records...")
    records = normalize_sources()
    write_unified(records)

    print("3/4 Computing derived datasets...")
    payload = build_analysis_payload()
    write_analysis(payload)

    print("4/4 Exporting site/data.json...")
    path = export_site_data()
    print(f"Done: {path}")


if __name__ == "__main__":
    run()
