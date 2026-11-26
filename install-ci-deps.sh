#!/usr/bin/env bash
# Install the same test dependencies for CI and AI review experiments.
set -euo pipefail
test "${CI:-}" = true
test "${DISTRO:-}" = ubuntu
if [ "$(id -un)" = reviewer ]; then
  # The review creates a writable .venv before calling this installer. Probe its base Python.
  python_bin=$(readlink -f "$(command -v python)")
  if probe=$(mktemp "$(dirname "$python_bin")/review-write-probe.XXXXXXXX" 2>/dev/null); then
    rm "$probe"
    echo "Reviewer can write to the selected Python toolchain" >&2
    exit 1
  fi
fi
if [ "${VIRTUAL_ENV:-}" != "$PWD/.venv" ]; then
  python -m venv .venv
fi
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/pytest --version
