#!/usr/bin/env python3
"""
Release validation script.

Checks before creating a release commit:
1. The version calculated from the current branch matches the expected version.
2. The expected version does not already exist in PyPI or the remote VCS tags.
3. The expected version is contiguous to the latest release in PyPI and VCS tags.

Usage:
    python validate-release.py <expected-version>

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

from packaging.version import InvalidVersion
from packaging.version import Version

REPO_URL = "https://github.com/pedro-psb/dynaconf.git"  # was dynaconf/dynaconf
PYPI_URL = "https://pypi.org/pypi/dynaconf/json"  # was pypi.org
RUNNING_CI = bool(os.getenv("CI"))


class InvalidReleaseError(Exception):
    pass


def _log(label: str, value: object) -> None:
    print(f"[DEBUG] {label}: {value}", file=sys.stderr)  # noqa: T201


class Repository:
    """Git repository introspection."""

    def current_branch(self) -> str:
        # --abbrev-ref resolves HEAD to the short branch name (e.g. "master").
        # In detached HEAD state it returns the literal string "HEAD".
        result = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
        ).strip()
        _log("current_branch", result)
        return result

    def root(self) -> str:
        # --show-toplevel always returns an absolute path regardless of which
        # subdirectory the process was launched from.
        result = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        _log("root", result)
        return result

    def working_tree_status(self) -> str:
        # --porcelain is a stable machine-readable format that is unaffected by
        # locale or git version. Empty output means the tree is clean.
        result = subprocess.check_output(
            ["git", "status", "--porcelain"], text=True
        )
        _log(
            "working_tree_status",
            repr(result.strip()) if result.strip() else "clean",
        )
        return result

    def sync_counts(self, url: str) -> tuple[int, int]:
        """Return (ahead, behind) commit counts relative to the remote master."""
        # Fetch by URL, not by remote name, so this works regardless of how
        # the user has their remotes configured.
        subprocess.run(
            ["git", "fetch", url, "master"], check=True, capture_output=True
        )
        # FETCH_HEAD is always written by the fetch above, so these counts
        # reflect exactly what was just fetched — no stale remote-tracking ref.
        ahead = int(
            subprocess.check_output(
                ["git", "rev-list", "--count", "FETCH_HEAD..HEAD"], text=True
            ).strip()
        )
        behind = int(
            subprocess.check_output(
                ["git", "rev-list", "--count", "HEAD..FETCH_HEAD"], text=True
            ).strip()
        )
        _log("sync_counts", f"ahead={ahead}, behind={behind}")
        return ahead, behind

    def local_version_tags(self) -> list[str]:
        # git tag emits one exact tag name per line with no decorations,
        # so splitting on newlines gives a precise list for membership checks.
        # Non-version tags (e.g. "list", "latest") are silently skipped.
        output = subprocess.check_output(["git", "tag", "--list"], text=True)
        tags = []
        for tag in output.splitlines():
            try:
                Version(tag)
                tags.append(tag)
            except InvalidVersion:
                pass
        _log("local_version_tags", tags)
        return tags

    def remote_version_tags(self, url: str) -> list[str]:
        # Queries the remote directly over the git protocol without touching
        # any local clone state, so the result always reflects the server.
        # Non-version tags are silently skipped.
        output = subprocess.check_output(
            ["git", "ls-remote", "--tags", url], text=True
        )
        tags = []
        no_version_tags = []
        for line in output.splitlines():
            ref = line.split("\t")[1]
            if ref.endswith("^{}"):
                continue
            tag = ref.removeprefix("refs/tags/")
            try:
                Version(tag)
                tags.append(tag)
            except InvalidVersion:
                no_version_tags.append(tag)
                pass
        _log("remote_not_version_tags", no_version_tags)
        _log("remote_version_tags", tags)
        return tags

    def commits_since_tag(self, tag: str) -> list[str]:
        # --format=%H emits one bare hash per line with no decorations,
        # making it locale-independent and stable across git versions.
        # Empty output (tag at HEAD) correctly produces an empty list.
        output = subprocess.check_output(
            ["git", "log", f"{tag}..HEAD", "--format=%H"], text=True
        )
        result = output.splitlines()
        _log("commits_since_tag", result)
        return result


# Version calculation


def get_calculated_next_version() -> str:
    """Return the next release version as computed from the current branch state.

    Reads the dev version (e.g. 3.3.0-dev0) via bump-my-version and returns
    the release version it would produce (e.g. 3.3.0).
    """
    result = subprocess.check_output(
        ["bump-my-version", "show", "--increment", "pre", "new_version"],
        text=True,
    ).strip()
    _log("calculated_next_version", result)
    return result


def check_version_format(version: str) -> None:
    """Raise if `version` is not a clean X.Y.Z release (no pre-release suffix)."""
    v = Version(version)
    if v.is_prerelease or v.is_postrelease or v.local:
        raise InvalidReleaseError(
            f"{version!r} is not a clean release version (expected X.Y.Z)"
        )


def check_version_matches_expected(calculated: str, expected: str) -> None:
    """Raise if the calculated version does not match the expected version.

    Guards against releasing the wrong version when the branch has already
    been bumped beyond what was intended.
    """
    if calculated != expected:
        raise InvalidReleaseError(
            f"calculated version {calculated!r} does not match expected {expected!r}"
        )


# Fetchers


def fetch_pypi_versions() -> list[str]:
    """Return the list of versions published on PyPI for dynaconf.

    Queries https://pypi.org/pypi/dynaconf/json and returns the keys of the
    releases dict (e.g. ["3.2.3", "3.2.4", ...]).
    """
    try:
        with urllib.request.urlopen(PYPI_URL, timeout=10) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as e:
        raise InvalidReleaseError(
            f"failed to fetch PyPI versions from {PYPI_URL!r}: {e}"
        ) from e
    result = list(data["releases"].keys())
    _log("pypi_versions", result)
    return result


# Checks (shared between PyPI and VCS)


def check_is_unique(version: str, released: list[str]) -> None:
    """Raise if `version` is already present in `released`."""
    if not released:
        raise InvalidReleaseError("released list cannot be empty")
    if version in released:
        raise InvalidReleaseError(f"{version!r} is already released")


def check_is_contiguous(version: str, released: list[str]) -> None:
    """Raise if `version` is not a contiguous increment from the latest in `released`.

    For example, if the latest release is 3.2.4, only 3.2.5, 3.3.0, or 4.0.0
    are valid. A jump to 3.2.6 or 3.4.0 would be rejected.
    """
    if not released:
        raise InvalidReleaseError("released list cannot be empty")
    latest = max(released, key=Version)
    lat_x, lat_y, lat_z = Version(latest).release
    new_x, new_y, new_z = Version(version).release
    valid = (
        (new_x, new_y, new_z) == (lat_x, lat_y, lat_z + 1)
        or (new_x, new_y, new_z) == (lat_x, lat_y + 1, 0)
        or (new_x, new_y, new_z) == (lat_x + 1, 0, 0)
    )
    if not valid:
        raise InvalidReleaseError(
            f"{version!r} is not a contiguous increment from {latest!r}"
        )


def check_on_release_branch(
    repo: Repository, *, is_backport_release: bool = False
) -> None:
    """Raise if the current branch is not an allowed release branch."""
    if is_backport_release:
        raise NotImplementedError("backport releases are not yet supported")
    branch = repo.current_branch()
    if branch != "master":
        raise InvalidReleaseError(
            f"branch {branch!r} is not an allowed release branch"
        )


def check_no_local_tag(repo: Repository, version: str) -> None:
    """Raise if `version` already exists as a local git tag."""
    if version in repo.local_version_tags():
        raise InvalidReleaseError(
            f"tag {version!r} already exists locally. "
            f"Consider removing it with: git tag -d {version} "
            f"(only if it does not exist upstream)."
        )


def check_tag_exists_on_remote(repo: Repository, version: str) -> None:
    """Raise if `version` does not exist as a remote git tag."""
    if version not in repo.remote_version_tags(REPO_URL):
        raise InvalidReleaseError(
            f"tag {version!r} does not exist on remote {REPO_URL!r}"
        )


def check_in_sync_with_upstream(repo: Repository) -> None:
    """Raise if the local branch is ahead, behind, or diverged from upstream master."""
    ahead, behind = repo.sync_counts(REPO_URL)
    if ahead > 0 and behind > 0:
        raise InvalidReleaseError(
            f"branch has diverged: {ahead} commit(s) ahead, {behind} behind upstream"
        )
    if behind > 0:
        raise InvalidReleaseError(
            f"branch is {behind} commit(s) behind upstream"
        )
    if ahead > 0:
        raise InvalidReleaseError(
            f"branch is {ahead} commit(s) ahead of upstream"
        )


def check_has_unreleased_commits(repo: Repository, latest_tag: str) -> None:
    """Raise if there are no real commits since `latest_tag`.

    The first commit after a release tag is always the post-release bump
    (e.g. 3.2.4 → 3.2.5.dev0), so at least two commits are required.
    """
    commits = repo.commits_since_tag(latest_tag)
    if len(commits) <= 1:
        raise InvalidReleaseError(
            f"no unreleased commits since {latest_tag!r} "
            f"(only the post-release bump commit found)"
        )


def check_clean_working_tree(repo: Repository) -> None:
    """Raise if the working tree has any staged, unstaged, or untracked changes."""
    status = repo.working_tree_status()
    if status.strip():
        raise InvalidReleaseError(f"working tree is not clean:\n{status}")


def run_from_root(repo: Repository) -> None:
    os.chdir(repo.root())


def main(expected: str, *, publish: bool = False) -> None:
    repo = Repository()
    run_from_root(repo)

    pypi_versions = fetch_pypi_versions()
    remote_tags = repo.remote_version_tags(REPO_URL)
    latest_remote_tag = max(remote_tags, key=Version)
    calculated = get_calculated_next_version()

    _log("mode", "publish" if publish else "release")
    _log("running_ci", RUNNING_CI)
    _log("next_version", calculated)
    _log("expected", expected)
    _log("repo_url", REPO_URL)
    _log("pypi_url", PYPI_URL)
    _log("latest_remote_tag", latest_remote_tag)

    if publish:
        # Publish mode: checked out at master with full history.
        # Tag is already on the remote; PyPI publish has not happened yet.

        check_version_format(expected)
        check_tag_exists_on_remote(repo, expected)
        prior_tags = [t for t in remote_tags if t != expected]
        check_is_contiguous(expected, prior_tags)

        # PyPI
        check_is_unique(expected, pypi_versions)
        check_is_contiguous(expected, pypi_versions)
    else:
        # Release mode: full pre-flight before creating the release commit.
        # Local state
        check_on_release_branch(repo)
        check_version_matches_expected(calculated, expected)
        check_clean_working_tree(repo)
        if not RUNNING_CI:
            check_no_local_tag(repo, expected)
            check_in_sync_with_upstream(repo)
        check_has_unreleased_commits(repo, latest_remote_tag)
        check_version_format(expected)

        # PyPI
        check_is_unique(expected, pypi_versions)
        check_is_contiguous(expected, pypi_versions)

        # Remote VCS tags
        check_is_unique(expected, remote_tags)
        check_is_contiguous(expected, remote_tags)

    print(f"[OK] Release {expected!r} passed all validation checks.")  # noqa: T201


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version", help="Expected release version (e.g. 3.3.0)"
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Skip local git pre-flight checks (use when validating before publishing)",
    )
    args = parser.parse_args()
    try:
        main(args.version, publish=args.publish)
    except InvalidReleaseError as e:
        print(f"[ERROR] {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)
