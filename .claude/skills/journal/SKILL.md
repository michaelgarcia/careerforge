---
name: journal
description: >
  Add a dated note to a company's journal without changing application status: recruiter
  conversations, interviewer names and roles, impressions, next steps. Use for "note that...",
  "remember what the recruiter said", "log this conversation", "add a note about X".
argument-hint: "[company] [the note]"
---
Append a dated note to the journal for a company or application.

$ARGUMENTS

The journal lives at `user_data/postings/journal/{company-slug}.md`. Use it to record recruiter conversations, interview impressions, next steps, and any context worth remembering between sessions.

**How to determine the company slug:**
- Lowercase the company name, replace spaces with hyphens (e.g., "Google" → `google`, "Acme Robotics" → `acme-robotics`)
- If $ARGUMENTS references a specific application slug, use the company portion of that slug

**Steps:**
1. Read `user_data/postings/applications.csv` — find the latest event for matching applications to surface current status and any existing slug context
2. Read `user_data/postings/journal/{company-slug}.md` if it exists; otherwise create it with this header:

```markdown
# {Company Name} — Application Journal

## Active Applications
<!-- Updated automatically by /journal and /track -->

## Contacts
<!-- Add recruiter/HM names, emails, LinkedIn here -->

## Log
```

3. Append a new dated entry under `## Log` in this format:

```markdown
### YYYY-MM-DD
{Content of the note. Include: who was spoken to, what was said, key outcomes, next steps, any links to output files.}
```

4. Update the `## Active Applications` section to reflect the current status of all applications for this company (read from CSV)
5. Confirm what was written and to which file

**Do not fabricate any details.** Only record what the user provides. If recruiter name or contact info is mentioned, add it under `## Contacts` if not already there.
