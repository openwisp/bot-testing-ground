#!/usr/bin/env bash
# Assemble the shared and stage-specific review instructions in prompt order.
set -euo pipefail

DIR=$(dirname "$(realpath "$0")")
PROMPTS="$DIR/../prompts"
STAGE=$1
MINUTES=$2
GUIDANCE=$3
# Stage files use a numeric prefix to show their order in the review process.
case "$STAGE" in
  review) STEP=1 ;;
  security-review) STEP=2 ;;
  final-review) STEP=3 ;;
esac
sed "s/{{REVIEW_MINUTES}}/$MINUTES/" "$PROMPTS/shared/context.md"
cat "$PROMPTS/stages/$STEP-$STAGE.md" "$GUIDANCE" "$PROMPTS/shared/verification.md"
