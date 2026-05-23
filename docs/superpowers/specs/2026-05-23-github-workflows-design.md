# GitHub Workflows & PyPI Publishing Design

**Date:** 2026-05-23
**Status:** Approved

## Overview

Add GitHub Actions workflows and Dependabot configuration to the `kx` repository so that pull requests are validated, the package is published to PyPI on release, and dependencies stay up to date.

## Files to Create

| Path | Purpose |
|------|---------|
| `.github/workflows/pr.yml` | PR validation — install and build check |
| `.github/workflows/release.yml` | Publish to PyPI on `release/**` branch push |
| `.github/workflows/codeql.yml` | Security analysis for Python |
| `.github/dependabot.yml` | Automated dependency updates |
| `.github/scripts/extract-version.sh` | Parse semver from branch name |

## PR Workflow (`pr.yml`)

- **Trigger:** `pull_request` to `main` or `develop`
- **Runner:** `ubuntu-latest`, timeout 5 minutes
- **Steps:**
  1. `actions/checkout@v6`
  2. `actions/setup-python@v5` with Python 3.12
  3. `pip install build` to install the build frontend
  4. `pip install -e .` to install the package and its dependencies
  5. `python -m build` to verify the package builds into a clean dist

## Release Workflow (`release.yml`)

- **Trigger:** `push` to branches matching `release/**` (e.g. `release/v1.2.3`)
- **Required secret:** `PYPI_TOKEN` — a PyPI API token scoped to the `kx` project
- **Jobs:**

### `build-and-publish`
1. `actions/checkout@v6`
2. Extract version from branch name via `.github/scripts/extract-version.sh`
3. `actions/setup-python@v5` with Python 3.12
4. `pip install build twine`
5. Bump `version` in `pyproject.toml` using `sed`
6. `python -m build`
7. `twine upload` with `PYPI_TOKEN`
8. Expose `version` as a job output

### `merge`
- Depends on `build-and-publish`
- Requires `pull-requests: write` permission
- Creates a PR from the release branch to `main` titled `Release vX.Y.Z`
- Enables auto-merge

## CodeQL Workflow (`codeql.yml`)

- **Trigger:** `pull_request` to `main` or `develop`; weekly schedule (`cron: '0 0 * * 1'`)
- **Language:** `python`
- **Permissions:** `actions: read`, `contents: read`, `security-events: write`
- **Steps:** checkout → `codeql-action/init@v4` → `codeql-action/analyze@v4`

## Dependabot (`dependabot.yml`)

Two update entries, both on a weekly schedule:
- `pip` ecosystem at directory `/`
- `github-actions` ecosystem at directory `/`

## Extract Version Script (`.github/scripts/extract-version.sh`)

Copied verbatim from existing repos. Strips the `release/v` prefix, validates the result matches `X.Y.Z` semver, and exits non-zero on invalid input.

## Secrets Required

| Secret | Where to set | Purpose |
|--------|-------------|---------|
| `PYPI_TOKEN` | Repository → Settings → Secrets | Authenticate `twine upload` |

## Version Bump Strategy

The release workflow uses `sed` to set the version in `pyproject.toml` to the value extracted from the branch name immediately before building. This means the published package version always matches the branch name regardless of what version is committed in the branch. The mutation happens only in the runner's working directory and is not committed back to git.
