Show me an overview of my current job search pipeline.

Read `postings/applications.csv` and present a summary of all applications.

**How to compute current state from the CSV:**
- The CSV is an event log (one row per status transition, append-only)
- Current status for each application = the status field of the last row sharing that slug
- Days in current status = days since the timestamp of that last row

**Output format:**

Group active applications (not in: rejected, withdrawn, accepted, closed, ghosted) by status. For each, show:
- Company and role title
- Current status
- Days since last status change (flag in amber if 14+ days — may need follow-up)
- Last note (from the most recent CSV row for that slug)

Then show:

**Terminal outcomes** — count of accepted / rejected / withdrawn / ghosted / closed

**Count breakdown by status** — all statuses with at least one application

**Next-action recommendations** — one line per active application:
- `standby` → "Check in with recruiter if 2+ weeks since last contact"
- `in_loop` / `loop_completed` → "Await decision; follow up after agreed timeline"
- `applied` → "Follow up if 2+ weeks since submission"
- `recruiter_screen` / `hm_screen` / `technical_screen` → "Prepare for next round"
- `offered` / `negotiating` → "Immediate action required"
- `on_hold` → "Monitor; reach out if 30+ days with no update"

Also check `postings/journal/` — if journal files exist for active companies, mention them so the user knows context is available ("Journal available: postings/journal/google.md").
