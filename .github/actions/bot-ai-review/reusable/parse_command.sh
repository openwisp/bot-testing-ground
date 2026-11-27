#!/usr/bin/env bash
# Select the review stage and model from a pull request comment.
set -euo pipefail

# GitHub comments can have CRLF line endings or surrounding whitespace.
COMMAND=$(printf '%s' "$BODY" | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
case "$COMMAND" in
  /review) STAGE=review NAME=${GENERAL_MODEL:-} EFFORT=${GENERAL_EFFORT:-} ;;
  /security-review) STAGE=security-review NAME=${SECURITY_MODEL:-} EFFORT=${SECURITY_EFFORT:-} ;;
  /final-review) STAGE=final-review NAME=${FINAL_MODEL:-} EFFORT=${FINAL_EFFORT:-} ;;
  *)
    echo "Not a review command"
    exit 0
    ;;
esac
case "$EFFORT" in
  *[!a-zA-Z0-9._-]*) echo "::error::Invalid effort: $EFFORT"; exit 1 ;;
esac
echo "stage=$STAGE" >>"$GITHUB_OUTPUT"
if [ -n "${PROVIDER:-}" ] && [ -n "$NAME" ]; then
  echo "model=$PROVIDER/$NAME" >>"$GITHUB_OUTPUT"
fi
if [ -n "$EFFORT" ]; then
  echo "effort=$EFFORT" >>"$GITHUB_OUTPUT"
fi
