# LinkedIn Job Scanner — Reference

## Overview

The LinkedIn Scanner is a two-tier automated job discovery pipeline integrated into CareerForge. It queries LinkedIn's public Guest API across configurable search scopes, deduplicates results globally in a local SQLite database, pre-filters with rule-based hard constraints, and LLM-scores shortlisted candidates against your profile. Only the highest-fit opportunities are surfaced via `/scan`.

**Why it exists:** The existing `scorer` agent is reactive (you bring it a posting). The scanner is proactive — it discovers, filters, scores, and surfaces jobs autonomously every day so you don't have to manually search.

---

## Architecture

```
Tier 1 — Data Collection (pure Python, no LLM)
┌─────────────────────────────────────────────────────────┐
│  config/search_scopes.yaml  config/preferences.yaml     │
│          │                         │                    │
│          ▼                         ▼                    │
│   scripts/linkedin/sync.py  ← map_preferences.py       │
│          │                                              │
│          ▼                                              │
│   data/jobs.db  (SQLite, global dedup via PRIMARY KEY)  │
│          │                                              │
│          ▼                                              │
│   scripts/linkedin/pre_filter.py                        │
│   (marks hard_filtered=1 for clearly wrong jobs)        │
└─────────────────────────────────────────────────────────┘

Tier 2 — Scoring & Reporting (LLM, via /scan)
┌─────────────────────────────────────────────────────────┐
│   scripts/linkedin/export_for_scoring.py                │
│   (exports unscored jobs as markdown files)             │
│          │                                              │
│          ▼                                              │
│   job-scanner agent  (claude-haiku-4-5-20251001)        │
│   reads candidate_profile.yaml + candidate_narrative.md │
│   scores each job on 6 dimensions                       │
│          │                                              │
│          ▼                                              │
│   scripts/linkedin/update_scores.py                     │
│   (writes scores to job_scores table)                   │
│          │                                              │
│          ▼                                              │
│   scripts/linkedin/report.py                            │
│   output/lead_reports/linkedin_scan_YYYY-MM-DD.md       │
└─────────────────────────────────────────────────────────┘
```

---

## Package: `tools/linkedin_job_search/`

Copied from the standalone `linkedin-job-search` library. Scripts add `tools/` to `sys.path` — no install required.

| Module | Role |
|---|---|
| `client.py` | `LinkedInJobSearch` — HTTP client with rate limiting, retry, pagination. `search()` and `enrich_jobs()`. |
| `models.py` | Pydantic models: `SearchResult`, `EnrichedJob`, `GeoLocation`. Enums: `ExperienceLevel`, `WorkModel`, `DatePosted`, `JobType`. |
| `storage.py` | Original JSONL store (not used by scanner; kept for CLI compatibility). |
| `exceptions.py` | `LinkedInAPIError`, `ParseError`. |
| `cli.py` | Original CLI entry point (`linkedin-jobs search ...`). Not used by scanner. |
| `email_parser.py` | Parse LinkedIn job alert `.eml` files. |
| `email_source.py` | IMAP source for fetching alert emails. |
| `config.py` | `EmailConfig` and `load_email_config()` for IMAP credentials. |

---

## SQLite Schema (`data/jobs.db`)

Initialised by `scripts/linkedin/init_db.py`. Git-ignored — local only.

### `jobs` table
| Column | Type | Description |
|---|---|---|
| `job_id` | TEXT PK | LinkedIn job posting ID (global dedup key) |
| `title` | TEXT | Job title |
| `company_name` | TEXT | Company |
| `location` | TEXT | Location string from LinkedIn |
| `job_url` | TEXT | Direct LinkedIn URL |
| `posted_time` | TEXT | Raw LinkedIn string ("3 days ago") |
| `collected_at` | TEXT | ISO datetime when first collected |
| `full_description` | TEXT | Full job description (from enrichment) |
| `seniority_level` | TEXT | LinkedIn seniority label |
| `employment_type` | TEXT | Full-time, Part-time, etc. |
| `job_function` | TEXT | LinkedIn job function category |
| `industries` | TEXT | Industry labels |
| `salary_info` | TEXT | Salary if present in posting |
| `enriched_at` | TEXT | ISO datetime of enrichment |
| `source_scope` | TEXT | Which search scope first found this job |
| `first_seen_run` | INTEGER | FK to `search_runs.id` |

### `search_runs` table
Logs every sync run. Used for auditing and provenance (`first_seen_run`).

### `job_scores` table
| Column | Type | Description |
|---|---|---|
| `job_id` | TEXT PK | FK to `jobs.job_id` |
| `score` | INTEGER | Overall 0-100 score |
| `tier` | TEXT | tier1 / tier2 / tier3 / filtered |
| `skill_match` | INTEGER | 0-100 |
| `experience_alignment` | INTEGER | 0-100 |
| `domain_fit` | INTEGER | 0-100 |
| `growth_potential` | INTEGER | 0-100 |
| `company_quality` | INTEGER | 0-100 |
| `preference_match` | INTEGER | 0-100 |
| `hard_filtered` | INTEGER | 1 = rejected by rule-based filter |
| `filter_reason` | TEXT | Reason if hard_filtered=1 |
| `notes` | TEXT | LLM-generated tailoring notes |
| `presented_at` | TEXT | ISO datetime when shown to user (null = not yet shown) |

---

## `config/search_scopes.yaml` — Schema Reference

```yaml
scopes:
  - name: unique_identifier          # Used in --scope CLI flag and DB records
    description: "Human-readable"
    keywords: "keyword string"       # LinkedIn free-text search
    locations:                       # List of location strings
      - "Remote"
      - "Chicago, IL"
    experience_levels:               # internship | entry-level | associate |
      - mid-senior                   # mid-senior | director | executive
      - director
    work_model: remote               # remote | hybrid | on-site (omit for any)
    date_posted: past-week           # past-24h | past-week | past-month | any-time
    limit: 75                        # Max jobs per location per run
    enabled: true                    # false = skip without deleting
```

**Tips:**
- Add new scopes and test with `--scope <name> --dry-run`
- Disable noisy scopes with `enabled: false` — keeps config for reference
- The `target_companies` scope has its `companies` list auto-populated from `preferences.yaml` at runtime by `map_preferences.py`
- A synthetic `from_preferences` scope is also auto-generated each run from `preferences.yaml` fields

---

## Preferences Mapping

`map_preferences.py` translates `config/preferences.yaml` fields to LinkedIn search parameters:

| `preferences.yaml` field | Maps to |
|---|---|
| `hard_constraints.location.remote_only: true` | `work_model = remote`, location = "Remote" |
| `hard_constraints.location.acceptable_locations` | Search locations list |
| `hard_constraints.location.include_hybrid` | `work_model = hybrid` |
| `hard_constraints.role_types` | `experience_levels` (see mapping table below) |
| `search_config.target_titles` | Prefix of `keywords` string |
| `search_config.keywords` | Appended to `keywords` string |
| `search_config.target_companies` | Injected into `target_companies` scope |
| `linkedin_scanner.lead_score_threshold` | `--threshold` default in `report.py` |
| `linkedin_scanner.max_score_per_run` | `--limit` default in `export_for_scoring.py` |
| `linkedin_scanner.export_lookback_days` | `--days` default in `export_for_scoring.py` |

**Role type → LinkedIn experience level mapping:**

| `role_types` value | LinkedIn `experience_levels` |
|---|---|
| Individual Contributor | mid-senior |
| Technical Lead | mid-senior, director |
| Staff Architect | mid-senior, director |
| Principal Architect | director |
| Director | director |
| VP | executive |
| C-Level | executive |

---

## Script Reference

### `scripts/linkedin/init_db.py`
Initialises `data/jobs.db` with the full schema. Safe to re-run.
```bash
python scripts/linkedin/init_db.py
```

### `scripts/linkedin/map_preferences.py`
Prints the auto-generated scope and target companies from preferences.yaml.
```bash
python scripts/linkedin/map_preferences.py
```

### `scripts/linkedin/sync.py`
Main sync orchestration. Fetches jobs for all enabled scopes and stores in DB.
```bash
python scripts/linkedin/sync.py                          # all enabled scopes
python scripts/linkedin/sync.py --scope ai_architect_remote  # one scope
python scripts/linkedin/sync.py --dry-run                # no DB writes
python scripts/linkedin/sync.py --bootstrap              # past-month filter
```

### `scripts/linkedin/pre_filter.py`
Rule-based hard filter. Marks clearly wrong jobs as `hard_filtered=1`.
```bash
python scripts/linkedin/pre_filter.py                    # default 14-day window
python scripts/linkedin/pre_filter.py --days 30          # wider window
python scripts/linkedin/pre_filter.py --reset            # clear flags and re-run
```

### `scripts/linkedin/export_for_scoring.py`
Exports unscored, non-filtered jobs as markdown files for LLM scoring.
```bash
python scripts/linkedin/export_for_scoring.py
python scripts/linkedin/export_for_scoring.py --output /tmp/jobs/ --days 7 --limit 30
```

### `scripts/linkedin/update_scores.py`
Writes LLM scores from a JSON file back to the `job_scores` table.
```bash
python scripts/linkedin/update_scores.py --input /tmp/scores.json
python scripts/linkedin/update_scores.py --input /tmp/scores.json --dry-run
```

### `scripts/linkedin/report.py`
Generates a ranked markdown report of scored jobs above threshold.
```bash
python scripts/linkedin/report.py                        # default threshold from prefs
python scripts/linkedin/report.py --threshold 60         # lower threshold
python scripts/linkedin/report.py --no-mark              # don't mark as presented
python scripts/linkedin/report.py --limit 30             # more jobs in report
```

---

## Job-Scanner Agent

**File:** `.claude/agents/job-scanner.md`
**Model:** `claude-haiku-4-5-20251001` — fast, low cost, well-suited to repetitive structured scoring.

**KB files loaded:**
- `knowledge_base/candidate_profile.yaml` — skills, roles, achievements (required for scoring)
- `knowledge_base/candidate_narrative.md` — career narrative (required for context)
- `config/preferences.yaml` — constraints, threshold, batch size

**NOT loaded:** `candidate_reviews.yaml`, `candidate_feedback_narrative.md` (not needed for scoring — saves tokens).

**Scoring rubric (6 dimensions, each 0-100):**

| Dimension | Weight | What it measures |
|---|---|---|
| `skill_match` | 25% | Technical skills overlap |
| `preference_match` | 25% | Location, remote, comp, role type alignment |
| `experience_alignment` | 12.5% | Seniority fit |
| `domain_fit` | 12.5% | Industry/domain match to preferred domains |
| `growth_potential` | 12.5% | Career goal alignment |
| `company_quality` | 12.5% | Company reputation, scale, culture signal |

**Tier thresholds:**
- `tier1`: ≥ 75 — pursue immediately
- `tier2`: 60-74 — worth considering
- `tier3`: 45-59 — borderline
- `filtered`: < 45 — not worth pursuing

**Batch limit:** `max_score_per_run` in `preferences.yaml` (default: 30).

---

## `/scan` Command

Invokes the job-scanner agent to run the full pipeline:

```
/scan
/scan --scope ai_architect_remote      # test a single scope
/scan --bootstrap                      # first run: past-month data
/scan --dry-run                        # fetch without writing to DB
```

Reports are saved to `output/lead_reports/linkedin_scan_YYYY-MM-DD.md`.

---

## Automation Setup

### Claude Code Cron (Tier 2 — Scoring)

Schedule the `/scan` command to run daily using CronCreate. Example: every day at 8 AM.

To set up, ask: "Create a daily cron job at 8 AM that runs /scan"

The cron runs the full pipeline including sync, filter, scoring, and report generation.

### Optional OS-Level Sync (Tier 1 — Data Collection Only)

For zero-LLM data collection that runs even when Claude Code is closed:

**Windows Task Scheduler:**
1. Open Task Scheduler → Create Basic Task
2. Trigger: Daily at 6:00 AM
3. Action: Start a program
   - Program: `python`
   - Arguments: `scripts/linkedin/sync.py && python scripts/linkedin/pre_filter.py`
   - Start in: `F:\workspace\careerforge`
4. Log output: redirect to `data/sync.log`

This decouples data freshness from Claude Code availability and keeps LLM costs minimal.

---

## Calibration Guide

### Test a Single Scope (Dry-Run)
```bash
python scripts/linkedin/sync.py --scope ai_architect_remote --dry-run
```
Prints how many jobs would be fetched without writing to DB.

### Compare Scope Coverage
```bash
python scripts/linkedin/sync.py --scope ai_architect_remote
python scripts/linkedin/sync.py --scope applied_ai_chicago
sqlite3 data/jobs.db "SELECT source_scope, COUNT(*) FROM jobs GROUP BY source_scope"
```

### Check Pre-Filter Hit Rate
```bash
python scripts/linkedin/pre_filter.py
sqlite3 data/jobs.db "SELECT hard_filtered, COUNT(*) FROM job_scores GROUP BY hard_filtered"
sqlite3 data/jobs.db "SELECT filter_reason, COUNT(*) FROM job_scores WHERE hard_filtered=1 GROUP BY filter_reason ORDER BY COUNT(*) DESC"
```

### Check Score Distribution
```bash
sqlite3 data/jobs.db "SELECT tier, COUNT(*) FROM job_scores WHERE score IS NOT NULL GROUP BY tier"
```

### Re-Score with Different Criteria
Lower threshold to see more jobs in the report:
```bash
python scripts/linkedin/report.py --threshold 55 --no-mark
```

Reset scores and re-score (deletes scores, not jobs):
```bash
sqlite3 data/jobs.db "DELETE FROM job_scores WHERE hard_filtered=0"
/scan
```

---

## Deduplication Details

- `jobs.job_id` is the `PRIMARY KEY` — guarantees global dedup across all scopes and all days
- `sync.py` uses `INSERT OR IGNORE` — duplicate job IDs are silently skipped
- `search_runs.jobs_skipped` counts how many duplicates were absorbed each run
- `jobs.source_scope` records which scope **first** found a job (first writer wins)
- **Bootstrap:** Run `sync.py --bootstrap` once (uses `past-month`) to populate historical data. Subsequent daily runs use `past-week`. SQLite dedup absorbs all overlap — no special handling needed.
- **Cross-scope dedup:** If `ai_architect_remote` and `applied_ai_chicago` both find the same job, it is stored once with `source_scope = ai_architect_remote` (whichever ran first).

---

## Troubleshooting

### Rate limiting (HTTP 429)
LinkedIn throttles the Guest API. `sync.py` uses 1.5s delay between requests with exponential backoff. If you see many 429s:
- Increase `request_delay` in the `LinkedInJobSearch()` constructor in `sync.py`
- Run fewer scopes per day (disable some in `search_scopes.yaml`)

### Empty results
- Check that `keywords` and `locations` in the scope are correct
- Test with `--dry-run` and reduce `limit` to 10
- LinkedIn may have changed HTML structure — check `client.py` parsers

### YAML parse errors in preferences.yaml
The original file had `[]` followed by list items on subsequent lines (silently ignored by PyYAML). This has been fixed — lists now use proper block syntax. If you edit `preferences.yaml`, ensure list items are indented under the key, not after `[]`.

### SQLite "database is locked"
Two processes writing simultaneously. Ensure only one `sync.py` runs at a time. If using OS-level scheduler + cron, stagger their start times (e.g., sync at 6 AM, /scan at 8 AM).

### DB migration (schema changes)
Delete `data/jobs.db` and re-run `init_db.py` followed by `sync.py --bootstrap`. Jobs will be re-fetched; scores will need to be re-generated.
