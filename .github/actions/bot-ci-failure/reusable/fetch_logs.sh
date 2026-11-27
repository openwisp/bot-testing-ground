#!/usr/bin/env bash
# Collect failed job log sections between GitHub group and error markers.
set -eo pipefail
if [ -n "${MAX_LOG_BYTES:-}" ] && \
  { ! [[ "$MAX_LOG_BYTES" =~ ^[0-9]+$ ]] || [ "$MAX_LOG_BYTES" -lt 32 ]; }; then
  echo "MAX_LOG_BYTES must be an integer of at least 32." >&2
  exit 1
fi
echo "Getting failed jobs for run $RUN_ID..."
JOBS_ENDPOINT="repos/$REPO/actions/runs/$RUN_ID"
# The reviewer needs logs from the attempt it selected, even if CI is retried.
if [ -n "${ATTEMPT:-}" ]; then
  JOBS_ENDPOINT+="/attempts/$ATTEMPT"
fi
if ! JOB_IDS=$(gh api --paginate "$JOBS_ENDPOINT/jobs" \
  -q '.jobs[] | select(.conclusion=="failure") | .id'); then
  if [ -n "${MAX_LOG_BYTES:-}" ]; then
    echo "Failed jobs unavailable." > failed_logs.txt
  else
    echo "Could not fetch failed jobs for run $RUN_ID." > failed_logs.txt
  fi
  exit 0
fi
if [ -z "$JOB_IDS" ]; then
  echo "No failed jobs found." > failed_logs.txt
  exit 0
fi
if [ -n "${MAX_LOG_BYTES:-}" ]; then
  JOB_COUNT=$(wc -w <<<"$JOB_IDS")
  JOB_LIMIT=$((MAX_LOG_BYTES / JOB_COUNT))
  if [ "$JOB_LIMIT" -lt 32 ]; then
    echo "MAX_LOG_BYTES is too small for the failed jobs." >&2
    exit 1
  fi
fi
: > failed_logs.txt
FOUND_ERROR=false
for JOB_ID in $JOB_IDS; do
  echo "Processing job $JOB_ID"
  TRUNCATED=false
  # A small final excerpt does not bound the download or awk's group buffer.
  # Limit raw input for review requests before writing or parsing it.
  if [ -n "${MAX_LOG_BYTES:-}" ]; then
    FETCHED=true
    gh api --allow-escape-sequences "repos/$REPO/actions/jobs/$JOB_ID/logs" \
      | head -c 1048577 > job_logs.txt || FETCHED=false
    if [ "$(wc -c < job_logs.txt)" -gt 1048576 ]; then
      # Keep any errors in the retained prefix and reserve room for the marker.
      TRUNCATED=true
      FETCHED=true
      JOB_LIMIT=$((JOB_LIMIT - 12))
    fi
  else
    FETCHED=true
    gh api --allow-escape-sequences "repos/$REPO/actions/jobs/$JOB_ID/logs" > job_logs.txt || FETCHED=false
  fi
  if [ "$FETCHED" != true ]; then
    if [ -n "${MAX_LOG_BYTES:-}" ]; then
      printf 'Job %s logs unavailable.\n' "$JOB_ID" | head -c "$JOB_LIMIT" >> failed_logs.txt
    else
      echo "Could not fetch logs for job $JOB_ID; skipping." >> failed_logs.txt
    fi
    continue
  fi
  {
    echo "===== JOB $JOB_ID ====="
    # Start a fresh buffer at each group header and keep it only if an error follows.
    awk '
    /##\[group\]/ {
        buffer = $0 "\n"
        next
    }
    {
        buffer = buffer $0 "\n"
        if (/##\[error\]/) {
            printf "%s\n", buffer
            buffer = ""
        }
    }
    ' job_logs.txt
    echo ""
  } > job_excerpt.txt
  if grep -q "##\[error\]" job_excerpt.txt; then
    FOUND_ERROR=true
  fi
  if [ -n "${MAX_LOG_BYTES:-}" ] && [ "$(wc -c < job_excerpt.txt)" -gt "$JOB_LIMIT" ]; then
    # Divide each job's budget among its errors so a later cleanup failure
    # cannot hide the original test failure.
    ERROR_COUNT=$(grep -c "##\[error\]" job_excerpt.txt || true)
    HEADER="JOB $JOB_ID"$'\n'
    printf '%s' "$HEADER" > job_limited.txt
    if [ "$ERROR_COUNT" -eq 0 ]; then
      printf '[truncated]\n' >> job_limited.txt
    else
      SECTION_LIMIT=$(((JOB_LIMIT - ${#HEADER}) / ERROR_COUNT))
      MARKER=$'[truncated]\n'
      if [ "$SECTION_LIMIT" -le "${#MARKER}" ]; then
        printf '%s' "$MARKER" >> job_limited.txt
      else
        LC_ALL=C awk -v limit="$SECTION_LIMIT" -v marker="$MARKER" '
        { buffer = buffer $0 "\n" }
        /##\[error\]/ {
          if (length(buffer) > limit && limit > length(marker)) {
            printf "%s%s", marker, substr(buffer, length(buffer) - (limit - length(marker)) + 1)
          } else if (length(buffer) > limit) {
            printf "%s", substr(marker, 1, limit)
          } else {
            printf "%s", buffer
          }
          buffer = ""
        }
        ' job_excerpt.txt >> job_limited.txt
      fi
    fi
    head -c "$JOB_LIMIT" job_limited.txt >> failed_logs.txt
  else
    cat job_excerpt.txt >> failed_logs.txt
  fi
  if [ "$TRUNCATED" = true ]; then
    printf '[truncated]\n' >> failed_logs.txt
    JOB_LIMIT=$((JOB_LIMIT + 12))
    FOUND_ERROR=true
  fi
done
if [ ! -s failed_logs.txt ] || [ "$FOUND_ERROR" != true ]; then
  if [ -n "${MAX_LOG_BYTES:-}" ]; then
    echo "Failed logs unavailable." > failed_logs.txt
  else
    echo "Failed jobs found but logs unavailable." > failed_logs.txt
  fi
fi
