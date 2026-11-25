# CareerForge: Architecture Review and Revamp Plan

> **Historical record.** This is the review and plan from the November 2026 restructure, kept for reference. Parts A to C describe the layout *before* the changes. The **Implementation log** at the end records what was actually built and where it differs from the plan (for example, output names use `<slug>_score_<date>.md`, not `lead_report_<slug>_<date>.md`). The current layout is documented in `docs/usage.md`.


Prepared 2026-11-23. Review and plan only: no project file has been changed except this one.

**Docs consulted** (fetched today from `https://code.claude.com/docs/llms.txt`):
`memory.md`, `claude-directory.md`, `skills.md`, `commands.md`, `sub-agents.md`, `hooks.md`, `settings.md`, `settings-reference.md`, `output-styles.md`, `best-practices.md`, `plugins/components.md`, `plugins/manifest-reference.md`. All are under `https://code.claude.com/docs/en/`. Doc citations below use the form **[skills]**, **[memory]** and so on.

Some fetched pages were long enough that their later sections came back summarized rather than verbatim (`skills.md` frontmatter table, the SessionStart details in `hooks.md`). Where a recommendation rests on one of those sections, the citation is marked *(summary)*. Verify those before implementing.

**Personal data:** the knowledge base, sources, postings and outputs were read for structure only. This document names fields, files and counts, not their content.

---

# Part A: Review

## Verdict

The content is strong. The integrity model in `SOUL.md`, the framing-versus-evidence rule, the resume-writer's tailoring boundary and the resumable, hash-based ingestion are better thought out than most projects of this kind. Personal data has never been committed (`git log` shows no history for any KB, preferences or tracker file).

The plumbing has fallen behind the platform, in three ways that matter:

1. **Three agents run interviews, and subagents can't hold a conversation.** Story capture, north star and preferences setup are written as "ask one question, wait for the answer" interviews. Per **[sub-agents]**, a subagent starts with a fresh context, has no `AskUserQuestion`, and returns one final message, usually in the background. These flows only work when the main session relays every answer, and the main session never sees the agent's instructions.
2. **Routing and onboarding live in a 191-line CLAUDE.md that every subagent also loads.** **[memory]** says to aim for under 200 lines and to move multi-step procedures into skills. **[sub-agents]** says non-fork subagents load the CLAUDE.md hierarchy. So 11 agents each pay for an onboarding script and dispatcher table they never use. There is also no state check, so nothing makes Claude "already know" the project state when you say hi.
3. **Rules are restated, and the copies have drifted.** There are two scoring rubrics with different weights and tiers, three schema definitions that disagree, four broken file paths, and candidate-specific facts hard-coded into generic agent files that are committed to a public repo.

None of this needs new infrastructure. Almost every fix is moving or rewriting markdown.

## Strengths (keep these)

| # | Strength | Where | Why it works |
|---|---|---|---|
| S1 | **Integrity model with concrete behaviors** | `SOUL.md` "Principles in Practice"; `CLAUDE.md` Global Rule 1 ("Framing versus evidence") | Each value is tied to a specific agent behavior, which makes the abstract rules testable. The framing/evidence split (north star, variants and memories decide wording; only the profile and narrative supply facts) is the most important design idea here. |
| S2 | **Resumable, idempotent ingestion** | `kb-builder.md` Steps 1–2 (content hashes, `in_progress` marking, merge-per-file) | It survives interruptions and re-runs cleanly, and it already contains the data a staleness check needs. |
| S3 | **Tailoring boundary** | `resume-writer.md` "The Tailoring Boundary" (signal layer vs. evidence layer, three-tier terminology) | It is a precise, checkable rule. The self-review checklist enforces it. |
| S4 | **Honest gates and degraded modes** | `scorer.md` and `interview-prep.md` "Degraded Mode"; `resume-writer.md` and `cover-letter.md` "KB Required Gate" | Each agent says what it can do without a KB, and refuses only where that would mean fabricating. This maps directly onto the state-aware routing in Phase 3. |
| S5 | **Event-log tracker plus journal** | `templates/applications_csv.template.md`, `track.md`, `journal.md` | The append-only CSV gives a history, and the journal carries the narrative. The rule that a combined update is one action, not two, is good UX. |
| S6 | **Candidate memories folder** | `templates/memory.template.md`, `knowledge_base/memories/` | One rule per file, gitignored, framed as wording rather than facts. It is the right home for corrections (Global Rule 12). |
| S7 | **Gitignore hygiene** | `.gitignore` (blanket `output/**`, `knowledge_base/**`, `postings/*`) | Blanket excludes replaced an enumerated list that had leaked. History is clean. |
| S8 | **Sensible tool scoping** | Agent frontmatter | Every agent has an explicit `tools` allowlist (**[sub-agents]**: an omitted list inherits everything). The read-heavy agents (`scorer`, `career-explorer`) don't get `Edit`, and `preferences-setup` gets no web tools. |
| S9 | **Deterministic work in scripts, judgment in prompts** | `scripts/linkedin/*`, `scripts/company_scanner/*`, `scripts/generate_docx.py` | Scanning, filtering and .docx rendering are scripts. The LLM only scores and classifies, which matches `SOUL.md`'s "intelligence in prompts" principle. |

## Issues, ranked by impact

| # | Issue | Evidence | Doc behavior it conflicts with or misses |
|---|---|---|---|
| **I1** | **Interactive interviews are built as subagents.** `story-capture`, `north-star` and `preferences-setup` all say to ask one question and wait for the reply. | `story-capture.md` "Ask questions one at a time. Wait for a response"; `north-star.md` Step 3; `preferences-setup.md` "INTERVIEW MODE (12 Phases)" | **[sub-agents]**: a non-fork subagent starts with a fresh context and doesn't inherit the parent conversation, `AskUserQuestion` is removed from every subagent, the result comes back as one final message, and custom subagents run in the background by default. **[skills]**: a skill without `context: fork` runs inline in the main conversation and its body loads only when invoked. |
| **I2** | **No awareness of project state at session start.** The onboarding checks only run when particular phrases appear ("how do I get started"). "Hi", "help" or "I have an interview Tuesday" in a half-built workspace get no state-aware reply. Stale KB and active interview loops are never detected. | `CLAUDE.md` lines 3–12 ("Activate this section when…") | **[memory]**: CLAUDE.md is context, not enforced configuration. **[hooks]** *(summary)*: SessionStart can inject up to 10,000 characters of context before the first prompt. Nothing here uses either mechanism to compute state. |
| **I3** | **CLAUDE.md carries procedures and loads into every subagent.** 191 lines, about 13.8 KB (roughly 3.5k tokens). About 115 of those lines are onboarding flows, a dispatcher table, multi-step workflows and a directory tour. `SOUL.md` is referenced ("See `SOUL.md`") but not imported, so the integrity core never loads at all. | `.claude/CLAUDE.md:3-150`, `:121` | **[memory]**: under 200 lines per file; procedures go in skills or path-scoped rules; `@path` imports load with the importing file. **[best-practices]**: "Only write down what Claude can't find by reading the repo." **[sub-agents]** *(summary)*: non-fork subagents load CLAUDE.md. |
| **I4** | **Interview-prep orchestration exists nowhere the main session can read it.** The agent says "the orchestrator (main Claude Code session) is responsible for creating the directory" and parses a `ROUNDS_DATA` block to fan out per-round agents. `prep.md` lists only the step names. The main session never reads `interview-prep.md`, so the parallel pipeline depends on Claude guessing the protocol. | `interview-prep.md` "Task Dispatch"; `.claude/commands/prep.md:7`; `grep orchestrat .claude/CLAUDE.md .claude/commands` finds nothing relevant | **[skills]**: put multi-step procedures in a skill, with supporting files referenced from SKILL.md. **[sub-agents]**: the main session only sees an agent's `description`. |
| **I5** | **Candidate-specific data is hard-coded in committed, generic files.** The repo is public (README, marketplace) and is meant to be cloned by other candidates. Examples: the resume-writer names the candidate's specific certifications and an employer-internal speaker tier; the job-scanner rubric names the candidate's domains; `scan-companies.md` hard-codes the candidate's city, comp floor and IC-only rule; `CLAUDE.md` and `track.md` use a real recruiter's first name and a real role in examples; `docs/usage.md` uses a real prep folder name. | `resume-writer.md:409, 441, 462-474`; `job-scanner.md:103-106`; `scan-companies.md:9`; `CLAUDE.md:87,89,104`; `track.md:13-16`; `docs/usage.md` | The project's own Global Rule 1: candidate framing belongs in `knowledge_base/` (north star, variants, memories). Also `SOUL.md`'s "single source of truth". |
| **I6** | **Broken and stale references.** (a) kb-builder reads `knowledge_base/profile_schema.md`, which doesn't exist; the schema is at `docs/profile_schema.md`. (b) preferences-setup reads `config/preferences.template.yaml`, which doesn't exist; it is at `templates/preferences.template.yaml`. (c) `/prep` with no arguments falls back to `postings/tracker.yaml` and an `interviewing` status, but neither exists any more (the tracker is now `applications.csv`). (d) `/cf-init` still creates `postings/tracker.yaml` with the old status set. (e) `docs/usage.md` documents `tracker.yaml`. (f) `templates/tracker.template.yaml` is orphaned. | `kb-builder.md:22`; `preferences-setup.md` (2 refs); `prep.md:5`; `cf-init.md:146-160`; `docs/usage.md` | (none: these are plain correctness bugs) |
| **I7** | **Two scoring rubrics disagree.** The same posting gets a different score depending on whether it arrives through `/score` or `/scan`. | `scorer.md` Step 4 (weights 30/25/15/10/10/10; tiers 80/60/40); `job-scanner.md` Step 5 (weights 25/25/12.5×4; tiers 75/60/45) | The project's single-source-of-truth principle. **[skills]**: shared reference files. |
| **I8** | **Framing files are wired into some deliverables and not others.** `interview-prep`, `scorer`, `job-scanner` and `story-capture` never read `knowledge_base/memories/`. `scorer` and `job-scanner` ignore the north star's not-targeted list, even though `north-star.md` says it anchors "every resume, cover letter, and job score". `interview-prep` never reads `postings/journal/<company>.md`, which is where recruiter and interviewer names are recorded, so it can't break a loop down by interviewer. | `grep` of path references per agent (see Appendix A.2); `north-star.md` intro; your auto-memory note "interview-prep not yet wired to the folder" | Global Rule 14 ("Read `knowledge_base/memories/` before producing any deliverable"). |
| **I9** | **Commands are thin, frontmatter-less wrappers, which makes routing weak.** None of the 16 command files has frontmatter. Their listed descriptions are their first lines, such as "Use the kb-builder agent to ingest…", which describe implementation rather than user intent. `/cf-init`, which clones a repo and runs `pip install`, can be invoked by the model. | `.claude/commands/*.md`; this session's skill listing shows exactly those first lines | **[skills]**: "Custom commands have been merged into skills"; commands still work, but skills add supporting files, `description`/`when_to_use`, `argument-hint`, `disable-model-invocation`, and `context: fork` + `agent:` to run a skill as a named subagent. "For a new command, use a skill" (**[claude-directory]**). |
| **I10** | **Agent descriptions route by name, not intent.** `job-scanner` and `company-scanner` say "Use when the user runs /scan…". `scorer` claims "when asked to find relevant opportunities", which overlaps job discovery. `preferences-setup` has no "use when" clause. Nothing routes "research this company" or "negotiate my offer", even though both capabilities exist inside interview-prep sub-tasks. | Frontmatter in Appendix A.2 | **[sub-agents]**: Claude delegates based on `description`; keep descriptions short and phrased as when to use the agent. |
| **I11** | **The KB schema is defined in three places and they disagree.** `docs/profile_schema.md` says the performance-review sections are archived. `templates/candidate_profile.template.yaml` still has them at the top level. `kb-builder.md` "Merge strategy" still tells the builder to write them. The schema also has no `source` field on certifications, awards, speaking, education or skills, although Global Rule 9 requires one for every fact. The live profile uses an undocumented `personal.languages_spoken`. Achievements have no stable `id`, and the leadership scope that Rule 8 requires has no structured field. | `docs/profile_schema.md`; `templates/candidate_profile.template.yaml:96-117`; `kb-builder.md:241-245`. Live profile structure: 76 achievements, all with `source`; `source` on 6 of 17 publications and 5 of 16 projects, and absent from certifications, awards and speaking. | Single source of truth. Global Rules 8 and 9. |
| **I12** | **Staleness is detected only inside kb-builder.** `ingestion_progress.yaml` has hashes, but nothing else checks it. A new source file, a north star older than the profile, or a narrative older than the profile goes unnoticed until someone runs `/build-kb`. There is also no read-only "is my KB healthy?" check, even though the kb-builder description promises "verifying KB accuracy". | `kb-builder.md` Step 1; no audit mode in any file | (design gap) |
| **I13** | **Story capture breaks the provenance chain.** Captured stories are recorded with `source: story-capture-session-DATE`, which is not a file. The raw transcript is never saved to `sources/`, so a later `/build-kb` can't see it and `SOUL.md`'s "trace to the specific source document" isn't possible for these stories. | `story-capture.md` "Knowledge Base Integration" step 3 | `SOUL.md` "Traceability"; Global Rule 9. |
| **I14** | **Committed permissions are effectively "allow everything".** `Bash(*:*)` in the shared `settings.json` makes the other ~60 Bash entries meaningless and pre-approves any command, including `curl` and `git push`, for anyone who clones the repo. The `rm` deny rules are the only guard. | `.claude/settings.json` | **[settings]** *(summary)*: shared project settings are committed "so teammates get it"; personal convenience belongs in `settings.local.json`; `permissions.allow` applies after folder trust. |
| **I15** | **Scratch files and filename collisions.** Four agents write candidate content to `/tmp/…`, which is outside the gitignored tree and ambiguous on Windows (Git Bash `/tmp` and Python's view of `/tmp` differ). The scorer writes `lead_report_[YYYY-MM-DD].md`, so a second `/score` on the same day overwrites the first, which conflicts with Global Rule 2. The slug style differs across outputs (`resume_[company]_[role]`, `[company]_[role_short]_[date]/`, kebab-case CSV slugs). | `resume-writer.md` Step 5; `cover-letter.md` Step 6; `job-scanner.md:83-164`; `company-scanner.md:83-169`; `scorer.md` Step 6 | Global Rule 2. |
| **I16** | **Plugin distribution loses all of the project's rules.** In the "non-technical" plugin install path, the user's folder has no `.claude/CLAUDE.md`, and **[plugins/components]** says plugins can't ship a CLAUDE.md that loads as context ("put them in a skill"). Plugin users get no Global Rules, no onboarding and no dispatcher. The manifest is also at the repo root, while **[plugins/manifest-reference]** documents `.claude-plugin/plugin.json`; whether a root manifest is accepted isn't stated. | `plugin.json`, `README.md` "Primary path", `cf-init.md` (writes no CLAUDE.md) | **[plugins/components]**, **[plugins/manifest-reference]** |
| **I17** | **Model choices are dated or implicit.** `job-scanner` pins a full dated model ID instead of an alias. `company-scanner` sets no model, so it inherits the main session's model (possibly Opus) for bulk classification. The writing agents all use `sonnet`; that's reasonable, but the highest-stakes prose (resume, north star) might justify a stronger model. | Agent frontmatter | **[sub-agents]**: `model` accepts aliases (`haiku`, `sonnet`, `opus`, `inherit`); if omitted, the parent's model is used (after `CLAUDE_CODE_SUBAGENT_MODEL`); "Control costs by routing tasks to faster, lower-cost models like Haiku." |
| **I18** | **Reference material sits in odd places.** `.claude/agents/templates/interview-prep-formats.md` lives inside the agents directory with no frontmatter; it's unclear whether the agent loader ignores it or warns. There are two `templates/` folders with different meanings. `roadmap/` is undated planning material mixed in with live docs. | Tree in Appendix A.1 | **[claude-directory]**: `agents/` files need `name` + `description`; skills hold supporting files next to `SKILL.md`. |

**Considered, no change proposed:**
- **AGENTS.md.** **[memory]** says Claude Code reads AGENTS.md only as a fallback when no CLAUDE.md exists, and suggests `@AGENTS.md` to share one file across tools. You use only Claude Code, so a second instruction file would just be something to keep in sync.
- **Output styles.** **[output-styles]** says a custom style drops Claude Code's software-engineering instructions and applies to the main thread only, not subagents. CareerForge still runs scripts and edits files, and its tone rules belong in the memories and the start skill. A style adds little here.
- **Splitting the 107 KB profile.** Every deliverable agent reads roughly 40k tokens of profile plus narrative. That's acceptable at this size, and splitting it would complicate every reader. Revisit only if the profile doubles.

---

# Part B: Change proposals

Dependency order follows the numbering where possible. Each proposal stands on its own.

---

### C1: Fix broken references and retire the old tracker
**Category:** hygiene · **Priority:** must · **Effort:** S · **Risk:** none (every target path verified on disk) · **Depends on:** none

**Files:** modify `.claude/agents/kb-builder.md`, `.claude/agents/preferences-setup.md`, `.claude/commands/prep.md`, `.claude/commands/cf-init.md`, `docs/usage.md`; delete `templates/tracker.template.yaml`.

**Current → proposed:**
- `kb-builder.md:22` `knowledge_base/profile_schema.md` → `docs/profile_schema.md`.
- `preferences-setup.md` `config/preferences.template.yaml` (2×) → `templates/preferences.template.yaml`.
- `prep.md` no-argument fallback: "check `postings/tracker.yaml` for … 'interviewing'" → "read `postings/applications.csv`, take the latest row per slug, and pick the most recent application whose status is one of `recruiter_screen`, `hm_screen`, `technical_screen`, `in_loop`; if several, ask which."
- `cf-init.md`: stop generating `postings/tracker.yaml`. Instead create `postings/applications.csv` with the header row from `templates/applications_csv.template.md` and create `postings/journal/`. Add `output/career_paths` and `output/career_exploration` to the `mkdir` list.
- `docs/usage.md`: replace the `tracker.yaml` sections with a pointer to `templates/applications_csv.template.md`.

**Why:** I6. Today kb-builder can't read the schema it's told to follow, preferences-setup can't find its template, and `/prep` with no argument fails silently.
**Outcome:** every path in an agent or command resolves, and a fresh `/cf-init` workspace matches the tracker the rest of the system uses.

---

### C2: Move candidate-specific content out of committed files
**Category:** hygiene · **Priority:** must · **Effort:** M · **Risk:** resume output could change if the moved rules aren't picked up. Mitigation: move each rule into a KB file the agent already reads, and diff one resume before and after. · **Depends on:** none

**Files:** modify `.claude/agents/resume-writer.md`, `.claude/agents/job-scanner.md`, `.claude/agents/company-scanner.md`, `.claude/commands/scan-companies.md`, `.claude/CLAUDE.md`, `.claude/commands/track.md`, `docs/usage.md`. Gitignored files I would write with your approval: `knowledge_base/resume_variants.md`, `knowledge_base/memories/*.md`, `config/preferences.yaml`.

**Proposed:**
- **resume-writer:** replace the candidate's certification line, internal-jargon examples and named role lenses with generic rules, such as "Lead with the certifications the chosen variant lists; summarize the rest in one line" and "Translate employer-internal terms (see `knowledge_base/memories/`)". The specific content moves to `resume_variants.md` (certifications per variant) and a memory file (the internal-to-external term table).
- **job-scanner:** "Match core skills (…) heavily" becomes "Weight the skills and domains in `config/preferences.yaml` `soft_preferences.preferred_domains` and the north star's first-ranked lens." This merges with C13 if you accept both.
- **scan-companies / company-scanner:** the fixed location, comp-floor and IC rules move to a `company_scan_criteria:` block in `config/preferences.yaml` (gitignored). The command and agent read it from there.
- **CLAUDE.md, track.md, usage.md:** replace real names and roles in examples with neutral placeholders ("Recruiter called, said feedback was strong").
- **Optional:** `config/company_targets.yaml` lists the companies you target. Rename it to `templates/company_targets.template.yaml` with two example companies and gitignore the real file. I'm only flagging this; whether a target list is sensitive is your call.

**Why:** I5. These files are public and generic by design (Global Rule 1 puts framing in `knowledge_base/`). Today a second user who clones the repo gets your certifications in their resume rules.
**Outcome:** the repo is shareable as-is, and your own behavior is unchanged because the rules move to files the agents already read.

---

### C3: Make committed permissions conservative
**Category:** hygiene · **Priority:** should · **Effort:** S · **Risk:** you see a few more permission prompts until you add the broad rules to your local settings · **Depends on:** none

**Files:** modify `.claude/settings.json` and `.claude/settings.local.template.json`.

**Proposed:** remove `Bash(*:*)` and the entries it was hiding that aren't needed (`curl`, `chmod`, `env`, `export`, `set`, `xargs`, `tee`, `zip`). Keep the project's real needs: `python`, `python3`, `rg`, `git` read verbs (`git status`, `git diff`, `git log`), `pdftotext`, `sqlite3`, `ls`, `wc`, `find`, `mkdir`, `cp`. Keep the `rm` denies and add `Bash(git push:*)` to `deny`. Move anything you personally want auto-approved into `settings.local.json`, which is already gitignored. Put a commented example in the template.

**Why:** I14. **[settings]** says shared project settings are what every teammate gets, and personal settings belong in local.
**Outcome:** anyone cloning the repo gets a safe default, and your workflow is unchanged once your local file is set.

---

### C4: Create a small set of shared reference files
**Category:** context efficiency · **Priority:** should · **Effort:** M · **Risk:** low; agents keep a one-line summary of each rule in case a read is skipped · **Depends on:** none

**Files:** create `.claude/reference/achievement-format.md`, `.claude/reference/kb-context.md`, `.claude/reference/output-naming.md`. Modify the agents that restate them: `kb-builder`, `story-capture`, `resume-writer`, `cover-letter`, `interview-prep`, `scorer`, `career-explorer`, `north-star`.

`.claude/reference/` isn't a Claude Code-managed directory, so nothing in it auto-loads. Agents read these files by path when they need them.

**Proposed contents:**
- `achievement-format.md`: the XYZ formula and field mapping (`description`=X, `metrics`=Y, `impact`=Z), the leadership-scope requirement, the "(unquantified)" convention, verb-fidelity ("match the KB's verb"), and the banned-word list. It is restated in 8 files today.
- `kb-context.md`: the KB gate (profile exists and `personal.name` isn't the template default), which files are evidence and which are framing, "read every file in `knowledge_base/memories/`", and the `rg --no-ignore` rule for gitignored paths. It is restated in 7 files today.
- `output-naming.md`: one naming rule for every deliverable (see C17).

Agent change pattern:
```markdown
## Knowledge base
Read `.claude/reference/kb-context.md` and follow it. Short version: profile + narrative are evidence; north star, variants and memories are framing only.
```

**Why:** I7, I8, I11 stem from rules being restated. **[skills]** recommends keeping long instructions concise and moving reference material into files that load on demand.
**Outcome:** each rule is edited in one place. Agents get roughly 1–2k tokens shorter, and the rule set stops drifting.

---

### C5: Path-scoped rules for the tracker and the KB
**Category:** context efficiency · **Priority:** should · **Effort:** S · **Risk:** a rule loads only once a matching file is touched, so each one keeps a one-line pointer in CLAUDE.md · **Depends on:** none (pairs with C9)

**Files:** create `.claude/rules/tracker.md` and `.claude/rules/knowledge-base.md`.

```markdown
---
paths:
  - "postings/**"
---
# Application tracker rules
- `postings/applications.csv` is append-only: one row per status transition; never edit or delete rows.
- Valid statuses: discovered, saved, researching, applying, applied, recruiter_screen, hm_screen,
  technical_screen, in_loop, loop_completed, offer_pending, offered, negotiating, accepted,
  rejected, withdrawn, on_hold, standby, ghosted, closed.
- A message with a status change AND narrative = one CSV row + one journal entry, in the same reply.
- Schema and journal format: `templates/applications_csv.template.md`.
```

`knowledge-base.md` would use `paths: ["knowledge_base/**"]` and carry the provenance rule (`source` on every fact, `"unverified"` when unknown), "validate YAML after every write", and "kb-builder never edits `north_star.md` or `resume_variants.md`".

**Why:** **[memory]** says a rule with `paths` loads when Claude reads, writes or edits a matching file, including single-file `cat`/`head`, and that only-sometimes-relevant rules belong there. Global Rule 10's 20-status enum is in every session and every subagent today, even ones that never touch the tracker.
**Outcome:** about 25 lines leave the always-loaded context, and they still appear exactly when the tracker or KB is touched, in the main session or a subagent.

---

### C6: Convert the remaining commands to skills, with intent-first descriptions
**Category:** structure / routing · **Priority:** should · **Effort:** M · **Risk:** low. Slash names stay identical. A skill and a command with the same name resolve to the skill (**[skills]**), so each command file is deleted when its skill lands. · **Depends on:** none. C7, C8, C11 and C15 each create their own skill, and this change covers the rest.

**Files:** move `.claude/commands/{build-kb,resume,cover-letter,score,explore,scan,scan-companies,analytics,track,journal,status,cf-init}.md` → `.claude/skills/<name>/SKILL.md`. Move `templates/applications_csv.template.md` content into `.claude/skills/track/schema.md` and leave a pointer behind. Delete `.claude/commands/` once it's empty.

**Two patterns:**

*Agent-backed skills* (`build-kb`, `resume`, `cover-letter`, `score`, `explore`, `scan`, `scan-companies`) run as the named subagent:
```yaml
---
name: resume
description: >
  Tailor a resume (.docx + .pdf) to a specific job posting, grounded only in the
  knowledge base. Use when the user wants a resume for a role, pastes a posting and
  says "apply", "tailor", or "update my resume for this".
argument-hint: "[posting URL, pasted text, or postings/<slug>]"
context: fork
agent: resume-writer
background: false
---
Create a tailored resume for this posting: $ARGUMENTS
```
*Inline skills* (`track`, `journal`, `status`, `analytics`) run in the main conversation, as they do today.

*Setup:* `cf-init` gets `disable-model-invocation: true`, so it runs only when you type it: it clones a repo and installs packages.

**Why:** I9, I10. **[skills]**: commands are merged into skills; skills add supporting files, `description`, `argument-hint`, invocation control, and `context: fork` with `agent:`. Descriptions are what Claude routes on, and today they read "Use the kb-builder agent…".
**Outcome:** plain-language requests match on intent words. The wrapper-to-agent link becomes declarative (`agent: resume-writer`) instead of prose. Supporting files become possible.

The `context: fork` + `agent` + `background` fields come from a summarized section of the skills page. Verify them on one skill before converting the rest.

---

### C7: Turn the three interview-style agents into inline skills
**Category:** agent design · **Priority:** must · **Effort:** M · **Risk:** the north-star derive step reads the full KB (about 40k tokens) into the main conversation rather than a separate context. Accept that, or keep a read-only fork for the derive step only (described below). · **Depends on:** none

**Files:** move `.claude/agents/story-capture.md` → `.claude/skills/capture-story/SKILL.md`, `.claude/agents/north-star.md` → `.claude/skills/north-star/SKILL.md`, `.claude/agents/preferences-setup.md` → `.claude/skills/setup-preferences/SKILL.md`. Delete the three agent files and their command wrappers. Update `plugin.json`.

```yaml
---
name: capture-story
description: >
  Interview the candidate about a project or achievement and add it to the knowledge
  base in XYZ form. Use when they say "I worked on…", "add this to my profile",
  "new achievement", or paste a brain dump or transcript about past work.
argument-hint: "[optional transcript or brain dump]"
---
```
The body is the current agent text, unchanged except that "you" now runs in the main thread. Its "ask one question, wait" rules now work as written.

**Alternative for north-star only:** keep a read-only `north-star-derive` agent (`tools: Read, Grep, Glob, Bash`) that returns the hypothesis. The inline skill calls it, then runs the interview. That's more pieces, so I'd only do it if the main-context cost bothers you.

**Why:** I1. **[sub-agents]**: subagents get a fresh context, no `AskUserQuestion`, and return one final message, in the background by default. **[skills]**: an inline skill's body loads only on invocation and runs in the conversation.
**Outcome:** interviews actually converse with you. No relay through the main session, no risk of the main session answering on your behalf, and the instructions are in front of the model that's asking the questions.

---

### C8: State-aware start (the "self-describing on startup" experience)
**Category:** onboarding / routing · **Priority:** must · **Effort:** M · **Risk:** the first reply of each session costs about 3–6 file checks (Glob/Read) · **Depends on:** none (C9 removes the old onboarding text; C10 optionally automates the checks; C15 supplies the deeper staleness check)

**Files:** create `.claude/skills/start/SKILL.md` and `.claude/skills/start/routing.md`. Add a short "First message" section to `.claude/CLAUDE.md`.

**Mechanism comparison** (Claude Code never speaks first; something must run on your first message):

| Option | How it works | Pros | Cons |
|---|---|---|---|
| (a) CLAUDE.md instruction | "Before replying to the first message, run the state check" | Markdown only; always in context; works for clone installs | Costs a few tool calls on turn 1; it's an instruction, not enforced (**[memory]**); absent in plugin installs (I16) |
| (b) SessionStart hook | A command prints state facts, injected before the first prompt (**[hooks]** *(summary)*) | Zero tool calls; reliable; the only option that reaches plugin installs via `hooks/hooks.json` | Needs a shell command, which breaks your markdown-only rule; Windows shell differences; output capped at 10,000 characters |
| (c) `/start` skill | The state table and openings live in a skill, loaded when relevant or typed | Markdown only; costs nothing until used; doubles as "where am I?" | Auto-invocation from a description isn't guaranteed |

**Recommendation: (a) + (c) now, (b) as optional C10.** CLAUDE.md carries about 8 lines that say *when* to check and *which* files to look at. The skill carries the full state table, the openings and the routing map. If you accept C10, the hook supplies the facts and the same skill interprets them.

**CLAUDE.md snippet:**
```markdown
## First message of a session
Unless the message is a slash command, determine the workspace state before replying:
check knowledge_base/sources/, knowledge_base/candidate_profile.yaml (template if
personal.name is "Your Name"), config/preferences.yaml, and the latest rows of
postings/applications.csv. Then follow the `start` skill: open with the line for that
state, and answer what the user actually asked in the same reply.
```

**States, detection (files only), and openings:**

| # | State | Detected by | Opening (Claude adapts, then answers the user's actual message) |
|---|---|---|---|
| S0 | Not initialized | `knowledge_base/` or `config/` missing (a plugin user before `/cf-init`) | "This folder isn't set up for CareerForge yet. Want me to set it up now? It takes about a minute." |
| S1 | Nothing yet | `knowledge_base/sources/` has only `.gitkeep`, and the profile is missing or the template | "No career material yet. Drop your resume, LinkedIn PDF, reviews or project write-ups into `knowledge_base/sources/` and I'll build your profile (best results). Or, if you have a specific job or interview right now, I can start there without a profile." |
| S2 | Sources, no KB | Sources present; profile missing or template | "I can see N files in your sources but no profile yet. Want me to build it now (about 5 minutes), or start with just your latest resume so we can move faster?" |
| S3 | KB stale | A source path isn't listed in `ingestion_progress.yaml`, or an entry is `pending`/`modified`/`error`; or `north_star.md` is older than `candidate_profile.yaml` | "Your profile is built, but N source files have changed or were added since the last build. Want me to fold them in first? Everything else works now either way." |
| S4 | KB ready, no filters | Profile real; `config/preferences.yaml` missing or template | "Your profile is ready. Two minutes on your search filters (location, salary floor, role types) and scoring gets much sharper. Want to do that now?" |
| S5 | Ready | Profile + preferences real | "Your profile is ready. I can tailor a resume to a posting, research a company, prep you for an interview loop, find and score new roles, or update your tracker. What's going on?" |
| S6 | Active pipeline (adds to S3–S5) | `applications.csv` latest status per slug in `recruiter_screen`…`loop_completed`, `offered` or `negotiating`; flag 14+ days without a change | Adds one line: "You have 2 active interview processes (one in loop, one waiting 16 days on a recruiter screen). Want to pick one up?" |

States are checked in order S0→S5, and S6 is appended to whichever applies. If the user's message already states an intent, the opening shrinks to one clause and the work starts. "I have an interview Tuesday" in S1 gets: "No profile yet, so I'll prep you from the posting and public research, and we can add your stories after. What's the posting?"

The "modified file" case (same path, new content) is only detectable through the hashes kb-builder computes. The start check catches added files and pending entries. A deeper check is C15.

**Routing map** (in `routing.md`; slash commands stay as optional shortcuts):

| Plain-language intent (examples) | Route | Needs | If the state is missing |
|---|---|---|---|
| "hi", "help", "where was I?" | `start` opening for the state | none | n/a |
| Pastes a posting or URL with no instruction | Check the tracker: if that company or role has an interview status → offer prep; otherwise ask the 5-option question (score / resume / cover letter / prep / full package) | none | n/a |
| "Is this a good fit?", "score this" | `score` | KB optional | No KB: job-quality mode, with the existing banner |
| "Tailor my resume for this", "apply to X" | `resume` (or the full-package chain) | KB required | Offer a **quick build** (ingest only the `Resumes and mind maps/` folder, about 2 minutes, using kb-builder's existing priority order) or the full build. No resume without a KB (`SOUL.md`). |
| "Write a cover letter" | `cover-letter` | KB required | Same as resume |
| "I got an interview at X", "prep me for Tuesday" | **Interview chain** (below) | KB optional | No KB: prep without the story bank, then offer `capture-story` for the gaps |
| "Research company X", "what do you know about X?" | `research-company` (C11) | none | n/a |
| "They made me an offer", "how do I negotiate?" | `track offered` → compensation research (C11) → journal | KB optional | No KB: market ranges only |
| "Find me jobs", "what's new?" | `scan` (named companies in `company_targets.yaml` → `scan-companies`) | KB + preferences | Offer `setup-preferences` first |
| "I applied to X", "rejected by Y", "recruiter called…" | `track` (+ journal if narrative) | none | n/a |
| "Note that…", "remember what the recruiter said" | `journal` | none | n/a |
| "I worked on X", "add this project", pasted brain dump about past work | `capture-story` | KB recommended | No KB: offer build first; a story can still be saved to `sources/` (C16) |
| "I added new files", "update my profile" | `build-kb` | sources | n/a |
| "Is my profile up to date?", "check my KB" | `kb-check` (C15) | KB | Treat as S1/S2 |
| "What roles fit me?", "what should I target?" | `explore` | KB | Offer build first |
| "What's my positioning?", "where am I headed?" | `north-star` | KB | Offer build first |
| "Only remote", "raise my salary floor" | `setup-preferences` (text mode) | none | n/a |
| "Status?", "what should I do today?" | `status` (+ scan suggestion if last scan is 3+ days old) | tracker | "No applications tracked yet." |

**One-question rule:** ask a clarifying question only when two routes would produce different saved artifacts *and* neither the message, the workspace state nor the tracker settles it. Ask one question with numbered options and the likely one first. Otherwise pick, say in one line what you're doing, and start. Never ask for something that's already on disk.

**Chained workflows** (each step offered, not forced; steps already done are skipped):
- **Interview chain:** `track` (status → interview stage) → `journal` (who, when, round) → `research-company` (reused if `postings/<slug>/company_research.md` is under 30 days old) → `prep` (journal interviewer and round info take precedence over public research) → story gaps → offer `capture-story`.
- **Apply chain** (keeps today's): score → resume → cover letter → `track applying`.
- **New material chain:** `build-kb` → `kb-check` → if new evidence touches a role lens, offer `north-star refresh`.
- **Offer chain:** `track offered` → compensation research → journal.

**Why:** I2, I10, and the target experience you described.
**Outcome:** any first message gets a reply that reflects the real state. No name needs to be known. Ambiguity costs at most one question.

---

### C9: Lean CLAUDE.md that imports SOUL.md
**Category:** context efficiency · **Priority:** must · **Effort:** S · **Risk:** a rule could get lost in the move. Mitigation: line-by-line mapping in the diff summary. · **Depends on:** C8 (onboarding and dispatcher move there). C5 is recommended (tracker detail moves there).

**Files:** modify `.claude/CLAUDE.md`.

**Proposed shape (about 75 lines, plus 55 imported from SOUL.md):**
```markdown
# CareerForge
Multi-agent job search for a single candidate. Integrity rules: @../SOUL.md

## First message of a session        ← C8 snippet (8 lines)
## Where things live                 ← 12 lines: only gitignored or non-obvious paths
## Core principles                   ← unchanged (4 lines)
## Global rules                      ← the 15 rules, each 1–2 lines; detail → .claude/reference/ and rules/
```
Removed from always-loaded context: the Onboarding flows A–E, the Intent Dispatcher table, the multi-step and compound sections (all moved to the `start` skill), and the long directory tour. Per **[best-practices]**, discoverable layout is left out; gitignored paths stay listed because Grep can't see them.

`@../SOUL.md`: per **[memory]**, imports resolve relative to the importing file, so from `.claude/CLAUDE.md` the path is `../SOUL.md`. Imports load at startup with the importing file.

**Why:** I3. **[memory]**: under 200 lines; procedures go in skills. **[sub-agents]** *(summary)*: non-fork subagents load CLAUDE.md, so this saving applies 11 times over.
**Outcome:** CLAUDE.md itself shrinks by about 60%. Even after adding SOUL.md, always-on context per session and per subagent drops by about 30%, and the integrity core (`SOUL.md`) is actually loaded for the first time.

---

### C10 (optional): SessionStart hook that injects state facts
**Category:** onboarding · **Priority:** nice-to-have (should, if you distribute as a plugin) · **Effort:** S · **Risk:** shell portability: on Windows without Git Bash the hook shell is PowerShell (**[hooks]**), and this one-liner would fail. A failure is non-blocking and C8's markdown check still runs, so the downside is only losing the speed-up. · **Depends on:** C8

**This is the one non-markdown exception.** It adds a hook entry to `.claude/settings.json` (and, for plugin users, `hooks/hooks.json` using `${CLAUDE_PLUGIN_ROOT}`). It adds no script file.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          {
            "type": "command",
            "timeout": 10,
            "command": "cd \"$CLAUDE_PROJECT_DIR\" && echo '[CareerForge state]' && echo \"sources=$(find knowledge_base/sources -type f ! -name .gitkeep 2>/dev/null | wc -l)\" && echo \"profile=$(grep -q 'Your Name' knowledge_base/candidate_profile.yaml 2>/dev/null && echo template || ([ -f knowledge_base/candidate_profile.yaml ] && echo ready || echo missing))\" && echo \"preferences=$([ -f config/preferences.yaml ] && echo present || echo missing)\" && echo \"sources_newer_than_last_build=$(find knowledge_base/sources -type f ! -name .gitkeep -newer knowledge_base/ingestion_progress.yaml 2>/dev/null | wc -l)\" && echo \"north_star=$([ -f knowledge_base/north_star.md ] && echo present || echo missing)\" && echo \"tracker_rows=$(($(wc -l < postings/applications.csv 2>/dev/null || echo 1)-1))\" && echo 'Interpret with the start skill.'"
          }
        ]
      }
    ]
  }
}
```

Plain stdout from a SessionStart hook is added to Claude's context (**[hooks]** *(summary)*). It prints facts only; the `start` skill interprets them. The newer-than check uses file modification times, so a file copied with its original timestamp can be missed. kb-builder's hashes remain the real check.

**Markdown-only alternative:** C8 on its own (Claude runs the same checks with Glob/Read on the first message).
**Why:** I2, I16. It's faster and more reliable than an instruction, and it's the only mechanism that reaches plugin installs.
**Outcome:** Claude has the state before you type, at zero tool calls.

---

### C11: Interview-prep orchestration in a skill, plus a company-research route
**Category:** agent design / routing · **Priority:** must · **Effort:** M · **Risk:** low; the agent's `task_type` contract is unchanged · **Depends on:** none (C12 adds the journal and memories inputs)

**Files:** create `.claude/skills/prep/SKILL.md` and `.claude/skills/research-company/SKILL.md`. Move `.claude/agents/templates/interview-prep-formats.md` → `.claude/skills/prep/formats.md` and update the 5 path references in `interview-prep.md`. Delete `.claude/commands/prep.md` and the empty `.claude/agents/templates/`.

**`prep` (inline skill, because it orchestrates parallel subagents from the main session):**
1. Resolve the posting: argument, `postings/<slug>/`, or the tracker fallback from C1.
2. Create `output/interview_prep/<slug>_<date>/`.
3. Read `postings/journal/<company>.md` for known rounds and interviewers. Insider facts beat public research (this is already your memory rule).
4. In parallel, run `interview-prep` subagents with `task_type: process_research` (seeded with the journal facts), `company_research` (skipped if under 30 days old) and `compensation_research`.
5. Parse `ROUNDS_DATA` from `00_interview_process.md`, then launch one `round_prep` per round in parallel, passing the named interviewer and role if known.
6. Run `story_bank`, then report gaps and offer `capture-story`.

**`research-company`:** `context: fork`, `agent: interview-prep`, body "`task_type: company_research` for $ARGUMENTS; write to `postings/<slug>/company_research.md`". Description: "Research a company's mission, recent news, culture and products. Use for 'tell me about X', 'research X before my call'."

**Compensation and offer route:** add one line to the `prep` skill: "`/prep comp <posting>` runs only `compensation_research`". Routed from "negotiate" and "is this offer good?".

**Why:** I4, I8, I10. **[skills]**: procedures and supporting files belong in skills. The main session can only follow an orchestration protocol it can read.
**Outcome:** the parallel per-round pipeline runs deterministically. Prep becomes interviewer-aware from your journal, and "research X" and "negotiate" have routes.

---

### C12: Wire the framing files into every deliverable agent
**Category:** agent design · **Priority:** should · **Effort:** S · **Risk:** scores may shift slightly when not-targeted roles get flagged; that's the intent · **Depends on:** C4 (one shared `kb-context.md` to point at)

**Files:** modify `interview-prep.md`, `scorer.md`, `job-scanner.md`, and `capture-story` (after C7).

**Proposed:**
- All four read `knowledge_base/memories/` (Global Rule 14).
- `scorer` and `job-scanner` read the north star's role lenses and not-targeted list. A match on the not-targeted list is reported as "NOT TARGETED: <reason>" rather than silently scored low.
- `interview-prep` `round_prep` reads the north star's "How to apply" section, so answer angles use the chosen lens.

**Why:** I8.
**Outcome:** the corrections you already wrote into memories apply to prep packs and scores too, and the north star finally anchors scoring as the north-star agent claims it does.

---

### C13: One scoring rubric
**Category:** single source of truth · **Priority:** should · **Effort:** S · **Risk:** historical scores in `data/jobs.db` and in old reports stay on the old weights, so they aren't comparable with new ones. **You need to pick the weights and tiers.** · **Depends on:** C4

**Files:** create `.claude/reference/scoring-rubric.md`; modify `scorer.md` Step 4 and `job-scanner.md` Step 5.

**Proposed:** one table of six dimensions using the JSON keys the scripts already expect (`skill_match`, `experience_alignment`, `domain_fit`, `growth_potential`, `company_quality`, `preference_match`), plus one set of weights, one set of tier thresholds, the MQ cap rule (from scorer) and the company-quality guide (from job-scanner). My suggested default is scorer's weights with job-scanner's tier names. `update_scores.py` needs no change, because it receives the same keys.

**Why:** I7.
**Outcome:** a posting gets the same score whether you paste it or the scanner finds it.

---

### C14: One KB schema, extended additively
**Category:** KB · **Priority:** should · **Effort:** M · **Risk:** low; every new field is optional, so the current profile stays valid. kb-builder fills new fields on its next run and never back-fills invented values. · **Depends on:** C1 (the schema path fix)

**Files:** modify `docs/profile_schema.md` (canonical), `templates/candidate_profile.template.yaml` (example only; header comment points to the schema), and `kb-builder.md` (delete the stale performance-review "Merge strategy").

**Proposed schema changes:**
```yaml
experience:
  - company: ""
    # ...
    achievements:
      - id: "ach-<company>-<short-slug>"   # NEW optional: stable key for variants, story bank, prep
        description: ""                    # X
        metrics: ""                        # Y, or "(unquantified)"
        impact: ""                         # Z
        leadership:                        # NEW optional: Rule 8 as structure, not prose
          team_size: ""                    # e.g. "8 direct, 30 cross-functional"
          scope: ""                        # team | cross-functional | org | company
          formal: true
        tags: []                           # NEW optional: free-form themes (lens matching, prep)
        skills_used: []
        source: ""                         # required (unchanged)
certifications: [{ ..., source: "" }]      # NEW optional source on every section (Rule 9)
awards:         [{ ..., source: "" }]
speaking:       [{ ..., source: "" }]
education:      [{ ..., source: "" }]
personal:
  languages_spoken: []                     # document what the live profile already uses
```
Plus a short "Growing the schema" note: add optional fields only, update this file first, then kb-builder.

**Why:** I11.
**Outcome:** one schema to read. Stable IDs let `resume_variants.md` and story banks point at achievements instead of copying text. Provenance becomes possible for every section.

---

### C15: Read-only KB health check
**Category:** KB · **Priority:** should · **Effort:** S · **Risk:** none (read-only) · **Depends on:** none (C8's S3 state uses it when present)

**Files:** create `.claude/skills/kb-check/SKILL.md` (inline; tools Read, Glob, Bash for `rg --no-ignore` and the YAML parse).

**Checks and report:**
- **Sources:** files not in `ingestion_progress.yaml`; entries marked pending, error or removed; mtime newer than `last_run`.
- **Provenance:** `source` values pointing to files that no longer exist; count of `unverified`.
- **XYZ gaps:** achievements with `(unquantified)` or empty metrics, so you know what story capture should ask about.
- **Freshness:** `candidate_narrative.md`, `north_star.md` and `resume_variants.md` older than `candidate_profile.yaml`.
- **Validity:** `candidate_profile.yaml` parses.

Ends with the recommended next action (`build-kb`, `capture-story` or `north-star refresh`).

Description: "Check whether the career knowledge base is current and complete. Use for 'is my profile up to date?', 'what's missing from my KB?', or before an important application."

**Why:** I12; the kb-builder description promises "verifying KB accuracy", but no mode does it.
**Outcome:** staleness and gaps become visible without running a full rebuild.

---

### C16: Story capture writes its source file
**Category:** KB · **Priority:** nice-to-have · **Effort:** S · **Risk:** kb-builder could re-ingest a story and duplicate it. Mitigation: story capture registers the file as `ingested` (with its hash) in `ingestion_progress.yaml` in the same step. · **Depends on:** C7

**Files:** modify `.claude/skills/capture-story/SKILL.md`.

**Proposed:** after confirmation, save the confirmed story (Q&A or transcript) to `knowledge_base/sources/Stories/<YYYY-MM-DD>-<slug>.md`. Set each achievement's `source` to that path. Add the file to `ingestion_progress.yaml` as `ingested`, and add a `source_index.md` row as today.

**Why:** I13.
**Outcome:** every captured story traces to a real document, and a future full rebuild keeps it instead of losing it.

---

### C17: Scratch space and collision-free filenames
**Category:** hygiene · **Priority:** should · **Effort:** S · **Risk:** low; existing outputs are untouched · **Depends on:** C4 (the rule lives in `output-naming.md`)

**Files:** modify `resume-writer.md`, `cover-letter.md`, `job-scanner.md`, `company-scanner.md`, `scorer.md`.

**Proposed:**
- `/tmp/...` → `output/.work/...`. It's already gitignored by `output/**`, it resolves the same way on Windows and Mac, and candidate data stays inside the project.
- The scorer writes `lead_report_<slug>_<YYYY-MM-DD>.md` for a single posting and `lead_report_batch_<YYYY-MM-DD>_<HHMM>.md` for several.

**Why:** I15; Global Rule 2.
**Outcome:** no silent overwrite on the second `/score` of the day, and no personal data outside the ignored tree.

---

### C18: Agent frontmatter refresh (descriptions and models)
**Category:** agent design / routing · **Priority:** should · **Effort:** S · **Risk:** a model change alters cost and quality, so the model choices are yours to make · **Depends on:** none

**Files:** modify the frontmatter of all remaining agents.

**Proposed descriptions** (what the agent does and when to use it, no command names):
- `job-scanner`: "Discovers new roles on LinkedIn across saved search scopes, filters them on hard constraints, and scores the shortlist. Use for 'find me jobs', 'what's new', or a scheduled daily scan."
- `company-scanner`: "Checks the career pages of specific named companies for new postings and updates each company's tracker. Use when the user asks about openings at a particular target company."
- `scorer`: drop "when asked to find relevant opportunities" (that's discovery, which belongs to job-scanner).

**Models:** `job-scanner` gets `model: haiku` (an alias instead of the pinned dated ID). `company-scanner` gets `model: sonnet` (it sets nothing today, so it inherits the main model). For `resume-writer` and `cover-letter`, decide between `sonnet` (today's cost) and `opus` (stronger prose for the highest-stakes outputs); I'd lean `opus` for resume-writer only. North star is inline after C7, so it uses the session's model.

**Why:** I10, I17. **[sub-agents]**: delegation is driven by `description`; `model` accepts aliases.
**Outcome:** better automatic delegation, and the scanner follows model updates without edits.

---

### C19: One application slug everywhere
**Category:** naming · **Priority:** nice-to-have · **Effort:** M · **Risk:** low if applied only to new outputs; old files keep their names · **Depends on:** C4, C17

**Proposed:** the tracker's `{company}-{role-short}` kebab slug becomes the key for `postings/<slug>/`, `output/resumes/<slug>_resume_<date>.docx`, `output/cover_letters/<slug>_cover_letter_<date>.docx`, `output/interview_prep/<slug>_<date>/` and `postings/journal/<company>.md`. Every deliverable agent appends its output path to the application's CSV `output_files` via `track`.

**Why:** I15 (three slug styles today). You asked for outputs "organized per target company and role". This gets you that without restructuring `output/`.
**Outcome:** `status` can list everything produced for an application, and filenames sort by application.

---

### C20: Plugin packaging that carries the rules
**Category:** structure · **Priority:** nice-to-have · **Effort:** M · **Risk:** touches `scripts/create_plugin_zip.py` (existing Python), and the plugin path needs a real install test · **Depends on:** C6, C7, C8, C9 (the skills to package)

**Files:** move `plugin.json` → `.claude-plugin/plugin.json`; update the `skills` and `agents` lists; modify `scripts/create_plugin_zip.py` and `.claude/skills/cf-init/SKILL.md`.

**Proposed:** `cf-init` copies a workspace CLAUDE.md template (the lean C9 version) into the user's folder as `.claude/CLAUDE.md`. This is the markdown-only way to give plugin users the Global Rules and the first-message check. Optionally also ship C10's hook in `hooks/hooks.json`.

**Why:** I16. **[plugins/components]**: a plugin can't ship a CLAUDE.md that loads as context, and instructions go in skills. **[plugins/manifest-reference]**: the manifest lives at `.claude-plugin/plugin.json`.
**Outcome:** a plugin install behaves like a clone install.

---

# Part C: Decision table

| ID | Title | Priority | Effort | Depends on | Decision |
|---|---|---|---|---|---|
| C1 | Fix broken references, retire old tracker | must | S | none | |
| C2 | Move candidate-specific content out of committed files | must | M | none | |
| C3 | Conservative committed permissions | should | S | none | |
| C4 | Shared reference files | should | M | none | |
| C5 | Path-scoped rules (tracker, KB) | should | S | none | |
| C6 | Remaining commands → skills, intent-first descriptions | should | M | none | |
| C7 | Interview-style agents → inline skills | must | M | none | |
| C8 | State-aware start skill + routing map | must | M | none | |
| C9 | Lean CLAUDE.md importing SOUL.md | must | S | C8 (C5 recommended) | |
| C10 | Optional SessionStart hook | nice | S | C8 | |
| C11 | Prep orchestration skill + company research route | must | M | none | |
| C12 | Wire framing files into all deliverables | should | S | C4 | |
| C13 | One scoring rubric | should | S | C4 | |
| C14 | One KB schema, extended additively | should | M | C1 | |
| C15 | Read-only KB health check | should | S | none | |
| C16 | Story capture writes its source file | nice | S | C7 | |
| C17 | Scratch space + collision-free filenames | should | S | C4 | |
| C18 | Agent frontmatter refresh | should | S | none | |
| C19 | One application slug everywhere | nice | M | C4, C17 | |
| C20 | Plugin packaging that carries the rules | nice | M | C6–C9 | |

**Smallest set that delivers the target experience:** C1, C7, C8, C9, C11. Adding C2 makes the repo safe to share.

**After you decide:** I implement only the accepted changes, in dependency order, and show a diff summary after each. Old slash names keep working throughout. I finish by describing how a fresh session responds in each state S0–S6 and by running 8–10 plain-language requests through the routing map.

---

# Appendix A: Inventory

## A.1 File tree (relevant files)

| Path | Type | Purpose |
|---|---|---|
| `.claude/CLAUDE.md` | instruction | Onboarding flows, intent dispatcher, layout, 15 global rules (191 lines) |
| `SOUL.md` | instruction | Integrity values and boundaries (referenced, not imported) |
| `.claude/settings.json` | config | Shared permissions (broad allow, `rm` deny) |
| `.claude/settings.local.json` / `.local.template.json` | config | Personal permissions (gitignored) / starter |
| `.claude/agents/*.md` (11) | agent | See A.2 |
| `.claude/agents/templates/interview-prep-formats.md` | template | Output formats for prep sub-tasks |
| `.claude/commands/*.md` (16) | command | See A.3 |
| `plugin.json`, `marketplace.json` | config | Plugin manifest (repo root) and marketplace entry |
| `config/resume_style.yaml` | config | Resume formatting (committed) |
| `config/company_targets.yaml` | config | Company career-page targets (committed) |
| `config/preferences.yaml`, `config/search_scopes.yaml` | data | Hard and soft filters, LinkedIn scopes (gitignored) |
| `templates/*.template.*` (9) | template | Starters: profile, narrative, preferences, scopes, north star, memory, ingestion progress, tracker CSV doc, legacy `tracker.template.yaml` (orphaned) |
| `knowledge_base/sources/` (86 files, 10 folders) | data | Raw career material (gitignored) |
| `knowledge_base/candidate_profile.yaml` (107 KB) | data | Structured evidence |
| `knowledge_base/candidate_narrative.md` (58 KB) | data | Narrative evidence |
| `knowledge_base/source_index.md`, `ingestion_progress.yaml` | data | Provenance log, ingestion state with hashes |
| `knowledge_base/north_star.md`, `resume_variants.md`, `memories/` (4) | data (framing) | Positioning, lens→variant map, wording rules |
| `knowledge_base/candidate_summary_compact.md` | data | Compact summary for company-scanner (generated by script) |
| `knowledge_base/archive/` | data | Retired review YAML |
| `postings/<slug>/` (~14), `postings/candidates/`, `postings/archive/` | data | Posting text and company research per role |
| `postings/applications.csv`, `postings/journal/*.md` | data | Event-log tracker, per-company journals |
| `output/{resumes,cover_letters,interview_prep,lead_reports,analytics,career_exploration,career_paths,cheat_sheet,company_trackers}/` | output | Deliverables by type (gitignored); plus 2 loose files at `output/` root |
| `scripts/generate_docx.py`, `convert_docx_to_pdf.py`, `convert_md_to_pdf.py` | script | Document rendering |
| `scripts/linkedin/*`, `scripts/company_scanner/*`, `tools/linkedin_job_search/*` | script | Scanner pipelines |
| `scripts/setup_*`, `launch_*`, `create_plugin_zip.py`, `application_analytics.py` | script | Install, launch, packaging, analytics |
| `docs/profile_schema.md` | reference | Profile schema (one of three definitions) |
| `docs/usage.md`, `docs/linkedin-scanner.md`, `docs/company-scanner.md` | reference | User and reference docs (`usage.md` has stale tracker sections) |
| `docs/*.png`, `*.excalidraw`, `analytics_demo.html` | reference | Diagrams and demo |
| `roadmap/path-{0,1,3}-*.md` | reference | Future-direction notes |
| `README.md`, `LICENSE`, `pyproject.toml`, `requirements.txt` | meta | Project meta |

## A.2 Agents

None set `permissionMode`, `skills`, `memory`, `maxTurns` or `color`.

| Agent | Model | Tools | Trigger (description gist) | Reads | Writes | Depends on |
|---|---|---|---|---|---|---|
| kb-builder | sonnet | R W E Bash Grep Glob WebFetch | Ingest sources, rebuild, verify KB | sources/, memories/, `knowledge_base/profile_schema.md` (**missing**) | profile, narrative, source_index, ingestion_progress | none |
| story-capture | sonnet | R W E Bash Grep Glob | Add a project or achievement (interactive) | profile | profile, narrative, source_index | none |
| north-star | sonnet | R W E Bash Grep Glob | Define or refresh positioning (interactive) | profile, narrative, variants, memories, preferences, north_star, `output/career_paths/` | north_star.md | resume_variants consistency |
| preferences-setup | sonnet | R W E Bash | Set preferences (interactive or text) | preferences, `config/preferences.template.yaml` (**missing**) | preferences.yaml | none |
| resume-writer | sonnet | R W E Bash Grep Glob WebFetch WebSearch | Resume for a posting | profile, narrative, north_star, variants, memories, resume_style, preferences, postings/ | output/resumes (.docx/.pdf), /tmp JSON | generate_docx.py, convert_docx_to_pdf.py |
| cover-letter | sonnet | R W E Bash Grep Glob WebFetch WebSearch | Cover letter for a posting | profile, narrative, north_star, memories, postings/<role>/company_research.md | output/cover_letters (.docx/.pdf, app notes), /tmp JSON | generate_docx.py; interview-prep's research |
| interview-prep | sonnet | R W E Bash Grep Glob WebFetch WebSearch | Prep for an interview (5 `task_type`s) | profile, narrative, formats template, postings/ | output/interview_prep/<dir>/, postings/<role>/company_research.md | an undocumented orchestrator in the main session |
| scorer | sonnet | R W Bash Grep Glob WebFetch WebSearch | Score postings; also "find opportunities" | profile, preferences, postings/ | output/lead_reports/lead_report_<date>.md | none |
| career-explorer | sonnet | R W Bash Grep Glob WebFetch WebSearch | Discover best-fit roles | profile, narrative, north_star, preferences | output/career_exploration/ | north_star |
| job-scanner | dated Haiku ID | R W E Bash Grep Glob | "Use when the user runs /scan" | profile, narrative, preferences, /tmp exports | DB via scripts, output/lead_reports/linkedin_scan_*.md | scripts/linkedin/* |
| company-scanner | (inherits) | R W Bash Grep Glob | "Use when the user runs /scan-companies" | candidate_summary_compact.md, /tmp exports | DB, output/company_trackers/*.xlsx, output/analytics | scripts/company_scanner/* |

## A.3 Commands

None has frontmatter, so the description is the first line. All are model-invocable.

| Command | Kind | Wraps / does | Reads / writes |
|---|---|---|---|
| build-kb | wrapper | kb-builder | sources → KB |
| capture-story | wrapper | story-capture | KB |
| north-star | wrapper | north-star (restates its file list) | KB |
| setup-preferences | wrapper | preferences-setup | preferences |
| resume | wrapper | resume-writer (restates read order) | KB → output/resumes |
| cover-letter | wrapper | cover-letter | KB → output/cover_letters |
| score | wrapper | scorer | → output/lead_reports |
| prep | wrapper | interview-prep pipeline (names steps only); falls back to **missing** `postings/tracker.yaml` | → output/interview_prep |
| explore | wrapper | career-explorer (restates method) | → output/career_exploration |
| scan | wrapper | job-scanner (9 steps, flags) | DB, reports |
| scan-companies | wrapper | company-scanner (8 steps, **hard-coded candidate criteria**) | DB, trackers |
| analytics | inline | runs `scripts/linkedin/analytics.py` | → output/analytics |
| track | inline | CSV row + journal | postings/ |
| journal | inline | journal entry | postings/journal |
| status | inline | pipeline summary from CSV | reads postings/ |
| cf-init | inline | scaffold workspace, clone scripts, pip install, write preferences / **old tracker** / .gitignore | many |

## A.4 Data pipeline

```
knowledge_base/sources/  ──(kb-builder: hash diff, per-file merge)──▶  candidate_profile.yaml  (evidence, structured)
        ▲                                                       ├──▶  candidate_narrative.md (evidence, prose; rewritten at end of run)
        │                                                       ├──▶  source_index.md        (provenance rows)
 (story-capture writes      ──────────────────────────────────▶ └──▶  ingestion_progress.yaml (hash, status, last_run)
  profile + narrative directly; no source file)

north-star (interview) ──▶ north_star.md ──(hand-maintained)──▶ resume_variants.md        (framing)
memories/ (hand-written)                                                                    (framing)
scripts/company_scanner/generate_candidate_summary.py ──▶ candidate_summary_compact.md   (derived)

Readers:  resume-writer, cover-letter ← evidence + framing
          interview-prep, scorer, job-scanner ← evidence only (no memories / north star)
          career-explorer ← evidence + north star
          company-scanner ← compact summary
Outputs:  output/<type>/…   research: postings/<role>/company_research.md   tracker: postings/applications.csv (+ journal)
```

**Staleness:** detected only by kb-builder at the start of `/build-kb` (hash diff). Nothing flags new sources, or a north star, variants or compact summary that is older than the profile. No agent checks before generating.

## A.5 Context at session start (approximate)

| Loads at startup | Size |
|---|---|
| `.claude/CLAUDE.md` | 13.8 KB ≈ 3.5k tokens. **Also loaded into every non-fork subagent.** |
| Auto memory `MEMORY.md` (user-level, outside repo) | ≈ 1.2k tokens; first 200 lines / 25 KB (**[memory]**) |
| 11 agent descriptions | ≈ 0.9k tokens |
| 16 command descriptions (first lines) | ≈ 0.5k tokens |
| `SOUL.md` | **not loaded** (referenced, not imported) |

**On demand:** command bodies (on invocation); agent bodies (2–7k tokens each, inside the subagent); KB files (profile + narrative ≈ 40k tokens per deliverable agent); templates and formats.

**After the must-priority changes (C7–C9):** CLAUDE.md + SOUL.md ≈ 2.5k tokens at startup and in each subagent; `start` skill ≈ 1.5k tokens on the first message only; rules files load only when the tracker or KB is touched.

---

# Implementation log (2026-11-24)

All 20 changes are accepted and implemented on branch `revamp/claude-code-structure` (not committed). Decisions: resume-writer uses `opus`; the scoring weights are the balanced blend (skills 30, experience 20, preferences 20, domain 10, growth 10, company 10) with tiers 75 / 60 / 45.

Where the build differs from the plan, and why:

| Change | Difference | Why |
|---|---|---|
| C2 | The company-scan criteria stay in the gitignored compact summary (`knowledge_base/candidate_summary_compact.md`) rather than a new `preferences.yaml` block. | The agent already read them from there; a second copy would duplicate them. |
| C2 | Not changed: `scripts/company_scanner/*.py` (summary generator, dashboard labels, the `chicago_yn` column) and `docs/linkedin-scanner.md` / `templates/search_scopes.template.yaml` (example city geoId). | These are Python code and database schema, outside the markdown-only scope. They still contain the candidate's city and comp floor. |
| C3 | `settings.local.json` was not touched. | Widening a user's own permissions is the user's call; the template shows how. |
| C6 | `.claude/commands/` and `.claude/agents/templates/` are empty but still on disk. | `rmdir` is on the deny list. Git doesn't track empty folders. |
| C11 | The prep formats file moved to `.claude/reference/interview-prep-formats.md`, not the prep skill folder. The tracker schema likewise went to `.claude/reference/tracker-schema.md`. | Plugin workspaces get `.claude/reference/` copied in by `cf-init`; skill folders stay inside the plugin cache, where agents can't read them by project path. |
| C10 | The hook reports more signals than drafted: name-normalized "sources not in the progress file", unfinished entries, filled vs. empty preferences. It runs one `awk` pass (about 0.3 s). | A cold-read test found the first draft and the start skill disagreed on states. Testing on the real workspace found the existing progress file uses a legacy layout (`sources_processed[].file`, `complete`), so exact path matching gave false positives. |
| C8 | States now stack (one base state plus add-ons), with a help menu in every state, slot-filling in the one-question rule, and explicit stage, offer and posting-match rules. | Defects found by the cold-read test. |
| C14 | kb-builder converts a legacy-layout progress file to the documented format on its next run. | Found during C10 testing. |
| C20 | The manifest's `author` field became an object. | `claude plugin validate` rejected the string form. |
| C20 | `cf-init` fetches its files from the GitHub `main` branch. | Plugin installs only get the new layout after this branch is merged and pushed. |
| Follow-up | The company scanner now reads its criteria from `config/preferences.yaml` (`company_scanner` block plus `hard_constraints`); the hard-coded values left in Python under C2 are gone. The DB column keeps the legacy name `chicago_yn`. LinkedIn city geoIds moved to `linkedin_scanner.geo_ids`. Docs rewritten; stale diagrams replaced by a Mermaid diagram in the README. `/cf-init update` added. | Second pass, 2026-11-24. |
