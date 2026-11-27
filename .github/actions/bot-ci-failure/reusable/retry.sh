#!/usr/bin/env bash
# Retry transient failures at most three times per commit.
set -eo pipefail
MAX_RETRIES=3
MARKER="<!-- ci-transient-retry $HEAD_SHA -->"
# If GitHub cannot return the previous markers, another retry could exceed the cap.
if ! COMMENTS=$(gh pr view "$PR_NUM" --repo "$REPO" --json comments --jq '.comments[].body' 2>/dev/null); then
  echo "::warning::Could not check previous retries. Skipping auto-retry."
  echo "retried=false" >> "$GITHUB_OUTPUT"
  exit 0
fi
# grep prints 0 but exits 1 when a successful lookup contains no markers.
RETRY_COUNT=$(grep -cF "$MARKER" <<< "$COMMENTS" || true)
echo "Previous retries: $RETRY_COUNT"
if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
  echo "Max retries ($MAX_RETRIES) reached; skipping."
  echo "retried=false" >> "$GITHUB_OUTPUT"
  exit 0
fi
NEXT=$((RETRY_COUNT + 1))
if gh api -X POST "repos/$REPO/actions/runs/$RUN_ID/rerun-failed-jobs" 2>/dev/null; then
  echo "retried=true" >> "$GITHUB_OUTPUT"
  printf -v BODY '%s\n%s%s' \
    "$MARKER" \
    "The CI is failing due to transient infrastructure issues (not related to your code). " \
    "I have restarted the failed jobs automatically ($NEXT/$MAX_RETRIES)."
  gh pr comment "$PR_NUM" --repo "$REPO" --body "$BODY"
else
  echo "::warning::Could not re-run failed jobs (missing actions:write permission?). Skipping auto-retry."
  echo "retried=false" >> "$GITHUB_OUTPUT"
fi
