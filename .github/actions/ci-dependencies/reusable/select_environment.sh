#!/usr/bin/env bash
# Select the review environment from the trusted CI matrix.
set -euo pipefail

DIR=$(dirname "$(realpath "$0")")
JOB=$(yq -o=json '.jobs.test' "$CI_ROOT/.github/workflows/ci.yml")
MATRIX=$(jq '.strategy.matrix // null' <<<"$JOB")
PYTHON_VERSION=
DJANGO_VERSION=
NODE_VERSION=
ROW='{}'
if [ "$MATRIX" = null ]; then
  if [ -n "${REVIEW_MATRIX_OVERRIDE:-}" ]; then
    echo "::error::A matrix override requires a CI matrix" >&2
    exit 1
  fi
else
  ARGS=()
  if [ -n "${REVIEW_MATRIX_OVERRIDE:-}" ]; then
    ARGS+=("$REVIEW_MATRIX_OVERRIDE")
  fi
  ROW=$(python3 "$DIR/select_matrix.py" "${ARGS[@]}" <<<"$MATRIX")
  PYTHON_VERSION=$(jq -r '.["python-version"] // ""' <<<"$ROW")
  DJANGO_VERSION=$(jq -r '.["django-version"] // ""' <<<"$ROW")
  NODE_VERSION=$(jq -r '.["node-version"] // ""' <<<"$ROW")
fi
if [ -z "$PYTHON_VERSION" ]; then
  PYTHON_VERSION=$(jq -r '[.steps[]? | select((.uses // "") | startswith("actions/setup-python@")) |
    .with["python-version"] // ""] | first // ""' <<<"$JOB")
fi
if [ -z "$NODE_VERSION" ]; then
  NODE_VERSION=$(jq -r '[.steps[]? | select((.uses // "") | startswith("actions/setup-node@")) |
    .with["node-version"] // ""] | first // ""' <<<"$JOB")
fi
NODE_VERSION_FILE=$(jq -r '[.steps[]? | select((.uses // "") | startswith("actions/setup-node@")) |
  .with["node-version-file"] // ""] | first // ""' <<<"$JOB")
if [ -z "$PYTHON_VERSION" ] && [ -z "$NODE_VERSION" ] && [ -z "$NODE_VERSION_FILE" ] &&
  [ -f "$CI_ROOT/.nvmrc" ]; then
  NODE_VERSION_FILE=.nvmrc
fi
if [ -z "$PYTHON_VERSION" ] && [ -z "$NODE_VERSION_FILE" ] && [ -z "$NODE_VERSION" ]; then
  echo "::error::$CI_ROOT/.github/workflows/ci.yml: unsupported review runtime" >&2
  exit 1
fi
BROWSERS=$(jq -r '.env.AI_REVIEW_BROWSERS // ""' <<<"$JOB")
if [ -z "$BROWSERS" ]; then
  # Preserve the existing pilot's browser setup without assuming all Node projects need Chrome.
  BROWSERS=$(jq -r 'if any(.steps[]?; (.uses // "") | startswith("browser-actions/setup-chrome@"))
    then "chrome" else "none" end' <<<"$JOB")
fi
CHROME=false
FIREFOX=false
case "$BROWSERS" in
  none) ;;
  chrome) CHROME=true ;;
  firefox) FIREFOX=true ;;
  chrome,firefox|firefox,chrome) CHROME=true; FIREFOX=true ;;
  *) echo "::error::Unsupported AI_REVIEW_BROWSERS: $BROWSERS" >&2; exit 1 ;;
esac
CACHE_GLOB=$(jq -r '.env.AI_REVIEW_CACHE_GLOB // ""' <<<"$JOB")
if [ -n "$CACHE_GLOB" ] &&
  { [[ ! "$CACHE_GLOB" =~ ^[a-zA-Z0-9_./*?-]+$ ]] || [[ "$CACHE_GLOB" == *..* ]]; }; then
  echo "::error::Invalid AI_REVIEW_CACHE_GLOB" >&2
  exit 1
fi
CACHE_AXES=$(jq -r '.env.AI_REVIEW_CACHE_AXES // ""' <<<"$JOB")
# Resolve only direct matrix references, not secrets or arbitrary expressions.
INSTALLER_ENV=$(jq -ce --argjson row "$ROW" '
  ((.env // {}) + ([.steps[]? | select(.id == "deps") | .env // {}] | first // {}))
  | to_entries
  | map(select((.value | type) == "string" and
      (.value | test("^\\$\\{\\{\\s*matrix\\.[A-Za-z0-9_-]+\\s*\\}\\}$"))))
  | map(. as $entry |
      ($entry.value | capture("matrix\\.(?<axis>[A-Za-z0-9_-]+)").axis) as $axis |
      if ($entry.key | test("^[A-Za-z_][A-Za-z0-9_]*$")) and ($row | has($axis)) and
         (($row[$axis] | type) == "string" or ($row[$axis] | type) == "number" or
          ($row[$axis] | type) == "boolean") and
         (($row[$axis] | tostring | contains("\u0000")) | not)
      then {key: $entry.key, value: ($row[$axis] | tostring)}
      else error("invalid matrix environment") end)
  | from_entries' <<<"$JOB")
SYSTEM_DEPS=$(jq -r '.env.AI_REVIEW_SYSTEM_DEPS // false' <<<"$JOB")
case "$SYSTEM_DEPS" in
  true|false) ;;
  *) echo "::error::Invalid AI_REVIEW_SYSTEM_DEPS" >&2; exit 1 ;;
esac
CACHE_VARIANT=
if [ -n "$CACHE_AXES" ]; then
  if [[ ! "$CACHE_AXES" =~ ^[a-zA-Z0-9_,-]+$ ]]; then
    echo "::error::Invalid AI_REVIEW_CACHE_AXES" >&2
    exit 1
  fi
  CACHE_VARIANT=$(jq -er --arg axes "$CACHE_AXES" \
    '. as $row | ($axes | split(",")) as $keys |
     [$keys[] as $key |
      (if $row | has($key) then $row[$key] else error("missing cache axis") end) | tostring |
      if test("^[a-zA-Z0-9_.-]+$") then . else error("invalid cache axis") end] | join(":")' \
    <<<"$ROW")
fi
{
  echo "python_version=$PYTHON_VERSION"
  echo "django_version=$DJANGO_VERSION"
  echo "node_version_file=$NODE_VERSION_FILE"
  echo "node_version=$NODE_VERSION"
  echo "chrome=$CHROME"
  echo "firefox=$FIREFOX"
  echo "extra_cache_glob=$CACHE_GLOB"
  echo "extra_cache_variant=$CACHE_VARIANT"
  echo "system_deps=$SYSTEM_DEPS"
  echo "installer_env=$INSTALLER_ENV"
} >> "$GITHUB_OUTPUT"
