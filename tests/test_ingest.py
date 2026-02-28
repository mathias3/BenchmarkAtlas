from pipeline.config import SOURCES


def test_sources_present():
    assert "arc_evaluations" in SOURCES
    assert "hle_models" in SOURCES
