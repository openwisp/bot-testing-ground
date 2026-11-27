#!/usr/bin/env bash
# Recognize the shared CI entry point without breaking other repositories.
set -euo pipefail
workflow="$CI_ROOT/.github/workflows/ci.yml"
enabled=false
if [ -f "$workflow" ] && job=$(yq -o=json '.jobs.test // {}' "$workflow"); then
  enabled=$(jq -r 'any(.steps[]?; .id == "deps" and .run == "./install-ci-deps.sh")' <<<"$job")
fi
echo "enabled=$enabled" >> "$GITHUB_OUTPUT"
