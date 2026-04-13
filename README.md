# CareerForge

Job searching manually is slow, inconsistent, and doesn't scale — you're rewriting resumes from scratch for each posting, manually scrolling LinkedIn every day, and walking into interviews underprepared.

CareerForge is a personal AI job search system powered by Claude Code. It automates the repetitive work across the full search lifecycle — from daily job discovery, to tailored applications in minutes, to walking into every interview prepared.

**Find roles worth pursuing.** The Career Explorer maps the current job market against your actual skills and experience, surfacing roles you're genuinely qualified for — including ones you might not have considered. The LinkedIn Job Scanner then runs daily across configurable search scopes, hard-filters out anything that fails your requirements (location, compensation, employment type), and LLM-scores the rest against your profile so only the strongest matches reach you.

**Apply in minutes, not hours.** Point the Resume Writer at any job posting and it generates a tailored `.docx` resume — achievements reordered, keywords matched, qualification gaps flagged — grounded entirely in your verified knowledge base. The Cover Letter agent does the same, adding company research it pulls fresh from the web.

**Walk into every interview prepared.** The Interview Prep agent researches the company, maps out the interview process and rounds, generates predicted questions per stage, and builds a personal story bank showing which of your own achievements best answers each question — all in one command.

## Install as a Plugin (Recommended)

If you already have [Claude Code](https://claude.ai/code) installed, this is the fastest path — no cloning, no package managers:

```
/plugin marketplace add michaelgarcia/careerforge
/plugin install careerforge@careerforge
```

Then create a workspace directory, open Claude Code in it, and run `/cf-init`. CareerForge will scaffold the folder structure and walk you through the rest.

---

*Prefer to clone the full source? See [Getting Started](#getting-started) below.*

---

## Getting Started

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| [Claude Pro](https://claude.ai) | Any | Required for Claude Code |
| [Claude Code](https://claude.ai/code) | Latest | The AI shell CareerForge runs in |
| [Git](https://git-scm.com/downloads) | Any | For cloning the repository |
| [Node.js](https://nodejs.org) | 18+ | For resume/cover letter `.docx` generation |
| [Python](https://www.python.org) | 3.11+ | For the LinkedIn job scanner |

### Step 1 — Get the code

```bash
git clone https://github.com/michaelgarcia/careerforge.git
cd careerforge
```

### Step 2 — Run setup

The setup script installs all dependencies and confirms your environment is ready.

**Windows** — double-click `setup.bat`

**Mac / Linux** — open Terminal in the careerforge folder and run:
```bash
bash setup.sh
```


### Step 3 — Launch CareerForge

**Windows** — double-click `launch.bat`

**Mac / Linux** — double-click `launch.command`
_(First time on Mac: right-click → Open to bypass Gatekeeper, then double-click works normally.)_

Or from any terminal in the careerforge folder:
```bash
claude
```

### Step 4 — Get started

Once Claude Code opens, just say:

> **"I'm ready to get started"**

CareerForge will check your setup, walk you through building your profile from your resume and career documents, and get you ready for your first job scan — all in one conversation.

After your profile is set up, you can talk to CareerForge in plain English:

- *"Find me jobs in machine learning"*
- *"I want to apply to [paste URL]"*
- *"I have an interview at AnyCompany next week"*
- *"What's my application status?"*

No need to memorize commands — CareerForge figures out what you need and routes to the right tool automatically.

---

## What it looks like in practice

![Analytics Demo](docs/analytics_demo.png)

*354 jobs collected across 5 search scopes → 287 hard-filtered by location/type → 67 LLM-scored → **6 top matches surfaced automatically***

---

## High level overview and Architecture

![Analytics Demo](docs/CareerForge_Introduction.png)

---

## Design Principles

**Files over databases.** At this scale (one candidate, hundreds of job postings), structured files on disk beat a database every time. JSON for structured data, markdown for narrative, grep for search.

**Prompt engineering over code.** The agents' intelligence lives in their system prompts, not in code. Invest time in prompt refinement — the orchestration code should be minimal glue.

**Subagents for review, not generation.** Use cheaper models (Sonnet) as reviewer subagents that check the output of the main generation step. This catches formatting issues, ATS problems, and tone mismatches without doubling your Opus costs.

**Idempotent outputs.** Every agent should write to a predictable output path. Re-running with the same inputs should produce a clean new output, not corrupt previous work.

**Source provenance.** The KB builder should track where every fact came from. When a resume claims "increased revenue by 40%," you should be able to trace that back to the specific source document.

**Keep it simple.** Resist adding infrastructure, dependencies, or tooling unless the benefit is clear and immediate. Voice input? Use an external app and paste the transcript. Batch processing? A for-loop in bash. Database? A JSON file. Complexity is a cost — pay it only when you must.


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
