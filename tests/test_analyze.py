from pipeline.analyze import _pareto_frontier


def test_pareto_frontier_monotonic_score():
    points = [
        {"cost_per_task": 1.0, "score": 20.0},
        {"cost_per_task": 2.0, "score": 25.0},
        {"cost_per_task": 3.0, "score": 24.0},
        {"cost_per_task": 4.0, "score": 35.0},
    ]
    frontier = _pareto_frontier(points)
    assert len(frontier) == 3
    assert frontier[-1]["score"] == 35.0


def test_pareto_frontier_skips_missing_score_and_non_dominant_points():
    points = [
        {"model": "cheap", "cost_per_task": 0.1, "score": 10.0},
        {"model": "missing", "cost_per_task": 0.2, "score": None},
        {"model": "dominated", "cost_per_task": 0.3, "score": 9.0},
        {"model": "better", "cost_per_task": 0.4, "score": 12.0},
    ]
    frontier = _pareto_frontier(points)
    assert [row["model"] for row in frontier] == ["cheap", "better"]
