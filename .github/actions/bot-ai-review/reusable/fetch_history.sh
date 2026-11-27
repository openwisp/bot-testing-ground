#!/usr/bin/env bash
# Collect pull request discussion and context for the review.
set -euo pipefail

DIR=$(dirname "$(realpath "$0")")
OUT="$RUNNER_TEMP/history"
API="repos/$OWNER/$NAME"
mkdir -p "$OUT"
gh api --paginate --slurp "$API/issues/$PR_NUMBER/comments" >"$OUT/comments.json"
gh api --paginate --slurp "$API/pulls/$PR_NUMBER/reviews" >"$OUT/reviews.json"
gh api --paginate --slurp "$API/pulls/$PR_NUMBER/comments" >"$OUT/review-comments.json"
gh api graphql --paginate --slurp -F owner="$OWNER" -F name="$NAME" \
  -F number="$PR_NUMBER" -F query=@"$DIR/history.graphql" >"$OUT/threads.json"
python3 "$DIR/history.py" "$OUT" >"$DATA_DIR/history.json"
python3 "$DIR/context.py" "$OWNER/$NAME" "$PR_NUMBER" >"$DATA_DIR/context.json"
