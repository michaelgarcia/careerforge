# Candidate Memory Template

Copy this into `user_data/knowledge_base/memories/<slug>.md` to add a short, candidate-specific rule that every agent should respect.

**What belongs here:** rules about *this candidate*. Voice and wording preferences, confidentiality constraints such as codenames that must never appear in a deliverable, claims that need extra scrutiny, corrections you have had to make more than once.

**What does not belong here:** facts about the candidate's career. Those go in `candidate_profile.yaml` (structured) or `candidate_narrative.md` (prose), with a traceable source. A memory binds *wording and selection*, never evidence.

**What also does not belong here:** repository and tooling facts that are true for every user of CareerForge. Those go in `.claude/CLAUDE.md`, which is committed.

One rule per file. Keep each under roughly 30 lines. This folder is gitignored and entirely user-maintained, so it may be empty, and that is fine.

---

```markdown
---
name: <short-kebab-case-slug, matching the filename>
description: <one line, so an agent can tell at a glance whether this rule is relevant>
---

<The rule itself. State it as an instruction an agent can follow. Be specific:
"never write X, use Y instead" beats "be careful about X".>

**Why:** <The reason, with a date or an incident where you have one. A rule with no
recorded reason gets silently dropped the first time it is inconvenient.>

**How to apply:** <When and where it binds. Which deliverables, which stage, and any
exception that is genuinely allowed.>
```

---

## Worked example

```markdown
---
name: no-internal-codenames
description: "Never use internal employer codenames in KB prose or deliverables; use the approved generic descriptors"
---

Never write internal employer codenames in KB prose, resumes, cover letters, interview
prep, or any other output. Approved descriptors:

- "<INTERNAL_CODENAME>" becomes "<a neutral description of what the product does>"

**Why:** Candidate instruction on <date> while ingesting sources marked Confidential.
These are confidentiality obligations, not style preferences.

**How to apply:** The only allowed occurrence is a source filename inside a KB `source`
field, which traceability requires. If a generated draft contains a codename, replace it
before delivering.
```
