# Company Scanner — Phase 1 Reference

Tracks a small, named list of company career pages and maintains one Excel spreadsheet per company. Runs on request ("scan my target companies", or `/scan-companies`), skips days without issue, and never loses your human edits (Reviewed / Applied status).

Phase 1 supports companies on the Greenhouse ATS public API — no browser automation needed. Phase 2 (Google) extends the same pipeline with Playwright and will be documented separately.

---

## 1. What Was Built

The system is a **5-step deterministic pipeline** with one AI classification step in the middle. The steps run in order, each one reading from SQLite and writing back to it, until the final step writes the Excel file.

```
Greenhouse API
     │
     ▼
[1] sync.py              ← fetch all jobs, upsert into SQLite (100% deterministic)
     │
     ▼
[2] mark_deleted.py      ← flag jobs no longer on the site (100% deterministic)
     │
     ▼
[3] export_for_review.py ← export only new/changed jobs as JSON (100% deterministic)
     │
     ▼
[4] AI agent             ← classify IC vs. manager, location, comp range (NON-deterministic)
     │
     ▼
[5] apply_classifications.py  ← write AI judgments back to SQLite (100% deterministic)
     │
     ▼
[6] write_trackers.py    ← build/update anthropic.xlsx from SQLite (100% deterministic)
```

The AI agent (Step 4) only handles fields that genuinely require judgment:
- Is this role IC or manager?
- Is the location inside the candidate's location scope (home city or remote)?
- What is the comp range (parsed from prose)?

Everything else — fetching, deduplication, deletion detection, Excel formatting, the freeze/Deleted rules — is plain Python with no LLM calls.

---

## 2. Files Involved

### Configuration

| File | Purpose |
|---|---|
| `config/company_targets.yaml` | List of companies to monitor (gitignored; start from `templates/company_targets.template.yaml`). The single place to add/remove companies, change department IDs, or disable a company. |
| `config/preferences.yaml` → `company_scanner` | The filter criteria: `home_city`, `role_rule`, `function_scope`. Location and comp floor come from `hard_constraints`. Set them by saying "set up my job filters". |

Example (from the template):

```yaml
companies:
  - name: examplecorp
    display_name: ExampleCorp
    ats: greenhouse
    fetch_method: api
    board_token: examplecorp
    department_ids:
      - 1234567890   # from the team= parameter in the careers page URL
    enabled: true
```

`department_ids` come from the `team=` query parameter in the company's filtered careers page URL. They map 1:1 to Greenhouse department IDs.

### Scripts — `scripts/company_scanner/`

| Script | What it does |
|---|---|
| `init_db.py` | Creates the three SQLite tables on first use. Safe to re-run (uses `CREATE TABLE IF NOT EXISTS`). Also handles schema migrations (e.g. adding new columns to existing tables). |
| `fetch_greenhouse.py` | Contains the Greenhouse API client and the `sync_company()` function. Not a runnable script on its own — called by `sync.py`. |
| `sync.py` | **Entry point for Step 1.** Loads `company_targets.yaml`, dispatches each enabled company to the right fetcher. Accepts `--company <name>` and `--dry-run`. |
| `mark_deleted.py` | **Step 2.** Finds jobs whose `last_seen_run` does not match the latest successful scan run and sets `still_listed=0`. |
| `export_for_review.py` | **Step 3.** Exports jobs that have no classification yet, or whose description changed since last classified (tracked via SHA-256 hash). Writes one JSON file per job + a `manifest.json`. |
| `apply_classifications.py` | **Step 5.** Reads the AI agent's JSON output, validates it, upserts into `company_job_classifications`. Never touches Excel. |
| `write_trackers.py` | **Step 6.** The only script that touches `.xlsx` files. Fully deterministic — reads SQLite, applies the upsert/freeze/Deleted rules, saves the tracker. |
| `generate_candidate_summary.py` | One-time setup helper. Generates `knowledge_base/candidate_summary_compact.md` from your full KB. This file is the condensed candidate context the AI agent reads — it keeps the agent's context small so classification is fast. |

### Database — `data/jobs.db`

Shared with the LinkedIn scanner (different tables, same file). Three tables are used by the company scanner:

**`company_jobs`** — one row per job ever seen on a target site, regardless of fit.

| Column | Type | Notes |
|---|---|---|
| `job_id` | TEXT PK | Prefixed with `gh_` for Greenhouse jobs (e.g. `gh_4461450008`) |
| `source_company` | TEXT | Matches the `name` field in `company_targets.yaml` |
| `title` | TEXT | Job title |
| `department` | TEXT | Comma-separated department names |
| `location_raw` | TEXT | Pipe-separated locations (e.g. `San Francisco, CA \| New York City, NY`) |
| `description_text` | TEXT | Full job description, HTML stripped to plain text |
| `job_url` | TEXT | Direct link to the posting |
| `posted_or_updated_at` | TEXT | Timestamp from the ATS |
| `first_seen_at` | TEXT | ISO timestamp when this job first entered the DB |
| `last_seen_at` | TEXT | ISO timestamp of the most recent sync that saw this job |
| `still_listed` | INTEGER | 1 = currently on the site, 0 = no longer listed |
| `raw_json` | TEXT | Full original API response (for debugging/auditing) |
| `first_seen_run` | INTEGER | FK → `company_scan_runs.id` of the run that first added this job |
| `last_seen_run` | INTEGER | FK → `company_scan_runs.id` of the most recent run that saw this job |

**`company_job_classifications`** — one row per classified job.

| Column | Type | Notes |
|---|---|---|
| `job_id` | TEXT PK FK | Links to `company_jobs` |
| `is_manager` | INTEGER | 0/1/NULL (NULL = not yet classified) |
| `in_location_scope` | INTEGER | 0/1/NULL |
| `chicago_yn` | INTEGER | 0/1/NULL — the home city (`company_scanner.home_city`) specifically, separate from remote scope. Legacy column name, kept so existing databases keep working. |
| `ote_low` | INTEGER | Low end of OTE range in dollars, or NULL if not stated |
| `ote_high` | INTEGER | High end of OTE range, or NULL if not stated |
| `base_low` | INTEGER | Low end of base salary range, or NULL |
| `base_high` | INTEGER | High end of base salary range, or NULL |
| `equity_yn` | INTEGER | 0/1/NULL |
| `disposition` | TEXT | One of: `qualified`, `rejected_manager_role`, `rejected_location`, `rejected_comp_floor`, `rejected_other` |
| `notes` | TEXT | Short sentence explaining the disposition |
| `classified_at` | TEXT | ISO timestamp of classification |
| `source_description_hash` | TEXT | SHA-256 of the description text at classification time — used to detect re-classification needs |

**`company_scan_runs`** — audit log of every sync run.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-incrementing run ID |
| `company` | TEXT | |
| `run_at` | TEXT | ISO timestamp |
| `jobs_found` | INTEGER | Total jobs matching configured filters |
| `jobs_added` | INTEGER | Net new rows inserted |
| `jobs_updated` | INTEGER | Rows refreshed (already existed) |
| `jobs_marked_deleted` | INTEGER | Updated separately by `mark_deleted.py` |
| `status` | TEXT | `running` during the run, then `success` on completion |

### Agent — `.claude/agents/company-scanner.md`

The AI agent definition. Instructs the agent to:
1. Read `knowledge_base/candidate_summary_compact.md` for classification context
2. Run each pipeline script in order (sync → mark_deleted → export → classify → apply → write)
3. Classify each exported job using the fixed filter criteria in the compact candidate summary (location scope, role types, comp floor)
4. Present a per-company summary with new qualified postings listed

### Skill — `.claude/skills/scan-companies/SKILL.md`

Triggered by plain language ("any new openings at Anthropic?", "scan my target companies") or the `/scan-companies` shortcut. Runs the company-scanner agent with any arguments you pass (`--company`, `--dry-run`).

### Output — `output/company_trackers/`

One `.xlsx` file per company. Not committed to git (gitignored). The tracker for Anthropic is at `output/company_trackers/anthropic.xlsx`.

### Candidate Context — `knowledge_base/candidate_summary_compact.md`

Generated once from your full KB by `generate_candidate_summary.py`. Scoped to classification only (NOT for resume/cover letter generation, which still needs the full KB). Gitignored.

---

## 3. How to Run It

### Prerequisites

First-time setup only:

```bash
# Install openpyxl if not already done
pip install -r requirements.txt

# Initialize the company-scanner tables in the shared database
python scripts/company_scanner/init_db.py

# Generate the condensed candidate context (requires a built KB)
python scripts/company_scanner/generate_candidate_summary.py
```

If `generate_candidate_summary.py` exits with an error, it says what is missing: a built profile ("build my profile") or the `company_scanner` preferences ("set up my job filters"). The agent regenerates the compact summary whenever preferences or the profile are newer than it.

---

### Option A — Recommended: just ask

This is the intended daily-use path. Say "scan my target companies" (or "any new openings at Anthropic?"), or type the shortcut:

```
/scan-companies
```

Or to scope to one company:

```
/scan-companies --company anthropic
```

The company-scanner agent handles everything: runs all six scripts in order, classifies the new jobs, writes the Excel tracker, and gives you a summary with newly qualified postings listed.

---

### Option B — Run the scripts manually (step by step)

Useful for debugging, testing individual steps, or understanding what's happening.

**Step 1 — Fetch jobs from the careers site:**

```bash
python scripts/company_scanner/sync.py
# Or scope to one company:
python scripts/company_scanner/sync.py --company anthropic
# Preview without writing:
python scripts/company_scanner/sync.py --company anthropic --dry-run
```

**Step 2 — Mark jobs no longer on the site:**

```bash
python scripts/company_scanner/mark_deleted.py --company anthropic
```

**Step 3 — Export jobs needing classification:**

```bash
python scripts/company_scanner/export_for_review.py \
  --company anthropic \
  --output output/.work/company_scan/
```

Read `manifest.json` to see what was exported:

```bash
# On Windows:
python -c "import json; m=json.load(open('output/.work/company_scan/manifest.json')); [print(e) for e in m]"
```

If the manifest is empty, there are no new or changed jobs — skip to Step 5.

**Step 4 — Classify (AI step).**

The agent does this automatically when using `/scan-companies`. If running manually, this step requires the AI agent. The expected JSON output format is:

```json
[
  {
    "job_id": "gh_1234567",
    "is_manager": false,
    "in_location_scope": true,
    "chicago_yn": false,
    "ote_low": 230000,
    "ote_high": 280000,
    "base_low": null,
    "base_high": null,
    "equity_yn": true,
    "disposition": "qualified",
    "notes": "Remote-eligible IC role, OTE stated and clears the floor.",
    "description_hash": "<copied from the exported job JSON>"
  }
]
```

`disposition` must be one of: `qualified`, `rejected_manager_role`, `rejected_location`, `rejected_comp_floor`, `rejected_other`.

**Step 5 — Apply classifications back to the database:**

```bash
python scripts/company_scanner/apply_classifications.py \
  --input output/.work/company_classifications.json
# Validate without writing:
python scripts/company_scanner/apply_classifications.py \
  --input output/.work/company_classifications.json \
  --dry-run
```

**Step 6 — Write the Excel tracker:**

```bash
python scripts/company_scanner/write_trackers.py --company anthropic
```

Output: `output/company_trackers/anthropic.xlsx`

---

### Useful database queries

```bash
python -c "
import sqlite3
con = sqlite3.connect('data/jobs.db')
cur = con.cursor()

# All jobs found today
cur.execute(\"SELECT title, location_raw, job_url FROM company_jobs WHERE source_company='anthropic' AND still_listed=1 ORDER BY first_seen_at DESC LIMIT 10\")
for r in cur.fetchall(): print(r)
"
```

```bash
python -c "
import sqlite3
con = sqlite3.connect('data/jobs.db')
cur = con.cursor()

# See all rejected jobs and why
cur.execute(\"SELECT j.title, c.disposition, c.notes FROM company_jobs j JOIN company_job_classifications c ON j.job_id=c.job_id WHERE c.disposition != 'qualified' ORDER BY c.classified_at DESC\")
for r in cur.fetchall(): print(r)
"
```

```bash
python -c "
import sqlite3
con = sqlite3.connect('data/jobs.db')
cur = con.cursor()

# Scan run history
cur.execute('SELECT id, company, run_at, jobs_found, jobs_added, jobs_updated, status FROM company_scan_runs ORDER BY id DESC LIMIT 10')
for r in cur.fetchall(): print(r)
"
```

---

## 4. What Is Deterministic vs. Non-Deterministic

### Fully deterministic (plain Python, no LLM)

| Component | Why it's deterministic |
|---|---|
| `sync.py` / `fetch_greenhouse.py` | HTTP GET to a JSON API, upsert to SQLite via `INSERT ... ON CONFLICT DO UPDATE`. Same input always produces the same DB state. |
| `mark_deleted.py` | Pure SQL: `UPDATE ... WHERE last_seen_run != latest_run_id`. No judgment, no randomness. |
| `export_for_review.py` | Hash comparison (`sha256` of description text), JSON file writes. Identical DB state always produces identical export. |
| `apply_classifications.py` | SQL upsert from a JSON file. The file is the input; the script is purely mechanical. |
| `write_trackers.py` | Rule-based upsert from SQLite to `.xlsx`. Fixed column order, explicit freeze rules, explicit Deleted-flip logic. Re-running on the same DB state always produces the same spreadsheet. The only environmental non-determinism is a file lock (Excel has the file open), handled by retry + `.xlsx.new` fallback. |
| `init_db.py` | `CREATE TABLE IF NOT EXISTS` — idempotent DDL. |

### Non-deterministic (AI judgment)

| Component | What varies and why |
|---|---|
| Step 4 — AI classification | The AI classifies IC vs. manager, location scope, and parses comp ranges from prose. Two runs over the same job description could produce slightly different `notes` text and, in edge cases, different `disposition` outcomes. This is unavoidable — these fields genuinely require reading comprehension of ambiguous text. |

### Key design implication

Because the AI step outputs a JSON file and the mechanical `apply_classifications.py` script writes it to the DB, the AI output is **auditable and correctable**:

- You can open the JSON file before running Step 5 and edit a misclassification directly.
- You can re-run Steps 5–6 with a corrected JSON without re-running the AI.
- Re-running the AI on a job whose description hasn't changed will not re-classify it (Step 3 skips already-classified, unchanged jobs). To force re-classification, you can clear the row from `company_job_classifications` in SQLite.

---

## 5. Tracker Column Reference

The Excel file (`output/company_trackers/anthropic.xlsx`) has 10 columns:

| Column | Human-editable? | Notes |
|---|---|---|
| Job ID | No | Primary key, format `gh_<number>` for Greenhouse. Immutable — used for row identity across runs. |
| Posting status | **Yes** | Automation writes `New` on first insertion. You change it to `Reviewed`, `Applied`, etc. Automation only writes `Deleted` (when a job disappears from the site). Never overwritten once set, except for the `New/Reviewed → Deleted` flip. |
| Manager role | No | `Yes` / `No` / blank. Refreshed every run from the AI classification. |
| Title | No | Refreshed every run from the live posting. |
| OTE compensation range | No | Parsed from description prose by AI. Blank if not stated — posting is not rejected for missing comp. |
| Base Salary Range | No | Same. |
| Equity | No | `Yes` / `No` / blank. |
| Home city | No | `Yes` / `No` — whether your home city (`company_scanner.home_city`) is listed as an eligible location. Trackers created before this change keep the old header label until regenerated. |
| Location | No | Raw location string(s) from the ATS, refreshed every run. |
| Date created | **Yes** | Set to today's date when the row is first inserted. Immutable — never overwritten. |

### Status lifecycle

```
[automation] New  →  [you] Reviewed  →  [you] Applied
                  ↘
                   [automation, if job disappears] Deleted

Applied is terminal — automation never changes it.
```

---

## 6. First run

The first scan classifies every job that has no classification yet, then writes only the qualified ones to the tracker. Make sure your profile is built and the `company_scanner` block in `config/preferences.yaml` is filled in first; the agent will tell you if either is missing.
