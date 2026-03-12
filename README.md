# CareerForge

A multi-agent system powered by Claude Code that covers the full job search lifecycle: knowledge base management, tailored resume generation, cover letter writing, lead generation/filtering, and interview preparation.

## Architecture

```
                           ┌──────────────────────────┐
                           │   Candidate Knowledge     │
                           │       Base (KB)           │
                           │  (structured YAML/MD)     │
                           └────────────┬─────────────┘
                                        │
          ┌─────────────────────────────┼──────────────────────────────┐
          │                             │                              │
   ┌──────▼──────────────┐   ┌──────────▼──────────────┐   ┌──────────▼──────────────┐
   │     KB Layer        │   │    Delivery Layer        │   │   Discovery Layer       │
   │─────────────────────│   │─────────────────────────│   │─────────────────────────│
   │ • KB Builder        │   │ • Resume Writer          │   │ • Lead Gen              │
   │ • Story Capture     │   │ • Cover Letter           │   │ • Career Explorer       │
   │ • Preferences Setup │   │ • Interview Prep         │   │ • Job Scanner           │
   └─────────────────────┘   └─────────────────────────┘   └─────────────────────────┘
```

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

## Get Started

This section walks you through going from zero to your first tailored resume. By the end, you'll have a populated knowledge base built from your own materials and a job-specific resume ready to send.

### 1. Load your source materials

Drop everything you have about your career into `knowledge_base/sources/`. CareerForge accepts multimodal inputs — the more you provide, the richer your profile:

- Resumes and CVs (PDF, DOCX)
- Mind maps and career diagrams (images)
- Project screenshots and architecture diagrams
- Performance reviews or recommendation letters
- Conference talk slides or transcripts
- Published articles or blog posts
- Portfolio pieces and project write-ups

No need to organize or pre-process — the KB Builder will extract and structure everything for you.

### 2. Build your knowledge base

Run the KB Builder agent to ingest your source materials and create your structured candidate profile:

```bash
claude "Use the kb-builder agent to ingest all sources in knowledge_base/sources/ and build my candidate profile."
```

This generates your `candidate_profile.yaml` (structured data) and `candidate_narrative.md` (prose version) — the foundation that all other agents read from.

### 3. Generate a tailored resume

With your knowledge base ready, point the Resume Writer at any job posting to get a targeted resume:

```bash
claude "Use the resume-writer agent to create a resume tailored to this job posting: [paste URL or job description]"
```

Your resume lands in `output/resumes/` as a formatted `.docx` file, with achievements and skills prioritized to match the role.

### 4. Explore further

You now have the core workflow down. CareerForge has eight more agents to help with your search — cover letters, lead scoring, story capture, interview prep, career exploration, and an automated LinkedIn job scanner. Read on in the [Usage](#usage) section below to see what each one can do.

## Slash Commands

CareerForge ships with custom slash commands that provide one-line invocation for every workflow step. Type these directly in Claude Code:

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

Commands are defined in `.claude/commands/`. Add or modify them to customize your workflow.

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

### Lead Gen

Scores and filters job postings against your profile and preferences. Respects hard constraints from `config/preferences.yaml`.

```bash
# Single posting
claude "Use the lead-gen agent to score this job posting against my profile: [paste URL]"

# Batch — drop multiple postings into a folder
claude "Use the lead-gen agent to score all postings in ./input_postings/ and produce a ranked report."
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

All agents (resume-writer, cover-letter, lead-gen, interview-prep) can read from these folders. The interview-prep and cover-letter agents also write `company_research.md` into the subfolder for shared reuse.

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
│   │   ├── lead-gen.md                # Agent #5 — Lead Generation & Filtering
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
│       └── scan.md                    # /scan      — Daily LinkedIn job scan
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
│   ├── lead_reports/                  # Generated lead gen reports (gitignored)
│   ├── interview_prep/                # Generated interview prep guides (gitignored)
│   └── career_exploration/            # Generated career exploration reports (gitignored)
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
        └── report.py                  # Generate ranked markdown report
```

## Configuration

### Job Search Preferences (`config/preferences.yaml`)

Edit this file to define your hard filters and soft preferences. The lead-gen agent reads this to score postings.

### Resume Style (`config/resume_style.yaml`)

Controls formatting preferences — fonts, section ordering, page length targets.

### MCP Servers (`.claude/settings.json`)

Pre-configured with filesystem access scoped to this project. Add additional MCP servers as needed (e.g., email integration for lead gen from inbox).

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

For extra safety, you can add a pre-push hook that scans for personal data patterns. This is a local-only safeguard (git hooks aren't committed to the repo).

## Design Principles

**Files over databases.** At this scale (one candidate, hundreds of job postings), structured files on disk beat a database every time. JSON for structured data, markdown for narrative, grep for search.

**Prompt engineering over code.** The agents' intelligence lives in their system prompts, not in code. Invest time in prompt refinement — the orchestration code should be minimal glue.

**Subagents for review, not generation.** Use cheaper models (Sonnet) as reviewer subagents that check the output of the main generation step. This catches formatting issues, ATS problems, and tone mismatches without doubling your Opus costs.

**Idempotent outputs.** Every agent should write to a predictable output path. Re-running with the same inputs should produce a clean new output, not corrupt previous work.

**Source provenance.** The KB builder should track where every fact came from. When a resume claims "increased revenue by 40%," you should be able to trace that back to the specific source document.

**Keep it simple.** Resist adding infrastructure, dependencies, or tooling unless the benefit is clear and immediate. Voice input? Use an external app and paste the transcript. Batch processing? A for-loop in bash. Database? A JSON file. Complexity is a cost — pay it only when you must.

## Migration Path to Agent SDK

When you're ready to move to the Claude Agent SDK for batch processing, scheduling, or programmatic control:

1. Each `.claude/agents/*.md` system prompt translates directly into `ClaudeAgentOptions.system_prompt`
2. Tool restrictions translate into `ClaudeAgentOptions.allowed_tools`
3. MCP server configs translate into custom Python `@client.tool` functions
4. The knowledge base and output structure remain identical
5. See the architecture plan document for full SDK code patterns

## Tips

- **Iterate on prompts first.** The agent markdown files are the primary lever. Refine them based on output quality before adding complexity.
- **Use `/agents` in Claude Code** to verify all agents are loaded.
- **Use `--print` flag** for non-interactive / scriptable runs.
- **Check `knowledge_base/source_index.md`** to verify what the KB builder has ingested.

## Key Features

1. **Your resume never contains anything you didn't do** — Every achievement, skill, and metric in every deliverable traces back to your source documents. Agents flag gaps honestly rather than fill them with plausible-sounding fabrications.

2. **One profile, every job search workflow covered** — Update your knowledge base once and every agent picks it up automatically — resumes, cover letters, lead scoring, and interview prep all draw from the same verified source.

3. **Your achievements always land with maximum impact** — The XYZ formula ("Accomplished X, measured by Y, by doing Z") is enforced at every step — extraction, resume writing, cover letter stories, and interview coaching — so every claim is quantified and credible.

4. **Stop and resume without losing work** — The KB Builder tracks what's already been processed. You can interrupt ingestion mid-session and pick up exactly where you left off the next time you run it.

5. **Resumes that work well with ATS filters** — Output is a properly formatted Word document built to ATS parsing standards — no tables for layout, no key information buried in headers, keyword optimization grounded in your actual experience.

6. **Know your qualification gaps before you apply** — Before writing your resume or scoring a posting, every stated minimum qualification is checked against your profile and any gaps are surfaced — so you're not surprised by a rejection.

7. **Stop wasting time on roles that don't meet your requirements** — Hard constraints (compensation floor, location, role type) are enforced as absolute filters. Postings that violate them are excluded outright — never just scored lower and left in the pile.

8. **Full interview prep in one command** — Research on the company, interview process, compensation ranges, and per-round question guides with your own story pointers all generated together — including a consolidated story bank showing which of your achievements answers which questions.

9. **Company research you only do once** — Research generated for interview prep is reused automatically when writing cover letters for the same company. No duplicate web searches, no inconsistency between documents.

10. **Turn vague stories into resume-ready bullets** — Story Capture walks you through a guided interview (or extracts from a transcript you paste in) and pushes back until every impact statement has a real number behind it.

11. **Discover roles you didn't know you were qualified for** — Career Explorer works outward from your profile to map the landscape of genuinely fitting roles in the current market — with real job posting examples, pay ranges from Levels.fyi and Glassdoor, and work-life balance data.

12. **No need for prompting — all important flows accessible through slash commands** — Every major workflow step has a dedicated slash command (`/resume`, `/cover-letter`, `/score`, `/prep`, `/capture-story`, `/build-kb`, `/explore`, `/track`, `/status`) you can invoke directly in Claude Code.

13. **Your personal data never accidentally ends up in git** — All personal files — profile, narrative, preferences, source materials, generated outputs — are gitignored by default. `git add .` is always safe to run.

14. **Read your interview prep on your phone** — `scripts/convert_md_to_pdf.js` converts any prep guide to a clean, mobile-friendly PDF with styled tables and formatted answer guides, ready to read anywhere.

15. **Automated LinkedIn Job Scanner** — Daily discovery pipeline that queries LinkedIn across configurable search scopes, deduplicates results in a local SQLite database, pre-filters with rule-based hard constraints, and LLM-scores shortlisted candidates against your profile. Surfaces only the highest-fit opportunities via `/scan`.
