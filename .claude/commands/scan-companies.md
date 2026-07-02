Use the company-scanner agent to scan configured company career pages for new job postings:

1. Read candidate context (knowledge_base/candidate_summary_compact.md), generating it via scripts/company_scanner/generate_candidate_summary.py if missing
2. Sync jobs from all enabled companies in config/company_targets.yaml (scripts/company_scanner/sync.py)
3. Mark jobs no longer listed as still_listed=0 (scripts/company_scanner/mark_deleted.py)
4. Export new/changed jobs needing classification (scripts/company_scanner/export_for_review.py)
5. Classify each exported job (IC vs. manager, location scope, comp parsing, disposition) against the fixed filter criteria (Chicago/Remote-USA, IC-only, $220k+ comp floor)
6. Apply classifications to SQLite, then write each company's Excel tracker (scripts/company_scanner/apply_classifications.py, scripts/company_scanner/write_trackers.py)
7. Generate the HTML audit dashboard covering all companies (scripts/company_scanner/analytics.py)
8. Present a concise summary per company: sync stats, classification breakdown by disposition, tracker changes, newly-qualified postings, and the dashboard path

Arguments (optional): $ARGUMENTS
- "--company <name>" — run only that named company (e.g., "anthropic"), passed through to sync.py, mark_deleted.py, export_for_review.py, and write_trackers.py
- "--dry-run" — fetch but don't write to the database (sync.py only; skips remaining steps)
