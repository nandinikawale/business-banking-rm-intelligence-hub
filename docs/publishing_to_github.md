# Updating the GitHub repository

The repository already exists at:
https://github.com/nandinikawale/business-banking-rm-intelligence-hub

Use this guide for subsequent updates. Do not run git init, recreate the repository,
or add origin again. Preparing this guide does not perform a commit or push.

## Review what is included

Include source, tests, README files, architecture and feature documentation,
CHANGELOG.md, the MIT LICENSE, pyproject.toml, uv.lock, the seven default synthetic
CSVs, app configuration, actual screenshots and the CI workflow.

The reviewed October 2026 PDF is a historical development report. Current behavior
is described by README.md, CHANGELOG.md and docs/analytics_features.md. Its unfinished
local Word draft is ignored and is not maintained application documentation.

Virtual environments, caches, dist/, alternative datasets, generated reports,
credentials and local editor configuration remain ignored. Never add real banking
records, confidential policies or credentials.

## Open the project root

In the VS Code PowerShell terminal:

```powershell
cd 'C:\Users\nandi\OneDrive\Desktop\Study\Repositories\PracticeRepositories\gen-academy-projects\business-banking-rm-intelligence-hub'
git status --short
git branch --show-current
git remote -v
```

Confirm the branch is main and origin points to your repository. If either differs,
inspect your configuration before pushing; do not replace a remote blindly.

## Local checks

```powershell
py -3.13 -m uv run --locked --group app pytest -q
py -3.13 -m uv run --locked --group app ruff check .
py -3.13 -m uv run --locked --group app ruff format --check .
```

The maintainer runs these checks before handing over an update. Repeat them when
you make additional code changes. Tests use temporary fixtures, not the bundled CSVs.

## Stage and inspect

```powershell
git add .
git status --short
git diff --cached --stat
git diff --cached --check
```

Review staged files before committing. The seven default CSVs are already tracked
and should have no changes in this update. The ZIP and unfinished Word draft should
not be listed. The reviewed PDF may appear as a new file.

If Git opens a scrollable viewer with a colon at the bottom, press q to return to
the terminal. No output from --check means no whitespace errors were found.

## Commit and upload

```powershell
git commit -m "Add deposit movement, profitability insights and worklist export"
git push origin main
```

The commit records the update locally; the push uploads it. Use your own configured
GitHub authentication. If nothing is staged, there is nothing new to commit.
If the remote has newer commits, inspect and integrate them; do not force-push.

## Verify on GitHub

Refresh the repository and confirm the new commit, README image, feature guide,
changelog and code are present. Inspect the actual workflow result in Actions.
Local test success is not a substitute for confirming that run.

A fresh clone should follow README.md: install Python 3.13 and uv, synchronize
locked app dependencies and launch streamlit_app/app.py. Generation is optional
because the seven default fictional CSVs are included.

Uploading source does not host the running app. Streamlit Community Cloud deployment
is the next separate step; cloud dependency preparation has not been applied here.

## Optional project snapshot

```powershell
py -3.13 scripts/package_for_github.py
```

This refreshes dist/business-banking-rm-intelligence-hub-github.zip with source,
maintained docs, screenshots, the optional historical PDF and default data.
The archive is ignored by Git. Commit the source tree rather than uploading
the ZIP as the repository.
