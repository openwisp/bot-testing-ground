"""Exercise the CI environment prepared for the review fixture."""

import sys


def test_review_uses_virtualenv():
    assert sys.prefix != sys.base_prefix
