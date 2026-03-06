"""Normalize ARC and HLE sources into a unified model-centric schema."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
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

        # Fallback: recursively collect dict-like records in nested payloads.
        records: list[dict[str, Any]] = []

        def _walk(node: Any) -> None:
            if isinstance(node, list):
                for child in node:
                    _walk(child)
            elif isinstance(node, dict):
                if any(
                    key in node
                    for key in (
                        "model",
                        "model_name",
                        "name",
                        "modelId",
                        "hle",
                        "score",
                        "scores",
                        "calibration_error",
                        "costPerTask",
                        "cost_per_task",
                    )
                ):
                    records.append(node)
                for value in node.values():
                    _walk(value)

        _walk(payload)
        return records
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


def _normalize_alias_key(name: str) -> str:
    normalized = name.strip().lower()
    normalized = normalized.replace("_", "-")
    normalized = re.sub(r"-(\d{4}-\d{2}-\d{2}|\d{8}|\d{6})$", "", normalized)
    normalized = re.sub(r"[^a-z0-9-]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized)
    return normalized.strip("-")


def _canonical_name(name: str, aliases: dict[str, str]) -> str:
    raw = name.strip()
    candidates = (
        raw.lower(),
        raw.lower().replace("_", "-"),
        _slugify(raw),
        _normalize_alias_key(raw),
        _normalize_alias_key(_slugify(raw)),
    )
    for candidate in candidates:
        alias = aliases.get(candidate)
        if alias:
            return alias
    return raw


def _flatten_hle_record(item: dict[str, Any]) -> dict[str, Any]:
    """Flatten HLE API records that nest scores inside a 'scores' sub-object."""
    flat = dict(item)
    scores = item.get("scores")
    if isinstance(scores, dict):
        for key, value in scores.items():
            if key not in flat:
                flat[key] = value
        # Normalize common score-key variants to unified field names.
        if "hle" not in flat:
            for key in ("hleScore", "hle_score", "humanitys_last_exam", "humanitysLastExam"):
                if key in scores:
                    flat["hle"] = scores[key]
                    break
        if "calibration_error" not in flat:
            for key in ("hle_calibration_error", "calibrationError", "calibration_error", "ece", "expected_calibration_error"):
                if key in scores:
                    flat["calibration_error"] = scores[key]
                    break
        if "arc_agi_2" not in flat:
            for key in ("arcAgi2", "arc_agi_2", "arc", "arc_score"):
                if key in scores:
                    flat["arc_agi_2"] = scores[key]
                    break
    return flat


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
        if item.get("display") is False:
            continue
        canonical = _canonical_name(model_name, aliases)
        arc_model_meta[canonical] = item

    for item in arc_eval:
        model_name = _extract_first(item, MODEL_KEY_CANDIDATES)
        if not isinstance(model_name, str):
            continue
        if item.get("display") is False:
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

        raw_arc_score = _to_float(_extract_first(item, ("score", "overall_score", "pass_rate", "accuracy")))
        # ARC API returns scores as 0-1 fractions; normalize to 0-100 percentages.
        arc_score = raw_arc_score * 100.0 if raw_arc_score is not None and raw_arc_score <= 1.0 else raw_arc_score
        arc_cost = _to_float(
            _extract_first(item, ("costPerTask", "cost_per_task", "cost", "usd_per_task"))
        )
        arc_tasks = _to_int(
            _extract_first(
                item,
                ("tasks_evaluated", "tasksEvaluated", "num_tasks", "n_tasks", "sample_size"),
            )
        )

        record = model_index.get(model_key)
        if record is None:
            record = UnifiedModelRecord(
                model_key=model_key,
                canonical_name=canonical,
                provider=str(provider) if provider else None,
                release_date=str(release_date) if release_date else None,
                arc_score=arc_score,
                arc_cost_per_task=arc_cost,
                arc_tasks_evaluated=arc_tasks,
                hle_score=None,
                calibration_error=None,
                hle_arc_agi_2=None,
                source_arc="https://arcprize.org/media/data/leaderboard/evaluations.json",
                source_hle=None,
            )
            model_index[model_key] = record
            continue

        if record.provider is None and provider is not None:
            record.provider = str(provider)
        if record.release_date is None and release_date is not None:
            record.release_date = str(release_date)
        if arc_score is not None:
            record.arc_score = max(record.arc_score, arc_score) if record.arc_score is not None else arc_score
        if arc_cost is not None:
            record.arc_cost_per_task = (
                min(record.arc_cost_per_task, arc_cost) if record.arc_cost_per_task is not None else arc_cost
            )
        if arc_tasks is not None:
            record.arc_tasks_evaluated = (
                max(record.arc_tasks_evaluated, arc_tasks)
                if record.arc_tasks_evaluated is not None
                else arc_tasks
            )

    for raw_item in hle_models:
        item = _flatten_hle_record(raw_item)
        model_name = _extract_first(item, MODEL_KEY_CANDIDATES)
        if not isinstance(model_name, str):
            continue

        canonical = _canonical_name(model_name, aliases)
        model_key = _slugify(canonical)

        provider = _extract_first(item, PROVIDER_KEY_CANDIDATES)
        release_date = _extract_first(item, ("release_date", "releaseDate", "created_at", "date"))

        hle_score = _to_float(
            _extract_first(
                item,
                ("hle", "hleScore", "hle_score", "humanitys_last_exam", "humanitysLastExam", "score", "accuracy"),
            )
        )
        calibration_error = _to_float(
            _extract_first(
                item,
                ("calibration_error", "hle_calibration_error", "calibrationError", "ece", "expected_calibration_error"),
            )
        )
        hle_arc = _to_float(_extract_first(item, ("arc_agi_2", "arcAgi2", "arc", "arc_score")))

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
                hle_score=hle_score,
                calibration_error=calibration_error,
                hle_arc_agi_2=hle_arc,
                source_arc=None,
                source_hle="https://dashboard.safe.ai/api/models",
            )
            model_index[model_key] = record
            continue

        if record.provider is None and provider is not None:
            record.provider = str(provider)
        if record.release_date is None and release_date is not None:
            record.release_date = str(release_date)
        if hle_score is not None:
            record.hle_score = max(record.hle_score, hle_score) if record.hle_score is not None else hle_score
        if calibration_error is not None:
            record.calibration_error = (
                min(record.calibration_error, calibration_error)
                if record.calibration_error is not None
                else calibration_error
            )
        if hle_arc is not None:
            record.hle_arc_agi_2 = hle_arc
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
