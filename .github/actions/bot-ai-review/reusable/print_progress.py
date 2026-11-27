"""Print the review's tool calls while it runs.

Follow the events files until the review process ends: commands when they
start, recorded by the sandbox shell, and tool calls when they end, reported
by OpenCode. The job log then shows the last command even if the runner is
lost while it runs.
Lines are checked for the provider's credentials like the output of a
finished review: a line is hidden when it contains one, or when the
credentials cannot be read. Every token seen is saved for the scan of the
review's output, which can contain a token replaced during the review.
"""

import json
import os
import sys
import time


def read_credentials(path, model):
    """Return the provider tokens, or None when they cannot be checked."""
    try:
        with open(path) as f:
            providers = json.load(f)
    except FileNotFoundError:
        # Copilot is configured with an auth file, other providers may not be.
        return None if model.startswith("github-copilot/") else set()
    except (OSError, ValueError):
        return None
    if not isinstance(providers, dict):
        return None
    tokens = {
        token
        for provider in providers.values()
        if isinstance(provider, dict)
        for token in (
            provider.get("refresh"),
            provider.get("access"),
            provider.get("key"),
        )
        if isinstance(token, str) and token
    }
    if model.startswith("github-copilot/") and not tokens:
        return None
    return tokens


def describe(event):
    if event.get("type") == "tool_start":
        args = event.get("args") or [""]
        return f"Started: {args[-1]}"
    part = event.get("part") or {}
    state = part.get("state") or {}
    inputs = state.get("input") or {}
    target = inputs.get("command") or inputs.get("url", "")
    return f"Tool: {part.get('tool')} ({state.get('status')}) {target}"


def running(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def parse(line):
    try:
        event = json.loads(line)
    except ValueError:
        return None
    if isinstance(event, dict) and event.get("type") in ("tool_start", "tool_use"):
        return event
    return None


def when(event):
    timestamp = event.get("timestamp")
    return timestamp if isinstance(timestamp, (int, float)) else 0


def show(event, tokens, known):
    # A refresh can leave the file briefly incomplete: hide only this line then.
    if tokens is None:
        return "Tool call hidden: the credentials could not be read"
    text = describe(event)
    if any(token in text for token in known):
        return "Tool call hidden: it contains a credential"
    return text


def save(path, tokens):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.writelines(f"{token}\n" for token in tokens)


def main():
    auth, model, initial, history, pid, *paths = sys.argv[1:]
    # The credentials before the review started, which a refresh may replace.
    known = read_credentials(initial, model) or set()
    files = [open(path, "rb") for path in paths]
    # Process only complete lines, which OpenCode may write in parts.
    partial = [b""] * len(files)
    pending = []
    while True:
        # Check before the last read, so events written before the end are printed.
        ended = not running(int(pid))
        # Records are written as they happen: those over a second old are in the files.
        written = time.time() * 1000 - 1000
        for index, f in enumerate(files):
            *lines, partial[index] = (partial[index] + f.read()).split(b"\n")
            pending += filter(None, map(parse, lines))
        # Read the credentials after the events, so they include any token the
        # events can contain. Read them between events too, so a token replaced
        # before the next event is still known.
        tokens = read_credentials(auth, model)
        if tokens is not None:
            known |= tokens
        # Print the records of both files in the order they happened, holding
        # each until any earlier record of the other file has been read.
        pending.sort(key=when)
        while pending and (ended or when(pending[0]) <= written):
            print(show(pending.pop(0), tokens, known), flush=True)
        if ended:
            break
        time.sleep(0.2)
    save(history, known)


if __name__ == "__main__":
    main()
