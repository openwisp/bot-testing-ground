"""Builds the context of a pull request for the review.

Usage: context.py <repository> <number>

- Includes the title, the description and the issues it references.
- Fetches at most MAX_ISSUES OpenWISP issues, so the description cannot
  make the workflow request arbitrary resources.
"""

import json
import re
import subprocess
import sys

MAX_ISSUES = 5
REFERENCE = re.compile(
    r"https://github\.com/(openwisp/[\w.-]+)/issues/(\d+)"
    r"|(?<![\w/.-])(openwisp/[\w.-]+)?#(\d+)\b",
    re.IGNORECASE,
)


def gh(*args):
    result = subprocess.run(
        ["gh", "api", *args], check=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)


def references(body, repository, number):
    found = []
    for match in REFERENCE.finditer(body):
        repo = match.group(1) or match.group(3) or repository
        reference = (repo.lower(), int(match.group(2) or match.group(4)))
        if reference != (repository.lower(), number) and reference not in found:
            found.append(reference)
    return found[:MAX_ISSUES]


def author(item):
    return (item.get("user") or {}).get("login")


def message(item):
    return {"author": author(item), "body": item.get("body") or ""}


def fetch_issue(repository, number):
    try:
        issue = gh(f"repos/{repository}/issues/{number}")
    except subprocess.CalledProcessError as error:
        if "HTTP 404" in (error.stderr or ""):
            return None
        print(f"Failed to fetch {repository}#{number}: {error.stderr}", file=sys.stderr)
        return {
            "repository": repository,
            "number": number,
            "error": "Issue context unavailable.",
        }
    if "pull_request" in issue:
        return None
    result = {
        "repository": repository,
        "number": number,
        "title": issue["title"],
        **message(issue),
    }
    try:
        pages = gh(
            "--paginate", "--slurp", f"repos/{repository}/issues/{number}/comments"
        )
        result["comments"] = [message(comment) for page in pages for comment in page]
    except subprocess.CalledProcessError as error:
        print(
            f"Failed to fetch comments for {repository}#{number}: {error.stderr}",
            file=sys.stderr,
        )
        result["comments_error"] = "Issue discussion unavailable."
    return result


def main():
    repository, number = sys.argv[1], int(sys.argv[2])
    pr = gh(f"repos/{repository}/pulls/{number}")
    body = pr.get("body") or ""
    issues = (
        fetch_issue(*reference) for reference in references(body, repository, number)
    )
    context = {
        "title": pr["title"],
        **message(pr),
        "issues": [issue for issue in issues if issue],
    }
    print(json.dumps(context, indent=1))


if __name__ == "__main__":
    main()
