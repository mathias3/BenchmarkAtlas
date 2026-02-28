#!/usr/bin/env python3
"""Agent-first CLI facade for BenchmarkAtlas (Repokit-style experiment)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.analyze import build_analysis_payload, write_analysis
from pipeline.export import export_site_data
from pipeline.ingest import fetch_all
from pipeline.transform import normalize_sources, write_unified


def cmd_scan(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    files = [p for p in root.rglob("*") if p.is_file()]
    report = {
        "path": str(root),
        "file_count": len(files),
        "sample": [str(p.relative_to(root)) for p in files[:20]],
    }
    print(json.dumps(report, indent=2))
    return 0


def cmd_eval(_: argparse.Namespace) -> int:
    fetch_all()
    records = normalize_sources()
    write_unified(records)
    payload = build_analysis_payload()
    out = write_analysis(payload)
    print(json.dumps({"status": "ok", "analysis_path": str(out), "model_count": len(records)}, indent=2))
    return 0


def cmd_viz(_: argparse.Namespace) -> int:
    out = export_site_data()
    print(json.dumps({"status": "ok", "site_data": str(out)}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atlas", description="BenchmarkAtlas agent-first CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan repository and emit JSON report")
    scan.add_argument("--path", default=".")
    scan.set_defaults(func=cmd_scan)

    eval_cmd = sub.add_parser("eval", help="Fetch + transform + analyze benchmark data")
    eval_cmd.set_defaults(func=cmd_eval)

    viz = sub.add_parser("viz", help="Export processed analysis to site/data.json")
    viz.set_defaults(func=cmd_viz)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
