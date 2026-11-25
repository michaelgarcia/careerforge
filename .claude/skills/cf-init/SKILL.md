---
name: cf-init
description: >
  Set up a new CareerForge workspace in the current folder: folders, starter config, scripts
  and Python packages. Run once after installing the CareerForge plugin; run with "update"
  to refresh the scripts and shared rules after a plugin update.
disable-model-invocation: true
argument-hint: "[update]"
---
Initialize a CareerForge workspace in the current directory. Creates all required folders and starter configuration files so the agents have a place to read from and write to.

Run this once after installing the CareerForge plugin, from whichever directory you want to use as your job search workspace.

Arguments: $ARGUMENTS

**Update mode.** If the arguments contain `update`, refresh only the runtime files and stop: run Step 3a's fetch (it overwrites `scripts/`, `tools/`, `templates/`, `SOUL.md`, `.claude/CLAUDE.md`, `.claude/reference/` and `.claude/rules/`), then Step 3b. Never touch `knowledge_base/`, `config/`, `postings/`, `output/` or `data/`. Report what was refreshed. If `.claude/CLAUDE.md` differs from the downloaded one and the user may have edited it, show the diff and ask before overwriting it.

## Steps

**Step 1 — Check if already initialized**

Use the Glob tool to check whether `knowledge_base/sources/` exists in the current directory.

If it exists, report:
> "Your CareerForge workspace is already initialized here. Just tell me what you'd like to do: build your profile, find jobs, prep for an interview, or anything else. (To refresh the scripts and shared rules after a plugin update, run `/cf-init update`.)"

Then stop — do not recreate anything.

**Step 2 — Create the directory structure**

```bash
mkdir -p knowledge_base/sources knowledge_base/archive knowledge_base/memories config postings/journal output/resumes output/cover_letters output/interview_prep output/lead_reports output/analytics output/career_exploration output/career_paths output/.work data .claude
```

**Step 3 — Bootstrap runtime files and Python dependencies**

Skip 3a entirely if `scripts/generate_docx.py` already exists (the user is working inside a cloned repo, which already has everything).

**3a — Fetch scripts, tools, templates and the workspace rules**

A plugin can't ship a CLAUDE.md or rules files that load as context, so this step copies them into the workspace: the project instructions (`.claude/CLAUDE.md` and the `SOUL.md` it imports), the path-scoped rules (`.claude/rules/`), and the shared reference files every agent reads (`.claude/reference/`).

1. Verify git is available: `git --version`
2. If it is, fetch only what the workspace needs:

```bash
git clone --depth=1 --filter=blob:none --no-checkout https://github.com/michaelgarcia/careerforge _cf_bootstrap_tmp && cd _cf_bootstrap_tmp && git sparse-checkout set --no-cone /scripts/ /tools/ /templates/ /SOUL.md /.claude/CLAUDE.md /.claude/reference/ /.claude/rules/ && git checkout && cd .. && cp -r _cf_bootstrap_tmp/scripts _cf_bootstrap_tmp/tools _cf_bootstrap_tmp/templates _cf_bootstrap_tmp/SOUL.md . && cp -r _cf_bootstrap_tmp/.claude/CLAUDE.md _cf_bootstrap_tmp/.claude/reference _cf_bootstrap_tmp/.claude/rules .claude/
```

3. Tell the user the `_cf_bootstrap_tmp` folder can be deleted (this project's permissions block `rm`, so don't try to delete it yourself).
4. If git is NOT available, display this message and continue:
> "git is not available, so I skipped the download. To enable resume and cover letter generation, copy `scripts/`, `tools/`, `templates/`, `SOUL.md`, `.claude/CLAUDE.md`, `.claude/reference/` and `.claude/rules/` from https://github.com/michaelgarcia/careerforge into this folder."

**3b — Install Python dependencies**

Run the following command. Use `--quiet` to keep output clean. If it fails, show the exact error and ask the user to run it manually.

```bash
pip install --quiet python-docx markdown xhtml2pdf docx2pdf pydantic httpx pyyaml beautifulsoup4
```

On Windows, also run `pip install --quiet pywin32` (needed by `docx2pdf` for Word COM automation; not required on macOS/Linux).

**Step 4 — Write starter files**

Never overwrite a file that already exists; check first with Glob.

- `knowledge_base/sources/.gitkeep`: an empty file.
- `config/preferences.yaml`: copy `templates/preferences.template.yaml`.
- `config/search_scopes.yaml`: copy `templates/search_scopes.template.yaml`.
- `config/company_targets.yaml`: copy `templates/company_targets.template.yaml`.
- `postings/applications.csv`: the application tracker, an append-only event log with one row per status change. Write only the header row:

```
event_id,timestamp,slug,company,title,job_url,status,previous_status,note,output_files
```

- `.gitignore`:

```
# CareerForge — private data (never commit these)
knowledge_base/
postings/
data/
config/preferences.yaml
config/search_scopes.yaml
config/company_targets.yaml
.claude/settings.local.json

# Generated output (may contain personal data)
output/
```

**Step 5 — Confirm and guide**

After creating all files and directories, respond with:

> "Your CareerForge workspace is ready.
>
> 1. Drop your career documents into `knowledge_base/sources/`: resumes, LinkedIn exports, performance reviews, project write-ups. PDF, DOCX, TXT and MD all work.
> 2. Then just tell me what you need, in your own words. For example: *"build my profile"*, *"set up my job filters"*, *"I have an interview at Acme next week"*, *"is this job a good fit?"*
>
> **One more thing:** `knowledge_base/memories/` is yours. Drop a short file in there for any rule you want every agent to follow, such as a wording preference or a project name that must never appear in a deliverable. See `templates/memory.template.md` for the format. It is gitignored and never generated, so it stays exactly as you leave it.
>
> Your data stays entirely on your machine. Nothing is synced or uploaded."

Every new session in this folder starts with a state check, so the next time the user opens it, Claude already knows what's there.
