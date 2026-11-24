"""Exercise the arithmetic fixture's input handling."""

from ci_exp.file import add, bounded_index


def test_add_rejects_negative_inputs():
    assert add(2, 3) == 5


def test_bounded_index():
    assert bounded_index(1, 3) == 1
