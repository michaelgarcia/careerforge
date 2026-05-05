# CareerForge — Application Tracker Reference

Application tracking uses two complementary files:

- **`postings/applications.csv`** — structured event log (one row per status transition, gitignored)
- **`postings/journal/{company-slug}.md`** — free-form narrative notes per company (gitignored)

---

## CSV Schema

```
event_id, timestamp, slug, company, title, job_url, status, previous_status, note, output_files
```

| Field | Type | Description |
|-------|------|-------------|
| `event_id` | integer | Auto-incrementing. Read last row to determine next ID. |
| `timestamp` | ISO 8601 | `YYYY-MM-DDTHH:MM:SS`. Use current datetime. |
| `slug` | string | Unique application identifier. Use `{company}-{role-short}` in kebab-case. Matches `postings/` subfolder name where it exists. |
| `company` | string | Company name (display form, e.g. "Google") |
| `title` | string | Job title as listed in the posting |
| `job_url` | string | Link to the original posting (optional) |
| `status` | enum | New status (see enum below) |
| `previous_status` | enum | Prior status — read the last row for this slug to populate |
| `note` | string | Free-text transition context. Quote if it contains commas. |
| `output_files` | string | Comma-separated paths to generated files (e.g., `output/resumes/resume_google_2026-05-04.docx`) |

**The CSV is append-only. Never edit or delete existing rows.**

---

## Status Enum

```
discovered       — Job surfaced (scanner or manual), not yet evaluated
saved            — Bookmarked for later review
researching      — Actively evaluating fit; generating score/resume/prep
applying         — Application materials being prepared
applied          — Application submitted; awaiting response
recruiter_screen — Phone/video screen with recruiter
hm_screen        — Hiring manager introductory screen
technical_screen — Technical phone/video screen (pre-loop)
in_loop          — Active full interview loop (onsite or virtual)
loop_completed   — Loop finished; awaiting decision
offer_pending    — Verbal offer extended; written offer in progress
offered          — Written offer received
negotiating      — Negotiating terms/comp
accepted         — Offer accepted; start date confirmed
rejected         — Rejected at any stage (capture which stage in note field)
withdrawn        — Candidate withdrew
on_hold          — Position paused by company; candidate still in consideration
standby          — In company's pipeline; no active role right now
ghosted          — No response after application or follow-up(s)
closed           — Position filled before or without application
```

Analytics-meaningful groupings:
- **Active**: `recruiter_screen` → `loop_completed`
- **Terminal / positive**: `accepted`
- **Terminal / negative**: `rejected`, `withdrawn`, `ghosted`, `closed`
- **Holding**: `on_hold`, `standby`
- **Pre-application**: `discovered`, `saved`, `researching`, `applying`, `applied`

---

## Journal Format

`postings/journal/{company-slug}.md`:

```markdown
# {Company Name} — Application Journal

## Active Applications
- **{Role Title}** — Status: `{status}` (last updated: YYYY-MM-DD)

## Contacts
- **{Name}** — {Role}, {Company} | {email or LinkedIn}

## Log

### YYYY-MM-DD
{Free-form narrative: who was spoken to, what was said, key outcomes, next steps, links to output files.}
```

---

## Analytics

Run `python scripts/application_analytics.py` to generate an HTML dashboard at `output/analytics/application_pipeline_YYYY-MM-DD.html`.

The dashboard shows:
- Active pipeline with days-in-status (rows in amber = stale, 14+ days)
- Status distribution chart
- Stage velocity (average days per stage)
- Terminal outcome rates
