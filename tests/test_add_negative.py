"""Exercise negative operands in the existing arithmetic fixture."""

from ci_exp.file import add


def test_add_negative_operand():
    assert add(-2, 3) == 1
