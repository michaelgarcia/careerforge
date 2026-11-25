---
name: prep
description: >
  Prepare the candidate for an interview loop: research the process and company, break the loop
  into rounds and interviewers, generate likely questions per round mapped to the candidate's real
  stories, and build a story bank. Use for "I have an interview at X", "prep me for Tuesday",
  "practice questions for my loop". Use "comp" for offer and negotiation research only.
argument-hint: "[posting URL, pasted text, or postings/<slug>] [comp]"
---

# Interview prep (coordinator)

You run this in the main conversation and coordinate `interview-prep` subagents. Each subagent does one `task_type`; you create the folder, pass paths, parse the rounds and fan out. Output formats for every sub-task: `.claude/reference/interview-prep-formats.md` (tell each subagent this path).

Arguments: $ARGUMENTS

## 1. Resolve the application

- **Posting:** a URL (fetch it), pasted text, or `postings/<slug>/` (read the posting file in it; PDFs via `pdftotext -layout`).
- **No argument:** read `postings/applications.csv`, take the latest row per slug, and use the most recent application whose status is `recruiter_screen`, `hm_screen`, `technical_screen` or `in_loop`. If several match, ask which one. If none, ask for the posting.
- **Slug:** per `.claude/reference/output-naming.md` (reuse the tracker's slug when one exists).
- If a URL yields no readable job description, stop and ask. Never substitute a different posting.

## 2. Gather insider facts first

Read `postings/journal/<company>.md` if it exists (use `rg --no-ignore` or Read; it is gitignored). Extract what the candidate has actually been told: the rounds and their order, interviewer names and roles, format, dates, focus areas, recruiter guidance. **Insider facts beat public research.** Pass them to `process_research` and to every `round_prep` as "Known from the candidate's journal". If the journal names an interviewer for a round, that round's prep is written for that person's role and likely angle.

## 3. Create the output folder

`output/interview_prep/<slug>_<YYYY-MM-DD>/` (append `_2` if it exists).

## 4. Research in parallel

Launch these `interview-prep` subagents at the same time, each with the posting text, `output_dir`, the slug, and the formats path:

| task_type | Skip when |
|---|---|
| `process_research` (include the journal facts) | never |
| `company_research` | `postings/<slug>/company_research.md` exists and is under 30 days old: copy it into `output_dir` instead |
| `compensation_research` | never |

If the argument includes `comp`, run only `compensation_research`, report, and stop.

## 5. Fan out one agent per round

Read `00_interview_process.md` and parse the JSON inside its `<!-- ROUNDS_DATA [...] -->` block. If it is missing or invalid, ask the `process_research` agent to fix it rather than guessing rounds. Then launch one `round_prep` subagent per round, in parallel, each with: the posting text, the round descriptor (number, slug, name, format, duration, focus), any journal facts for that round (interviewer name and role), and `output_dir`.

## 6. Story bank and gaps

After every round file exists, run one `story_bank` subagent. Then report to the user:
- the files written, with paths
- rounds where the KB has no strong story (the "Gaps to Prepare" sections), and offer `capture-story` to fill them before the interview
- anything the journal said that public research contradicted

## Without a knowledge base

If the KB is not ready (`.claude/reference/kb-context.md`), say so in one line and run everything except `story_bank`; the subagents use their degraded mode. Offer `build-kb` afterwards.
