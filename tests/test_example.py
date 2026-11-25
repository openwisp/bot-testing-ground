"""Exercise the small arithmetic fixture used for review experiments."""

from ci_exp.file import add


def test_add():
    assert add(2, 3) == 5
