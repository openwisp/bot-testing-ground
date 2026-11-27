"""Check that OpenCode exposes the requested variant for the review model."""

import json
import sys


def main():
    model, effort = sys.argv[1:]
    lines = sys.stdin.read().splitlines()
    for index, line in enumerate(lines):
        if line.strip() != model:
            continue
        try:
            start = index + 1
            metadata, _ = json.JSONDecoder().raw_decode("\n".join(lines[start:]))
        except json.JSONDecodeError:
            break
        if effort in (metadata.get("variants") or {}):
            return
        break
    print(f"::error::Effort {effort!r} is not available for {model}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
