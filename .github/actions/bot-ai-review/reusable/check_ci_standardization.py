"""Check for standard CI entry points on the pull request's trusted base."""

import json
import os
import subprocess
import sys

CI_WORKFLOW = ".github/workflows/ci.yml"
INSTALLER = "install-ci-deps.sh"


def tree(repository, sha):
    output = subprocess.check_output(
        ["gh", "api", f"repos/{repository}/git/trees/{sha}"], text=True
    )
    data = json.loads(output)
    if data.get("truncated"):
        raise ValueError("GitHub returned an incomplete tree")
    return data


def entry(data, name, kind):
    return next(
        (
            item
            for item in data["tree"]
            if item["path"] == name and item["type"] == kind
        ),
        None,
    )


def check(repository, base_sha):
    """Find missing CI entry points using at most three reads of the trusted base tree.

    PR files cannot establish whether the base branch adopted the convention.
    We do not check dependency caches: CI setups differ, so checking them
    reliably is not worth the cost unless it becomes a recurring problem.
    """
    root = tree(repository, base_sha)
    installer = entry(root, INSTALLER, "blob")
    github = entry(root, ".github", "tree")
    workflows = None
    if github:
        workflows = entry(tree(repository, github["sha"]), "workflows", "tree")
    workflow = None
    if workflows:
        workflow = entry(tree(repository, workflows["sha"]), "ci.yml", "blob")
    missing = []
    if not workflow:
        missing.append(CI_WORKFLOW)
    if not installer:
        missing.append(INSTALLER)
    return missing


def main():
    """Report an unavailable check separately from confirmed missing files.

    Stable branches keep their original CI, so only pull requests to the
    default branch report missing entry points.
    """
    if os.environ.get("BASE_REF", "") != os.environ.get("DEFAULT_BRANCH", ""):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write("status=skipped\nmissing=\n")
        return
    try:
        missing = check(os.environ["REPOSITORY"], os.environ["BASE_SHA"])
    except (
        subprocess.SubprocessError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as error:
        print(f"::warning::Could not check CI entry points: {error}", file=sys.stderr)
        status, missing = "unknown", []
    else:
        status = "missing" if missing else "present"
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"status={status}\nmissing={', '.join(missing)}\n")


if __name__ == "__main__":
    main()
