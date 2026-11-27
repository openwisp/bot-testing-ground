#!/usr/bin/env bash
# Read and validate the pull request's head and base commit references.
set -euo pipefail

PR=$(gh api "repos/$REPOSITORY/pulls/$PR_NUMBER")
HEAD_SHA=$(jq -er '.head.sha' <<<"$PR")
BASE_SHA=$(jq -er '.base.sha' <<<"$PR")
BASE_REF=$(jq -er '.base.ref' <<<"$PR")
for SHA in "$HEAD_SHA" "$BASE_SHA"; do
  if ! [[ "$SHA" =~ ^[0-9a-f]{40}$ ]]; then
    echo "::error::Invalid commit reference"
    exit 1
  fi
done
if ! git check-ref-format --branch "$BASE_REF" >/dev/null; then
  echo "::error::Invalid base branch"
  exit 1
fi
{
  echo "head_sha=$HEAD_SHA"
  echo "base_sha=$BASE_SHA"
  echo "base_ref=$BASE_REF"
} >>"$GITHUB_OUTPUT"
