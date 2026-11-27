# Using CareerForge

Talk to CareerForge in plain language. You never need to know a command or agent name: describe what's going on and it picks the right workflow. Each section below shows things you can say, plus the optional slash-command shortcut in parentheses for when you already know what you want.

When you open a session, CareerForge checks your workspace (sources, profile, preferences, active applications) and opens with where things stand. Say "hi" or "help" any time to see that again.

---

## 1. Set up

### First run

> "Set up CareerForge" (`/setup`)

The first session offers this on its own: it creates your private `user_data/` folder with starter settings and installs the Python packages. Everything personal lives in `user_data/`, and nothing in it is ever part of the code (see [Your data and updates](#your-data-and-updates)).

### Build your profile

Drop everything you have about your career into `user_data/knowledge_base/sources/`: resumes and CVs, LinkedIn exports, performance reviews, project write-ups, talk slides or transcripts, published articles, certifications. PDF, DOCX, Markdown, text and images all work. The more you provide, the richer your profile.

> "Build my profile" · "I added new files, update my profile" (`/build-kb`)
>
> In a hurry? "Build my profile from just my resume first" (`/build-kb quick`), and add the rest later.

This writes `user_data/knowledge_base/candidate_profile.yaml` (structured evidence; schema in `docs/profile_schema.md`), `candidate_narrative.md` (your career in prose), and a provenance log that traces every fact to a source file. Re-running only processes new or changed files.

### Set your job search filters

> "Set up my job filters" · "Remote only, at least $250k, AI/ML roles" (`/setup-preferences`)

With no details, it interviews you one question at a time. With a description, it extracts the settings and asks you to confirm. Hard constraints (location, comp floor, sponsorship, dealbreakers) filter postings out; soft preferences shape emphasis and scoring.

### Define your north star (optional, recommended)

> "What's my positioning?" · "Where am I headed?" (`/north-star`)

Reads your profile, proposes a reading of your career, and interviews you to sharpen it into a positioning statement, ranked role lenses, a not-targeted list and a forward trajectory. Every resume, cover letter and score uses it for framing. It never supplies facts.

---

## 2. Keep your profile healthy

> "Is my profile up to date?" · "What's missing from my KB?" (`/kb-check`)

A read-only check: source files not yet processed, provenance problems, achievements missing metrics, and files older than your profile. It ends with one recommended next step.

> "I worked on a migration project last year, add it to my profile" · paste a voice-memo transcript (`/capture-story`)

An interview (or extraction from your text) that turns a story into XYZ achievements: *accomplished X, as measured by Y, by doing Z*. It pushes for real numbers and never invents them. The story is saved under `user_data/knowledge_base/sources/Stories/` so every achievement traces to a file.

---

## 3. Evaluate and apply

> "Is this a good fit? [URL or pasted posting]" · "Should I apply?" · "Compare these three roles" (`/score`)

Scores the posting with one rubric (skills 30%, experience 20%, preferences 20%, domain, growth and company quality 10% each), checks every minimum qualification against your profile, and flags roles on your not-targeted list. Works without a profile as a job-quality analysis.

> "Tailor my resume for this posting" (`/resume`) · "Write a cover letter for it" (`/cover-letter`)

Both produce `.docx` and `.pdf`, grounded only in your profile. The resume picks the variant from your north star, aligns the summary and skills to the posting, and keeps your achievement wording as it is in your profile. Both report gaps honestly.

> "I want to apply to [URL]"

The full application: score → resume → cover letter → log it in your tracker, offered one step at a time.

Pasting a posting with no instructions gets one question with these options. If the role is one you're already interviewing for, it offers interview prep instead.

---

## 4. Interviews

> "I have an interview at Acme on Tuesday" · "Prep me for my loop" (`/prep`)

Logs the stage, researches the company (or reuses research under 30 days old), and maps out the interview process. It uses what you've told it in your journal, such as round order and interviewer names and roles, ahead of public research. It then prepares each round in parallel (likely questions, with answer angles drawn from your real stories), builds a story bank, and lists the gaps worth filling before the day.

> "Research Globex" · "What do you know about Globex?" (`/research-company`)

Mission, recent news, products, culture and engineering practice, saved to `user_data/postings/<slug>/company_research.md` so resumes, cover letters and prep reuse it. It checks your own notes first.

> "The recruiter said the loop has four rounds, the last with the VP" (`/journal`)

A dated note in `user_data/postings/journal/<company>.md`. Prep reads it.

---

## 5. Offers

> "They made me an offer, is it any good?" · "How should I negotiate?"

Logs the offer, researches compensation for the role and location (`/prep <posting> comp`), and journals the details and deadlines. If it doesn't know the company or the numbers, it asks for both in one question.

---

## 6. Find jobs

> "Find me jobs" · "What's new?" (`/scan`, first run: `/scan --bootstrap`)

Syncs your LinkedIn search scopes (`user_data/config/search_scopes.yaml`), filters on your hard constraints without any LLM cost, scores the shortlist with the shared rubric, and writes `user_data/output/lead_reports/linkedin_scan_<date>.md` plus a dashboard. To make it daily, ask: "Create a daily task at 8 AM that runs my job scan." Full reference: `docs/linkedin-scanner.md`.

> "Any new openings at Anthropic?" · "Scan my target companies" (`/scan-companies`)

Watches the career pages in `user_data/config/company_targets.yaml` (copy `templates/company_targets.template.yaml` to start) and keeps one Excel tracker per company, filtered by the `company_scanner` criteria in your preferences. Reference: `docs/company-scanner.md`.

> "Show the dashboard" (`/analytics`)

An interactive HTML report of the LinkedIn pipeline: score distribution, scope performance, tiers and filter reasons.

---

## 7. Track applications

> "I applied to Stripe" · "Recruiter screen with Google on Friday" · "I'm in standby at Acme, the recruiter said the role was filled" (`/track`)

Each status change is one appended row in `user_data/postings/applications.csv`. Anything narrative (who said what, next steps) also goes into the company journal, in the same step. Statuses and schema: `.claude/reference/tracker-schema.md`.

> "What's my status?" · "What should I follow up on?" (`/status`)

Active applications by stage, days since the last change (flagged at 14+), outcomes, and a next action for each.

---

## 8. Explore your options

> "What roles fit me?" · "What should I target?" (`/explore`)

A research report of 5–8 role categories that fit your profile, starting from your north star's lenses: real example postings, compensation ranges and work-life balance data, with every fit claim tied to your profile.

---

## Your data and updates

> "Update CareerForge" · "Is there a new version?" (`/update`)

- **One folder is yours: `user_data/`.** It holds your documents, profile, preferences, postings, tracker, generated files and the jobs database. It's gitignored and contains no repo files, so updates never change it. Everything else in the folder is the product.
- **Every update backs it up first**, to `~/CareerForge-backups/careerforge_<date>.zip` (the newest 3 are kept; the log is `update_log.txt` there). Then it shows what's new and any **Action needed** notes from `CHANGELOG.md`, and fast-forwards with `git merge --ff-only --no-overwrite-ignore`, which stops rather than write over a file of yours.
- **Restore:** unzip a backup into the CareerForge folder; it recreates `user_data/` as it was. Run `python scripts/backup_workspace.py` any time for an extra backup.
- **Older installs** (before November 2026) kept data in top-level `knowledge_base/`, `config/`, `postings/`, `output/` and `data/`. The first session after updating copies it into `user_data/` with `scripts/migrate_to_user_data.py` (copy only, verified by checksum) and leaves the old folders for you to delete.
- **Don't** delete the folder and clone it again to fix something: that deletes `user_data/` too.

## Where things go

| What | Where |
|---|---|
| Your documents | `user_data/knowledge_base/sources/` |
| Postings and company research | `user_data/postings/<slug>/` (the slug is `company-role`, e.g. `acme-staff-engineer`) |
| Tracker and journals | `user_data/postings/applications.csv`, `user_data/postings/journal/<company>.md` |
| Resumes, cover letters | `user_data/output/resumes/<slug>_resume_<date>.docx`, `user_data/output/cover_letters/<slug>_cover_letter_<date>.docx` |
| Interview prep | `user_data/output/interview_prep/<slug>_<date>/` |
| Scores and scan reports | `user_data/output/lead_reports/` |
| Scratch files | `user_data/output/.work/` |

Nothing is ever overwritten: a second file on the same day gets `_2`. Everything above is gitignored. Full rules: `.claude/reference/output-naming.md`.

## Configuration

| File | What it controls |
|---|---|
| `user_data/config/preferences.yaml` | Hard constraints, soft preferences, LinkedIn settings (including `geo_ids` for cities), and the `company_scanner` criteria. Start from `templates/preferences.template.yaml`, or just say "set up my job filters". |
| `user_data/config/search_scopes.yaml` | LinkedIn search scopes. Template: `templates/search_scopes.template.yaml`. |
| `user_data/config/company_targets.yaml` | Company career pages to watch. Template: `templates/company_targets.template.yaml`. |
| `user_data/config/resume_style.yaml` | Optional: your own resume fonts, section order, page length, bullets per role. Without it, `templates/resume_style.yaml` is used; copy that file here to customize. |
| `user_data/knowledge_base/memories/` | Your own short rules every deliverable follows: wording, names that must never appear, claims that need extra care. Format: `templates/memory.template.md`. |

## Utilities

```bash
# Markdown to PDF (e.g. interview prep for reading on a phone); PDFs are written next to the originals
python scripts/convert_md_to_pdf.py user_data/output/interview_prep/acme-staff-engineer_2026-03-05/
python scripts/convert_md_to_pdf.py user_data/output/interview_prep/ --recursive

# Word to PDF (Windows, needs Microsoft Word); resumes and cover letters do this automatically
python scripts/convert_docx_to_pdf.py --input user_data/output/resumes/acme-sre_resume_2026-03-15.docx

# LinkedIn pipeline dashboard
python scripts/linkedin/analytics.py
```

## How it's built

- **Skills** (`.claude/skills/<name>/SKILL.md`) are the entry points: one per workflow, matched to what you say by their descriptions. The interview-style ones (capture-story, north-star, setup-preferences) and the `prep` coordinator run in your conversation; the rest hand the work to a specialized agent.
- **Setup and updates:** the `setup` skill creates `user_data/` and installs packages; the `update` skill backs up and updates safely. Scripts find `user_data/` through `scripts/paths.py`.
- **Agents** (`.claude/agents/`, 8 of them) do the heavy work in their own context: kb-builder, resume-writer, cover-letter, interview-prep, scorer, career-explorer, job-scanner, company-scanner.
- **Shared rules** (`.claude/reference/`) hold everything more than one agent needs (KB context, achievement format, scoring rubric, output naming, interview-prep formats, tracker schema). **Path rules** (`.claude/rules/`) load only when the tracker or KB is touched.
- **Startup check:** a SessionStart hook in `.claude/settings.json` summarizes the workspace state (including whether `user_data/` exists and the Python packages are installed) before your first message; the `start` skill turns that into the opening line.
- **Integrity:** `SOUL.md` (loaded with the project instructions) is the contract: every claim traces to your profile, and framing files never supply facts.
