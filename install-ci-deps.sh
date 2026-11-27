#!/usr/bin/env bash
# Install the same test dependencies for CI and AI review experiments.
set -euo pipefail
python -m pip install -r requirements-test.txt
