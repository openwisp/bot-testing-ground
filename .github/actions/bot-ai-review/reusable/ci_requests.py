"""Read bot-authored request records used by the CI review coordinator."""

import hashlib
import hmac
import json
import os
import re
import subprocess
from urllib.parse import urlencode

from ci_results import AmbiguousCIError, classify, gh, select_run

# Do not pass the signing key to gh or other child processes.
STATE_KEY = os.environ.pop("CI_STATE_KEY", "").encode()
MARKER = re.compile(r"<!-- ai-review-request (\{.*\}) ([0-9a-f]{64}) -->")


def record_body(request, message):
    if not STATE_KEY:
        raise ValueError("CI request signing key is unavailable")
    payload = json.dumps(request, separators=(",", ":"), sort_keys=True)
    signature = hmac.new(STATE_KEY, payload.encode(), hashlib.sha256).hexdigest()
    return f"{message}\n\n<!-- ai-review-request {payload} {signature} -->"


def parse_record(comment, app_id):
    """Trust only a signed record bound to this app comment.

    Other bots use the same app and may quote untrusted text.
    """
    app = comment.get("performed_via_github_app") or {}
    if app.get("id") != app_id:
        return None
    match = MARKER.search(comment.get("body") or "")
    if not match or not STATE_KEY:
        return None
    expected = hmac.new(STATE_KEY, match.group(1).encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, match.group(2)):
        return None
    try:
        record = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(record, dict) or record.get("record_id") != comment.get("id"):
        return None
    return record


def active_request(comments, app_id, stage, head_sha):
    for comment in comments:
        record = parse_record(comment, app_id)
        if record and (
            record.get("stage") == stage
            and record.get("head_sha") == head_sha
            and record.get("state") in ("waiting", "reviewing")
        ):
            return comment
    return None


def resume_record(api, dispatch, app_id, repository, pr_number):
    """Resume only an app-authored dispatch for a signed waiting record on this PR."""
    app = dispatch.get("performed_via_github_app") or {}
    match = re.fullmatch(r"/ai-review-resume ([0-9]+)", dispatch.get("body") or "")
    if app.get("id") != app_id or not match:
        return None
    comment = api.comment(int(match.group(1)))
    issue_url = f"https://api.github.com/repos/{repository}/issues/{pr_number}"
    record = parse_record(comment, app_id)
    if (
        comment.get("issue_url") != issue_url
        or not record
        or record.get("state") != "waiting"
        or record.get("repository") != repository
        or record.get("pr_number") != pr_number
    ):
        return None
    return comment


def register(api, app_id, pr_number, request, pr):
    # The caller must serialize registration and resumption so both cannot
    # claim the same request between reading and updating its comment.
    comments = api.comments(pr_number)
    existing = active_request(comments, app_id, request["stage"], request["head_sha"])
    if existing:
        old = parse_record(existing, app_id)
        review_run_id = old.get("review_run_id")
        if old.get("base_ref") != request.get("base_ref"):
            old["state"] = "done"
            api.update(
                existing["id"],
                record_body(old, "The pull request changed base; review skipped."),
            )
        elif old["state"] == "waiting":
            # A failed update or a lost completion event can leave CI finished
            # while the request still says waiting. Recheck the same record.
            old["review_run_id"] = request.get("review_run_id")
            request.clear()
            request.update(old)
            return check_ci(api, existing["id"], request, pr)
        else:
            if not review_run_id:
                return "duplicate", None, None
            # A workflow can fail before its cleanup job. Recover on the next
            # request only after GitHub confirms that workflow is no longer running.
            if api.workflow_run(review_run_id)["status"] != "completed":
                return "duplicate", None, None
            old["state"] = "done"
            api.update(
                existing["id"],
                record_body(old, "Previous review ended without cleanup."),
            )
    request = {**request, "state": "waiting"}
    # Bind the signed request to its actual comment ID before checking CI.
    # A completion during registration is caught by the subsequent CI check.
    comment_id = api.create(pr_number, "Checking primary CI.")
    request["record_id"] = comment_id
    api.update(comment_id, record_body(request, "Checking primary CI."))
    return check_ci(api, comment_id, request, pr)


def resume(api, comment, app_id, pr, review_run_id=None):
    request = parse_record(comment, app_id)
    if not request or request.get("state") != "waiting":
        return "ignored", None, None
    request["review_run_id"] = review_run_id
    if not is_current(pr, request):
        request["state"] = "done"
        api.update(
            comment["id"],
            record_body(request, "The pull request changed or closed; review skipped."),
        )
        return "stopped", comment["id"], None
    return check_ci(api, comment["id"], request, pr)


def coordinate(
    api, app_id, repository, pr_number, request, dispatch, review_run_id=None
):
    if dispatch is not None:
        comment = resume_record(api, dispatch, app_id, repository, pr_number)
        if comment is None:
            return {}
        try:
            api.delete(dispatch["id"])
        except (subprocess.SubprocessError, OSError):
            pass
        request = parse_record(comment, app_id)
    else:
        request = {**request, "repository": repository, "pr_number": pr_number}
    request["review_run_id"] = review_run_id
    pr = api.pull(pr_number)
    if dispatch is None:
        if not is_current(pr, request):
            api.create(pr_number, "The pull request changed or closed; review skipped.")
            return {}
        state, record_id, run = register(api, app_id, pr_number, request, pr)
    else:
        state, record_id, run = resume(api, comment, app_id, pr, review_run_id)
    if state != "ready":
        return {}
    return {
        **request,
        "record_id": record_id,
        "run_id": run["id"],
        "attempt": run["run_attempt"],
    }


def wake(api, app_id, run):
    if (
        run.get("path") != ".github/workflows/ci.yml"
        or run.get("event") != "pull_request"
    ):
        return
    created_at = run.get("created_at")
    if not created_at:
        raise ValueError("CI run creation time is unavailable")
    for pr_number in api.wake_candidates(run):
        try:
            comments = api.wake_comments(pr_number, created_at)
        except (RuntimeError, subprocess.SubprocessError, json.JSONDecodeError):
            api.create(
                pr_number,
                "CI completion could not check review requests. Request another review if needed.",
            )
            continue
        for comment in comments:
            request = parse_record(comment, app_id)
            if (
                request
                and request.get("state") == "waiting"
                and request.get("head_sha") == run["head_sha"]
                and request.get("pr_number") == pr_number
            ):
                # A new app comment starts the existing serialized review workflow
                # without holding a runner. Dispatching the workflow through the
                # Actions API would require Actions write permission on the app.
                api.create(pr_number, f"/ai-review-resume {comment['id']}")


def finish(
    api,
    app_id,
    pr_number,
    comment_id,
    publication_result,
    review_url="",
    setup_failed=False,
    run_url="",
):
    comment = api.comment(comment_id)
    request = parse_record(comment, app_id)
    if not request or request.get("state") != "reviewing":
        return
    pr = api.pull(pr_number)
    request["state"] = "done"
    if not is_current(pr, request):
        update = "Review skipped: the pull request changed or closed."
    elif review_url:
        update = f"[review completed]({review_url})."
    elif publication_result == "success":
        update = "review completed, but the link is unavailable."
    elif setup_failed:
        update = (
            f"review could not install the CI dependencies ([run]({run_url})). "
            "Another review fails the same way until the installer or the "
            "review runner is fixed."
        )
    else:
        update = f"review did not complete ([run]({run_url})). Request another review."
    waiting = request.get("waiting_message")
    message = f"{waiting}\n\nUpdate: {update}" if waiting else f"Update: {update}"
    api.update(comment_id, record_body(request, message))


def is_current(pr, request):
    """Reject a retargeted PR even when its head commit has not changed."""
    return (
        pr["state"] == "open"
        and pr["head"]["sha"] == request["head_sha"]
        and pr.get("base", {}).get("ref") == request.get("base_ref")
    )


def could_have_triggered(pr, run_created_at):
    """Keep uncertain PRs, but exclude those created later or closed before the run."""
    if not run_created_at or not pr.get("created_at"):
        return True
    return pr["created_at"] <= run_created_at and (
        not pr.get("closed_at") or pr["closed_at"] >= run_created_at
    )


def was_open_at(events, run_created_at):
    """Exclude a PR only when its history shows it was closed before the run."""
    changes = [
        event for event in events if event.get("event") in ("closed", "reopened")
    ]
    if not run_created_at or any(not event.get("created_at") for event in changes):
        return True
    if any(event["created_at"] == run_created_at for event in changes):
        return True
    earlier = [event for event in changes if event["created_at"] < run_created_at]
    if not earlier:
        return True
    latest = max(event["created_at"] for event in earlier)
    return any(
        event["event"] == "reopened"
        for event in earlier
        if event["created_at"] == latest
    )


def check_ci(api, comment_id, request, pr):
    try:
        if request.get("run_id") and request.get("attempt"):
            # A retry started after the selected attempt finished must not
            # postpone the review when its completion event arrives late.
            run = api.run_attempt(request["run_id"], request["attempt"])
        else:
            run = api.ci_run(pr)
    except AmbiguousCIError as error:
        request["state"] = "done"
        api.update(
            comment_id,
            record_body(
                request,
                f"{error}. Request a new review when CI matches this pull request.",
            ),
        )
        raise
    except Exception:
        request["state"] = "done"
        api.update(
            comment_id,
            record_body(request, "Could not check CI. Request a new review."),
        )
        raise
    if run is None:
        request["state"] = "done"
        api.update(
            comment_id,
            record_body(
                request,
                "No CI run found for this commit. The run may not be visible yet, or the "
                "workflow may have skipped this PR because of a branch or path filter. "
                "Request the review again once CI starts.",
            ),
        )
        return "stopped", comment_id, None
    state = classify(run)
    request["state"] = {"ready": "reviewing", "waiting": "waiting", "stopped": "done"}[
        state
    ]
    request["run_id"] = run["id"]
    request["attempt"] = run["run_attempt"]
    if state == "waiting":
        message = (
            f"Waiting for [CI to complete]({run['html_url']}) "
            f"before reviewing {request['head_sha'][:7]}."
        )
        request["waiting_message"] = message
    elif state == "ready":
        waiting = request.get("waiting_message")
        update = "Update: review is running."
        message = f"{waiting}\n\n{update}" if waiting else update
    else:
        message = f"CI did not finish successfully or fail: {run['html_url']}. Request a new review."
    api.update(comment_id, record_body(request, message))
    return state, comment_id, run


def gh_page(endpoint):
    """Bound each wake lookup so a stalled API cannot occupy the entire handler."""
    output = subprocess.check_output(["gh", "api", endpoint], text=True, timeout=10)
    return json.loads(output)


def bounded_pages(endpoint, limit):
    """Fail visibly instead of silently ignoring records beyond the scan limit."""
    items = []
    for page in range(1, limit + 1):
        result = gh_page(f"{endpoint}&page={page}")
        items.extend(result)
        if len(result) < 100:
            return items
    raise RuntimeError("CI completion scan limit reached; request another review")


class GitHub:
    def __init__(self, repository):
        self.repository = repository

    def comments(self, pr_number):
        endpoint = f"repos/{self.repository}/issues/{pr_number}/comments?per_page=100"
        return [comment for page in gh(endpoint) for comment in page]

    def wake_comments(self, pr_number, created_at):
        # A waiting record is created after its selected CI run exists.
        query = urlencode({"per_page": 100, "since": created_at})
        endpoint = f"repos/{self.repository}/issues/{pr_number}/comments?{query}"
        return bounded_pages(endpoint, 3)

    def wake_candidates(self, run):
        """Keep PRs that existed during the run, including those closed afterward."""
        created_at = run["created_at"]
        source = (run.get("head_repository") or {}).get("full_name", "")
        associated = {item["number"] for item in run.get("pull_requests", [])}
        candidates = {}
        if "/" in source and run.get("head_branch"):
            query = urlencode(
                {
                    "state": "all",
                    "head": f"{source.split('/')[0]}:{run['head_branch']}",
                    "per_page": 100,
                }
            )
            for pr in bounded_pages(f"repos/{self.repository}/pulls?{query}", 5):
                repo = pr["head"].get("repo") or {}
                if repo.get("full_name", "").lower() == source.lower():
                    candidates[pr["number"]] = pr
        if len(associated) > 20:
            raise RuntimeError(
                "CI completion candidate limit reached; request another review"
            )
        for number in associated - candidates.keys():
            candidates[number] = self.pull(number)
        numbers = [
            number
            for number, pr in candidates.items()
            if could_have_triggered(pr, created_at)
        ]
        if len(numbers) > 20:
            raise RuntimeError(
                "CI completion candidate limit reached; request another review"
            )
        return sorted(numbers)

    def comment(self, comment_id):
        return gh(f"repos/{self.repository}/issues/comments/{comment_id}")[0]

    def pull(self, pr_number):
        return gh(f"repos/{self.repository}/pulls/{pr_number}")[0]

    def workflow_run(self, run_id):
        return gh(f"repos/{self.repository}/actions/runs/{run_id}")[0]

    def run_attempt(self, run_id, attempt):
        endpoint = f"repos/{self.repository}/actions/runs/{run_id}/attempts/{attempt}"
        return gh(endpoint)[0]

    def issue_events(self, pr_number):
        endpoint = f"repos/{self.repository}/issues/{pr_number}/events?per_page=100"
        return [event for page in gh(endpoint) for event in page]

    def pulls_for_run(self, run):
        """Find candidate PRs by source branch, including forks GitHub omits from the run."""
        numbers = {item["number"] for item in run.get("pull_requests", [])}
        source = run.get("head_repository") or {}
        full_name = source.get("full_name", "")
        if "/" in full_name and run.get("head_branch"):
            owner = full_name.split("/", 1)[0]
            query = urlencode(
                {
                    "state": "all",
                    "head": f"{owner}:{run['head_branch']}",
                    "per_page": 100,
                }
            )
            pages = gh(f"repos/{self.repository}/pulls?{query}")
            for page in pages:
                for pr in page:
                    repo = pr["head"].get("repo") or {}
                    if repo.get("full_name", "").lower() == full_name.lower():
                        numbers.add(pr["number"])
        return [{"number": number} for number in sorted(numbers)]

    def create(self, pr_number, body):
        endpoint = f"repos/{self.repository}/issues/{pr_number}/comments"
        return self.write("POST", endpoint, body)["id"]

    def update(self, comment_id, body):
        endpoint = f"repos/{self.repository}/issues/comments/{comment_id}"
        self.write("PATCH", endpoint, body)

    def delete(self, comment_id):
        subprocess.run(
            [
                "gh",
                "api",
                "--method",
                "DELETE",
                f"repos/{self.repository}/issues/comments/{comment_id}",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )

    def write(self, method, endpoint, body):
        output = subprocess.check_output(
            ["gh", "api", "--method", method, endpoint, "--input", "-"],
            input=json.dumps({"body": body}),
            text=True,
        )
        return json.loads(output)

    def ci_run(self, pr):
        """Find the latest primary run only when its source branch identifies one PR."""
        sha = pr["head"]["sha"]
        endpoint = (
            f"repos/{self.repository}/actions/workflows/ci.yml/runs"
            f"?event=pull_request&head_sha={sha}&per_page=100"
        )
        runs = [run for page in gh(endpoint) for run in page["workflow_runs"]]
        run = select_run(runs, pr)
        if run:
            candidates = [
                candidate
                for candidate in (
                    self.pull(item["number"]) for item in self.pulls_for_run(run)
                )
                if could_have_triggered(candidate, run.get("created_at"))
            ]
            histories = {}
            if len(candidates) > 1 and run.get("created_at"):
                for candidate in candidates:
                    histories[candidate["number"]] = self.issue_events(
                        candidate["number"]
                    )
                candidates = [
                    candidate
                    for candidate in candidates
                    if was_open_at(histories[candidate["number"]], run["created_at"])
                ]
            if len(candidates) != 1 or candidates[0]["number"] != pr["number"]:
                raise AmbiguousCIError(
                    "CI run cannot be uniquely matched to multiple pull requests"
                )
            # A run for the same head can predate a retarget and test the old
            # base. GitHub's current PR association does not establish its base.
            events = histories.get(pr["number"])
            if events is None:
                events = self.issue_events(pr["number"])
            if any(
                event.get("event")
                in ("base_ref_changed", "automatic_base_change_succeeded")
                and event["created_at"] >= run["created_at"]
                for event in events
            ):
                raise AmbiguousCIError("CI run predates a base branch change")
        return run
