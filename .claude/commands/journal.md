Append a dated note to the journal for a company or application.

$ARGUMENTS

The journal lives at `postings/journal/{company-slug}.md`. Use it to record recruiter conversations, interview impressions, next steps, and any context worth remembering between sessions.

**How to determine the company slug:**
- Lowercase the company name, replace spaces with hyphens (e.g., "Google" → `google`, "Blue River Technology" → `blue-river-technology`)
- If $ARGUMENTS references a specific application slug, use the company portion of that slug

**Steps:**
1. Read `postings/applications.csv` — find the latest event for matching applications to surface current status and any existing slug context
2. Read `postings/journal/{company-slug}.md` if it exists; otherwise create it with this header:

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
