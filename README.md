# CareerForge

Job searching manually is slow, inconsistent, and doesn't scale — you're rewriting resumes from scratch for each posting, manually scrolling LinkedIn every day, and walking into interviews underprepared.

CareerForge is a personal AI job search system powered by Claude Code. It automates the repetitive work across the full search lifecycle — from daily job discovery, to tailored applications in minutes, to walking into every interview prepared.

**Find roles worth pursuing.** The Career Explorer maps the current job market against your actual skills and experience, surfacing roles you're genuinely qualified for — including ones you might not have considered. The LinkedIn Job Scanner then runs daily across configurable search scopes, hard-filters out anything that fails your requirements (location, compensation, employment type), and LLM-scores the rest against your profile so only the strongest matches reach you.

**Apply in minutes, not hours.** Point the Resume Writer at any job posting and it generates a tailored `.docx` resume — achievements reordered, keywords matched, qualification gaps flagged — grounded entirely in your verified knowledge base. The Cover Letter agent does the same, adding company research it pulls fresh from the web.

**Walk into every interview prepared.** The Interview Prep agent researches the company, maps out the interview process and rounds, generates predicted questions per stage, and builds a personal story bank showing which of your own achievements best answers each question — all in one command.

---

## What can it do for you?

| I want to... | Use this |
|---|---|
| Build my profile from my resume | `/build-kb` |
| Configure my job search filters | `/setup-preferences` |
| Find jobs automatically every day | `/scan` |
| Score a specific job posting | `/score` |
| Generate a tailored resume | `/resume` |
| Write a tailored cover letter | `/cover-letter` |
| Prepare for an interview | `/prep` |
| Discover what roles I'm best suited for | `/explore` |
| View my application pipeline | `/status` |
| Generate a pipeline analytics report | `/analytics` |

---

## What it looks like in practice

![Analytics Demo](docs/analytics_demo.png)

*354 jobs collected across 5 search scopes → 287 hard-filtered by location/type → 67 LLM-scored → **6 top matches surfaced automatically***

---

## Why CareerForge?

**Discover** — Career Explorer maps roles you're qualified for. Daily LinkedIn scans across configurable search scopes bring fresh postings to you automatically.

**Filter** — Hard constraints (location, compensation, employment type) eliminate noise before any AI token is spent. You never see a role that fails your requirements.

**Apply** — Resume Writer and Cover Letter agents generate bespoke, fully-sourced documents matched to each posting. One command, minutes to a finished `.docx`.

**Prepare** — Interview Prep generates company research, per-round question guides, and a story bank tied to your own achievements — everything you need before you walk in.

---

## Key Features

1. **Accuracy-first deliverables** — Every achievement, skill, and metric in every resume and cover letter traces back to your source documents. Agents flag gaps honestly rather than fill them with fabrications.

2. **Automated daily discovery** — LinkedIn scanner queries configurable search scopes, deduplicates results in a local SQLite database, hard-filters with rule-based constraints, and LLM-scores shortlisted candidates against your profile.

3. **Hard constraints are hard** — Compensation floor, location, and role type are enforced as absolute filters. Postings that violate them are excluded outright — never just scored lower and buried in the list.

4. **Full interview prep in one command** — Company research, interview process, predicted questions per round, and your own story pointers — all generated together, with a story bank showing which of your achievements answers which questions.

5. **Your personal data never ends up in git** — All personal files (profile, narrative, preferences, source materials, generated outputs) are gitignored by default. `git add .` is always safe.

---

## High level overview and Architecture

![Analytics Demo](docs/CareerForge_Introduction.png)

---

## Install

### Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code/overview) installed and authenticated
- Node.js 18+ (for .docx generation via `docx-js`)
- `npm install -g docx`

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/michaelgarcia/careerforge.git
cd careerforge

# 2. Copy template files to create your personal configs
cp templates/candidate_profile.template.yaml knowledge_base/candidate_profile.yaml
cp templates/candidate_narrative.template.md knowledge_base/candidate_narrative.md
cp templates/preferences.template.yaml config/preferences.yaml
cp templates/tracker.template.yaml postings/tracker.yaml

# Optional: copy local Claude Code settings
cp .claude/settings.local.template.json .claude/settings.local.json

# 3. Edit the copied files with your personal data
#    - knowledge_base/candidate_profile.yaml  → your skills, experience, achievements
#    - knowledge_base/candidate_narrative.md   → your career narrative (or let KB Builder generate it)
#    - config/preferences.yaml                 → your job search filters (or run /setup-preferences to configure interactively)

# 4. Add source materials (resumes, transcripts, articles) to knowledge_base/sources/

# 5. Run the KB Builder to populate your knowledge base
claude "Use the kb-builder agent to ingest all sources in knowledge_base/sources/ and build my candidate profile."

# 6. Verify all agents are available
claude
# Then type: /agents
# You should see all nine agents listed
```

---

## Get Started

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

---

## Slash Commands

| Command | What it does |
|---------|-------------|
| `/build-kb` | Ingest all sources in `knowledge_base/sources/` and build your profile |
| `/setup-preferences [text or blank]` | Set up job search filters interactively or from free-form text |
| `/capture-story [transcript]` | Capture a new achievement (interactive if no args, extraction mode if you paste a transcript) |
| `/resume [URL or description]` | Generate a tailored resume for a job posting |
| `/cover-letter [URL or description]` | Generate a tailored cover letter for a job posting |
| `/score [URL or description]` | Score a job posting against your profile and preferences |
| `/prep [slug or URL]` | Run the full interview prep pipeline (defaults to latest "interviewing" application) |
| `/track [status update in plain English]` | Update the application tracker (e.g. "I submitted to Stripe") |
| `/status` | Overview of your job search pipeline, grouped by status |
| `/scan [--scope name] [--bootstrap]` | Run the LinkedIn job scanner: sync, filter, score, and report top opportunities |
| `/explore` | Discover best-fit roles from your profile across the current job market |
| `/analytics` | Generate an interactive HTML analytics dashboard from the jobs database |

Commands are defined in `.claude/commands/`. Add or modify them to customize your workflow.

---

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

## Project Structure

```
careerforge/
├── README.md                          # This file
├── .claude/
│   ├── CLAUDE.md                      # Project-wide persistent instructions
│   ├── settings.json                  # MCP servers, permissions
│   ├── settings.local.template.json   # Template for local settings
│   ├── agents/
│   │   ├── kb-builder.md              # Agent #1 — Knowledge Base Builder
│   │   ├── story-capture.md           # Agent #2 — Story Capture & Achievement Extraction
│   │   ├── preferences-setup.md       # Agent — Preferences Setup
│   │   ├── resume-writer.md           # Agent #3 — Resume Writer
│   │   ├── cover-letter.md            # Agent #4 — Cover Letter & Application
│   │   ├── scorer.md                  # Agent #5 — Scorer
│   │   ├── interview-prep.md          # Agent #6 — Interview Preparation
│   │   ├── career-explorer.md         # Agent #7 — Career Explorer
│   │   └── job-scanner.md             # Agent #8 — Proactive LinkedIn Job Scanner
│   └── commands/
│       ├── build-kb.md                # /build-kb  — Ingest sources & build profile
│       ├── setup-preferences.md       # /setup-preferences — Configure job search filters
│       ├── capture-story.md           # /capture-story — Capture an achievement
│       ├── resume.md                  # /resume    — Generate a tailored resume
│       ├── cover-letter.md            # /cover-letter — Generate a cover letter
│       ├── score.md                   # /score     — Score a job posting
│       ├── prep.md                    # /prep      — Full interview prep pipeline
│       ├── track.md                   # /track     — Update application tracker
│       ├── status.md                  # /status    — Job search pipeline overview
│       ├── scan.md                    # /scan      — Daily LinkedIn job scan
│       └── analytics.md               # /analytics — LinkedIn pipeline analytics dashboard
├── knowledge_base/                    # Fully gitignored — all contents stay local
│   ├── candidate_profile.yaml         # Your structured candidate data
│   ├── candidate_narrative.md         # Your narrative profile
│   ├── source_index.md                # Provenance log
│   └── sources/                       # Raw input materials
├── postings/                          # Job postings under consideration (gitignored)
│   ├── tracker.yaml                  # Your application tracker (gitignored)
│   └── [company_role]/
│       ├── job_description.md         # The full job posting (.md or .pdf)
│       └── company_research.md        # Auto-generated by agents
├── config/
│   ├── preferences.yaml               # Your preferences & hard filters (gitignored)
│   ├── resume_style.yaml              # Resume formatting preferences
│   └── search_scopes.yaml             # LinkedIn search scope configurations
├── data/
│   └── jobs.db                        # SQLite job database (gitignored, local only)
├── tools/
│   └── linkedin_job_search/           # LinkedIn Guest API client package
├── docs/
│   ├── analytics_demo.html            # Anonymized analytics demo
│   ├── analytics_demo.png             # Analytics screenshot (add after taking screenshot)
│   ├── linkedin-scanner.md            # LinkedIn scanner deep-dive reference
│   └── profile_schema.md              # YAML schema reference for candidate_profile.yaml
├── templates/
│   ├── candidate_profile.template.yaml # Template for candidate data
│   ├── candidate_narrative.template.md # Template for candidate narrative
│   ├── preferences.template.yaml       # Template for job search preferences
│   └── tracker.template.yaml           # Application tracker schema
├── output/
│   ├── resumes/                       # Generated resumes (gitignored)
│   ├── cover_letters/                 # Generated cover letters (gitignored)
│   ├── lead_reports/                  # Generated scorer reports (gitignored)
│   ├── interview_prep/                # Generated interview prep guides (gitignored)
│   ├── career_exploration/            # Generated career exploration reports (gitignored)
│   └── analytics/                     # Generated analytics dashboards (gitignored)
└── scripts/
    ├── generate_docx.js               # Helper: Node.js docx generator
    ├── convert_md_to_pdf.js           # Helper: Convert markdown files to PDF
    └── linkedin/
        ├── init_db.py                 # Initialise SQLite schema (run once)
        ├── map_preferences.py         # Convert preferences.yaml → search params
        ├── sync.py                    # Fetch jobs from LinkedIn → SQLite
        ├── pre_filter.py              # Rule-based hard filter (no LLM)
        ├── export_for_scoring.py      # Export unscored jobs as markdown
        ├── update_scores.py           # Write LLM scores back to SQLite
        ├── report.py                  # Generate ranked markdown report
        └── analytics.py               # Generate HTML analytics dashboard
```

---

## Configuration

### Job Search Preferences (`config/preferences.yaml`)

Edit this file to define your hard filters and soft preferences. The scorer agent reads this to score postings.

### Resume Style (`config/resume_style.yaml`)

Controls formatting preferences — fonts, section ordering, page length targets.

### MCP Servers (`.claude/settings.json`)

Pre-configured with filesystem access scoped to this project. Add additional MCP servers as needed (e.g., email integration for lead gen from inbox).

---

## Git Management

The `.gitignore` is configured so that **all personal data stays local automatically**. Running `git add .` is safe — it will never stage your profile, preferences, source materials, or generated outputs.

### For users who cloned this repo

Your personal files are never tracked by git:
- `knowledge_base/candidate_profile.yaml` — your structured profile
- `knowledge_base/candidate_narrative.md` — your narrative
- `knowledge_base/sources/*` — your source materials
- `config/preferences.yaml` — your job search preferences
- `output/**` — all generated resumes, cover letters, reports
- `postings/**` — job postings you're considering

If you want to contribute framework improvements (agent prompts, scripts, docs):

```bash
# Edit an agent prompt
# ... make changes to .claude/agents/resume-writer.md ...

# Stage and commit — only framework files will be included
git add .claude/agents/resume-writer.md
git commit -m "Improve resume-writer prompt for better ATS formatting"
git push
```

### For the project maintainer

The same `.gitignore` protection applies. Your typical workflow:

```bash
# Improve agents, scripts, or docs
# ... make changes ...

# Stage, commit, push — personal data stays local automatically
git add -A
git commit -m "Add new agent capability"
git push
```

No special steps needed to protect personal data — the `.gitignore` handles it.

---

## Design Principles

**Files over databases.** At this scale (one candidate, hundreds of job postings), structured files on disk beat a database every time. JSON for structured data, markdown for narrative, grep for search.

**Prompt engineering over code.** The agents' intelligence lives in their system prompts, not in code. Invest time in prompt refinement — the orchestration code should be minimal glue.

**Subagents for review, not generation.** Use cheaper models (Sonnet) as reviewer subagents that check the output of the main generation step. This catches formatting issues, ATS problems, and tone mismatches without doubling your Opus costs.

**Idempotent outputs.** Every agent should write to a predictable output path. Re-running with the same inputs should produce a clean new output, not corrupt previous work.

**Source provenance.** The KB builder should track where every fact came from. When a resume claims "increased revenue by 40%," you should be able to trace that back to the specific source document.

**Keep it simple.** Resist adding infrastructure, dependencies, or tooling unless the benefit is clear and immediate. Voice input? Use an external app and paste the transcript. Batch processing? A for-loop in bash. Database? A JSON file. Complexity is a cost — pay it only when you must.

---

## Migration Path to Agent SDK

When you're ready to move to the Claude Agent SDK for batch processing, scheduling, or programmatic control:

1. Each `.claude/agents/*.md` system prompt translates directly into `ClaudeAgentOptions.system_prompt`
2. Tool restrictions translate into `ClaudeAgentOptions.allowed_tools`
3. MCP server configs translate into custom Python `@client.tool` functions
4. The knowledge base and output structure remain identical
5. See the architecture plan document for full SDK code patterns

---

## Tips

- **Iterate on prompts first.** The agent markdown files are the primary lever. Refine them based on output quality before adding complexity.
- **Use `/agents` in Claude Code** to verify all agents are loaded.
- **Use `--print` flag** for non-interactive / scriptable runs.
- **Check `knowledge_base/source_index.md`** to verify what the KB builder has ingested.
