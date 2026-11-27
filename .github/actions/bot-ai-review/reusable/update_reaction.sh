#!/usr/bin/env bash
# Replace the pending reaction with the review's outcome.
set -euo pipefail

REACTIONS="repos/$REPOSITORY/issues/comments/$COMMENT_ID/reactions"
gh api -X DELETE "$REACTIONS/$REACTION_ID"
if [ "$PUBLISH_RESULT" = success ]; then
  CONTENT=rocket
elif [ "$REVIEW_RESULT" = cancelled ] || [ "$PUBLISH_RESULT" = cancelled ]; then
  exit 0
else
  CONTENT=confused
fi
gh api -X POST "$REACTIONS" -f content="$CONTENT" --silent
