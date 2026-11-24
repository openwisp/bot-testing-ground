"""Check that the review test entry point accepts only supported arguments."""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_rejects_runner_options_that_can_execute_code():
    result = subprocess.run(
        [sys.executable, str(ROOT / "runtests"), "-p", "untrusted_plugin"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "Unsupported test argument" in result.stderr


def test_accepts_a_focused_test():
    result = subprocess.run(
        [sys.executable, str(ROOT / "runtests"), "-q", "tests/test_example.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "1 passed" in result.stdout
