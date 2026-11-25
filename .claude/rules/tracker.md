---
paths:
  - "postings/**"
---
# Application tracker rules

- `postings/applications.csv` is an append-only event log: one row per status transition. Never edit or delete rows.
- `previous_status` is the `status` of the last row with the same slug. A new application starts with an empty `previous_status`.
- Valid statuses: `discovered`, `saved`, `researching`, `applying`, `applied`, `recruiter_screen`, `hm_screen`, `technical_screen`, `in_loop`, `loop_completed`, `offer_pending`, `offered`, `negotiating`, `accepted`, `rejected`, `withdrawn`, `on_hold`, `standby`, `ghosted`, `closed`.
- A message that carries both a status change and narrative (who said what, next steps) gets one CSV row **and** one entry in `postings/journal/<company>.md`, in the same reply. Never ask the user to split them.
- Journal entries record only what the user said. Never fabricate names, dates or outcomes.
- Full schema and journal format: `.claude/reference/tracker-schema.md`.
