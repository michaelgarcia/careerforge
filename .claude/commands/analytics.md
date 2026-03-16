Generate a LinkedIn pipeline analytics dashboard from the jobs database.

Run `python scripts/linkedin/analytics.py` to generate an interactive HTML report at `output/analytics/analytics_YYYY-MM-DD.html`. The report includes:
- Pipeline overview (total collected → hard-filtered → scored → top matches)
- Score distribution histogram
- Scope performance comparison (jobs collected vs. scored per search scope)
- Tier breakdown (Tier 1 / Tier 2 / Tier 3 / filtered)
- Top filter reasons (why jobs were hard-filtered)

After running, confirm the HTML file exists and report its path to the user. Then tell the user they can open it in any browser — no server required.
