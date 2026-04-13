Initialize a CareerForge workspace in the current directory. Creates all required folders and starter configuration files so the agents have a place to read from and write to.

Run this once after installing the CareerForge plugin, from whichever directory you want to use as your job search workspace.

## Steps

**Step 1 — Check if already initialized**

Use the Glob tool to check whether `knowledge_base/sources/` exists in the current directory.

If it exists, report:
> "Your CareerForge workspace is already initialized here.
>
> - Drop career documents into `knowledge_base/sources/` (resume, LinkedIn PDF, etc.)
> - Say **"build my profile"** to ingest them
> - Say **"find me jobs"** to run the LinkedIn scanner
> - Run `/setup-preferences` to configure your job search filters"

Then stop — do not recreate anything.

**Step 2 — Create the directory structure**

If `knowledge_base/sources/` does NOT exist, run the following bash command to create all required directories:

```bash
mkdir -p knowledge_base/sources knowledge_base/archive config postings output/resumes output/cover_letters output/interview_prep output/lead_reports output/analytics data
```

**Step 3 — Write starter files**

Write the following files using the Write tool. Do not overwrite any file that already exists — check first with Glob.

### `knowledge_base/sources/.gitkeep`
An empty file so the sources directory is tracked by git if the user commits their workspace.

Content: (empty — zero bytes)

### `config/preferences.yaml`

```yaml
# Job Search Preferences
# Edit this file to define your hard constraints and soft preferences.
# The scorer agent reads this to filter and score postings.
# The resume and cover letter agents use soft preferences for emphasis.
#
# TIP: Run /setup-preferences for a guided setup instead of editing this manually.

# ============================================================
# HARD CONSTRAINTS — postings that violate these are filtered out
# ============================================================
hard_constraints:

  location:
    remote_only: false
    acceptable_locations:
      - "United States"
    include_hybrid: true

  minimum_compensation_usd: 0

  requires_sponsorship: false

  dealbreakers: []
    # - "No defense/weapons industry"
    # - "No crypto/web3"

# ============================================================
# SOFT PREFERENCES — improve fit score but don't filter
# ============================================================
soft_preferences:

  preferred_domains: []
    # - "AI/ML"
    # - "Cloud Infrastructure"

  preferred_company_stage: []
    # - "Growth (50-500 employees)"
    # - "Scale-up (500-5000)"

  preferred_tech: []
    # - "Python"
    # - "Kubernetes"

  work_style: []
    # - "High autonomy"
    # - "Strong engineering culture"

  career_goals: []
    # - "Technical depth over breadth"
    # - "Path to Staff+ engineering"

# ============================================================
# SEARCH KEYWORDS — used by the LinkedIn scanner
# ============================================================
search_config:
  target_titles: []
    # - "Senior Software Engineer"
    # - "Staff Engineer"
    # - "ML Engineer"

  keywords: []
    # - "machine learning"
    # - "distributed systems"

  target_companies: []

# ============================================================
# LINKEDIN SCANNER
# ============================================================
linkedin_scanner:
  role_types:
    - "Individual Contributor"
  lead_score_threshold: 65
  max_score_per_run: 30
  export_lookback_days: 7
```

### `postings/tracker.yaml`

```yaml
# =============================================================================
# CareerForge — Application Tracker
# =============================================================================
#
# Tracks the lifecycle of every job application.
# Updated automatically by the /track command and relevant agents.
#
# STATUS VALUES: saved | applying | applied | interviewing |
#                offered | accepted | rejected | withdrawn | closed
#
# Each entry slug matches the postings/ subfolder name.
# =============================================================================

applications:
```

### `.gitignore`

```
# CareerForge — private data (never commit these)
knowledge_base/
data/
config/preferences.yaml
config/search_scopes.yaml

# Output files (optional — remove lines below if you want to commit generated docs)
output/
```

**Step 4 — Confirm and guide**

After creating all files and directories, respond with:

> "Your CareerForge workspace is ready.
>
> **Next steps:**
>
> 1. Drop your career documents into `knowledge_base/sources/`
>    Accepted formats: PDF, DOCX, TXT, MD — resumes, LinkedIn exports, performance reviews, anything describing your career.
>
> 2. Say **"build my profile"** — I'll read your documents and build a structured career profile.
>
> 3. Say **"set up my job preferences"** — I'll ask a few questions to configure your filters (location, salary, role types).
>
> 4. After that, just talk to me naturally:
>    - *"Find me jobs in machine learning"*
>    - *"I want to apply to [URL]"*
>    - *"I have an interview at AnyCompany next week"*
>
> Your data stays entirely on your machine — nothing is synced or uploaded."
