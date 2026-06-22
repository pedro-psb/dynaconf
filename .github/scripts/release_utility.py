#!/usr/bin/env python3
"""
Release utility for dynaconf.

Exit codes:
    0 — success
    1 — one or more checks failed or a step errored
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from abc import ABC
from abc import abstractmethod

from packaging.version import InvalidVersion
from packaging.version import Version

BUMP_FILES = [
    "CHANGELOG.md",
    "dynaconf/VERSION",
    "mkdocs.yml",
    "pyproject.toml",
]
RELEASE_COMMIT_MSG = "Release version {version}"
REPO_URL = "https://github.com/pedro-psb/dynaconf.git"  # was dynaconf/dynaconf
PYPI_URL = "https://test.pypi.org/pypi/dynaconf/json"  # was pypi.org
RUNNING_CI = bool(os.getenv("CI"))
DEFAULT_BRANCH = "master"


class InvalidReleaseError(Exception):
    pass


# Keep line breaks on the help display
HELP_FORMATTER = argparse.RawDescriptionHelpFormatter


def debug(label: str, value: object) -> None:
    print(f"[DEBUG] {label}: {value}", file=sys.stderr)  # noqa: T201


def info(msg: str) -> None:
    print(msg)  # noqa: T201


class Repository:
    """Git repository introspection."""

    def _git(self, *args) -> tuple[str, str]:
        result = subprocess.run(
            ["git", *args], check=True, capture_output=True, text=True
        )
        return result.stdout.strip(), result.stderr.strip()

    def _git_ok(self, *args) -> bool:
        result = subprocess.run(["git", *args], capture_output=True)
        return result.returncode == 0

    # --- read-only ---

    def current_branch(self) -> str:
        # --abbrev-ref resolves HEAD to the short branch name (e.g. "master").
        # In detached HEAD state it returns the literal string "HEAD".
        result, _ = self._git("rev-parse", "--abbrev-ref", "HEAD")
        debug("current_branch", result)
        return result

    def root(self) -> str:
        # --show-toplevel always returns an absolute path regardless of which
        # subdirectory the process was launched from.
        result, _ = self._git("rev-parse", "--show-toplevel")
        debug("root", result)
        return result

    def working_tree_status(self) -> str:
        # --porcelain is a stable machine-readable format that is unaffected by
        # locale or git version. Empty output means the tree is clean.
        result, _ = self._git("status", "--porcelain")
        debug("working_tree_status", repr(result) if result else "clean")
        return result

    def sync_counts(
        self, url: str, branch: str = DEFAULT_BRANCH
    ) -> tuple[int, int]:
        """Return (ahead, behind) commit counts relative to the remote branch."""
        # Fetch by URL, not by remote name, so this works regardless of how
        # the user has their remotes configured.
        self.fetch(url, branch)
        # FETCH_HEAD is always written by the fetch above, so these counts
        # reflect exactly what was just fetched — no stale remote-tracking ref.
        ahead_out, _ = self._git("rev-list", "--count", "FETCH_HEAD..HEAD")
        behind_out, _ = self._git("rev-list", "--count", "HEAD..FETCH_HEAD")
        ahead, behind = int(ahead_out), int(behind_out)
        debug("sync_counts", f"ahead={ahead}, behind={behind}")
        return ahead, behind

    def local_version_tags(self) -> list[str]:
        # git tag emits one exact tag name per line with no decorations,
        # so splitting on newlines gives a precise list for membership checks.
        # Non-version tags (e.g. "list", "latest") are silently skipped.
        output, _ = self._git("tag", "--list")
        tags = []
        for tag in output.splitlines():
            try:
                Version(tag)
                tags.append(tag)
            except InvalidVersion:
                pass
        debug("local_version_tags", sorted(tags, key=Version))
        return tags

    def remote_version_tags(self, url: str) -> list[str]:
        # Queries the remote directly over the git protocol without touching
        # any local clone state, so the result always reflects the server.
        # Non-version tags are silently skipped.
        output, _ = self._git("ls-remote", "--tags", url)
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
        debug("remote_not_version_tags", sorted(no_version_tags))
        debug("remote_version_tags", sorted(tags, key=Version))
        return tags

    def commits_since_tag(self, tag: str) -> list[str]:
        # --format=%H emits one bare hash per line with no decorations,
        # making it locale-independent and stable across git versions.
        # Empty output (tag at HEAD) correctly produces an empty list.
        output, _ = self._git("log", f"{tag}..HEAD", "--format=%H")
        result = output.splitlines()
        debug("commits_since_tag", result)
        return result

    def shortlog_since(self, tag: str, indent: int = 0) -> str:
        output, _ = self._git("shortlog", f"{tag}..")
        if not indent:
            return output
        prefix = " " * indent
        return "\n".join(
            f"{prefix}{line}" if line else "" for line in output.splitlines()
        )

    def user_identity(self) -> tuple[str, str]:
        name, _ = self._git("config", "user.name")
        email, _ = self._git("config", "user.email")
        return name, email

    def branch_exists(self, name: str) -> bool:
        return self._git_ok("rev-parse", "--verify", f"refs/heads/{name}")

    def branch_tip(self, name: str) -> str:
        tip, _ = self._git("rev-parse", f"refs/heads/{name}")
        return tip

    def is_ancestor(self, commit: str, of: str) -> bool:
        return self._git_ok("merge-base", "--is-ancestor", commit, of)

    def fetch(self, url: str, branch: str) -> None:
        self._git("fetch", url, branch)

    # --- write ---

    def stage(self, files: list[str]) -> None:
        self._git("add", *files)

    def commit(self, *messages: str) -> None:
        args = ["commit"]
        for msg in messages:
            args += ["--message", msg]
        self._git(*args)

    def create_tag(self, name: str, message: str) -> None:
        self._git("tag", "--annotate", name, "--message", message)

    def create_branch(self, name: str) -> None:
        self._git("branch", name)

    def fast_forward_branch(self, name: str, expected_tip: str) -> None:
        # update-ref is atomic: fails if the branch tip moved since we checked,
        # unlike `branch -f` which would silently overwrite any intervening change.
        self._git("update-ref", f"refs/heads/{name}", "HEAD", expected_tip)


class VersionBumper:
    """Wraps bump-my-version calls."""

    def _bmv(self, *args) -> tuple[str, str]:
        result = subprocess.run(
            ["bump-my-version", *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip(), result.stderr.strip()

    def calculated_next(self) -> str:
        result, _ = self._bmv("show", "--increment", "pre", "new_version")
        debug("calculated_next_version", result)
        return result

    def bump_to_release(self) -> str:
        """Bump dev -> release and return the new version string."""
        self._bmv("bump", "pre")
        version, _ = self._bmv("show", "current_version")
        return version

    def bump_to_next_dev(self) -> None:
        self._bmv("bump", "patch", "--commit")

    def update_changelog(self, version: str) -> None:
        subprocess.run(
            ["git-changelog", "--in-place", "--bump", version], check=True
        )


class Releaser(ABC):
    def __init__(self, repo: Repository, bumper: VersionBumper) -> None:
        self.repo = repo
        self.bumper = bumper

    @abstractmethod
    def validate(
        self, expected: str, *, pre_publish: bool = False
    ) -> None: ...

    @abstractmethod
    def release(self, *, yes: bool = False) -> None: ...

    def _cut_release(self, previous: str) -> str:
        info("[BUMP] Bumping version files: x.y.z-dev0 -> x.y.z")
        current_version = self.bumper.bump_to_release()

        info(f"[BUMP] Updating changelog for {current_version}")
        self.bumper.update_changelog(current_version)
        self.repo.stage(BUMP_FILES)
        shortlog = self.repo.shortlog_since(previous, indent=4)
        today = datetime.date.today().isoformat()
        name, email = self.repo.user_identity()

        info(f"[COMMIT] Creating release commit for {current_version}")
        self.repo.commit(
            RELEASE_COMMIT_MSG.format(version=current_version),
            "Shortlog of commits since last release:",
            shortlog,
        )
        self.repo.create_tag(
            current_version, f"Released in {today} by {name} <{email}>"
        )

        info(
            "[COMMIT] Creating post-release bump commit: x.y.z -> x.y.next-dev0"
        )
        self.bumper.bump_to_next_dev()

        return current_version

    def _confirm(self, yes: bool) -> None:
        if not yes:
            answer = input("Type 'yes' to confirm: ")
            if answer.strip().lower() != "yes":
                print("[ABORTED] Release cancelled.", file=sys.stderr)  # noqa: T201
                sys.exit(2)

    @staticmethod
    def _fetch_pypi_versions() -> list[str]:
        """Return the list of versions published on PyPI for dynaconf."""
        try:
            with urllib.request.urlopen(PYPI_URL, timeout=10) as response:
                data = json.loads(response.read())
        except urllib.error.HTTPError as e:
            raise InvalidReleaseError(
                f"failed to fetch PyPI versions from {PYPI_URL!r}: {e}"
            ) from e
        result = list(data["releases"].keys())
        debug("pypi_versions", sorted(result, key=Version))
        return result


class RollingReleaser(Releaser):
    def validate(self, expected: str, *, pre_publish: bool = False) -> None:
        pypi_versions = self._fetch_pypi_versions()
        remote_tags = self.repo.remote_version_tags(REPO_URL)
        calculated = self.bumper.calculated_next()

        debug("mode", "pre_publish" if pre_publish else "release")
        debug("running_ci", RUNNING_CI)
        debug("next_version", calculated)
        debug("expected", expected)
        debug("repo_url", REPO_URL)
        debug("pypi_url", PYPI_URL)
        debug("latest_remote_tag", max(remote_tags, key=Version))

        if pre_publish:
            check_version_format(expected)
            check_tag_exists_on_remote(self.repo, expected)
            prior_tags = [t for t in remote_tags if t != expected]
            check_is_contiguous(expected, prior_tags)
            check_is_unique(expected, pypi_versions)
            check_is_contiguous(expected, pypi_versions)
        else:
            check_on_release_branch(self.repo)
            check_version_matches_expected(calculated, expected)
            check_clean_working_tree(self.repo)
            if not RUNNING_CI:
                check_no_local_tag(self.repo, expected)
                check_in_sync_with_upstream(self.repo)
            check_has_unreleased_commits(self.repo, remote_tags)
            check_version_format(expected)
            check_is_unique(expected, pypi_versions)
            check_is_contiguous(expected, pypi_versions)
            check_is_unique(expected, remote_tags)
            check_is_contiguous(expected, remote_tags)

        info(f"[OK] Release {expected!r} passed all validation checks.")

    def release(self, *, yes: bool = False) -> None:
        previous = max(self.repo.local_version_tags(), key=Version)
        next_version = self.bumper.calculated_next()
        info(f"Previous release : {previous}")
        info(f"Next release     : {next_version}")
        self.validate(next_version)
        check_backport_branch_compatible(self.repo, next_version)
        self._confirm(yes)
        current_version = self._cut_release(previous)

        major, minor, _ = Version(current_version).release
        branch = f"{major}.{minor}"
        if not self.repo.branch_exists(branch):
            self.repo.create_branch(branch)
            info(f"[BRANCH] Created backport branch: {branch}")
        elif self.repo.is_ancestor(
            tip := self.repo.branch_tip(branch), "HEAD"
        ):
            self.repo.fast_forward_branch(branch, tip)
            info(f"[BRANCH] Fast-forwarded {branch} to HEAD")
        else:
            info(
                f"[BRANCH] Backport branch {branch} already exists and has diverged, skipping"
            )

        info("[COMMIT] Done.")


class BackportReleaser(Releaser):
    @staticmethod
    def _filter_series(
        versions: list[str],
        *,
        by_xy: tuple[int, int] | None = None,
        exclude: list[str] | None = None,
    ) -> list[str]:
        if by_xy is not None and exclude is not None:
            raise ValueError("by_xy and exclude are mutually exclusive")
        if by_xy is not None:
            major, minor = by_xy
            return [
                v for v in versions if Version(v).release[:2] == (major, minor)
            ]
        if exclude is not None:
            return [v for v in versions if v not in exclude]
        return list(versions)

    def validate(self, expected: str, *, pre_publish: bool = False) -> None:
        pypi_versions = self._fetch_pypi_versions()
        remote_tags = self.repo.remote_version_tags(REPO_URL)
        local_tags = self.repo.local_version_tags()
        calculated = self.bumper.calculated_next()
        major, minor, _ = Version(expected).release

        debug("mode", "backport-publish" if pre_publish else "backport")
        debug("running_ci", RUNNING_CI)
        debug("next_version", calculated)
        debug("expected", expected)
        debug("repo_url", REPO_URL)
        debug("pypi_url", PYPI_URL)

        series_remote = self._filter_series(remote_tags, by_xy=(major, minor))
        series_pypi = self._filter_series(pypi_versions, by_xy=(major, minor))
        series_local = self._filter_series(local_tags, by_xy=(major, minor))

        if pre_publish:
            prior_series = self._filter_series(
                series_remote, exclude=[expected]
            )
            check_version_format(expected)
            check_tag_exists_on_remote(self.repo, expected)
            check_is_contiguous(expected, prior_series)
            check_is_unique(expected, pypi_versions)
            check_is_contiguous(expected, series_pypi)
        else:
            check_is_patch_release(expected)
            check_on_backport_branch(self.repo, expected)
            check_version_format(expected)
            check_version_matches_expected(calculated, expected)
            check_clean_working_tree(self.repo)
            if not RUNNING_CI:
                check_no_local_tag(self.repo, expected)
                check_in_sync_with_upstream(
                    self.repo, branch=f"{major}.{minor}"
                )
            check_has_unreleased_commits(self.repo, series_local)
            check_is_unique(expected, pypi_versions)
            check_is_unique(expected, remote_tags)
            check_is_contiguous(expected, series_remote)

        info(f"[OK] Release {expected!r} passed all validation checks.")

    def release(self, *, yes: bool = False) -> None:
        next_version = self.bumper.calculated_next()
        info(f"Next release     : {next_version}")
        self.validate(next_version)

        major, minor, _ = Version(next_version).release
        series_local = self._filter_series(
            self.repo.local_version_tags(), by_xy=(major, minor)
        )
        previous = max(series_local, key=Version)
        info(f"Previous release : {previous}")
        self._confirm(yes)
        self._cut_release(previous)
        info("[COMMIT] Done.")


def run(args: argparse.Namespace) -> None:
    repo = Repository()
    bumper = VersionBumper()
    run_from_root(repo)

    if args.command == "validate":
        cls = BackportReleaser if args.backport else RollingReleaser
        cls(repo, bumper).validate(args.version, pre_publish=args.pre_publish)
    elif args.command == "rolling-release":
        RollingReleaser(repo, bumper).release(yes=args.yes)
    elif args.command == "backport-release":
        BackportReleaser(repo, bumper).release(yes=args.yes)
    elif args.command == "get":
        if args.item == "backport-branch":
            major, minor, _ = Version(bumper.calculated_next()).release
            info(f"{major}.{minor}")
        elif args.item == "next-version":
            info(bumper.calculated_next())
        elif args.item == "release-type":
            repo.fetch(REPO_URL, DEFAULT_BRANCH)
            info(
                "rolling"
                if repo.is_ancestor(args.value, "FETCH_HEAD")
                else "backport"
            )


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


def check_on_release_branch(repo: Repository) -> None:
    """Raise if the current branch is not master."""
    branch = repo.current_branch()
    if branch != DEFAULT_BRANCH:
        raise InvalidReleaseError(
            f"branch {branch!r} is not an allowed release branch"
        )


def check_on_backport_branch(repo: Repository, version: str) -> None:
    """Raise if the current branch is not the X.Y maintenance branch for `version`."""
    branch = repo.current_branch()
    major, minor, _ = Version(version).release
    expected = f"{major}.{minor}"
    if branch != expected:
        raise InvalidReleaseError(
            f"branch {branch!r} does not match version {version!r} (expected {expected!r})"
        )


def check_is_patch_release(version: str) -> None:
    """Raise if `version` is not a patch (Z > 0) release.

    Backport branches only ever produce patch releases. Minor and major bumps
    belong on master.
    """
    _, _, patch = Version(version).release
    if patch == 0:
        raise InvalidReleaseError(
            f"{version!r} is not a patch release (Z=0). "
            "Backport branches can only produce patch releases — "
            "bump the minor version on master instead."
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


def check_in_sync_with_upstream(
    repo: Repository, branch: str = DEFAULT_BRANCH
) -> None:
    """Raise if the local branch is ahead, behind, or diverged from the remote branch."""
    ahead, behind = repo.sync_counts(REPO_URL, branch)
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


def check_has_unreleased_commits(repo: Repository, series: list[str]) -> None:
    """Raise if there are no real commits since the latest tag in `series`.

    The first commit after a release tag is always the post-release bump
    (e.g. 3.2.4 → 3.2.5.dev0), so at least two commits are required.
    """
    if not series:
        raise InvalidReleaseError(
            "no local tags found for this series — "
            "ensure the repository was cloned with full history (fetch-depth: 0)"
        )
    latest_tag = max(series, key=Version)
    commits = repo.commits_since_tag(latest_tag)
    if len(commits) <= 1:
        raise InvalidReleaseError(
            f"no unreleased commits since {latest_tag!r} "
            f"(only the post-release bump commit found)"
        )


def check_clean_working_tree(repo: Repository) -> None:
    """Raise if the working tree has any staged, unstaged, or untracked changes."""
    status = repo.working_tree_status()
    if status:
        raise InvalidReleaseError(f"working tree is not clean:\n{status}")


def check_backport_branch_compatible(repo: Repository, version: str) -> None:
    """Raise if the X.Y backport branch exists and has diverged from HEAD.

    A diverged branch means a backport release is in progress on that branch
    and a rolling release would conflict with it.
    """
    major, minor, _ = Version(version).release
    branch = f"{major}.{minor}"
    if repo.branch_exists(branch) and not repo.is_ancestor(
        repo.branch_tip(branch), "HEAD"
    ):
        raise InvalidReleaseError(
            f"backport branch {branch!r} exists and has diverged from HEAD.\n"
            f"To release {version!r}, either:\n"
            f"  1) Use the backport-release command if the patch fix belongs on {branch}\n"
            f"  2) Bump the minor version on master to perform a {major}.{minor + 1}.0 release instead"
        )


def run_from_root(repo: Repository) -> None:
    os.chdir(repo.root())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=HELP_FORMATTER
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a release before or after tagging",
        formatter_class=HELP_FORMATTER,
    )
    validate_parser.add_argument(
        "version", help="Expected release version (e.g. 3.3.0)"
    )
    validate_parser.add_argument(
        "--pre-publish",
        action="store_true",
        help="Run publish-mode checks (tag already on remote, not yet on PyPI)",
    )
    validate_parser.add_argument(
        "--backport",
        action="store_true",
        help="Run backport-mode checks (patch release from an X.Y maintenance branch)",
    )

    rolling_parser = subparsers.add_parser(
        "rolling-release",
        help="Cut a VCS/git tagged release from whatever version is on main (no PyPI publish)",
        description=(
            "Cut a VCS/git tagged release from whatever version is currently on main.\n\n"
            "Does not publish to PyPI. Steps: bump dev -> release, update changelog, "
            "commit, tag, then bump to next dev."
        ),
        formatter_class=HELP_FORMATTER,
    )
    rolling_parser.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation prompt"
    )

    backport_parser = subparsers.add_parser(
        "backport-release",
        help="Cut a patch release from an X.Y maintenance branch (no PyPI publish)",
        description=(
            "Cut a patch release from the current X.Y maintenance branch.\n\n"
            "Does not publish to PyPI. Steps: bump dev -> release, update changelog, "
            "commit, tag, then bump to next dev. Must be run on an X.Y branch."
        ),
        formatter_class=HELP_FORMATTER,
    )
    backport_parser.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation prompt"
    )

    get_parser = subparsers.add_parser(
        "get",
        help="Print a computed release value and exit",
        description=(
            "Print a computed release value and exit.\n\n"
            "Supported items:\n"
            "  backport-branch  The X.Y branch name for the next release (e.g. 3.3.2 → '3.3', 3.4.0 → '3.4')\n"
            "  next-version     The calculated next release version (e.g. 3.3.2-dev0 → '3.3.2')\n"
            "  release-type     Whether a tag is a 'rolling' or 'backport' release (requires VALUE=<tag>)"
        ),
        formatter_class=HELP_FORMATTER,
    )
    get_parser.add_argument(
        "item",
        choices=["backport-branch", "next-version", "release-type"],
        help="The value to retrieve",
    )
    get_parser.add_argument(
        "value",
        nargs="?",
        help="Tag name (required for release-type)",
    )

    return parser


if __name__ == "__main__":
    _args = build_parser().parse_args()
    try:
        run(_args)
    except InvalidReleaseError as e:
        print(f"[ERROR] {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)  # noqa: T201
        sys.exit(2)
