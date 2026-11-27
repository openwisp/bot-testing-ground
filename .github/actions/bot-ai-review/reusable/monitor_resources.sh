#!/usr/bin/env bash
# Print the runner's memory, disk, and process usage until a process exits.
# The log then shows whether the review was exhausting the runner if it is lost.
set -euo pipefail

PID=$1
INTERVAL=$2
# Write each report in one call, so it is not split by the tool calls printed meanwhile.
print_usage() {
  local memory disk processes
  memory=$(free -m | awk '/^Mem:/ { print $3 "/" $2 }')
  disk=$(df -m / | awk 'NR == 2 { print $4 }')
  processes=$(ps -e --no-headers | wc -l)
  printf 'Resources: memory %s MiB used, disk %s MiB free, %s processes\n' \
    "$memory" "$disk" "$processes"
}

print_usage
ELAPSED=0
while kill -0 "$PID" 2>/dev/null; do
  sleep 1
  ELAPSED=$((ELAPSED + 1))
  if [ "$ELAPSED" -ge "$INTERVAL" ] && kill -0 "$PID" 2>/dev/null; then
    print_usage
    ELAPSED=0
  fi
done
