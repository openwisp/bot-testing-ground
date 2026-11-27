#!/usr/bin/env bash
# Post analysis only when both output and CI errors are present.
set -e
if [ ! -s solution.md ]; then
  echo "AI analysis produced no output; skipping comment."
  exit 0
fi
if ! grep -q "##\[error\]" failed_logs.txt 2>/dev/null; then
  echo "No CI failures detected; skipping comment."
  exit 0
fi
gh pr comment "$PR_NUM" --repo "$REPO" --body-file solution.md
