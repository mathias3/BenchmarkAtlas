"""Export analyzed payload to site data file."""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from .config import PROCESSED_DIR, SITE_DATA_PATH


def _load_analysis() -> dict[str, Any]:
    path = PROCESSED_DIR / "analysis.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing analysis payload: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def export_site_data() -> Path:
    analysis = _load_analysis()
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "project": "AGI Gap Atlas",
        "version": "0.1.0",
        "data": analysis,
    }
    SITE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SITE_DATA_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return SITE_DATA_PATH


if __name__ == "__main__":
    path = export_site_data()
    print(f"Exported -> {path}")
