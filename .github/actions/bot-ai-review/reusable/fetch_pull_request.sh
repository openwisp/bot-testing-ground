#!/usr/bin/env bash
# Prepare the pull request files, diff, and base-branch guidance for review.
set -euo pipefail

DIR=$(dirname "$(realpath "$0")")
git fetch --no-tags origin "refs/pull/$PR_NUMBER/head"
git worktree add --detach "$PR_DIR" "$HEAD_SHA"
# Keep the model's copy detached from the trusted checkout's Git metadata.
rm "$PR_DIR/.git"
mkdir -p "$DATA_DIR"
git diff "$BASE_SHA...$HEAD_SHA" >"$DATA_DIR/pr.diff"
python3 "$DIR/guidance.py" "$BASE_SHA" "$HEAD_SHA" >"$DATA_DIR/guidance.md"
# Do not let PR files redirect reads or supply their own OpenCode configuration and guidance.
find "$PR_DIR" -type l -delete
find "$PR_DIR" \( -name .opencode -o -name opencode.json -o -name opencode.jsonc \
  -o -name AGENTS.md -o -name CLAUDE.md -o -name CONTEXT.md \) -prune -exec rm -rf {} +
chmod -R a+rX,go-w "$PR_DIR"
