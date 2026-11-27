---
name: track
description: >
  Record an application status change (saved, applied, recruiter screen, loop, offer, rejection,
  withdrawal...) in user_data/postings/applications.csv, plus any narrative in the company journal. Use for
  "I applied to X", "I got rejected by Y", "I'm in the loop at X", "the recruiter called and...".
argument-hint: "[what happened, in your own words]"
---
Update the application tracker with the following information:

$ARGUMENTS

Valid status values: discovered | saved | researching | applying | applied | recruiter_screen | hm_screen | technical_screen | in_loop | loop_completed | offer_pending | offered | negotiating | accepted | rejected | withdrawn | on_hold | standby | ghosted | closed

Examples of valid inputs:
- "I submitted my application to Google Customer Engineer role"
- "I have a recruiter screen scheduled with Stripe on Friday"
- "I'm now in the loop at Anthropic for the FDE role"
- "Acme loop is complete — waiting on decision. The recruiter called, said feedback was strong."
- "Withdrawing from the Anthropic role"
- "Acme Staff Engineer — standby. Role was filled, recruiter keeping me in the pipeline for similar roles."

**Step 1 — Detect intent (both may apply simultaneously):**
- **Status change present?** → New status is explicitly or implicitly named (applied, in loop, rejected, etc.)
- **Narrative context present?** → Recruiter names, conversation details, interview impressions, next steps, or any context beyond just a status label

**Step 2 — If status change:**
1. Read `user_data/postings/applications.csv`
2. Find the last row matching this application's slug (match on company + role keywords)
3. If no match, create a new slug in the format `{company-kebab}-{role-short-kebab}`
4. Determine `previous_status` from the last matching row (empty if first event)
5. Append a new row with: next `event_id`, current ISO timestamp, slug, company, title, job_url (if known), new status, previous_status, brief note, any output file paths mentioned
6. Confirm the CSV row written

**Step 3 — If narrative context:**
1. Also run `/journal {company}` logic inline: append a dated entry to `user_data/postings/journal/{company-slug}.md`
2. The journal entry should capture: who was spoken to, what was said, key outcomes, next steps
3. If recruiter/HM name or contact info appears, add to the `## Contacts` section if not already present
4. Update the `## Active Applications` section based on the CSV state after Step 2
5. Confirm the journal file updated

**Step 4 — If only narrative (no status change):**
- Do Step 3 only; do not write a CSV row

**Important:** Never ask the user to split a combined status+narrative update into two commands. Handle both in one response.
