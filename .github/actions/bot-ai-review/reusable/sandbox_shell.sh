#!/usr/bin/env bash
# Run review commands as the sandbox user in a synchronized working copy.
# Pass command arguments through "$@" so the wrapper does not interpolate them into its shell code.
# OpenCode reports a tool call only once it ends, so record each command before it runs.
# The job log can then show a command that exhausts the runner. This runs as the runner
# user, so the sandbox user cannot change what is recorded.
if [ -n "${AI_REVIEW_STARTS:-}" ]; then
  # Time in milliseconds, like OpenCode's events, to print both in the order they happened.
  # Isolated mode: the working directory can be the pull request, whose modules must not
  # be imported by the runner user.
  python3 -I -c 'import json, sys, time
print(json.dumps({"type": "tool_start", "timestamp": int(time.time() * 1000), "args": sys.argv[1:]}))' \
    "$@" >>"$AI_REVIEW_STARTS" || true
fi
# Multiprocessing uses /dev/shm even with TMPDIR set. Keep its files off the host's /dev/shm.
exec sudo -n -- /usr/bin/env -i /usr/bin/unshare --mount --propagation private /bin/bash -ec '
  /usr/bin/mount -t tmpfs -o nosuid,nodev,noexec,mode=1777,size=512M tmpfs /dev/shm
  exec /usr/bin/sudo -n -H -u reviewer -- "$@"
' review-namespace \
  /usr/bin/python3 -I /usr/local/lib/ai-review-write-sandbox.py \
  /home/reviewer /tmp/ai-review/run /dev/shm -- \
  /usr/bin/env HOME=/home/reviewer USER=reviewer LOGNAME=reviewer \
  TMPDIR=/home/reviewer/.cache/ai-review-tmp \
  XDG_CONFIG_HOME=/home/reviewer/.config XDG_CACHE_HOME=/home/reviewer/.cache \
  XDG_DATA_HOME=/home/reviewer/.local/share "PATH=/home/reviewer/.local/bin:$PATH" \
  CI_DEPS_CACHE=/home/reviewer/.cache/ci-deps \
  "SE_CHROME=${SE_CHROME:-}" "SE_CHROMEDRIVER=${SE_CHROMEDRIVER:-}" \
  "CHROME_BIN=${SE_CHROME:-}" "GECKO_BIN=${GECKO_BIN:-}" SELENIUM_HEADLESS=1 /bin/bash -c '
/usr/local/bin/ai-review-sync /tmp/ai-review/pr /tmp/ai-review/run "$HOME/.ai-review-files" || exit 1
if [ -x /tmp/ai-review/run/.venv/bin/python ]; then
  export VIRTUAL_ENV=/tmp/ai-review/run/.venv
  export PATH="$VIRTUAL_ENV/bin:$PATH"
fi
case "$PWD/" in
  /tmp/ai-review/pr/*) cd "/tmp/ai-review/run${PWD#/tmp/ai-review/pr}" || exit 1 ;;
esac
exec /bin/bash "$@"' ai-review-shell "$@"
