#!/usr/bin/env bash
# Publish review findings and dismiss superseded reviews of the same stage.
set -euo pipefail

git checkout -B "ai-review-$PR_NUMBER" "$HEAD_SHA"

EVENT=$(jq -er '.event' "$FINDINGS")
VERDICT=$(jq -er '.verdict' "$FINDINGS")
TITLE=$(jq -r '.title // empty' "$FINDINGS")
SUMMARY=$(jq -er '.summary' "$FINDINGS")
BODY="AI $STAGE of $HEAD_SHA provided by \`${MODEL%%/*}\` / \`${MODEL#*/}\`

**Verdict: $VERDICT**

"
if [ "${CI_AWARE:-false}" != true ]; then
  BODY+="
CI was not checked or awaited. Maintainers can enable CI-aware reviews:
https://github.com/openwisp/openwisp-actions/issues/39

"
fi
case "${CI_STANDARD_STATUS:-unknown}" in
  missing)
    BODY+="Missing CI entry points on the base branch: $CI_STANDARD_MISSING.
See https://github.com/openwisp/openwisp-actions/issues/39.

" ;;
  unknown)
    BODY+="CI entry points could not be checked on the base branch.

" ;;
esac
if [ -n "$TITLE" ]; then
  BODY+="$TITLE

"
fi
BODY+=$SUMMARY
if [ "${CI_AWARE:-false}" = true ]; then
  # Identify this exact publication even when Crit posts the review with inline comments.
  REVIEW_MARKER="<!-- ai-review-run ${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT:-1} -->"
  BODY+=$'\n\n'"$REVIEW_MARKER"
fi
COMMENTS="$RUNNER_TEMP/comments.json"
jq '.comments' "$FINDINGS" >"$COMMENTS"
CURRENT_SHA=$(gh api "repos/$REPOSITORY/pulls/$PR_NUMBER" --jq '.head.sha')
CURRENT_STATE=$(gh api "repos/$REPOSITORY/pulls/$PR_NUMBER" --jq '.state')
CURRENT_BASE=$(gh api "repos/$REPOSITORY/pulls/$PR_NUMBER" --jq '.base.ref')
if [ "$CURRENT_SHA" != "$HEAD_SHA" ]; then
  echo "::error::The pull request head changed during the review; request another review"
  exit 1
fi
if [ "$CURRENT_STATE" != open ]; then
  echo "::error::The pull request closed during the review"
  exit 1
fi
if [ "$CURRENT_BASE" != "$BASE_REF" ]; then
  echo "::error::The pull request base changed during the review; request another review"
  exit 1
fi
if [ "$(jq 'length' "$COMMENTS")" -eq 0 ]; then
  jq -n --arg body "$BODY" --arg event "$EVENT" --arg commit "$HEAD_SHA" '{
    body: $body,
    commit_id: $commit,
    event: {comment: "COMMENT", approve: "APPROVE", "request-changes": "REQUEST_CHANGES"}[$event]
  }' | gh api -X POST "repos/$REPOSITORY/pulls/$PR_NUMBER/reviews" --input - --silent
else
  crit comment --json --file "$COMMENTS"
  crit push "$PR_NUMBER" --event "$EVENT" --message "$BODY"
fi
if [ "${CI_AWARE:-false}" = true ] && [ -n "${RECORD_ID:-}" ]; then
  # Match the marker and the app's bot account, not an unrelated review of the same commit.
  if BOT_ID=$(gh api "repos/$REPOSITORY/issues/comments/$RECORD_ID" --jq '.user.id') && \
    REVIEW_URL=$(gh api --paginate "repos/$REPOSITORY/pulls/$PR_NUMBER/reviews" | \
      jq -rs --arg marker "$REVIEW_MARKER" --arg bot "$BOT_ID" '
        [.[][] | select((.user.id | tostring) == $bot and ((.body // "") | contains($marker)))]
        | if length == 1 then .[0].html_url else empty end') && \
    [[ "$REVIEW_URL" == https://* && "$REVIEW_URL" != *$'\n'* ]]; then
    printf 'review_url=%s\n' "$REVIEW_URL" >> "$GITHUB_OUTPUT"
  else
    echo '::warning::Published review link is unavailable.'
  fi
fi
case "$VERDICT" in
  "Review not completed" | Inconclusive | "Maintainer decision needed") exit 0 ;;
esac

# Do not use the app's dismissal permission on another reviewer's change requests.
if ! gh api --paginate "repos/$REPOSITORY/pulls/$PR_NUMBER/reviews" |
  jq -rs --arg prefix "AI $STAGE of " '
    [.[][] | select(.user.login == "openwisp-companion[bot]" and (.body | startswith($prefix)))]
    | sort_by(.id) | .[:-1][]
    | select(.state == "CHANGES_REQUESTED") | .id' |
  while read -r REVIEW_ID; do
    if ! gh api -X PUT "repos/$REPOSITORY/pulls/$PR_NUMBER/reviews/$REVIEW_ID/dismissals" \
      -f message="Superseded by a newer AI $STAGE." -f event=DISMISS --silent; then
      echo "::warning::Published the review, but could not dismiss earlier review $REVIEW_ID"
    fi
  done; then
  echo "::warning::Published the review, but could not list earlier reviews for dismissal"
fi
