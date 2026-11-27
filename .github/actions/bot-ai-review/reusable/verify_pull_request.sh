#!/usr/bin/env bash
# Reject a review if the pull request changed or closed before it starts.
set -euo pipefail

PR=$(gh api "repos/$REPOSITORY/pulls/$PR_NUMBER" --jq '.state, .head.sha, .base.ref')
mapfile -t FIELDS <<<"$PR"
if [ "${FIELDS[0]:-}" != open ] || [ "${FIELDS[1]:-}" != "$HEAD_SHA" ] || \
  [ "${FIELDS[2]:-}" != "$BASE_REF" ]; then
  echo "::error::The pull request changed or closed; request another review"
  exit 1
fi
