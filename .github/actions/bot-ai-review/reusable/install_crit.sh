#!/usr/bin/env bash
# Install the pinned Crit binary after verifying its checksum.
set -euo pipefail

VERSION=v0.23.2
SHA256=10aa756a3146362be3a349cc8223955e23a1cd6daa0abbb13dd500741f793a90
curl -fsSLo "$RUNNER_TEMP/crit" \
  "https://github.com/tomasz-tomczyk/crit/releases/download/$VERSION/crit-linux-amd64"
echo "$SHA256  $RUNNER_TEMP/crit" | sha256sum --check
sudo install -m 0755 "$RUNNER_TEMP/crit" /usr/local/bin/crit
