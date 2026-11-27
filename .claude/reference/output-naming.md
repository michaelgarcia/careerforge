# Output naming and scratch space (shared)

## The application slug

One key per application, used everywhere: `{company}-{role-short}` in lowercase kebab-case, for example `acme-staff-ml-engineer`.

- If `user_data/postings/applications.csv` already has a row for this company and role, **reuse its slug**.
- Otherwise derive it, and use the same slug for the `user_data/postings/<slug>/` folder.
- Company-level files (journal) use the company part only: `user_data/postings/journal/acme.md`.

## Where each deliverable goes

| Deliverable | Path |
|---|---|
| Posting text | `user_data/postings/<slug>/posting.md` (or the file the user provided) |
| Company research | `user_data/postings/<slug>/company_research.md` (reused by resume, cover letter and prep) |
| Resume | `user_data/output/resumes/<slug>_resume_<YYYY-MM-DD>.docx` (+ `.pdf`) |
| Cover letter | `user_data/output/cover_letters/<slug>_cover_letter_<YYYY-MM-DD>.docx` (+ `.pdf`) |
| Application notes | `user_data/output/cover_letters/<slug>_app_notes_<YYYY-MM-DD>.md` |
| Interview prep | `user_data/output/interview_prep/<slug>_<YYYY-MM-DD>/` |
| Single-posting score | `user_data/output/lead_reports/<slug>_score_<YYYY-MM-DD>.md` |
| Multi-posting score | `user_data/output/lead_reports/batch_score_<YYYY-MM-DD>_<HHMM>.md` |
| LinkedIn scan report | `user_data/output/lead_reports/linkedin_scan_<YYYY-MM-DD>.md` (written by `scripts/linkedin/report.py`) |
| Career exploration | `user_data/output/career_exploration/career_exploration_<YYYY-MM-DD>.md` |

## Never overwrite

Before writing, check whether the path exists. If it does, append `_2`, `_3`, and so on. Never replace an existing deliverable without the user's confirmation (Global Rule 2). Files created before this convention keep their old names.

## Scratch files

Intermediate files (resume or letter JSON, scoring exports) go in `user_data/output/.work/`, never `/tmp`. It is gitignored, keeps candidate data inside the project, and resolves the same way on Windows and macOS. Create it with `mkdir -p user_data/output/.work` if needed.

## Record outputs in the tracker

When a deliverable is created for an application that is in `user_data/postings/applications.csv`, mention its path to the user and offer to log it. Tracker rows carry paths in `output_files`, written relative to `user_data/` (`output/resumes/...`), like every path stored inside personal files.
