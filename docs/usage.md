## Technical Reference

### Get Started (detailed walkthrough)

### Step 1 — Build your knowledge base

Drop everything you have about your career into `knowledge_base/sources/`. CareerForge accepts multimodal inputs — the more you provide, the richer your profile:

- Resumes and CVs (PDF, DOCX)
- Mind maps and career diagrams (images)
- Project screenshots and architecture diagrams
- Performance reviews or recommendation letters
- Conference talk slides or transcripts
- Published articles or blog posts
- Portfolio pieces and project write-ups

Then build your profile:

```bash
/build-kb
```

This generates `candidate_profile.yaml` (structured data) and `candidate_narrative.md` (prose version) — the foundation that all other agents read from.

### Step 2 — Configure your preferences

Set your hard constraints (location, compensation, role type) and soft preferences so every agent filters and tailors for you automatically:

```bash
/setup-preferences
```

Interactive mode walks through each section. Or pass a description directly: `/setup-preferences remote only, at least $250k, AI/ML roles`.

### Step 3 — Run your first scan

Fetch jobs across your configured search scopes, filter out noise, and get a ranked report of your best matches:

```bash
/scan --bootstrap
```

Use `--bootstrap` on the first run to pull the past month of data. From here, set up a daily cron ("Create a daily cron at 8 AM that runs /scan") for fully automated daily discovery.

From this point, the [Slash Commands](#slash-commands) and [Usage](#usage) sections cover everything else — resumes, cover letters, interview prep, and more.

## Configuration

### Job Search Preferences (`config/preferences.yaml`)

Edit this file to define your hard filters and soft preferences. The scorer agent reads this to score postings.

### Resume Style (`config/resume_style.yaml`)

Controls formatting preferences — fonts, section ordering, page length targets.

## Usage

### KB Builder

Ingests source materials (resumes, transcripts, articles) and builds the structured candidate profile.

```bash
claude "Use the kb-builder agent to ingest all sources in knowledge_base/sources/ and build my candidate profile."
```

Output: `knowledge_base/candidate_profile.yaml`, `knowledge_base/candidate_narrative.md`, `knowledge_base/source_index.md`

### Preferences Setup

Configures your job search preferences in `config/preferences.yaml` — the filters that every other agent reads to score, filter, and tailor for you.

```bash
# Guided interview mode — walks through each section conversationally
/setup-preferences

# Text extraction mode — paste a description of your preferences
/setup-preferences remote only, at least $250k, AI/ML roles at big tech or AI startups
```

Runs in two modes:
- **Interview mode** (no arguments): asks about each section one at a time, shows current values, and collects updates
- **Text extraction mode** (with arguments): parses your free-form description and maps it to the schema, then asks for confirmation

Output: Updated `config/preferences.yaml`

### Story Capture

Extracts achievements via guided interview or from transcripts. Uses the XYZ formula: Accomplished [X] as measured by [Y], by doing [Z].

```bash
# Interactive guided interview
claude "Use the story-capture agent to capture a new project story."

# From a transcript
claude "Use the story-capture agent to extract achievements from this transcript: [paste text]"
```

Output: Written directly to knowledge base files.

### Resume Writer

Generates tailored .docx resumes matched to a specific job posting.

```bash
claude "Use the resume-writer agent to create a resume tailored to this job posting: [paste URL or description]"
```

Output: `output/resumes/`

### Cover Letter

Generates tailored .docx cover letters with company research.

```bash
claude "Use the cover-letter agent to write a cover letter for this posting: [paste URL or description]"
```

Output: `output/cover_letters/`

### Scorer

Scores and filters job postings against your profile and preferences. Respects hard constraints from `config/preferences.yaml`.

```bash
# Single posting
claude "Use the scorer agent to score this job posting against my profile: [paste URL]"

# Batch — drop multiple postings into a folder
claude "Use the scorer agent to score all postings in ./input_postings/ and produce a ranked report."
```

Output: `output/lead_reports/`

### Interview Prep

Generates interview preparation guides with company research, predicted questions, and talking points.

```bash
# From a job posting URL
claude "Use the interview-prep agent to prepare interview questions for this posting: [paste URL]"

# From a saved posting file
claude "Use the interview-prep agent to prepare for the interview at postings/company_role_name/"
```

Output: `output/interview_prep/`. Company research is saved to `postings/[company_role]/company_research.md` for reuse by other agents.

### Career Explorer

Analyzes your profile and generates a research report of best-fit roles in the current job market — with real job posting examples, compensation estimates, and work-life balance data.

```bash
claude "Use the career-explorer agent to discover what roles I'm best suited for in today's market."
```

Output: `output/career_exploration/`

### LinkedIn Job Scanner

Runs a proactive daily pipeline: fetches jobs from LinkedIn across your configured search scopes, deduplicates in a local SQLite database, hard-filters with rule-based constraints (no LLM), LLM-scores shortlisted jobs against your profile, and generates a ranked report.

```bash
# Full pipeline (sync → filter → score → report)
/scan

# First run — fetch past month of data
/scan --bootstrap

# Test a single scope
/scan --scope ai_architect_remote
```

Configure search scopes in `config/search_scopes.yaml`. Set up a daily cron (ask Claude Code to "create a daily cron at 8 AM that runs /scan") for fully automated discovery.

Output: `output/lead_reports/linkedin_scan_YYYY-MM-DD.md`

See `docs/linkedin-scanner.md` for the full reference (scope schema, script CLI flags, calibration guide, troubleshooting).

### Utilities / Scripts

#### `convert_md_to_pdf.js` — Markdown to PDF

Converts `.md` files to PDF for mobile reading. PDFs are written alongside the originals; source files are never modified.

```bash
# Convert all .md files in a directory
node scripts/convert_md_to_pdf.js output/interview_prep/Google_PrincipalArchitectIV_2026-03-05/

# Convert a single file
node scripts/convert_md_to_pdf.js output/interview_prep/Google_PrincipalArchitectIV_2026-03-05/00_interview_process.md

# Recurse into subdirectories
node scripts/convert_md_to_pdf.js output/interview_prep/ --recursive
```

Or via npm: `npm run convert -- <path>`

Tables, blockquotes, and code blocks render with full CSS styling via headless Chromium (Puppeteer).

#### `analytics.py` — LinkedIn Pipeline Analytics

Generates an interactive HTML analytics dashboard from the jobs database with zero extra dependencies (uses Chart.js from CDN).

```bash
/analytics
# or directly:
python scripts/linkedin/analytics.py
```

Output: `output/analytics/analytics_YYYY-MM-DD.html` — open in any browser. Charts include score distribution, scope performance, tier breakdown, and top filter reasons.

### Application Tracker

Track the lifecycle of every application in `postings/tracker.yaml`. Claude Code reads and updates this file automatically when you mention application status changes.

```bash
# Add a new application
claude "I just saved a posting for Stripe Senior Engineer — add it to my tracker"

# Update status
claude "I submitted my application to Stripe"
claude "I got a phone screen scheduled with Google"
claude "I'm withdrawing from the Acme role"

# Review your pipeline
claude "List all my active applications"
claude "Show me everything in interviewing status"
```

The tracker uses a simple YAML format. See `templates/tracker.template.yaml` for the full schema and status values.

### Using the Postings Directory

Store job postings you're actively considering in the `postings/` directory. Each posting gets its own subfolder:

```
postings/company_sr_engineer/job_description.md
postings/startup_ml_lead/job_description.pdf
```

All agents (resume-writer, cover-letter, scorer, interview-prep) can read from these folders. The interview-prep and cover-letter agents also write `company_research.md` into the subfolder for shared reuse.

---
