"""Check ordinary percentage calculations for the review fixture."""

from ci_exp.file import percentage


def test_percentage():
    assert percentage(1, 4) == 25
    assert percentage(0, 0) == 0
