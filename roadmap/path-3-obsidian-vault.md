# Path 3 — CareerForge as an Obsidian Vault

## Status: Future / Post v1

This document captures the full specification for distributing CareerForge as an Obsidian
vault template. It is preserved here so it can be picked up in a future session with full
context, without having to rediscover the reasoning.

---

## Why This Path Is Interesting

Obsidian is a free, local-first markdown-based knowledge management app with ~2 million
active users and one of the most active plugin ecosystems in software. It runs on Mac,
Windows, and Linux. Its model — a folder of markdown and YAML files — is **structurally
identical to how CareerForge already works**.

The insight: CareerForge's `knowledge_base/`, `config/`, `output/`, and `postings/` folders
are already a structured collection of markdown and YAML files. The `.claude/agents/` files
are markdown. The candidate narrative is markdown. The job postings saved to disk are
markdown. **CareerForge is already, essentially, an Obsidian vault.** The only thing missing
is the Obsidian app sitting on top of it.

The Karpathy "LLM Wiki" pattern (see: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
makes this concrete: use an LLM as the "programmer" of a persistent wiki. The LLM reads
raw sources, builds structured markdown pages, and maintains them over time. The human uses
Obsidian to browse, search, and navigate the wiki. This is exactly what CareerForge does
with job search data — the agents build and maintain a structured knowledge base, and the
user needs a way to navigate it.

For non-technical users, Obsidian has a significant advantage over a terminal: it's a
**graphical app they can download and install like any other application**. No terminal,
no CLI, no package managers. The vault setup can be as simple as downloading a zip file
and opening it in Obsidian.

The **Claudian plugin** (https://github.com/YishenTu/claudian) makes this fully viable.
It embeds Claude Code as a chat panel inside Obsidian, with the Obsidian vault as Claude
Code's working directory. All existing `.claude/agents/*.md` subagents work unchanged.
Users can run CareerForge workflows from within Obsidian's interface without ever opening
a terminal.

The result: a zero-terminal, graphical, locally-hosted CareerForge experience using tools
that are free, stable, and already widely adopted.

---

## What This Path Is

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Obsidian App (UI Layer)                                         │
│                                                                 │
│  Sidebar: knowledge_base/  jobs/  output/  postings/           │
│  Claudian chat panel: "Generate a resume for this job"         │
│  Dataview tables: application status, job scores               │
│  Graph view: connections between jobs, skills, companies        │
└──────────────────┬──────────────────────────────────────────────┘
                   │ Claudian plugin (Claude Code in vault)
┌──────────────────▼──────────────────────────────────────────────┐
│ Claude Code (orchestration layer)                               │
│  .claude/agents/*.md — all 9 agents unchanged                  │
│  CLAUDE.md — routing rules unchanged                           │
│  .claude/commands/*.md — slash commands unchanged              │
└──────────┬──────────────────────────────┬───────────────────────┘
           │                              │
           ▼                              ▼
    Python scripts                 Node.js scripts
    (LinkedIn scanner)             (docx generation)
```

### What Gets Built

**1. Vault Template** (`careerforge-vault.zip`)

A pre-configured Obsidian vault that IS the CareerForge project directory. Contents:

```
careerforge/                          ← the vault root (= project root)
├── .obsidian/                        ← Obsidian config (community plugins, hotkeys, layout)
│   ├── community-plugins.json        ← pre-lists required plugins
│   ├── plugins/                      ← pre-installed plugin configs
│   └── workspace.json                ← default panel layout
├── .claude/                          ← unchanged CareerForge agents/commands
├── knowledge_base/                   ← unchanged (gitignored locally)
├── config/                           ← unchanged
├── output/                           ← unchanged
├── postings/                         ← unchanged
├── scripts/                          ← unchanged
├── tools/                            ← unchanged
├── dashboard.md                      ← new: Dataview-powered job search overview
├── GETTING_STARTED.md                ← new: visual guide for non-technical users
└── templates/                        ← new: Obsidian note templates for jobs, companies
```

The vault template ships with `.obsidian/` pre-configured so that users open it in Obsidian
and the right plugins are immediately enabled (or prompted to install).

**2. Required Obsidian Plugins (installed from community browser)**

| Plugin | Purpose |
|--------|---------|
| **Claudian** | Embeds Claude Code as a chat panel — the core execution engine |
| **Dataview** | SQL-like queries over YAML frontmatter for job tracking tables |
| **Shell Commands** | Fallback: run scripts via hotkey/button if Claudian isn't preferred |
| **Templater** | Note templates for new job postings, company research |

All four are available in Obsidian's Community Plugins browser (Settings → Community Plugins
→ Browse). Non-technical users can install them by clicking "Install" in the UI.

**3. `dashboard.md`** — the home page of the vault

A Dataview-powered dashboard that shows:
- Application pipeline summary (how many in each status)
- Recently scored jobs (above threshold)
- Upcoming interview prep reminders
- Quick-action buttons (via Shell Commands) for common tasks

Example Dataview block:
````markdown
```dataview
TABLE status, score, company, role
FROM "postings"
WHERE status != "closed"
SORT score DESC
```
````

**4. `GETTING_STARTED.md`** — non-technical user onboarding

A visual, step-by-step guide replacing the terminal-oriented README:
1. Open the Claudian panel (icon in left sidebar)
2. Drop your resume into `knowledge_base/sources/`
3. In the Claudian chat, type: "Build my profile"
4. Wait for confirmation, then type: "Find me jobs in [field]"
5. Browse results in the `jobs/` folder

**5. Setup Script** (`setup.sh` / `setup.bat`)

For the one-command installer path (dev-comfortable users), a script that:
1. Checks Obsidian is installed (if not, opens the Obsidian download page)
2. Checks Node.js + Python
3. Installs Python and Node.js deps
4. Opens the vault in Obsidian

For truly non-technical users:
1. Download Obsidian from obsidian.md (standard .exe/.dmg installer)
2. Download `careerforge-vault.zip` from GitHub releases
3. Extract → Open as Obsidian vault
4. Install 4 community plugins from within Obsidian's UI

---

## The Claudian Plugin in Detail

Claudian (https://github.com/YishenTu/claudian) is the keystone of this path. Key facts:

- **Active maintenance**: ~800 GitHub stars, updated as of 2024
- **How it works**: Opens Claude Code as a subprocess, setting the Obsidian vault as
  Claude Code's working directory. Chat panel appears inside Obsidian.
- **Capabilities**: File read/write, bash execution, multi-step conversations, fork/resume
- **Subagent support**: Because it's Claude Code underneath, all `.claude/agents/*.md`
  files work exactly as they do in the terminal version
- **No API key**: Uses Claude Code, which uses the user's Pro subscription

**Important to verify**: Claudian must be tested to confirm it correctly spawns CareerForge's
subagents via the `.claude/agents/` system. The vault directory structure must match what
Claude Code expects (`.claude/` at the root of the working directory).

---

## The Dataview Plugin in Detail

Dataview (https://github.com/blacksmithgu/obsidian-dataview) treats Obsidian notes as a
database. YAML frontmatter becomes queryable fields. This is what powers the job tracker
dashboard.

For CareerForge, job postings saved as markdown files with frontmatter like:
```yaml
---
company: Stripe
role: Senior ML Engineer
status: applied
score: 78
applied_date: 2026-04-12
---
```

Can be queried in any note:
```dataview
TABLE company, role, score, status
FROM "postings"
WHERE score > 70
SORT score DESC
```

This gives a live, updating table of top-scored jobs without any custom dashboard code.

The `tracker.yaml` file may need to be split into individual per-job markdown files for
Dataview to query efficiently. This is a small migration (~20 LOC Python script to convert).

---

## Tradeoffs vs. Path 2 (Enhanced Claude Code)

| Dimension | Path 3: Obsidian Vault | Path 2: Enhanced Claude Code |
|-----------|------------------------|------------------------------|
| **Implementation effort** | ~1 day (vault template + plugin config) | Hours (CLAUDE.md edits only) |
| **Non-technical accessibility** | Very high — GUI app, no terminal for daily use | Medium — requires terminal + Claude Code |
| **First install (non-technical)** | Download Obsidian + unzip vault template | Clone repo + install Claude Code |
| **Agent logic changes** | None (Claudian runs Claude Code unchanged) | None |
| **Routing** | CLAUDE.md unchanged, Claudian chat replaces terminal | Enhanced CLAUDE.md dispatcher |
| **Slash commands** | Work via Claudian chat (same as terminal) | Full support, unchanged |
| **Data visualization** | Rich: Dataview tables, graph view, backlinks | None (plain text output) |
| **Job tracking UX** | Visual dashboard in Obsidian | Read tracker.yaml output in terminal |
| **Mobile support** | Limited (Obsidian mobile, no script execution) | Limited (Claude Code mobile not available) |
| **Background scanning** | Needs API key + separate cron (not in Obsidian) | Same constraint |
| **Plugin update risk** | Community plugins can break on Obsidian updates | No plugin risk (no plugins) |
| **Distribution** | Vault template zip + community plugin install | Git clone |
| **Architecture** | CareerForge + Obsidian coupled by vault structure | Self-contained |

**When to choose Path 3 over Path 2:**
- When the target user genuinely cannot use a terminal (Obsidian replaces it)
- When you want a richer visual experience (job tracking dashboard, graph view)
- When you want the knowledge base to be browsable and navigable (not just agent output)
- When you want the vault's graph visualization to show skill → job → company relationships
- When you're building for knowledge workers who already use Obsidian

**When NOT to choose Path 3:**
- If Claudian's stability or subagent support is uncertain (must be verified first)
- If the target users don't want to install another app
- If you want the simplest possible first version

---

## Obsidian's "Graph View" as a Feature

One unique advantage of the Obsidian path worth highlighting: Obsidian's graph view shows
bidirectional links between notes as a visual graph. For CareerForge, this means:

- Job postings link to companies (through company mentions)
- Companies link to skills (through job requirements)
- Skills link to candidate profile achievements
- Applications link to interview prep notes

Non-technical users get a **visual map of their job search** for free, with no code. This
is genuinely differentiating vs. a terminal or even a web UI.

---

## Implementation Checklist (for future session)

- [ ] Verify Claudian plugin spawns CareerForge subagents correctly
  (test: open vault in Obsidian + Claudian, run `/resume test-url`, confirm subagent fires)
- [ ] Decide on tracker.yaml vs. per-job markdown files for Dataview
- [ ] Write migration script if per-job markdown is chosen
- [ ] Build vault template directory structure
- [ ] Configure `.obsidian/` with required community plugins listed
- [ ] Write `dashboard.md` with Dataview queries for job pipeline view
- [ ] Write `GETTING_STARTED.md` with visual non-technical onboarding
- [ ] Create Obsidian note templates for job postings and company research
- [ ] Write `setup.sh` / `setup.bat` for dep installation
- [ ] Package vault as downloadable `.zip` for GitHub releases
- [ ] Document plugin installation steps for non-technical users

---

## References

- Karpathy LLM Wiki pattern: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Claudian plugin: https://github.com/YishenTu/claudian
- Agent Client plugin: https://github.com/RAIT-09/obsidian-agent-client
- Dataview plugin: https://github.com/blacksmithgu/obsidian-dataview
- Shell Commands plugin: https://github.com/Taitava/obsidian-shellcommands
- Obsidian Job Tracker template: https://github.com/ammarlakis/obsidian-system-job-tracker
- Obsidian community plugins: https://obsidian.md/plugins
