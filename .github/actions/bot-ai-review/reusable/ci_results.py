"""Identify the CI run belonging to a pull request revision."""

import json
import os
import subprocess
import tempfile
from pathlib import Path


class AmbiguousCIError(ValueError):
    """The available run data cannot identify one pull request safely."""


def matching_runs(runs, pr):
    """Match the source and SHA without relying on GitHub's changing PR associations."""
    return [run for run in runs if matches_source(run, pr)]


def matches_source(run, pr):
    """Match the run's source even when GitHub associates it with another PR."""
    head = pr["head"]
    return (
        run["event"] == "pull_request"
        and run["head_sha"] == head["sha"]
        and head.get("repo")
        and run.get("head_repository")
        and run["head_repository"]["id"] == head["repo"]["id"]
        and run["head_branch"] == head["ref"]
    )


def classify(run):
    """Allow ordinary CI failures as evidence, but stop on other terminal outcomes."""
    if run["status"] != "completed":
        return "waiting"
    if run.get("conclusion") in ("success", "failure"):
        return "ready"
    return "stopped"


def select_run(runs, pr):
    """Find the newest candidate; the caller must resolve any shared PR associations.

    A retry keeps the same run ID and changes its attempt number.
    """
    return max(matching_runs(runs, pr), key=lambda run: run["id"], default=None)


def gh(endpoint):
    """Read every page, which gh prints as a separate JSON document."""
    output = subprocess.check_output(["gh", "api", "--paginate", endpoint], text=True)
    decoder = json.JSONDecoder()
    pages = []
    remaining = output.strip()
    while remaining:
        page, end = decoder.raw_decode(remaining)
        pages.append(page)
        remaining = remaining[end:].lstrip()
    return pages


def failed_logs(repository, run_id, attempt):
    script = (
        Path(__file__).resolve().parents[2] / "bot-ci-failure/reusable/fetch_logs.sh"
    )
    env = {
        **os.environ,
        "REPO": repository,
        "RUN_ID": str(run_id),
        "ATTEMPT": str(attempt),
        "MAX_LOG_BYTES": "65536",
    }
    with tempfile.TemporaryDirectory() as directory:
        result = subprocess.run(
            ["timeout", "--kill-after=5s", "60s", "bash", str(script)],
            cwd=directory,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        path = Path(directory) / "failed_logs.txt"
        if result.returncode != 0 or not path.is_file():
            return "Failed-job logs unavailable."
        return path.read_text(errors="replace")


def results(repository, run):
    """Collect jobs and logs for this attempt so a later retry cannot change the evidence."""
    attempt = run["run_attempt"]
    endpoint = (
        f"repos/{repository}/actions/runs/{run['id']}/attempts/{attempt}"
        "/jobs?per_page=100"
    )
    jobs = [job for page in gh(endpoint) for job in page["jobs"]]
    data = {
        "head_sha": run["head_sha"],
        "run_url": run["html_url"],
        "attempt": attempt,
        "conclusion": run["conclusion"],
        "jobs": [
            {
                "id": job["id"],
                "name": job["name"],
                "html_url": job["html_url"],
                "conclusion": job["conclusion"],
                "steps": job.get("steps", []),
            }
            for job in jobs
        ],
    }
    if run["conclusion"] == "failure":
        data["failed_job_excerpts"] = failed_logs(repository, run["id"], attempt)
    return data


def selected_results(repository, run_id, attempt, head_sha):
    endpoint = f"repos/{repository}/actions/runs/{run_id}/attempts/{attempt}"
    run = gh(endpoint)[0]
    if run["head_sha"] != head_sha:
        raise ValueError("CI run does not match the requested commit")
    if run["run_attempt"] != attempt or classify(run) != "ready":
        raise ValueError("Selected CI attempt is not ready")
    return results(repository, run)
