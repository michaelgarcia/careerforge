# Path 0 — CareerForge as a Claude Code Plugin

## Status: Implemented in v0.1 (partially) / Submit to marketplace post-testing

This document captures the full specification and rationale for distributing CareerForge as
a native Claude Code plugin. The plugin files (`plugin.json`, `marketplace.json`, `/cf-init`
command) have been created. The remaining step — submitting to the official Anthropic
marketplace — is deferred until after v0.2 testing is complete.

---

## Why This Path Is Interesting

Of the three distribution paths evaluated (MCP Server, Obsidian Vault, Plugin), this one is
uniquely compelling because **it requires no new architecture and no new infrastructure**. It
works entirely within the existing Claude Code agent system — the same 9 agents and 13 slash
commands that work today, made available globally to any Claude Code user via a single
install command.

### The core advantages

**Zero friction installation.** The current clone-based setup requires Git, Node.js, Python,
a terminal, and knowledge of several install commands. The plugin path reduces this to three
lines inside Claude Code itself — no terminal, no package manager, no path configuration.

**Global availability.** Agents and commands installed via the plugin system are available
in *any project directory* the user opens, not just the CareerForge repo folder. A user can
open Claude Code in their home directory and `/resume`, `/scan`, and all other commands work
immediately.

**Marketplace discoverability.** The official Anthropic marketplace (accessible via
`/plugin > Discover` in any Claude Code session) is the equivalent of the VS Code Extension
Marketplace — every Claude Code user can discover CareerForge without knowing it exists
beforehand. This is the highest-leverage distribution channel available.

**Minimal implementation cost.** The plugin packaging added exactly four files:
`plugin.json`, `marketplace.json`, `.claude/commands/cf-init.md`, and a README section.
Nothing in the existing agent or command system was modified.

---

## What This Path Is

### Architecture

```
Claude Code (any directory)
  │
  │  /plugin install careerforge@careerforge
  ▼
~/.claude/agents/         ← 9 agents installed here (user scope)
~/.claude/commands/       ← 13 commands installed here (user scope)
  │
  │  user runs /cf-init in their chosen workspace directory
  ▼
~/my-job-search/          ← workspace (wherever the user chooses)
  ├── knowledge_base/
  │   └── sources/        ← user drops career documents here
  ├── config/
  ├── postings/
  ├── output/
  └── data/
```

The key insight: **agents and commands live at user scope; data lives wherever the user
chooses**. These are decoupled. A user can have multiple CareerForge workspaces (e.g.,
one for each job search campaign) and switch between them by changing directories.

### The Directory Scaffolding Problem

The plugin system installs agents and commands — it does **not** create the local filesystem
structure that agents depend on (`knowledge_base/sources/`, `config/`, `output/`, etc.).
This is not a limitation of CareerForge specifically; it's a general characteristic of the
plugin system.

The solution is the `/cf-init` command, which is part of the plugin. It:
1. Detects whether the current directory is already a CareerForge workspace
2. If not, creates all required directories and writes minimal starter config files
3. Embeds all file content inline — no network access or template download needed
4. Ends with clear, actionable next steps for the user

`/cf-init` is idempotent: running it twice in the same directory is safe.

### File Inventory

| File | Purpose |
|------|---------|
| `plugin.json` | Plugin manifest — lists all agents and commands |
| `marketplace.json` | Marketplace catalog — enables `/plugin marketplace add` |
| `.claude/commands/cf-init.md` | Workspace scaffolding command |

---

## Three Distribution Tiers

### Tier 1 — Self-hosted GitHub (active now)

The `marketplace.json` in the repo enables anyone to add the CareerForge marketplace:

```
/plugin marketplace add michaelgarcia/careerforge
/plugin install careerforge@careerforge
```

Claude Code fetches `https://raw.githubusercontent.com/michaelgarcia/careerforge/main/marketplace.json`,
reads the plugin catalog, then fetches the plugin files from the same raw GitHub URLs.
No server, no npm publish, no additional hosting required. GitHub's raw content endpoint
is the "server."

**Reach:** Anyone who knows the repo URL.

### Tier 2 — Community registry (`claude-plugins.dev`)

Submit a listing to the community plugin registry. Users discover CareerForge through
community directories without needing to know the GitHub repo URL.

**Effort:** ~1 hour (fill out submission form, provide metadata).
**Reach:** Community-aware Claude Code users.

### Tier 3 — Official Anthropic marketplace

Submit via `platform.claude.com/plugins/submit`. After Anthropic review and approval,
CareerForge appears in the built-in `/plugin > Discover` tab for every Claude Code user.

**Effort:** Submission + approval process (timeline unknown).
**Reach:** All Claude Code users globally.
**Recommendation:** Submit after v0.2 testing confirms stability and polish.

---

## Complete User Journey (Plugin Path)

```
# Install (one time, ever)
/plugin marketplace add michaelgarcia/careerforge
/plugin install careerforge@careerforge

# Create a workspace
mkdir ~/my-job-search
cd ~/my-job-search
claude

# Scaffold the workspace
/cf-init
→ Creates knowledge_base/, config/, postings/, output/, data/
→ Writes starter preferences.yaml and tracker.yaml
→ "Drop your resume into knowledge_base/sources/"

# Build profile
# (drop resume.pdf into knowledge_base/sources/ via file manager)
"Build my profile"
→ kb-builder agent ingests documents, writes candidate_profile.yaml

# Configure preferences
"Set up my job preferences"
→ preferences-setup agent guides through filters

# Use naturally
"Find me jobs in machine learning"      → job-scanner
"Apply to [URL]"                         → scorer → resume-writer → cover-letter
"I have an interview at AnyCompany"      → interview-prep
```

---

## Tradeoffs vs. Clone Path

| Dimension | Plugin Path | Clone Path |
|-----------|-------------|------------|
| **Install friction** | 2 commands in Claude Code | git clone + setup.sh + Claude Code |
| **Prerequisites** | Claude Code only | Claude Code + Git + Node.js + Python |
| **Agent scope** | User scope (all directories) | Project scope (repo directory only) |
| **Updates** | `/plugin update careerforge` | `git pull` |
| **Workspace flexibility** | Any directory | The cloned repo directory |
| **Source code access** | No (agents only) | Full source |
| **Script execution** | Still requires Node.js + Python for scanner/docx | Same |
| **Distribution reach** | Marketplace-eligible | GitHub clone only |

**Both paths are valid and fully supported.** The clone path remains the preferred choice
for contributors, developers, and users who want full source access.

---

## Submission Checklist (for future session — Tier 3)

- [ ] v0.2 testing complete, known bugs resolved
- [ ] Review plugin.json schema against current official spec (field names may have changed)
- [ ] Verify marketplace.json format against official docs
- [ ] Test `/cf-init` idempotency on Windows, Mac, Linux
- [ ] Add a plugin icon/logo if required by submission form
- [ ] Write submission description (150 words max, highlighting key differentiators)
- [ ] Submit at platform.claude.com/plugins/submit
- [ ] Monitor for reviewer feedback

---

## Notes on plugin.json Schema

The `plugin.json` schema was written based on research into the Claude Code plugin system
as of April 2026. The exact field names (`agents`, `commands`, path format) should be
verified against the current official documentation before submitting to the marketplace.
If the schema has changed, adapt field names accordingly — the structure and intent are clear.

Official reference: https://code.claude.com/docs/en/plugins
