"""Extracts and validates the findings of an AI review.

Usage: extract_findings.py <model-output> <changed-files>

Prints the validated findings as JSON. When the model output does not
contain valid findings, prints a comment review explaining that the
review could not be completed.
"""

import json
import re
import sys

EVENTS = {"comment", "request-changes"}
MAX_COMMENTS = 20
MAX_BODY = 2000
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
FALLBACK = {
    "event": "comment",
    "summary": "The review could not be completed: the model output was not valid.",
    "comments": [],
}


def find_json(text):
    decoder = json.JSONDecoder()
    for start in reversed([m.start() for m in re.finditer(r"\{", text)]):
        try:
            data, _ = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "event" in data:
            return data
    return None


def validate(data, changed_files):
    event = data.get("event")
    summary = data.get("summary")
    comments = data.get("comments", [])
    if event not in EVENTS:
        return None
    if not isinstance(summary, str) or not summary.strip():
        return None
    if not isinstance(comments, list):
        return None
    valid_comments = []
    for comment in comments[:MAX_COMMENTS]:
        if not isinstance(comment, dict):
            continue
        path = comment.get("file")
        line = comment.get("line")
        body = comment.get("body")
        if (
            path in changed_files
            and isinstance(line, int)
            and not isinstance(line, bool)
            and line > 0
            and isinstance(body, str)
            and body.strip()
        ):
            valid_comments.append(
                {"file": path, "line": line, "body": body.strip()[:MAX_BODY]}
            )
    return {
        "event": event,
        "summary": summary.strip()[:MAX_BODY],
        "comments": valid_comments,
    }


def main():
    with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
        text = ANSI.sub("", f.read())
    with open(sys.argv[2], encoding="utf-8") as f:
        changed_files = {line.strip() for line in f if line.strip()}
    data = find_json(text)
    findings = validate(data, changed_files) if data else None
    print(json.dumps(findings or FALLBACK))


if __name__ == "__main__":
    main()
