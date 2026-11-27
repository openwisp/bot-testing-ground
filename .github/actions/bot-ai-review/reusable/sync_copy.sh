#!/usr/bin/env bash
# Synchronize review files without deleting unrelated sandbox files.
set -euo pipefail

export LC_ALL=C
SRC=$1
DST=$2
LIST=$3
# Serialize updates so parallel commands cannot compare against a stale file list.
exec 9>"$LIST.lock"
flock 9
NEW=$(mktemp "$LIST.XXXXXX")
# Keep paths NUL-separated and sorted in the same locale for comm, even with odd filenames.
(cd "$SRC" && find . \( -type f -o -type l \) -print0 | sort -z) >"$NEW"
if [ -f "$LIST" ]; then
  # Remove only paths that disappeared from the source since the last sync.
  comm -z -23 "$LIST" "$NEW" | (cd "$DST" && xargs -0 -r rm -f --)
fi
# Compare file contents because an edit can leave both its size and timestamp unchanged.
rsync -a --checksum --force "$SRC/" "$DST/"
mv "$NEW" "$LIST"
