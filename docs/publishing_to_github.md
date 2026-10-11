# Publishing to GitHub later

The project is prepared locally. The owner has created an empty GitHub repository; no
commit or push is performed by this checklist.

## Before uploading

- Read README.md and data/README.md, and verify setup from a fresh source folder.
- The clone and remote URLs use the GitHub account nandinikawale.
- Include the MIT LICENSE file already provided in the project root.
- Include pyproject.toml, uv.lock, .python-version, source, tests, docs,
  .streamlit/config.toml, .github/workflows/ci.yml, and directory placeholders.
- Include the seven default synthetic CSVs under data/synthetic/.
- Exclude .venv, caches, dist/, alternative datasets/reports, local editor settings,
  credentials and machine-specific agent-skill links.
- Run the documented tests and code checks.
- Default data is fictional and reproducible; never upload real banking datasets.

The project snapshot with the default dataset can be refreshed from the project root:

```sh
python scripts/package_for_github.py
```

This produces dist/business-banking-rm-intelligence-hub-github.zip.
Extract it to obtain the source folder. A ZIP committed by itself is a download,
not a replacement for the repository's source tree.

## Local Git setup when ready

From the source project root:

```sh
git init -b main
git status --short
git add .
git diff --cached --stat
git diff --cached --check
git commit -m "Initial release of Business Banking RM Intelligence Hub"
```

Review the staged files before committing. Configure your own Git author name
and email if Git requests them; use repository-local configuration if desired.
Do not use another person's identity.

## Remote upload when ready

Use the empty repository named business-banking-rm-intelligence-hub in your
nandinikawale GitHub account. Then run:

```sh
git remote add origin https://github.com/nandinikawale/business-banking-rm-intelligence-hub.git
git push -u origin main
```

Use your configured GitHub authentication. These are future instructions, not
commands executed during preparation.

Confirm the repository displays the root README, all three page modules, both
README files, and the lockfile. GitHub Actions should run its project checks;
review the actual remote result after upload.

## Clone verification

Follow the root README exactly: install uv, synchronize locked app dependencies,
launch Streamlit using the seven included default CSVs. Validation and regeneration
are optional; see data/README.md. Alternative datasets and reports are excluded.

Uploading source to GitHub does not host the running Streamlit app. Deployment
is a separate step.
