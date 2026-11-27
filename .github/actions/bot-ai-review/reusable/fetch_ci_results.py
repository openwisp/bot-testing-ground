"""Collect the selected CI attempt as untrusted review data."""

import json
import os
from pathlib import Path

from ci_results import selected_results


def main():
    data = selected_results(
        os.environ["REPOSITORY"],
        int(os.environ["CI_RUN_ID"]),
        int(os.environ["CI_ATTEMPT"]),
        os.environ["HEAD_SHA"],
    )
    destination = Path(os.environ["DATA_DIR"]) / "ci-results.json"
    destination.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
