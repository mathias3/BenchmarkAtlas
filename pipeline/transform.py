"""Normalize ARC and HLE sources into a unified model-centric schema."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .config import ALIASES_PATH, PROCESSED_DIR, SOURCES_DIR


MODEL_KEY_CANDIDATES = (
    "model",
    "model_name",
    "name",
    "modelId",
    "model_id",
)

PROVIDER_KEY_CANDIDATES = (
    "provider",
    "organization",
    "org",
    "company",
)


@dataclass
class UnifiedModelRecord:
    model_key: str
    canonical_name: str
    provider: str | None
    release_date: str | None
    arc_score: float | None
    arc_cost_per_task: float | None
    arc_tasks_evaluated: int | None
    hle_score: float | None
    calibration_error: float | None
    hle_arc_agi_2: float | None
    source_arc: str | None
    source_hle: str | None


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return cleaned.strip("-")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_aliases() -> dict[str, str]:
    if not ALIASES_PATH.exists():
        return {}
    raw = _read_json(ALIASES_PATH)
    return {str(k).lower(): str(v) for k, v in raw.items()}


def _extract_first(item: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in item:
            return item[key]
    return None


def _as_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for candidate in ("data", "results", "models", "evaluations", "items"):
            value = payload.get(candidate)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip().replace("%", "")
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _canonical_name(name: str, aliases: dict[str, str]) -> str:
    alias = aliases.get(name.lower())
    return alias if alias else name


def normalize_sources() -> list[UnifiedModelRecord]:
    aliases = _load_aliases()

    arc_eval_payload = _read_json(SOURCES_DIR / "arc_evaluations.json")
    arc_models_payload = _read_json(SOURCES_DIR / "arc_models.json")
    hle_payload = _read_json(SOURCES_DIR / "hle_models.json")

    arc_eval = _as_list(arc_eval_payload)
    arc_models = _as_list(arc_models_payload)
    hle_models = _as_list(hle_payload)

    model_index: dict[str, UnifiedModelRecord] = {}

    arc_model_meta: dict[str, dict[str, Any]] = {}
    for item in arc_models:
        model_name = _extract_first(item, MODEL_KEY_CANDIDATES)
        if not isinstance(model_name, str):
            continue
        canonical = _canonical_name(model_name, aliases)
        arc_model_meta[canonical] = item

    for item in arc_eval:
        model_name = _extract_first(item, MODEL_KEY_CANDIDATES)
        if not isinstance(model_name, str):
            continue
        canonical = _canonical_name(model_name, aliases)
        model_key = _slugify(canonical)

        arc_meta = arc_model_meta.get(canonical, {})
        provider = _extract_first(item, PROVIDER_KEY_CANDIDATES) or _extract_first(
            arc_meta, PROVIDER_KEY_CANDIDATES
        )
        release_date = (
            _extract_first(item, ("release_date", "releaseDate", "created_at", "date"))
            or _extract_first(arc_meta, ("release_date", "releaseDate", "created_at", "date"))
        )

        record = model_index.get(model_key)
        if record is None:
            record = UnifiedModelRecord(
                model_key=model_key,
                canonical_name=canonical,
                provider=str(provider) if provider else None,
                release_date=str(release_date) if release_date else None,
                arc_score=_to_float(_extract_first(item, ("score", "overall_score", "pass_rate", "accuracy"))),
                arc_cost_per_task=_to_float(_extract_first(item, ("cost_per_task", "cost", "usd_per_task"))),
                arc_tasks_evaluated=_to_int(
                    _extract_first(item, ("tasks_evaluated", "num_tasks", "n_tasks", "sample_size"))
                ),
                hle_score=None,
                calibration_error=None,
                hle_arc_agi_2=None,
                source_arc="https://arcprize.org/media/data/leaderboard/evaluations.json",
                source_hle=None,
            )
            model_index[model_key] = record
        else:
            record.arc_score = record.arc_score or _to_float(
                _extract_first(item, ("score", "overall_score", "pass_rate", "accuracy"))
            )
            record.arc_cost_per_task = record.arc_cost_per_task or _to_float(
                _extract_first(item, ("cost_per_task", "cost", "usd_per_task"))
            )

    for item in hle_models:
        model_name = _extract_first(item, MODEL_KEY_CANDIDATES)
        if not isinstance(model_name, str):
            continue
        canonical = _canonical_name(model_name, aliases)
        model_key = _slugify(canonical)

        provider = _extract_first(item, PROVIDER_KEY_CANDIDATES)
        release_date = _extract_first(item, ("release_date", "releaseDate", "created_at", "date"))

        record = model_index.get(model_key)
        if record is None:
            record = UnifiedModelRecord(
                model_key=model_key,
                canonical_name=canonical,
                provider=str(provider) if provider else None,
                release_date=str(release_date) if release_date else None,
                arc_score=None,
                arc_cost_per_task=None,
                arc_tasks_evaluated=None,
                hle_score=_to_float(_extract_first(item, ("hle", "score", "accuracy"))),
                calibration_error=_to_float(_extract_first(item, ("calibration_error", "ece"))),
                hle_arc_agi_2=_to_float(_extract_first(item, ("arc_agi_2", "arc", "arc_score"))),
                source_arc=None,
                source_hle="https://dashboard.safe.ai/api/models",
            )
            model_index[model_key] = record
        else:
            record.hle_score = record.hle_score or _to_float(
                _extract_first(item, ("hle", "score", "accuracy"))
            )
            record.calibration_error = record.calibration_error or _to_float(
                _extract_first(item, ("calibration_error", "ece"))
            )
            record.hle_arc_agi_2 = record.hle_arc_agi_2 or _to_float(
                _extract_first(item, ("arc_agi_2", "arc", "arc_score"))
            )
            record.source_hle = "https://dashboard.safe.ai/api/models"

    return list(model_index.values())


def write_unified(records: list[UnifiedModelRecord]) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "unified_models.json"
    out_path.write_text(json.dumps([asdict(record) for record in records], indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    records = normalize_sources()
    path = write_unified(records)
    print(f"Wrote {len(records)} records -> {path}")
