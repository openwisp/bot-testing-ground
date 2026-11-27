#!/usr/bin/env bash
# Fetch PR changes as data, using the app token only to resolve a missing base.
set -eo pipefail
: > pr.diff
if [ -z "$BASE_SHA" ]; then
  BASE_SHA=$(GH_TOKEN="$GH_APP_TOKEN" gh pr view "$PR_NUM" --repo "$REPO" \
    --json baseRefOid --jq '.baseRefOid') || true
fi
if [ -z "$BASE_SHA" ] || ! gh api -H 'Accept: application/vnd.github.diff' \
  "repos/$REPO/compare/$BASE_SHA...$HEAD_SHA" > pr.diff; then
  : > pr.diff
  echo "::warning::Could not fetch the PR diff; continuing without code context."
fi
