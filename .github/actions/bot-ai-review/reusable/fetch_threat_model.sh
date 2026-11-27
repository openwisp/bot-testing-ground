#!/usr/bin/env bash
# Fetch the OpenWISP threat model for the general review.
set -euo pipefail

mkdir -p "$DATA_DIR"
curl -fsSL --retry 5 --retry-all-errors -o "$DATA_DIR/threat-model.rst" \
  https://raw.githubusercontent.com/openwisp/openwisp-docs/master/security/threat-model.rst
