"""Check that a focused test can use the review environment's shared memory."""

import multiprocessing
import os
from pathlib import Path

import pytest


@pytest.mark.skipif(
    os.environ.get("USER") != "reviewer", reason="needs the review sandbox"
)
def test_shared_memory():
    assert Path(os.environ["VIRTUAL_ENV"]) == Path("/tmp/ai-review/run/.venv")
    semaphore = multiprocessing.Semaphore()
    assert semaphore.acquire(timeout=1)
    Path("/dev/shm/openwisp-review-smoke").touch()
