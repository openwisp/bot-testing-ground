"""Exercise the review extractor with a split final summary and earlier draft."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = (
    Path(os.environ.get("ACTIONS_ROOT", "openwisp-actions"))
    / ".github/actions/bot-ai-review/reusable/extract_findings.py"
)

with tempfile.TemporaryDirectory() as tmp:
    output = Path(tmp, "answer.txt")
    diff = Path(tmp, "pr.diff")
    output.write_text(
        'Earlier: {"verdict":"No issues found","title":"Draft",'
        '"summary":"No issues","comments":[]}\n'
        'Final: {"verdict":"Issues found","title":"Final",'
        '"summary":"- Bug", "- More details",'
        '"comments":[{"file":"app.py","line":1,"severity":"P1",'
        '"title":"Bug","body":"Details"}]}'
    )
    diff.write_text(
        "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -0,0 +1 @@\n+line\n"
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(output), str(diff), "security-review"],
        check=True,
        capture_output=True,
        text=True,
    )
    review = json.loads(result.stdout)
    assert review["verdict"] == "Issues found", review
    assert len(review["comments"]) == 1, review
