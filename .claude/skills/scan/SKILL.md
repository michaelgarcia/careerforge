---
name: scan
description: >
  Find new matching jobs on LinkedIn: sync the saved searches, filter on hard constraints, score
  the shortlist and report the best ones. Use for "find me jobs", "what's new?", "any new
  roles?", "run my daily scan".
argument-hint: "[--days N] [--scope <name>] [--dry-run] [--bootstrap]"
context: fork
agent: job-scanner
background: false
---
Run a LinkedIn job scan:

1. Read the candidate profile, narrative and preferences (see .claude/reference/kb-context.md)
2. Sync new jobs for all enabled search scopes (scripts/linkedin/sync.py --days <N>)
3. Apply the rule-based pre-filter (scripts/linkedin/pre_filter.py --days <N>)
4. Export unscored jobs (scripts/linkedin/export_for_scoring.py --days <N>)
5. Score each exported job with .claude/reference/scoring-rubric.md
6. Write scores to SQLite (scripts/linkedin/update_scores.py)
7. Generate the ranked report (scripts/linkedin/report.py)
8. Generate the analytics dashboard (scripts/linkedin/analytics.py)
9. Summarize the top opportunities, the report path and the dashboard path

Arguments: $ARGUMENTS
- `--days N`: lookback window (default 1). Passed to sync.py, pre_filter.py and export_for_scoring.py. sync.py maps N to LinkedIn's date filter: 1 = past 24h, 2-7 = past week, 8-30 = past month, >30 = any time.
- `--bootstrap`: first run; use `--days 30`.
- `--scope <name>`: run only that scope (for testing).
- `--dry-run`: fetch but don't write to the database.
