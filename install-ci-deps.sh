#!/usr/bin/env bash
# Install the same test dependencies for CI and AI review experiments.
set -euo pipefail
test "${CI:-}" = true
test "${DISTRO:-}" = ubuntu
if [ "$(id -un)" = reviewer ]; then
  if probe=$(mktemp "$(dirname "$(command -v python)")/review-write-probe.XXXXXXXX" 2>/dev/null); then
    rm "$probe"
    echo "Reviewer can write to the selected Python toolchain" >&2
    exit 1
  fi
fi
python -m venv .venv
.venv/bin/python -m pip install -r requirements-test.txt
