"""Adapt authenticated review events to the CI request coordinator."""

import json
import os

from ci_requests import GitHub, coordinate


def prepare(
    enabled, request, event_comment, repository, pr_number, app_id, review_run_id=None
):
    """Pass through legacy requests or ask the coordinator to authorize a CI-aware review.

    The coordinator verifies both an internal dispatch and its stored request.
    """
    if not enabled:
        return request
    dispatch = (
        event_comment
        if event_comment.get("body", "").startswith("/ai-review-resume ")
        else None
    )
    if dispatch is None and request.get("stage") not in (
        "review",
        "security-review",
        "final-review",
    ):
        return {}
    return coordinate(
        GitHub(repository),
        app_id,
        repository,
        pr_number,
        request,
        dispatch,
        review_run_id,
    )


def main():
    with open(os.environ["GITHUB_EVENT_PATH"]) as event_file:
        event = json.load(event_file)
    request = {
        "stage": os.environ.get("STAGE", ""),
        "head_sha": os.environ.get("HEAD_SHA", ""),
        "base_sha": os.environ.get("BASE_SHA", ""),
        "base_ref": os.environ.get("BASE_REF", ""),
        "model": os.environ.get("MODEL", ""),
        "effort": os.environ.get("EFFORT", ""),
        "comment_id": event["comment"]["id"],
    }
    result = prepare(
        os.environ.get("CI_ENABLED") == "true",
        request,
        event["comment"],
        os.environ["REPOSITORY"],
        int(os.environ["PR_NUMBER"]),
        int(os.environ["APP_ID"]),
        int(os.environ["GITHUB_RUN_ID"]),
    )
    # Output names are fixed and values may not introduce additional workflow
    # outputs, including when a repository variable contains a newline.
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        for key in (
            "stage",
            "head_sha",
            "base_sha",
            "base_ref",
            "model",
            "effort",
            "comment_id",
            "record_id",
            "run_id",
            "attempt",
        ):
            value = str(result.get(key, ""))
            if "\n" in value or "\r" in value:
                raise ValueError(f"Invalid {key}")
            output.write(f"{key}={value}\n")


if __name__ == "__main__":
    main()
