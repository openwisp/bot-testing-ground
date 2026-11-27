#!/usr/bin/env bash
# Select the runner image of the trusted CI test job for the review.
set -euo pipefail

RUNNER=ubuntu-latest
WORKFLOW=$(mktemp)
if gh api -H "Accept: application/vnd.github.raw" \
  "repos/$REPOSITORY/contents/.github/workflows/ci.yml?ref=$BASE_SHA" >"$WORKFLOW"; then
  CANDIDATE=$(yq '.jobs.test."runs-on" // ""' "$WORKFLOW" || true)
  if [[ "$CANDIDATE" =~ ^ubuntu-(latest|[0-9]{2}\.[0-9]{2})$ ]]; then
    RUNNER=$CANDIDATE
  fi
fi
rm -f "$WORKFLOW"
echo "runner=$RUNNER" >>"$GITHUB_OUTPUT"
