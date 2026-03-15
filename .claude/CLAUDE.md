# CareerForge — Project Instructions

## Soul

_CareerForge represents a real person's career. Accuracy is non-negotiable. See `SOUL.md` for the full philosophical foundation._

## Project Context

This is a multi-agent job search system for a single candidate. Nine specialized agents work from a shared knowledge base to cover the full job search lifecycle.

## Directory Layout

- `knowledge_base/` — The candidate's structured profile and raw source materials. This is the single source of truth. **Fully gitignored — all contents stay local.**
  - `candidate_profile.yaml` — Structured data: skills, roles, achievements, certifications, publications, awards, projects
  - `candidate_narrative.md` — Long-form narrative version of the candidate's background for LLM consumption
  - `source_index.md` — Provenance log mapping every KB fact to its source document
  - `sources/` — Raw input materials (resumes, transcripts, articles, etc.)
  - `archive/` — Retired KB data (performance reviews, peer feedback). Gitignored; not loaded by any agent.
- `config/preferences.yaml` — Job search hard filters and soft preferences (location, comp, role type, etc.)
- `config/resume_style.yaml` — Resume formatting preferences
- `config/search_scopes.yaml` — LinkedIn search scope definitions (committed)
- `templates/` — Copy-me starter templates (all committed):
  - `candidate_profile.template.yaml` — Template for candidate data
  - `candidate_narrative.template.md` — Template for candidate narrative
  - `preferences.template.yaml` — Template for job search preferences
  - `tracker.template.yaml` — Application tracker schema and status enum
- `postings/` — Job postings under consideration, organized as `postings/[company_role]/job_description.md`. Transient inputs, not part of the candidate's permanent profile.
  - `tracker.yaml` — Application lifecycle tracker (status, history, notes for each posting)
- `output/` — All generated deliverables, organized by type
- `scripts/generate_docx.js` — Node.js helper for .docx generation using docx-js
- `scripts/linkedin/` — Orchestration scripts: init_db, map_preferences, sync, pre_filter, export_for_scoring, update_scores, report.
  _Scripts add `scripts/` to `sys.path` and import as `from linkedin.X import Y`. The `tools/` directory is added separately; import as `from linkedin_job_search.X import Y`._
- `tools/` — LinkedIn Guest API client library (`linkedin_job_search/` package)
- `data/` — Local SQLite database (`jobs.db`, gitignored)
- `docs/` — Reference documentation (e.g., `linkedin-scanner.md`, `profile_schema.md`)

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code and data.
- **No Laziness**: Find root causes. No temporary fixes or workarounds.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid side effects.

## Global Rules

1. **Always read the knowledge base before generating any deliverable.** Never fabricate achievements, skills, or experiences. Every claim must trace to the KB files (`candidate_profile.yaml` and `candidate_narrative.md`). Use `candidate_profile.yaml` when you need structured data (skills, achievements, certifications). Use `candidate_narrative.md` when you need narrative context.

2. **Never overwrite existing outputs without confirmation.** Use timestamped or descriptive filenames (e.g., `resume_stripe_sr_ml_engineer_2026-02-13.docx`).

3. **Log every action.** When ingesting sources, updating the KB, or generating deliverables, append a log entry to the relevant index or output folder.

4. **Prefer structured data for querying, narrative for generation.** Use `candidate_profile.yaml` when you need to match skills/keywords. Use `candidate_narrative.md` when you need to write compelling prose about the candidate's experience.

5. **Respect the preferences config.** The `config/preferences.yaml` file defines the candidate's hard constraints (e.g., "remote only", "minimum $200k") and soft preferences (e.g., "prefers ML/AI roles"). The scorer agent must respect hard constraints as absolute filters. Resume and cover letter agents should weight soft preferences.

6. **Use web search for company context.** When writing cover letters or scoring job fit, search for recent company news, mission statements, and culture signals. Cite what you find.

7. **Output .docx for resumes and cover letters.** Use the `scripts/generate_docx.js` helper or the `docx` npm package via bash. Never output resumes as plain text or markdown — they must be properly formatted Word documents.

8. **Use the XYZ achievement formula.** When writing, extracting, or evaluating achievements, follow the pattern: "Accomplished [X] as measured by [Y], by doing [Z]." This maps directly to the achievement schema fields: `description` = X (what was accomplished), `metrics` = Y (how success was measured), `impact` = Z (what actions were taken). All agents should apply this formula when writing achievement bullets, extracting achievements from sources, or evaluating candidate-job fit. For leadership achievements, always include team size and scope of responsibility.

9. **Maintain full source traceability.** Every piece of data in the knowledge base — achievements, skills, endorsements, ratings, quotes — must include a `source` field tracing it back to the originating document. This applies to all agents that write to the KB, not just the KB Builder. When consuming KB data to generate deliverables, agents should be able to answer "where did this claim come from?" for any fact they use. If a source cannot be identified, flag the data point as `"source": "unverified"` rather than omitting the field. This is a foundational integrity requirement: the KB is only as trustworthy as its provenance chain.

10. **Keep the application tracker current.** When a user saves a new job posting, applies, receives a status update, or withdraws from a role, update `postings/tracker.yaml` accordingly. Each status change must append a new entry to the application's `history` list with the date and (optionally) a note. Valid statuses: `saved`, `applying`, `applied`, `interviewing`, `offered`, `accepted`, `rejected`, `withdrawn`, `closed`. When listing or summarizing applications, read from this file. See `templates/tracker.template.yaml` for the full schema.

11. **Delegate multi-step deliverables to named subagents.** For resumes, cover letters, interview prep, KB ingestion, and job scanning, delegate to the appropriate named subagent. Do not handle these workflows inline.

12. **Capture lessons after corrections.** After any user correction, save a `feedback` memory. Write it as a rule that prevents the same mistake — not a description of what happened. This is how the system learns across sessions.

13. **Verify before marking complete.** Never consider a task done without proving it works. For YAML edits: confirm it parses. For .docx: confirm the file exists and is non-zero. For scripts: confirm they run. Ask: "Would the user be satisfied if they saw this now?"
