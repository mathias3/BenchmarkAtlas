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
