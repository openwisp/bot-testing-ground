#!/usr/bin/env bash
# Install trusted CI dependencies as the unprivileged review user.
set -euo pipefail

RUN=${1:-/tmp/ai-review/run}
REVIEW_HOME=${2:-/home/reviewer}
INSTALLER_ENV=$(jq -ce 'if type == "object" and all(to_entries[];
  (.key | test("^[A-Za-z_][A-Za-z0-9_]*$")) and
  (.value | type == "string" and (contains("\u0000") | not)))
  then . else error("invalid installer environment") end' \
  <<<"${INSTALLER_ENV:-\{\}}")
mapfile -d '' -t MATRIX_ENV < <(jq -j 'to_entries[] | .key, "=", .value, "\u0000"' <<<"$INSTALLER_ENV")
MATRIX_DJANGO_VERSION=$(jq -r '.DJANGO_VERSION // ""' <<<"$INSTALLER_ENV")
DJANGO_VERSION=${DJANGO_VERSION:-$MATRIX_DJANGO_VERSION}
sudo rsync -a --chown=reviewer:reviewer --exclude=/.git --exclude=/openwisp-actions \
  "$GITHUB_WORKSPACE/" "$RUN/"
# Record base files before installation so synchronization removes files deleted by the PR.
(cd "$GITHUB_WORKSPACE" && find . \( -path ./.git -o -path ./openwisp-actions \
  -o -path ./node_modules \) -prune -o \( -type f -o -type l \) -print0 | LC_ALL=C sort -z) \
  | sudo -u reviewer tee "$REVIEW_HOME/.ai-review-files" >/dev/null
sudo install -d -o reviewer -g reviewer "$REVIEW_HOME/.cache"
if [ -d "$HOME/.cache/pip" ]; then
  sudo cp -a "$HOME/.cache/pip" "$REVIEW_HOME/.cache/"
fi
if [ -n "${YARN_CACHE_DIR:-}" ] && [ -d "$YARN_CACHE_DIR" ]; then
  sudo install -d -o reviewer -g reviewer "$REVIEW_HOME/.cache/yarn"
  sudo cp -a "$YARN_CACHE_DIR" "$REVIEW_HOME/.cache/yarn/"
fi
sudo chown -R reviewer:reviewer "$REVIEW_HOME/.cache"
mkdir -p "$HOME/.cache/ci-deps"
SYSTEM_DEPS_READY=0
if [ "${SYSTEM_DEPS_ENABLED:-false}" = true ]; then
  installer=$(git -C "$GITHUB_WORKSPACE" ls-tree "${DEFAULT_SHA:?}" -- install-ci-deps.sh)
  if [ -n "$installer" ]; then
    (
      system_root=$(mktemp -d "${RUNNER_TEMP:?}/system-deps.XXXXXXXX")
      trap 'git -C "$GITHUB_WORKSPACE" worktree remove --force "$system_root"' EXIT
      git -C "$GITHUB_WORKSPACE" worktree add --quiet --detach "$system_root" "$DEFAULT_SHA"
      cd "$system_root"
      # Do not pass the target branch's environment or tools to the default branch installer.
      /usr/bin/env -i HOME="$HOME" PATH=/usr/sbin:/usr/bin:/sbin:/bin CI=true \
        CI_QA="${CI_QA:-0}" CI_DEPS_CACHE="$HOME/.cache/ci-deps" CI_SYSTEM_DEPS_ONLY=1 \
        /bin/bash ./install-ci-deps.sh
    )
  else
    # Temporary rollout fallback (#47). This still trusts the PR target branch, never its head.
    echo "::warning::The default branch has no install-ci-deps.sh; using the PR target branch"
    (cd "$GITHUB_WORKSPACE" && env -i "${MATRIX_ENV[@]}" HOME="$HOME" PATH="$PATH" CI=true \
      DJANGO_VERSION="$DJANGO_VERSION" CI_QA="${CI_QA:-0}" \
      CI_DEPS_CACHE="$HOME/.cache/ci-deps" CI_SYSTEM_DEPS_ONLY=1 bash ./install-ci-deps.sh)
  fi
  SYSTEM_DEPS_READY=1
fi
if [ -d "$HOME/.cache/ci-deps" ]; then
  sudo cp -a "$HOME/.cache/ci-deps" "$REVIEW_HOME/.cache/"
  sudo chown -R reviewer:reviewer "$REVIEW_HOME/.cache/ci-deps"
fi
cd "$RUN"
# Keep installer output out of the Actions command channel, even on failure.
output=$(mktemp "${RUNNER_TEMP:?}/installer.XXXXXXXX")
trap 'rm -f -- "$output"' EXIT
stop=$(openssl rand -hex 16)
status=0
# The runner, not the reviewer, must own the captured log.
# shellcheck disable=SC2024
sudo -n -H -u reviewer /usr/bin/env -i /usr/bin/python3 -I /usr/local/lib/ai-review-write-sandbox.py \
  "$REVIEW_HOME" "$RUN" -- /usr/bin/env "${MATRIX_ENV[@]}" \
  HOME="$REVIEW_HOME" USER=reviewer LOGNAME=reviewer CI=true \
  PATH="$REVIEW_HOME/.local/bin:$PATH" DJANGO_VERSION="$DJANGO_VERSION" CI_QA="${CI_QA:-0}" \
  TMPDIR="$REVIEW_HOME/.cache/ai-review-tmp" \
  CI_SYSTEM_DEPS_READY="$SYSTEM_DEPS_READY" \
  CI_DEPS_CACHE="$REVIEW_HOME/.cache/ci-deps" \
  YARN_CACHE_FOLDER="$REVIEW_HOME/.cache/yarn" \
  /bin/bash -ec '
    if [ "$1" = true ]; then
      # Pip checks Unix permissions, which do not reflect Landlock write restrictions.
      python -m venv .venv
      export VIRTUAL_ENV="$PWD/.venv"
      export PATH="$VIRTUAL_ENV/bin:$PATH"
    fi
    exec /bin/bash ./install-ci-deps.sh
  ' prepare-review "${PREPARE_PYTHON:-false}" </dev/null >"$output" 2>&1 || status=$?
printf '::stop-commands::%s\n' "$stop"
cat -- "$output"
printf '\n::%s::\n' "$stop"
exit "$status"
