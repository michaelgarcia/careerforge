# CareerForge — Project Instructions

A job search system for one candidate: specialized skills and subagents working from a shared knowledge base. It represents a real person's career, so accuracy is non-negotiable. The integrity rules every agent follows:

@../SOUL.md

## First message of a session

Unless the message is a slash command (run those as typed), determine the workspace state before replying: `user_data/knowledge_base/sources/`, `user_data/knowledge_base/candidate_profile.yaml` (a template if it contains `name: "Your Name"`), `user_data/config/preferences.yaml`, and the latest rows of `user_data/postings/applications.csv`. If a `[CareerForge state]` block is already in context, use it instead. Then follow the `start` skill: open with the line for that state and answer what the user actually asked, in the same reply.

The user never needs to know a skill or agent name. Route plain-language requests with the `start` skill's routing map. Ask at most one clarifying question, and only when two routes would produce different saved artifacts. Tone: warm, direct, plain language, one question at a time.

## Where things live

The repository is the product. **Everything personal is in `user_data/`**, one gitignored folder with no tracked files inside it, so the Grep tool can't see it (Rule 15).

- `user_data/knowledge_base/`: `sources/` (raw documents), `candidate_profile.yaml` and `candidate_narrative.md` (**evidence**), `north_star.md`, `resume_variants.md` and `memories/` (**framing**), `source_index.md` and `ingestion_progress.yaml` (provenance and ingestion state)
- `user_data/config/`: `preferences.yaml`, `search_scopes.yaml`, `company_targets.yaml` (filters, LinkedIn scopes, company-scanner targets), and optionally `resume_style.yaml` (overrides the default `templates/resume_style.yaml`) and `config.ini` (email alerts)
- `user_data/postings/`: `<slug>/` posting text and company research, `applications.csv` (tracker), `journal/<company>.md`
- `user_data/output/`: deliverables by type; `user_data/output/.work/` for scratch files
- `user_data/data/`: the jobs database (`jobs.db`)
- `.claude/reference/`: shared rules agents read on demand (KB context, achievement format, output naming, scoring rubric, interview-prep formats, tracker schema)
- `.claude/rules/`: tracker and KB rules that load when those files are touched
- `docs/profile_schema.md`: the only profile schema. `templates/`: starter files and product defaults. `scripts/paths.py`: the one place scripts get `user_data/` from

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
10. **Keep the tracker current:** one appended row in `user_data/postings/applications.csv` per status change, plus a journal entry when there's narrative, in the same reply (`.claude/rules/tracker.md`).
11. **Delegate deliverables to their skill.** Resumes, cover letters, scoring, scans, exploration and KB builds run in their named subagent via their skill. Interviews (`capture-story`, `north-star`, `setup-preferences`) and interview-prep coordination (`prep`) run in the main conversation.
12. **Capture lessons after corrections.** Write the rule to `user_data/knowledge_base/memories/<slug>.md` (format: `templates/memory.template.md`, with **Why** and **How to apply**). Never record a lesson in this file or any other tracked product file: updates replace them. If a lesson seems true for every CareerForge user, also tell the user so they can raise it as product feedback.
13. **Verify before marking complete.** YAML parses; .docx exists and is non-zero; scripts run.
14. **Read every file in `user_data/knowledge_base/memories/` before producing any deliverable**, and fix any draft that violates one. The folder may be empty.
15. **Searching personal data:** everything under `user_data/` is gitignored, so the Grep tool reports "No matches found" there with no warning. Use `rg --no-ignore -n -i "pattern" user_data/<path>` via Bash. Treat a zero-match Grep result there as unproven.
16. **The data contract.** Personal data lives only in `user_data/`. The product never commits, ships, renames or deletes anything there, and never force-adds (`git add -f`) a gitignored file. Paths stored inside personal files (tracker `output_files`, journal links, prep notes) are relative to `user_data/`. A change that moves personal data ships a dated **Action needed** entry in `CHANGELOG.md`, which the `update` skill carries out with the user's consent.
17. **Updates go through the `update` skill.** It backs up `user_data/` outside the repo, then fast-forwards with `git merge --ff-only --no-overwrite-ignore`. Never run a bare `git pull`, `git reset --hard`, `git clean` or `git stash --all` in this repo.
