"""Wake stored review requests when a primary CI workflow completes."""

import json
import os

from ci_requests import GitHub, wake


def main():
    with open(os.environ["GITHUB_EVENT_PATH"]) as event_file:
        event = json.load(event_file)
    wake(
        GitHub(os.environ["REPOSITORY"]),
        int(os.environ["APP_ID"]),
        event["workflow_run"],
    )


if __name__ == "__main__":
    main()
