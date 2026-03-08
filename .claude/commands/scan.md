Use the job-scanner agent to run a daily LinkedIn job scan:

1. Read the candidate profile (candidate_profile.yaml, candidate_narrative.md) and preferences
2. Sync new jobs from LinkedIn using all enabled search scopes (scripts/linkedin/sync.py)
3. Apply rule-based pre-filter for hard constraints (scripts/linkedin/pre_filter.py)
4. Export unscored jobs as markdown (scripts/linkedin/export_for_scoring.py)
5. LLM-score each exported job using the 6-dimension rubric against the candidate profile
6. Write scores to SQLite (scripts/linkedin/update_scores.py)
7. Generate a ranked markdown report (scripts/linkedin/report.py)
8. Present a concise summary to the user with top opportunities

Arguments (optional): $ARGUMENTS
- If "--scope <name>" is passed, run only that named scope (for testing)
- If "--bootstrap" is passed, use past-month date filter for initial population
- If "--dry-run" is passed, fetch but don't write to database
