"""Release a completed CI-aware review request and update its comment."""

import os

from ci_requests import GitHub, finish


def main():
    finish(
        GitHub(os.environ["REPOSITORY"]),
        int(os.environ["APP_ID"]),
        int(os.environ["PR_NUMBER"]),
        int(os.environ["RECORD_ID"]),
        os.environ["PUBLISH_RESULT"],
        os.environ.get("REVIEW_URL", ""),
        os.environ.get("SETUP_FAILED") == "true",
        os.environ.get("RUN_URL", ""),
    )


if __name__ == "__main__":
    main()
