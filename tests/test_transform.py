import json

from pipeline import transform
from pipeline.analyze import _pareto_frontier


def test_slugify_basic():
    assert transform._slugify("Claude 3.5 Sonnet") == "claude-3-5-sonnet"


def test_flatten_hle_scores_object():
    row = {"name": "gpt-4o", "scores": {"hle": 31.2, "calibration_error": 0.11}}
    flat = transform._flatten_hle_record(row)
    assert flat["hle"] == 31.2
    assert flat["calibration_error"] == 0.11


def test_flatten_hle_scores_object_camel_case_keys():
    row = {"name": "gpt-4o", "scores": {"hleScore": 33.0, "calibrationError": 0.08, "arcAgi2": 41.5}}
    flat = transform._flatten_hle_record(row)
    assert flat["hle"] == 33.0
    assert flat["calibration_error"] == 0.08
    assert flat["arc_agi_2"] == 41.5


def test_flatten_hle_calibration_error_prefixed():
    """Real HLE API uses hle_calibration_error, not calibration_error."""
    row = {"name": "Gemini 3.1 Pro", "scores": {"hle": 45.9, "hle_calibration_error": 50.3, "arc_agi_2": 73.33}}
    flat = transform._flatten_hle_record(row)
    assert flat["hle"] == 45.9
    assert flat["calibration_error"] == 50.3
    assert flat["arc_agi_2"] == 73.33


def test_normalize_sources_extracts_camel_case_cost_and_filters_display(monkeypatch, tmp_path):
    sources = tmp_path / "sources"
    processed = tmp_path / "processed"
    aliases = tmp_path / "aliases.json"
    sources.mkdir(parents=True)
    processed.mkdir(parents=True)

    (sources / "arc_models.json").write_text(
        json.dumps(
            [
                {"modelId": "gpt-4o-2024-11-20", "provider": "OpenAI", "releaseDate": "2024-11-20"},
            ]
        ),
        encoding="utf-8",
    )
    (sources / "arc_evaluations.json").write_text(
        json.dumps(
            [
                {
                    "modelId": "gpt-4o-2024-11-20",
                    "provider": "OpenAI",
                    "score": 38.2,
                    "costPerTask": 0.43,
                    "tasksEvaluated": 120,
                    "display": False,
                },
                {
                    "modelId": "gpt-4o-2024-11-20",
                    "provider": "OpenAI",
                    "score": 39.1,
                    "costPerTask": 0.41,
                    "tasksEvaluated": 140,
                },
            ]
        ),
        encoding="utf-8",
    )
    (sources / "hle_models.json").write_text(
        json.dumps(
            [
                {
                    "name": "gpt-4o-2024-11-20",
                    "provider": "OpenAI",
                    "scores": {"hle": 30.0, "calibration_error": 0.1, "arc_agi_2": 40.0},
                }
            ]
        ),
        encoding="utf-8",
    )
    aliases.write_text(json.dumps({"gpt-4o": "GPT-4o"}), encoding="utf-8")

    monkeypatch.setattr(transform, "SOURCES_DIR", sources)
    monkeypatch.setattr(transform, "PROCESSED_DIR", processed)
    monkeypatch.setattr(transform, "ALIASES_PATH", aliases)

    rows = transform.normalize_sources()
    assert len(rows) == 1

    record = rows[0]
    assert record.canonical_name == "GPT-4o"
    assert record.arc_score == 39.1
    assert record.arc_cost_per_task == 0.41
    assert record.arc_tasks_evaluated == 140
    assert record.hle_score == 30.0
    assert record.calibration_error == 0.1


def test_multiple_arc_evals_choose_best_score_and_lowest_cost(monkeypatch, tmp_path):
    sources = tmp_path / "sources"
    aliases = tmp_path / "aliases.json"
    sources.mkdir(parents=True)

    (sources / "arc_models.json").write_text(json.dumps([]), encoding="utf-8")
    (sources / "hle_models.json").write_text(json.dumps([]), encoding="utf-8")
    (sources / "arc_evaluations.json").write_text(
        json.dumps(
            [
                {"model": "Model X", "score": 22.0, "cost_per_task": 1.1, "tasks_evaluated": 64},
                {"model": "Model X", "score": 27.0, "cost_per_task": 1.4, "tasks_evaluated": 50},
                {"model": "Model X", "score": 25.0, "cost_per_task": 0.7, "tasks_evaluated": 120},
            ]
        ),
        encoding="utf-8",
    )
    aliases.write_text(json.dumps({}), encoding="utf-8")

    monkeypatch.setattr(transform, "SOURCES_DIR", sources)
    monkeypatch.setattr(transform, "ALIASES_PATH", aliases)

    rows = transform.normalize_sources()
    assert len(rows) == 1

    record = rows[0]
    assert record.arc_score == 27.0
    assert record.arc_cost_per_task == 0.7
    assert record.arc_tasks_evaluated == 120


def test_canonical_name_fuzzy_date_suffix_alias_match():
    aliases = {"claude-3-5-sonnet": "Claude 3.5 Sonnet"}
    assert transform._canonical_name("claude-3-5-sonnet-20241022", aliases) == "Claude 3.5 Sonnet"


def test_arc_scores_normalized_to_percentage(monkeypatch, tmp_path):
    """ARC API returns 0-1 fractions; pipeline should normalize to 0-100."""
    sources = tmp_path / "sources"
    aliases = tmp_path / "aliases.json"
    sources.mkdir(parents=True)

    (sources / "arc_models.json").write_text(json.dumps([]), encoding="utf-8")
    (sources / "hle_models.json").write_text(json.dumps([]), encoding="utf-8")
    (sources / "arc_evaluations.json").write_text(
        json.dumps([{"modelId": "test-model", "score": 0.42, "costPerTask": 0.5}]),
        encoding="utf-8",
    )
    aliases.write_text(json.dumps({}), encoding="utf-8")

    monkeypatch.setattr(transform, "SOURCES_DIR", sources)
    monkeypatch.setattr(transform, "ALIASES_PATH", aliases)

    rows = transform.normalize_sources()
    assert len(rows) == 1
    assert rows[0].arc_score == 42.0  # 0.42 * 100


def test_pareto_frontier_with_realistic_shape_fields():
    points = [
        {"model": "A", "cost_per_task": 0.10, "score": 23.0},
        {"model": "B", "cost_per_task": 0.20, "score": 22.5},
        {"model": "C", "cost_per_task": 0.30, "score": 26.0},
        {"model": "D", "cost_per_task": 0.60, "score": 25.5},
        {"model": "E", "cost_per_task": 1.10, "score": 29.2},
    ]
    frontier = _pareto_frontier(points)
    assert [row["model"] for row in frontier] == ["A", "C", "E"]
