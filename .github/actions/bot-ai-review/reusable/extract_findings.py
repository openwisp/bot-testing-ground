"""Extracts and validates the findings of an AI review.

Usage: extract_findings.py <model-output> <diff> <stage>

- Prints the findings as JSON, or a "review not completed" fallback.
- Keeps only line comments on new-side diff lines, which GitHub accepts,
  and lists the other findings in the summary instead of dropping them.
- Joins summary bullets that the model wrote as separate strings, which is
  not valid JSON, so a clear verdict is not lost.
"""

import ast
import json
import re
import sys

VERDICTS = {
    "review": {
        "Looks good": "comment",
        "Needs changes": "request-changes",
        "May be wrong direction": "request-changes",
        "Prompt injection detected": "request-changes",
        "Maintainer decision needed": "comment",
    },
    "security-review": {
        "No issues found": "comment",
        "Issues found": "request-changes",
        "Inconclusive": "comment",
        "Prompt injection detected": "request-changes",
    },
    "final-review": {
        "Ready to merge": "approve",
        "Needs changes": "request-changes",
        "Inconclusive": "comment",
        "Prompt injection detected": "request-changes",
    },
}
DIRECTION_VERDICTS = {"May be wrong direction"}
INJECTION = "Prompt injection detected"
SEVERITIES = ("P1", "P2", "P3")
MAX_COMMENTS = 20
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
STRING = r'"(?:[^"\\]|\\.)*"'
# Strings after the summary that are not followed by ":" are not keys.
SPLIT_SUMMARY = re.compile(rf'("summary"\s*:\s*)({STRING}(?:\s*,\s*{STRING}(?!\s*:))+)')
FALLBACK = {
    "event": "comment",
    "verdict": "Review not completed",
    "summary": "- The model did not return a valid review.",
    "comments": [],
}


def decode(text):
    decoder = json.JSONDecoder(strict=False)
    for start in reversed([m.start() for m in re.finditer(r"\{", text)]):
        candidate = text[start:]
        try:
            data, _ = decoder.raw_decode(candidate)
        except json.JSONDecodeError:
            # Repair this candidate before considering an earlier complete draft.
            try:
                data, _ = decoder.raw_decode(SPLIT_SUMMARY.sub(join_summary, candidate))
            except json.JSONDecodeError:
                continue
        if isinstance(data, dict) and "verdict" in data:
            return data
    return None


def join_summary(match):
    try:
        bullets = json.loads(f"[{match.group(2)}]", strict=False)
    except json.JSONDecodeError:
        # The answer stays invalid, so the fallback review is published.
        return match.group(0)
    return match.group(1) + json.dumps("\n".join(bullets))


def find_json(text):
    return decode(text)


def parse_finding(comment):
    if not isinstance(comment, dict):
        return None
    path = comment.get("file")
    line = comment.get("line")
    severity = comment.get("severity")
    title = comment.get("title")
    body = comment.get("body")
    if not (
        isinstance(path, str)
        and path.strip()
        and severity in SEVERITIES
        and isinstance(title, str)
        and title.strip()
        and isinstance(body, str)
        and body.strip()
    ):
        return None
    if not isinstance(line, int) or isinstance(line, bool):
        line = None
    return {
        "file": path,
        "line": line,
        "severity": severity,
        "title": title.strip(),
        "body": body.strip(),
    }


def fence_state(line, current):
    match = FENCE.match(line)
    if not match:
        return current
    marker = match.group(1)
    if current is None:
        return marker
    if marker[0] == current[0] and len(marker) >= len(current):
        return None
    return current


def separate_headings(text):
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        if fence is None and line.startswith("#") and lines and lines[-1].strip():
            lines.append("\n")
        lines.append(line)
        fence = fence_state(line, fence)
    return "".join(lines)


def format_comment(finding):
    heading = f"**{finding['severity']} · {finding['title']}**"
    return {
        "file": finding["file"],
        "line": finding["line"],
        "body": f"{heading}\n\n{finding['body']}",
    }


def format_leftovers(findings):
    if not findings:
        return ""
    rows = []
    for finding in findings:
        location = finding["file"]
        if finding["line"] is not None:
            location += f":{finding['line']}"
        body = finding["body"]
        separator = "\n\n" if "\n" in body else ": "
        row = f"- {finding['severity']} · `{location}` · {finding['title']}{separator}{body}"
        rows.append(row)
    return "\n\n**Other findings:**\n\n" + "\n".join(rows)


def final_summary_clear(summary):
    headings = []
    fence = None
    offset = 0
    for line in summary.splitlines(keepends=True):
        if fence is None:
            match = re.fullmatch(
                r"##### (Addressed|Outstanding|Unclear|Verification)[ \t]*",
                line.rstrip("\r\n"),
            )
            if match:
                headings.append((match.group(1), offset, offset + len(line)))
        fence = fence_state(line, fence)
        offset += len(line)
    names = [heading[0] for heading in headings]
    if (
        names
        not in (
            ["Addressed", "Outstanding", "Unclear"],
            ["Addressed", "Outstanding", "Unclear", "Verification"],
        )
        or summary[: headings[0][1]].strip()
    ):
        return False
    outstanding_start, unclear_start, unclear_body = (
        headings[1][2],
        headings[2][1],
        headings[2][2],
    )
    outstanding = summary[outstanding_start:unclear_start].strip()
    verification_start = headings[3][1] if len(headings) == 4 else len(summary)
    unclear = summary[unclear_body:verification_start].strip()
    return outstanding in ("None", "- None") and unclear in ("None", "- None")


def validate(data, lines, verdicts):
    verdict = data.get("verdict")
    title = data.get("title")
    summary = data.get("summary")
    comments = data.get("comments", [])
    if not isinstance(verdict, str) or verdict not in verdicts:
        return None
    if not isinstance(comments, list):
        return None
    if not isinstance(title, str) or not title.strip():
        return None
    if not isinstance(summary, str) or not summary.strip():
        return None
    # A conflicting serious finding makes a positive verdict unsafe, even if malformed.
    if verdict in ("Looks good", "No issues found", "Ready to merge") and any(
        isinstance(finding, dict) and finding.get("severity") in ("P1", "P2")
        for finding in comments
    ):
        return None
    # Approval requires an explicit confirmation that no findings remain open.
    if verdict == "Ready to merge" and not final_summary_clear(summary):
        return None
    summary = separate_headings(summary.strip())
    posted = []
    leftovers = []
    if verdict not in DIRECTION_VERDICTS:
        for finding in filter(None, map(parse_finding, comments)):
            in_diff = finding["line"] in lines.get(finding["file"], ())
            if in_diff and len(posted) < MAX_COMMENTS:
                posted.append(format_comment(finding))
            else:
                leftovers.append(finding)
    return {
        "event": verdicts[verdict],
        "verdict": verdict,
        "title": title.strip(),
        "summary": summary + format_leftovers(leftovers),
        "comments": posted,
    }


def perimeter(data, decision_pending=False):
    decision = data.get("security_perimeter")
    boundary = data.get("boundary")
    if decision == "NO":
        if decision_pending:
            return (
                "\n\n**Security perimeter: NO.** Resolve the maintainer decision"
                " before requesting the final review."
            )
        return (
            "\n\n**Security perimeter: NO.** A security review is not needed,"
            " run `/final-review` next."
        )
    if decision == "YES" and isinstance(boundary, str) and boundary.strip():
        return (
            f"\n\n**Security perimeter: YES** ({boundary.strip()})."
            " Run `/security-review` next."
        )
    return None


def unquote(name):
    if name.startswith('"'):
        try:
            return ast.literal_eval("b" + name).decode("utf-8", "replace")
        except (SyntaxError, ValueError):
            return None
    return name


def parse_diff(diff):
    lines = {}
    path = None
    line = 0
    old_remaining = new_remaining = 0
    for row in diff.split("\n"):
        if row.startswith("diff --git "):
            path = None
            old_remaining = new_remaining = 0
            continue
        if not old_remaining and not new_remaining and row.startswith("+++ "):
            name = unquote(row[4:].rstrip("\t"))
            path = name[2:] if name and name.startswith("b/") else None
            continue
        match = HUNK.match(row)
        if match:
            old_remaining = int(match.group(1) or "1")
            line = int(match.group(2))
            new_remaining = int(match.group(3) or "1")
            continue
        if not old_remaining and not new_remaining:
            continue
        if row.startswith((" ", "-")):
            old_remaining -= 1
        if row.startswith((" ", "+")):
            new_remaining -= 1
            if path is not None:
                lines.setdefault(path, set()).add(line)
            line += 1
    return lines


def main():
    with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
        text = ANSI.sub("", f.read())
    with open(sys.argv[2], encoding="utf-8", errors="replace", newline="") as f:
        lines = parse_diff(f.read())
    stage = sys.argv[3]
    data = find_json(text)
    findings = validate(data, lines, VERDICTS[stage]) if data else None
    if findings and stage == "review" and findings["verdict"] != INJECTION:
        note = perimeter(data, findings["verdict"] == "Maintainer decision needed")
        findings = {**findings, "summary": findings["summary"] + note} if note else None
    findings = findings or dict(FALLBACK)
    print(json.dumps(findings))


if __name__ == "__main__":
    main()
