#!/usr/bin/env bash
# Install the same test dependencies for CI and AI review experiments.
set -euo pipefail
test "${CI:-}" = true
test "${DISTRO:-}" = ubuntu
python -m venv .ci-review-venv
.ci-review-venv/bin/python -m pip install -r requirements-test.txt
python -m pip install -r requirements-test.txt
