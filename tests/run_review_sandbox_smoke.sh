#!/usr/bin/env bash
# Exercise the production sandbox on a GitHub runner without invoking an AI model.
set -euo pipefail

actions=openwisp-actions/.github/actions
bash "$actions/bot-ai-review/reusable/prepare_sandbox.sh"
printf '\npytest --version\n' >> install-ci-deps.sh
INSTALLER_ENV='{}' PREPARE_PYTHON=true bash "$actions/ci-dependencies/reusable/prepare_review.sh"

pr=/tmp/ai-review/pr
mkdir "$pr"
install -m 644 tests/test_review_sandbox_smoke.py "$pr/test_review_sandbox_smoke.py"
(
  cd "$pr"
  /usr/local/bin/ai-review-shell -c 'pytest -q test_review_sandbox_smoke.py'
)
test ! -e /dev/shm/openwisp-review-smoke
