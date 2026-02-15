# CareerForge

A multi-agent system powered by Claude Code that covers the full job search lifecycle: knowledge base management, tailored resume generation, cover letter writing, lead generation/filtering, and interview preparation.

## Architecture

```
                      ┌──────────────────────────┐
                      │   Candidate Knowledge     │
                      │       Base (KB)           │
                      │  (structured JSON/MD)     │
                      └─────────┬────────────────┘
                                │
  ┌────────────┬────────────────┼────────────────┬──────────────┬──────────────┐
  │            │                │                │              │              │
┌─▼──────┐ ┌──▼───────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼──────┐
│ Story  │ │  Resume  │ │ Cover Letter│ │    Lead     │ │    KB     │ │ Interview  │
│Capture │ │  Writer  │ │ & Applicant │ │ Generation  │ │  Builder  │ │    Prep    │
└────────┘ └──────────┘ └─────────────┘ └─────────────┘ └───────────┘ └────────────┘
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
cp knowledge_base/candidate_profile.template.json knowledge_base/candidate_profile.json
cp knowledge_base/candidate_narrative.template.md knowledge_base/candidate_narrative.md
cp config/preferences.template.yaml config/preferences.yaml

# Optional: copy local Claude Code settings
cp .claude/settings.local.template.json .claude/settings.local.json

# 3. Edit the copied files with your personal data
#    - knowledge_base/candidate_profile.json  → your skills, experience, achievements
#    - knowledge_base/candidate_narrative.md   → your career narrative (or let KB Builder generate it)
#    - config/preferences.yaml                 → your job search filters and preferences

# 4. Add source materials (resumes, transcripts, articles) to knowledge_base/sources/
#    See knowledge_base/sources/README.md for supported formats and suggested organization.

# 5. Run the KB Builder to populate your knowledge base
claude "Use the kb-builder agent to ingest all sources in knowledge_base/sources/ and build my candidate profile."

# 6. Verify all agents are available
claude
# Then type: /agents
# You should see all six agents listed
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

This generates your `candidate_profile.json` (structured data) and `candidate_narrative.md` (prose version) — the foundation that all other agents read from.

### 3. Generate a tailored resume

With your knowledge base ready, point the Resume Writer at any job posting to get a targeted resume:

```bash
claude "Use the resume-writer agent to create a resume tailored to this job posting: [paste URL or job description]"
```

Your resume lands in `output/resumes/` as a formatted `.docx` file, with achievements and skills prioritized to match the role.

### 4. Explore further

You now have the core workflow down. CareerForge has four more agents to help with your search — cover letters, lead scoring, story capture, and interview prep. Read on in the [Usage](#usage) section below to see what each one can do.

## Usage

### KB Builder

Ingests source materials (resumes, transcripts, articles) and builds the structured candidate profile.

```bash
claude "Use the kb-builder agent to ingest all sources in knowledge_base/sources/ and build my candidate profile."
```

Output: `knowledge_base/candidate_profile.json`, `knowledge_base/candidate_narrative.md`, `knowledge_base/source_index.md`

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
│   └── agents/
│       ├── kb-builder.md              # Agent #1 — Knowledge Base Builder
│       ├── story-capture.md           # Agent #2 — Story Capture & Achievement Extraction
│       ├── resume-writer.md           # Agent #3 — Resume Writer
│       ├── cover-letter.md            # Agent #4 — Cover Letter & Application
│       ├── lead-gen.md                # Agent #5 — Lead Generation & Filtering
│       └── interview-prep.md          # Agent #6 — Interview Preparation
├── knowledge_base/
│   ├── candidate_profile.template.json # Template for candidate data
│   ├── candidate_narrative.template.md # Template for candidate narrative
│   ├── candidate_profile.json         # Your structured candidate data (gitignored)
│   ├── candidate_narrative.md         # Your narrative profile (gitignored)
│   ├── source_index.md                # Provenance log (gitignored)
│   └── sources/                       # Raw input materials (gitignored except README)
│       └── README.md                  # Instructions for source materials
├── postings/                          # Job postings under consideration (gitignored)
│   └── [company_role]/
│       ├── job_description.md         # The full job posting (.md or .pdf)
│       └── company_research.md        # Auto-generated by agents
├── config/
│   ├── preferences.template.yaml      # Template for job search preferences
│   ├── preferences.yaml               # Your preferences & hard filters (gitignored)
│   └── resume_style.yaml              # Resume formatting preferences
├── templates/
│   └── .gitkeep                       # Optional: custom .docx templates
├── output/
│   ├── resumes/                       # Generated resumes (gitignored)
│   ├── cover_letters/                 # Generated cover letters (gitignored)
│   ├── lead_reports/                  # Generated lead gen reports (gitignored)
│   └── interview_prep/               # Generated interview prep guides (gitignored)
└── scripts/
    └── generate_docx.js               # Helper: Node.js docx generator
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
- `knowledge_base/candidate_profile.json` — your structured profile
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
