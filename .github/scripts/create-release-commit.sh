#!/bin/bash
#
# Prepares and commits a release:
# 1. Bumps version files from dev to release (e.g. 3.2.5-dev0 -> 3.2.5)
# 2. Updates the changelog
# 3. Creates a tagged release-commit
# 4. Creates a post-release bump-commit (e.g. 3.2.5 -> 3.2.6-dev0)

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Bump version files: x.y.z-dev0 -> x.y.z
echo "[BUMP] Bumping version files: x.y.z-dev0 -> x.y.z"
bump-my-version bump pre

# Update changelog in-place
echo "[BUMP] Updating changelog"
CURRENT_VERSION="$(bump-my-version show current_version)"
git-changelog --in-place --bump "${CURRENT_VERSION:?is-empty}"

# Create release-commit
echo "[COMMIT] Creating release-commit"
git add \
    CHANGELOG.md \
    dynaconf/VERSION \
    mkdocs.yml \
    pyproject.toml

LATEST_RELEASE="$(git describe --tags --abbrev=0)"
NEW_VERSION="$(bump-my-version show current_version)"

COMMIT_TITLE="Release version ${NEW_VERSION:?is-empty}"
COMMIT_MSG="$(git shortlog "${LATEST_RELEASE:?is-empty}.." | sed 's/^./    &/')"
TAG_TITLE="${NEW_VERSION}"
TAG_MSG="Released in $(date -Idate) by $(git config user.name) <$(git config user.email)>"

git commit \
    --message "${COMMIT_TITLE}" \
    --message "Shortlog of commits since last release:" \
    --message "${COMMIT_MSG}"
git tag --annotate "${TAG_TITLE}" \
    --message "${TAG_MSG}"

# Create post-release bump-commit: x.y.z -> x.y.next-dev0
echo "[COMMIT] Creating post-release bump-commit: x.y.z -> x.y.next-dev0"
bump-my-version bump patch --commit

echo "[COMMIT] Done."
