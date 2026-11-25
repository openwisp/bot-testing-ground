"""Exercise the CI environment prepared for the review fixture."""

from ci_exp.file import add


def test_add_zero():
    assert add(3, 0) == 3
