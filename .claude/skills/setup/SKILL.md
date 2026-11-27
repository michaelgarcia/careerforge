---
name: setup
description: >
  One-time setup of CareerForge on this computer: create the private user_data/ folder with
  starter config, install the Python packages, and copy data from the old folder layout if
  there is any. Use when the startup check says initialized=no or python_deps=missing, or for
  "set up CareerForge", "install the packages", "it says a module is missing".
---

# Setup: user_data/ and Python packages

Everything personal lives in `user_data/` (gitignored, never in the repo). This skill creates it, installs what the scripts need, and never overwrites a file that already exists. Ask before installing anything.

## Step 1: Old layout? Copy, then stop

If `knowledge_base/candidate_profile.yaml` exists at the repo root, this install predates `user_data/` (November 2026). Don't scaffold anything. Tell the user:

> "Your data is in the old layout. I'll copy it into `user_data/` and check every file. Nothing is moved or deleted. OK?"

On yes, run `python scripts/migrate_to_user_data.py`. Show its per-folder table. If it reports `CONFLICT` or `VERIFY FAILED`, show those lines and stop. Otherwise say:

> "All N files are in `user_data/` and verified. Your old folders (`knowledge_base/`, `config/`, `postings/`, `output/`, `data/`) are untouched. Once you've had a look, you can delete them yourself."

Continue with Step 2 only if `python_deps=missing`.

## Step 2: Python

Run `python --version` (on macOS also try `python3 --version`). If you get 3.11 or newer, go on. Otherwise, explain that CareerForge's scripts (resumes, scans, dashboards) need Python 3.11+, and offer the install for their system:

- Windows: `winget install --id Python.Python.3.12 -e`
- macOS: `brew install python` (if Homebrew is missing, point to https://www.python.org/downloads/)
- Fallback: https://www.python.org/downloads/

Run it only after the user's yes. After an install, they may need to start a new session so the new `python` is on the PATH.

## Step 3: Packages

Run `python -m pip install --quiet -r requirements.txt`. If it fails, show the exact error and the command so they can run it themselves.

## Step 4: Create user_data/

Skip this step if `user_data/` already exists. Otherwise:

```bash
mkdir -p user_data/knowledge_base/sources user_data/knowledge_base/memories user_data/knowledge_base/archive user_data/config user_data/postings/journal user_data/output/.work user_data/data
```

Then copy each starter file only if the destination doesn't exist:

- `templates/preferences.template.yaml` → `user_data/config/preferences.yaml`
- `templates/search_scopes.template.yaml` → `user_data/config/search_scopes.yaml`
- `templates/company_targets.template.yaml` → `user_data/config/company_targets.yaml`
- `user_data/postings/applications.csv`: the header row only, from `.claude/reference/tracker-schema.md`

Resume formatting needs no copy: `templates/resume_style.yaml` is the default. To customize it, copy it to `user_data/config/resume_style.yaml`.

## Step 5: Confirm

> "CareerForge is set up.
>
> 1. Drop your career documents into `user_data/knowledge_base/sources/`: resumes, LinkedIn exports, performance reviews, project write-ups. PDF, DOCX, TXT and MD all work.
> 2. Then just tell me what you need, in your own words: *"build my profile"*, *"set up my job filters"*, *"I have an interview at Acme next week"*.
>
> Everything personal stays in `user_data/` on this computer. It's never part of the code, and updates never touch it. For rules you want every deliverable to follow, drop a short file in `user_data/knowledge_base/memories/` (format: `templates/memory.template.md`)."

If you installed Python in Step 2, tell them to start a new session first.
