"""Builds the full discussion of a pull request for the review.

Usage: history.py <directory>

- Reads every page fetched by fetch_history.sh, so no discussion is left out.
- Groups inline comments into threads with their resolved state.
- Removes the prompts that review bots such as CodeRabbit add for AI
  agents, so the reviewer does not mistake them for prompt injection.
"""

import json
import os
import re
import sys

AGENT_PROMPT = re.compile(
    r"<details>\s*<summary>(?:<[^>]*>|[^\w<])*"
    r"Prompt for (?:all review comments with )?AI agents\s*</summary>.*?</details>",
    re.IGNORECASE | re.DOTALL,
)


def load(directory, name):
    with open(os.path.join(directory, name), encoding="utf-8") as f:
        return json.load(f)


def flatten(pages):
    return [item for page in pages for item in page]


def author(item):
    return (item.get("user") or {}).get("login")


def message(item):
    body = item["body"]
    if (item.get("user") or {}).get("type") == "Bot":
        body = AGENT_PROMPT.sub("", body)
    return {"author": author(item), "body": body}


def build(comments, reviews, review_comments, threads):
    states = {
        thread["comments"]["nodes"][0]["fullDatabaseId"]: thread
        for thread in threads
        if thread["comments"]["nodes"]
    }
    grouped = {}
    for comment in review_comments:
        root = comment.get("in_reply_to_id") or comment["id"]
        grouped.setdefault(root, []).append(comment)
    return {
        "comments": [message(comment) for comment in comments],
        "reviews": [
            {**message(review), "state": review["state"], "commit": review["commit_id"]}
            for review in reviews
        ],
        "threads": [
            {
                "resolved": states.get(str(root), {}).get("isResolved"),
                "outdated": states.get(str(root), {}).get("isOutdated"),
                "path": replies[0]["path"],
                "line": replies[0]["line"],
                "comments": [message(reply) for reply in replies],
            }
            for root, replies in grouped.items()
        ],
    }


def main():
    directory = sys.argv[1]
    threads = [
        node
        for page in load(directory, "threads.json")
        for node in page["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    ]
    history = build(
        flatten(load(directory, "comments.json")),
        flatten(load(directory, "reviews.json")),
        flatten(load(directory, "review-comments.json")),
        threads,
    )
    print(json.dumps(history, indent=1))


if __name__ == "__main__":
    main()
