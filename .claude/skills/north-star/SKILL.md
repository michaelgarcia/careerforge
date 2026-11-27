---
name: north-star
description: >
  Define or refresh the candidate's career north star: positioning statement, narrative, ranked
  role lenses, not-targeted list and forward trajectory. Use for "what's my positioning?",
  "where am I headed?", "what am I aiming for?", "refresh my north star", or when
  user_data/knowledge_base/north_star.md is missing or older than the profile.
argument-hint: "[refresh | lenses only | a brain dump of how you see your positioning]"
---

# North Star

## Shared rules

This skill runs in the main conversation, so ask your questions directly and wait for the user's answers. Read these before starting:
- `.claude/reference/kb-context.md`: what the KB files are (evidence vs. framing), the readiness gate, `user_data/knowledge_base/memories/`, searching gitignored paths

Arguments: $ARGUMENTS

You help the candidate define the one document every other deliverable depends on: what they are, where they are headed, and how to say it. You do not start from a blank page. You read the knowledge base first, form a positioning hypothesis from the evidence, and then interview the candidate *against* that hypothesis.

**Core principle:** The north star is **framing, never evidence.** It decides what to lead with, how to word it, and which roles to pursue. It never supplies a fact. Every claim inside it must trace to `candidate_profile.yaml` or `candidate_narrative.md`. Direction comes from the candidate's own answers, never from your inference.

---

## KB Required Gate

**Before doing anything else**, check whether `user_data/knowledge_base/candidate_profile.yaml` exists and contains real data (i.e., `personal.name` is not `"Your Name"`).

If the file does not exist, or if it contains template defaults:
- Stop immediately. Do not attempt to define a north star.
- Respond:
  > "Your north star is the positioning that every resume, cover letter, and job score is built on, and it has to be grounded in your actual record. Without your profile, I would be inventing a career for you rather than reading one.
  >
  > Run `/build-kb` (drop your resume or career docs into `user_data/knowledge_base/sources/` first) and then come back. It usually takes about 5 minutes. Once your profile is ready, I can derive a positioning hypothesis from it and we can sharpen it together."

There is no degraded mode. A north star derived from nothing is fabrication.

---

## KB Files to Load

Read these before doing anything else:

| File | Why |
|------|-----|
| `user_data/knowledge_base/candidate_profile.yaml` | The evidence: roles, achievements, metrics, patents, speaking record |
| `user_data/knowledge_base/candidate_narrative.md` | The retrospective arc, where the recurring pattern is visible |
| `user_data/knowledge_base/resume_variants.md` | Existing role-family lens taxonomy that must stay consistent |
| `user_data/knowledge_base/memories/*.md` | Candidate-specific voice, wording, and confidentiality rules |
| `user_data/config/preferences.yaml` | Stated goals, target titles, hard constraints |
| `user_data/knowledge_base/north_star.md` | The current version, if one exists |
| `user_data/output/career_paths/*.md` | Prior trajectory research, if present |

**IMPORTANT:** every one of these paths is gitignored, and the Grep tool inherits ripgrep's gitignore behavior, so it returns "No matches found" with no warning that files were skipped. Search them with Bash instead:

```bash
rg --no-ignore -n -i "pattern" user_data/knowledge_base/
```

Treat a zero-match Grep result inside a gitignored path as unproven, not as a negative. Missing optional files (`north_star.md`, `user_data/output/career_paths/`, an empty `memories/`) are fine. Note their absence and continue.

---

## Mode Detection

| Mode | Trigger | Behavior |
|------|---------|----------|
| **CREATE** | No `user_data/knowledge_base/north_star.md` exists | Full derive, then interview, then write v1 |
| **REFRESH** | `north_star.md` exists, or `$ARGUMENTS` contains "refresh" | Re-derive against current KB, diff against the existing file, propose a version bump |
| **EXTRACT** | `$ARGUMENTS` contains a brain dump of how the candidate sees their positioning | Parse it first, map it to the file structure, then interview only to close the gaps it left |
| **PARTIAL** | `$ARGUMENTS` names a section (e.g. "lenses only") | Revise only that section and its dependents; leave the rest byte-identical |

If the mode is genuinely ambiguous, ask one question: *"Do you want to rebuild your north star from scratch, or refresh the one you have?"*

---

## Workflow

### Step 1 - Read the KB

Load every file in the table above. Note which optional ones were absent.

### Step 2 - Derive a positioning hypothesis

Work from the evidence to a proposal. Do **not** present this as a finished answer. Present it as a reading of the record that the candidate is about to correct.

Derive and write up:

1. **The recurring situation.** What keeps happening across roles, stated as a repeatable pattern rather than a skill list or a job title. This is the hardest and most valuable element. Look for the situation the candidate keeps walking into, not the tasks they performed.
2. **The proof of range.** The eras, technology waves, domains, or industries where the pattern repeated. For each, name the marquee proof *inside* it. Distinguish a genuine platform shift from an application of one.
3. **The altitude arc.** How the proof changed as seniority grew: what they pointed at early versus what they point at now. This preempts "are they senior enough?"
4. **The activity loop.** The distinct activities they own end to end. This preempts "which part do they actually own?"
5. **Three to four candidate role lenses.** For each, cite the **specific KB achievements** that support it. A lens with no evidence behind it is a guess, and you must label it as one.
6. **Anti-signals.** Lenses the record does *not* support, and why. Also any lens the record supports that the candidate's stated `career_goals` suggest they do not want.

**Flag every gap.** If a lens the candidate seems to want is not evidenced in the KB, say so plainly and say what evidence would close it. This is the "educate about gaps" obligation in `SOUL.md`, and it is more useful here than anywhere else in the system.

Present the hypothesis compactly. The candidate should be able to read it in under two minutes and start reacting.

### Step 3 - Interview against the hypothesis

**Ask ONE question at a time. Wait for a response before asking the next.** Adapt as you go and skip anything already answered, including anything answered by an EXTRACT-mode brain dump.

These are the questions the knowledge base cannot answer:

- **Q1 Pattern check.** "I read three recurring patterns in your record: [A], [B], [C]. Which one feels most like you, and what did I get wrong?"
- **Q2 Appetite.** "Which part of that work do you want more of, and which part do you want less of?"
- **Q3 Refusals.** "What are you not willing to do, even though you would be good at it?" (feeds **Not targeted**)
- **Q4 Altitude.** "Do you want to formalize decision rights, or keep the build depth? Is scope or headcount the thing you actually want?"
- **Q5 Lens ranking.** "Of the lenses I listed, which one leads, and which is the fallback?"
- **Q6 Horizon and risk.** "How many years to the seat you actually want, and what risk are you willing to carry to get there?" (feeds **Where this goes**)
- **Q7 Failure mode.** "What would make the next role a mistake, even if the title and the money were right?" (feeds **what kills this path**)
- **Q8 Framing check.** "Are the eras named right? Is anything on that list a proof point rather than a genuine shift?"

**Push back on vague answers**, the same way story capture pushes for metrics. If an answer is too abstract to act on, say so and ask for the concrete version:

> "That tells me the direction but not the boundary. If a recruiter called you tomorrow with a [role] that paid well, what would make you say no?"

Never supply the candidate's answer for them. If they genuinely do not know, record it as an open question in the file rather than resolving it yourself.

### Step 4 - Draft and present

Write the complete file structure (see below) and show it in full. Then ask:

> "Does this represent where you are headed? Anything to sharpen or cut?"

Apply corrections. Show the corrected sections. **Do not write anything to disk before explicit confirmation.** If the candidate interrupts before confirming, write nothing.

### Step 5 - Write and report

Write `user_data/knowledge_base/north_star.md` in a single Write call. Never write section by section, and never leave a partial file.

On **REFRESH** or **PARTIAL**: bump the version, date it, and append a Revision History entry naming what changed and why. A north star that changes without a recorded reason is drift, and the reason is the most valuable part of the entry.

Then report:

```
Wrote user_data/knowledge_base/north_star.md (v{N}, {date})

Sections: {list}
Role lenses: {ranked list}
Not targeted: {list}

This now feeds:
- resume-writer   - lens selection at Step 0, via resume_variants.md
- cover-letter    - positioning and framing for every letter
- career-explorer - the starting point for role discovery
- scorer, job-scanner - the not-targeted list and lens weighting in every score
- interview-prep  - which stories lead and how answers are framed

{Consistency warnings, if any}
{Open questions recorded in the file, if any}
```

---

## File Structure

Write these sections, in this order. Omit a section only when it has no content, and say so in the report.

| Section | Contents |
|---|---|
| `## Core statement` | One short role-neutral paragraph, sayable out loud. Metrics stay OUT so it survives being spoken. Optionally a punchier alternate opener. |
| `## Resume-header vision` | One line, 10 words or fewer. Optionally an extended form. |
| `## The narrative` | Three to five bolded-lead paragraphs: the pattern, the proof of range, the altitude arc, the full loop. |
| `## Structure of the argument` | Table: Element / Answers / Carried by. One claim, N proofs, each answering a silent objection. |
| `## Role lenses` | Two to four, **ranked**. Each with what the role is, the KB evidence behind it, and target titles. |
| `## Not targeted` | The explicit anti-list, with the boundary condition for each entry. |
| `## Where this goes` | One short block per live path: thesis, gates with rough timing, what kills it. |
| `## The personality engine` | Optional. Mark clearly as interview use, not public copy. |
| `## How to apply` | The operating rules: the filter for resume bullets and scored jobs, how to pick a lens per posting, where exact metrics are allowed. |
| `## Revision history` | Newest first. What changed and why. |

Keep detailed research (compensation tables, target company lists) in `user_data/output/career_paths/`. The north star holds the durable bet, not the supporting spreadsheet.

---

## Consistency with resume_variants.md

`user_data/knowledge_base/resume_variants.md` cites the north star by name as the authority for its lens taxonomy and for its not-targeted rule. Lens names you write must stay resolvable from it.

After drafting, check: does each lens referenced in `resume_variants.md` still exist in the north star under a recognizable name? Does the not-targeted list still cover what `resume_variants.md` says it covers?

If a lens is renamed, dropped, or added, **say so explicitly in the final report** and offer to update `resume_variants.md`. Do not edit that file silently, and do not leave the two disagreeing.

---

## Important Rules

- **The north star is framing, never evidence.** It governs selection, ordering, emphasis and wording. It never supplies a fact, a metric, or a credential. Every claim inside it traces to `candidate_profile.yaml` or `candidate_narrative.md`.
- **Never fabricate ambition.** Direction comes from the candidate's answers. If they have not said it, it does not go in the file. Record genuine uncertainty as an open question rather than resolving it.
- **Never fabricate evidence for a lens.** If the KB does not support a lens, label it as aspirational and name the evidence that would close the gap.
- **Never write without confirmation.** Write once, at the end, after an explicit yes.
- **One question at a time.** Wait for the answer. This is an interview, not a form.
- **Keep metrics out of the core statement** so it stays sayable in a room. Exact figures belong in the KB and the resume; public copy uses rounded, durable ones.
- **Follow every rule in `user_data/knowledge_base/memories/`** for all prose you write into the file, including voice rules and any confidentiality constraint on names or codenames.
- **Preserve what you are not changing.** In REFRESH and PARTIAL modes, sections outside the scope of the change stay byte-identical.
