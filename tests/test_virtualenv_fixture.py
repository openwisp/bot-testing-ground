"""Exercise the CI environment prepared for the review fixture."""

import sys
from pathlib import Path

import pytest


def test_review_uses_virtualenv():
    venv = Path(__file__).resolve().parents[1] / ".venv"
    assert Path(sys.prefix) == venv
    assert Path(pytest.__file__).resolve().is_relative_to(venv)
