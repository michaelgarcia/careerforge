Use the job-scanner agent to run a daily LinkedIn job scan:

1. Read the candidate profile (candidate_profile.yaml, candidate_narrative.md) and preferences
2. Sync new jobs from LinkedIn using all enabled search scopes (scripts/linkedin/sync.py --days <N>)
3. Apply rule-based pre-filter for hard constraints (scripts/linkedin/pre_filter.py --days <N>)
4. Export unscored jobs as markdown (scripts/linkedin/export_for_scoring.py --days <N>)
5. LLM-score each exported job using the 6-dimension rubric against the candidate profile
6. Write scores to SQLite (scripts/linkedin/update_scores.py)
7. Generate a ranked markdown report (scripts/linkedin/report.py)
8. Generate an analytics dashboard (scripts/linkedin/analytics.py)
9. Present a concise summary to the user with top opportunities, report path, and analytics path

Arguments (optional): $ARGUMENTS
- "--days N" controls the lookback window (default: 1 for daily runs)
  - Passed to sync.py as --days N (maps N to LinkedIn date filter: 1=past-24h, 2-7=past-week, 8-30=past-month, >30=any-time)
  - Passed to pre_filter.py as --days N
  - Passed to export_for_scoring.py as --days N
- "--scope <name>" — run only that named scope (for testing)
- "--dry-run" — fetch but don't write to database
