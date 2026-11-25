# CareerForge — Project Instructions

A job search system for one candidate: specialized skills and subagents working from a shared knowledge base. It represents a real person's career, so accuracy is non-negotiable. The integrity rules every agent follows:

@../SOUL.md

## First message of a session

Unless the message is a slash command (run those as typed), determine the workspace state before replying: `knowledge_base/sources/`, `knowledge_base/candidate_profile.yaml` (a template if it contains `name: "Your Name"`), `config/preferences.yaml`, and the latest rows of `postings/applications.csv`. If a `[CareerForge state]` block is already in context, use it instead. Then follow the `start` skill: open with the line for that state and answer what the user actually asked, in the same reply.

The user never needs to know a skill or agent name. Route plain-language requests with the `start` skill's routing map. Ask at most one clarifying question, and only when two routes would produce different saved artifacts. Tone: warm, direct, plain language, one question at a time.

## Where things live

Most of these paths are gitignored, so the Grep tool can't see them (Rule 15).

- `knowledge_base/` (gitignored): `sources/` (raw documents), `candidate_profile.yaml` and `candidate_narrative.md` (**evidence**), `north_star.md`, `resume_variants.md` and `memories/` (**framing**), `source_index.md` and `ingestion_progress.yaml` (provenance and ingestion state)
- `config/preferences.yaml`, `config/search_scopes.yaml` and `config/company_targets.yaml` (gitignored): filters, LinkedIn scopes, company-scanner targets. `config/resume_style.yaml`: resume formatting
- `postings/` (gitignored): `<slug>/` posting text and company research, `applications.csv` (tracker), `journal/<company>.md`
- `output/` (gitignored): deliverables by type; `output/.work/` for scratch files
- `.claude/reference/`: shared rules agents read on demand (KB context, achievement format, output naming, scoring rubric, interview-prep formats, tracker schema)
- `.claude/rules/`: tracker and KB rules that load when those files are touched
- `docs/profile_schema.md`: the only profile schema. `templates/`: starter files for new workspaces

## Core Principles

- **Simplicity First**: Make every change as simple as possible.
- **No Laziness**: Find root causes. No temporary fixes.
- **Minimal Impact**: Only touch what's necessary.
- **No Backward-Compat Shims**: This is a single-candidate tool. Make the clean change; don't maintain a second legacy code path. A sane default for a missing config key is fine.

## Global Rules

1. **Read the knowledge base before any deliverable; never fabricate.** Every claim traces to `candidate_profile.yaml` or `candidate_narrative.md`. North star, variants and memories are **framing**: they decide selection, ordering, emphasis and wording, never facts. Details: `.claude/reference/kb-context.md`.
2. **Never overwrite outputs without confirmation.** Naming and paths: `.claude/reference/output-naming.md`.
3. **Log every action.** Append a log entry when ingesting sources, updating the KB, or generating deliverables.
4. **Structured data for querying, narrative for generation.**
5. **Respect preferences.** Hard constraints are absolute filters; soft preferences guide emphasis.
6. **Use web search for company context** when writing cover letters or scoring fit.
7. **Resumes and cover letters are .docx** rendered only by `scripts/generate_docx.py` (`--type resume|cover_letter`) from a JSON content file. Never write ad-hoc generator scripts.
8. **XYZ achievements** with leadership scope: `.claude/reference/achievement-format.md`.
9. **Provenance:** every KB fact has a `source`, or `"unverified"`.
10. **Keep the tracker current:** one appended row in `postings/applications.csv` per status change, plus a journal entry when there's narrative, in the same reply (`.claude/rules/tracker.md`).
11. **Delegate deliverables to their skill.** Resumes, cover letters, scoring, scans, exploration and KB builds run in their named subagent via their skill. Interviews (`capture-story`, `north-star`, `setup-preferences`) and interview-prep coordination (`prep`) run in the main conversation.
12. **Capture lessons after corrections.** Write the rule to `knowledge_base/memories/<slug>.md` (format: `templates/memory.template.md`, with **Why** and **How to apply**). Rules about this candidate go there; rules true for every CareerForge user go in this file.
13. **Verify before marking complete.** YAML parses; .docx exists and is non-zero; scripts run.
14. **Read every file in `knowledge_base/memories/` before producing any deliverable**, and fix any draft that violates one. The folder may be empty.
15. **Searching gitignored paths:** `knowledge_base/`, `config/preferences.yaml`, `config/search_scopes.yaml`, `config/company_targets.yaml`, `postings/`, `output/` and `data/` are invisible to the Grep tool, which reports "No matches found" with no warning. Use `rg --no-ignore -n -i "pattern" <path>` via Bash. Treat a zero-match Grep result there as unproven.
