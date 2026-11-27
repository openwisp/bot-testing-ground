"""Prints the repository guidance that applies to a pull request.

Usage: guidance.py <base-sha> <head-sha>

- Reads the root AGENTS.md and those in directories above changed files.
- Uses the base branch version, so the pull request cannot change the
  rules it is reviewed against.
"""

import subprocess
import sys
from pathlib import PurePosixPath

NAME = "AGENTS.md"


def applicable(paths):
    return list(
        dict.fromkeys(
            str(parent / NAME)
            for path in paths
            for parent in reversed(PurePosixPath(path).parents)
        )
    )


def main():
    base, head = sys.argv[1:3]
    diff = subprocess.run(
        ["git", "diff", "--no-renames", "--name-only", "-z", f"{base}...{head}"],
        capture_output=True,
        text=True,
        check=True,
    )
    for path in applicable(filter(None, diff.stdout.split("\0"))):
        show = subprocess.run(
            ["git", "show", f"{base}:{path}"], capture_output=True, text=True
        )
        if show.returncode == 0:
            print(f"## {path}\n\n{show.stdout}")


if __name__ == "__main__":
    main()
