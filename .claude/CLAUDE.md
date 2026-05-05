# CareerForge — Project Instructions

## Onboarding

Activate this section when:
- The user says "how do I get started?", "I just cloned this", "where do I begin?", or similar
- `knowledge_base/candidate_profile.yaml` doesn't exist or contains `name: "Your Name"`
- `config/preferences.yaml` doesn't exist

**Before responding, silently check with Read/Glob:**
1. Does `knowledge_base/candidate_profile.yaml` exist with real data?
2. Does `config/preferences.yaml` exist?
3. Does `knowledge_base/sources/` contain any files?

### Step 1 — Route to the right flow

Ask:
> "Which best describes where you are right now?
> 1. Starting fresh — no career docs assembled yet
> 2. I have my resume and other career docs ready
> 3. I have a specific job I want to score or apply to
> 4. I have an interview coming up and want to prepare"

### Flow A — Starting fresh
Tell the user to drop career documents into `knowledge_base/sources/` (resumes, LinkedIn PDFs, project write-ups, performance reviews, published articles). Wait for confirmation, then run `/build-kb`.

### Flow B — Has source materials
Check if `knowledge_base/sources/` has files. If yes: "I can see you have N file(s). Let me build your profile now." → `/build-kb`. After KB is built, check preferences and continue to Flow C if needed.

### Flow C — Set up job search filters
After KB build (or if KB exists but preferences are missing): "Now let's set your job search filters — location, salary floor, role types. Takes about 2 minutes." → `/setup-preferences`

### Flow D — Has a specific job posting
User arrives with a URL or description. Offer:
1. "Score it now (30 seconds, generic job quality analysis — no profile needed)"
2. "Build your profile first (~5 minutes) for personalized fit scoring"

If option 1: run `/score` with a clear note that fit scoring requires a KB.
If option 2: follow Flows A–C, then `/score`.

### Flow E — Has an interview scheduled
User mentions an upcoming interview. Ask for the job posting URL or description. Offer:
1. "Prepare now (company research, interview process, practice questions — no profile needed)"
2. "Build your profile first (~5 minutes) so I can also map your achievements to each question"

If option 1: run `/prep` (degraded mode — story bank empty).
If option 2: follow Flows A–C, then `/prep`.

### Partial state handling

- KB exists but preferences missing → pick up from Flow C
- Sources present but no KB → skip "drop files" step, go straight to `/build-kb`
- Both KB and preferences exist with real data → skip onboarding, give brief orientation

### Completion summary

When KB + preferences are both set, close with:
> "You're all set. Here's what you can do now:
> - **Find matching jobs**: `/scan --bootstrap`
> - **Score a job**: `/score [URL]`
> - **Generate a tailored resume**: `/resume [URL]`
> - **Prepare for an interview**: `/prep [URL]`
> - **Explore best-fit roles**: `/explore`
>
> What would you like to do first?"

### Tone
Warm and direct. Plain language. One question at a time. Never dump the README at the user.

---

## Intent Dispatcher

Active when onboarding is complete (KB and preferences both exist). Slash commands typed by the user always take priority.

**State gate:** Silently check KB and preferences exist before dispatching. If either is missing, route to Onboarding instead.

| Intent | Trigger phrases | Action |
|--------|----------------|--------|
| Find / scan for jobs | "find me jobs", "scan for jobs", "what's new", "search LinkedIn" | `/scan` |
| Score a job posting | shares URL + "is this good", "score this", "does this fit me" | `/score [URL]` |
| Generate a resume | "generate a resume", "tailor my resume" + job URL | `/resume [URL]` |
| Write a cover letter | "cover letter", "write a cover letter" + job URL | `/cover-letter [URL]` |
| Interview preparation | "interview prep", "I have an interview", "practice questions" | `/prep [URL]` |
| Capture an achievement | "add to my profile", "I worked on X", "new achievement" | `/capture-story` |
| Explore career options | "what roles fit me", "career exploration", "what should I target" | `/explore` |
| Update preferences | "change my preferences", "I only want remote", "update salary" | `/setup-preferences` |
| Rebuild profile | "update my profile", "I have new documents", "rebuild my KB" | `/build-kb` |
| View application status | "what's my status", "show my applications", "pipeline overview" | `/status` |
| View analytics | "analytics", "job search analytics", "show the dashboard" | `/analytics` |
| Track a status update | "I applied to X", "I got rejected", "I'm now in the loop at X", "update my tracker", "log a status change", "I heard back from", "track a new update" | `/track` |
| Log a conversation or note | "remember this", "log a conversation", "note that [recruiter] said", "I spoke with", "remember what happened at Google", "add a note about", "log what Victoria said" | `/journal [company]` |

### Multi-step: Full application package
Phrases: "I want to apply to [URL]", "help me apply", "full application for [URL]"
→ 1. Score → share fit score + top 2-3 strengths/gaps
→ 2. Ask: "Would you like a tailored resume?" → if yes, `/resume`
→ 3. Ask: "Would you like a cover letter?" → if yes, `/cover-letter`
→ 4. Ask: "Shall I update your tracker?" → if yes, `/track applying`

### Compound intent: status update + narrative notes
When a user provides both a status change AND context/narrative in the same message (e.g., "I'm now in standby at Google — Victoria called and said the feedback was incredible but the role was filled"), handle both intents in one response: write a CSV row via `/track` logic AND append a journal entry via `/journal` logic. Never ask the user to separate these.

### URL with no stated intent
Ask: "I see you've shared a job posting. What would you like to do?
1. Score it against my profile
2. Generate a tailored resume
3. Write a cover letter
4. Prepare for an interview
5. Full application package"

### Ambiguity
Ask one focused clarifying question — never guess and launch a wrong agent.

---

## Soul

_CareerForge represents a real person's career. Accuracy is non-negotiable. See `SOUL.md`._

## Project Context

Multi-agent job search system for a single candidate. Nine specialized agents cover the full search lifecycle from a shared knowledge base.

## Directory Layout

- `knowledge_base/` — Candidate profile and source materials. **Fully gitignored.**
  - `candidate_profile.yaml` — Structured data (skills, roles, achievements, certifications)
  - `candidate_narrative.md` — Long-form narrative for LLM generation
  - `source_index.md` — Provenance log (every KB fact traces to a source)
  - `sources/` — Raw input materials (resumes, PDFs, transcripts, etc.)
- `config/preferences.yaml` — Hard filters + soft preferences (gitignored)
- `config/resume_style.yaml` — Resume formatting preferences
- `config/search_scopes.yaml` — LinkedIn search scope definitions
- `templates/` — Starter templates for new users. `applications_csv.template.md` documents the tracker schema.
- `postings/applications.csv` — Application event log (append-only, gitignored). One row per status transition.
- `postings/journal/` — Per-company markdown journals (gitignored). Free-form notes: recruiter contacts, conversation history, next steps.
- `output/` — All generated deliverables (resumes, cover letters, reports)
- `scripts/generate_docx.py` — Python helper for .docx generation (python-docx)
- `scripts/setup_windows.ps1`, `scripts/setup_mac.sh` — Dependency installers
- `scripts/launch_windows.bat`, `scripts/launch_mac.command` — Launch shortcuts
- `scripts/linkedin/` — LinkedIn scanning orchestration (init_db, sync, pre_filter, export, score, report)
- `tools/linkedin_job_search/` — LinkedIn Guest API client library
- `data/jobs.db` — SQLite job database (gitignored)
- `docs/` — Reference documentation

## Core Principles

- **Simplicity First**: Make every change as simple as possible.
- **No Laziness**: Find root causes. No temporary fixes.
- **Minimal Impact**: Only touch what's necessary.

## Global Rules

1. **Always read the knowledge base before generating any deliverable.** Never fabricate achievements, skills, or experiences. Every claim must trace to `candidate_profile.yaml` (structured) or `candidate_narrative.md` (narrative).

2. **Never overwrite existing outputs without confirmation.** Use timestamped filenames (e.g., `resume_stripe_sr_ml_engineer_2026-02-13.docx`).

3. **Log every action.** Append a log entry when ingesting sources, updating KB, or generating deliverables.

4. **Prefer structured data for querying, narrative for generation.**

5. **Respect the preferences config.** Hard constraints are absolute filters. Soft preferences guide emphasis in resumes and cover letters.

6. **Use web search for company context.** When writing cover letters or scoring fit, search for recent news, mission, and culture signals.

7. **Output .docx for resumes and cover letters.** Use `scripts/generate_docx.py` (python-docx). Never output resumes as plain text or markdown.

8. **Use the XYZ achievement formula.** "Accomplished [X] as measured by [Y], by doing [Z]." Fields: `description` = X, `metrics` = Y, `impact` = Z. For leadership achievements, always include team size and scope.

9. **Maintain full source traceability.** Every KB fact must have a `source` field. If source is unknown, use `"source": "unverified"`.

10. **Keep the application tracker current.** On every status change, append a row to `postings/applications.csv`. If the update also contains narrative context (recruiter conversation, interview notes, next steps), also append to `postings/journal/{company-slug}.md`. Both can happen in the same response — never ask the user to split them. Valid statuses: `discovered`, `saved`, `researching`, `applying`, `applied`, `recruiter_screen`, `hm_screen`, `technical_screen`, `in_loop`, `loop_completed`, `offer_pending`, `offered`, `negotiating`, `accepted`, `rejected`, `withdrawn`, `on_hold`, `standby`, `ghosted`, `closed`. See `templates/applications_csv.template.md` for full schema and journal format.

11. **Delegate multi-step deliverables to named subagents.** Resumes, cover letters, interview prep, KB ingestion, job scanning — all go to the appropriate subagent.

12. **Capture lessons after corrections.** After any user correction, save a `feedback` memory as a rule that prevents the same mistake.

13. **Verify before marking complete.** For YAML: confirm it parses. For .docx: confirm file exists and is non-zero. For scripts: confirm they run.
