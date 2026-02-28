from pipeline.transform import _slugify


def test_slugify_basic():
    assert _slugify("Claude 3.5 Sonnet") == "claude-3-5-sonnet"
