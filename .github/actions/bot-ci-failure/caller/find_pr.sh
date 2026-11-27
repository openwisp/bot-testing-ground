#!/usr/bin/env bash
# Find the open pull request associated with a failed workflow run.
set -eo pipefail

emit_pr() {
  local pr_number="$1"
  local pr_author
  pr_author=$(gh pr view "$pr_number" --repo "$REPO" --json author \
    --jq '.author.login // empty' 2>/dev/null || echo "")
  if [ -z "$pr_author" ] || [ "$pr_author" = "null" ]; then
    echo "::warning::Could not fetch PR author for PR #$pr_number"
  fi
  echo "number=$pr_number" >> "$GITHUB_OUTPUT"
  echo "author=$pr_author" >> "$GITHUB_OUTPUT"
}

matching_pr() {
  # A commit can appear in multiple PRs. Only accept one open PR with the run's exact head.
  jq --slurp --raw-output --arg head_sha "$EVENT_HEAD_SHA" \
    --arg head_repo "$EVENT_HEAD_REPOSITORY" --arg head_branch "$EVENT_HEAD_BRANCH" '
    [.[][] | select(.state == "open" and .head.sha == $head_sha
      and .head.repo.full_name == $head_repo and .head.ref == $head_branch)]
    | if length == 1 then .[0].number else empty end' 2>/dev/null || true
}

PR_NUMBER="$PR_NUMBER_PAYLOAD"
if [ -n "$PR_NUMBER" ]; then
  echo "Found PR #$PR_NUMBER from workflow payload."
  emit_pr "$PR_NUMBER"
  exit 0
fi
echo "Payload empty. Searching for PR via Commits API..."
if PULL_REQUESTS=$(gh api --paginate \
  "repos/$REPO/commits/$EVENT_HEAD_SHA/pulls?per_page=100" 2>/dev/null); then
  PR_NUMBER=$(printf '%s\n' "$PULL_REQUESTS" | matching_pr)
else
  PR_NUMBER=""
fi
if [ -n "$PR_NUMBER" ] && [ "$PR_NUMBER" != "null" ]; then
  echo "Found PR #$PR_NUMBER using Commits API."
  emit_pr "$PR_NUMBER"
  exit 0
fi
echo "API lookup failed/empty. Searching open PRs for matching head SHA..."
# GitHub's head filter takes owner:branch, not owner/repository:branch.
HEAD_OWNER="${EVENT_HEAD_REPOSITORY%%/*}"
if [ -n "$HEAD_OWNER" ] && [ -n "$EVENT_HEAD_BRANCH" ] && \
  OPEN_PRS=$(gh api --method GET --paginate "repos/$REPO/pulls" \
    -f state=open -f "head=$HEAD_OWNER:$EVENT_HEAD_BRANCH" -F per_page=100 2>/dev/null); then
  PR_NUMBER=$(printf '%s\n' "$OPEN_PRS" | matching_pr)
else
  PR_NUMBER=""
fi
if [ -n "$PR_NUMBER" ]; then
  echo "Found PR #$PR_NUMBER by scanning open PRs."
  emit_pr "$PR_NUMBER"
  exit 0
fi
echo "::warning::No open PR found. This workflow run might not be attached to an open PR."
