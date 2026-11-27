#!/usr/bin/env bash
# Fetch and extract the shared OpenWISP review guidance.
set -euo pipefail

DIR=$(dirname "$(realpath "$0")")
OUT="$RUNNER_TEMP/shared-guidance"
SOURCE="$RUNNER_TEMP/shared-agents.md"
mkdir -p "$OUT"
if [ -n "${GH_TOKEN:-}" ]; then
  for _ in 1 2 3 4 5; do
    if gh api -H "Accept: application/vnd.github.raw" \
      "repos/$OWNER/openwisp-opencode-configs/contents/AGENTS.md" >"$SOURCE"; then
      break
    fi
    rm -f "$SOURCE"
    sleep 5
  done
fi
if ! [ -s "$SOURCE" ]; then
  echo "::warning::The shared AI guidance could not be downloaded"
fi
python3 "$DIR/shared_guidance.py" "$SOURCE" "$OUT/guidance.md" "$OUT/notes.md"
