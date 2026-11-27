#!/usr/bin/env bash
# Install the same test dependencies for CI and AI review experiments.
set -euo pipefail
if [ "${CI_SYSTEM_DEPS_READY:-0}" != 1 ]; then
    # Like openwisp-config's json-c build: CMake 4 rejects projects that
    # need compatibility with CMake older than 3.5, so this only works on
    # the runner image pinned in ci.yml.
    fixture=$(mktemp -d)
    printf 'cmake_minimum_required(VERSION 2.8)\nproject(fixture NONE)\n' \
        >"$fixture/CMakeLists.txt"
    cmake -S "$fixture" -B "$fixture/build" >/dev/null
    rm -rf "$fixture"
fi
if [ "${CI_SYSTEM_DEPS_ONLY:-0}" = 1 ]; then
    exit 0
fi
python -m pip install -r requirements-test.txt
