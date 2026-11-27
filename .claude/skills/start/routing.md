# Routing map

Map what the user says to a skill. Slash commands are optional shortcuts; the user never needs them.

"Needs" is the state the route requires. "If missing" is what to offer instead, never a dead end. When the user accepts a setup step (build, preferences), **keep their original request** (the posting URL or text, the company) and resume it automatically once the setup finishes.

| The user says (examples) | Route | Needs | If missing |
|---|---|---|---|
| "hi", "help", "where was I?", "what can you do?" | the `start` opening for the current state, plus the help menu for help-type questions | none | n/a |
| Pastes a posting or URL with no instruction | **Pasted-posting rule** (below) | none | n/a |
| "is this a good fit?", "should I apply?", "score this" | `score` | profile optional | no profile: job-quality mode (the scorer says so) |
| "tailor my resume for this", "I want to apply to X" | `resume`, or the **apply chain** for "apply" | profile | Offer a quick build (`/build-kb quick`, resume folder only, about 2 minutes) or the full build. No resume without a profile: it would require fabrication (`SOUL.md`). Keep the posting; run `resume` on it as soon as the build finishes. |
| "write a cover letter", "answer the application questions" | `cover-letter` | profile | same as resume |
| "I got an interview at X", "prep me for Tuesday", "practice questions" | **interview chain** | profile optional | no profile: prep runs without the story bank; offer `capture-story` after |
| "research X", "what do you know about X?" | First check `user_data/postings/journal/<company>.md` and any `user_data/postings/*/company_research.md` for that company, and lead with what's already there (the candidate's own notes first). Then `research-company` if there's no research or it's 30+ days old, or if the user asks for fresh research. | none | n/a |
| "they made me an offer", "how do I negotiate?", "is this offer good?" | **offer chain** | profile optional | no profile: market ranges only |
| "find me jobs", "what's new?", "run my scan" | `scan`; for a named company listed in `user_data/config/company_targets.yaml`, `scan-companies` | profile **and** preferences filled | profile missing → offer `build-kb`. Preferences missing or empty → offer `setup-preferences`. After either finishes, offer to run the scan ("Want me to run your first scan now? Use `--bootstrap` for a 30-day lookback.") |
| "any openings at <target company>?" | `scan-companies` | profile | offer `build-kb` |
| "I applied to X", "rejected by Y", "the recruiter called and…" | `track` (+ journal when there's narrative). `track` creates `user_data/postings/applications.csv` with its header if it doesn't exist. | none | n/a |
| "note that…", "remember what the recruiter said" | `journal` | none | n/a |
| "I worked on X", "add this project", a pasted brain dump about past work | `capture-story` | profile recommended | no profile: offer `build-kb` first; the story can still be saved as a source file |
| "I added new files", "update my profile", "rebuild my KB" | `build-kb` | sources | ask them to drop files into `user_data/knowledge_base/sources/` |
| "is my profile up to date?", "what's missing from my KB?" | `kb-check` | profile | report S1 or S2 instead |
| "what roles fit me?", "what should I target?" | `explore` | profile | offer `build-kb` |
| "what's my positioning?", "where am I headed?" | `north-star` | profile | offer `build-kb` |
| "only remote", "raise my salary floor", "change my preferences" | `setup-preferences` (text mode) | none | n/a |
| "what's my status?", "what should I do today?" | `status`, plus suggest `scan` if the newest `user_data/output/lead_reports/linkedin_scan_*.md` is 3+ days old | tracker | "No applications tracked yet." Offer `scan` or `score` |
| "show the dashboard", "analytics" | `analytics` | jobs database (`user_data/data/jobs.db`) | offer `scan --bootstrap` |
| "update CareerForge", "get the latest version", "pull from GitHub" | `update` | none | n/a |
| "set up CareerForge", "install the packages", "it says a module is missing" | `setup` | none | n/a |

## Pasted-posting rule

1. Read the company and title from the posting.
2. Look in `user_data/postings/applications.csv` for an **active** slug (see the start skill) with the same company.
   - **Same company and same or very similar title** (or the posting URL equals the row's `job_url`): "This looks like the [role] at [company] you're interviewing for ([stage]). Want me to prep you for that loop?" Offer prep only, but accept any other request.
   - **Same company, different title**: ask one question: "Is this the [tracked role] you're already in process for, or a different role at [company]?" Then continue as below.
   - **No match**, or the match is for a non-active status (`saved`, `applied`, …): ask the five-option question below.
3. Matching is case-insensitive and ignores suffixes like "Inc.", "Corp" or "LLC".

> "I see a job posting. What would you like?
> 1. Score it against your profile
> 2. Tailor a resume
> 3. Write a cover letter
> 4. Prep for an interview
> 5. The full application (score, resume, cover letter, tracker)"

## The one-question rule

Ask a clarifying question only in one of these two cases:
1. **Choosing a route:** two routes would produce different saved artifacts, and neither the message, the workspace state nor the tracker settles it.
2. **Filling required inputs:** the route can't start without something only the user knows: the company, the posting, offer figures, or which of several active applications. Ask for all the missing inputs in **one** combined question.

Ask with numbered options when there are options, most likely first. Otherwise pick, say in one line what you're doing, and start. Never ask for something already on disk.

## Chained workflows

Offer each step; don't force it. Skip steps already done (check the tracker, `user_data/postings/<slug>/` and `user_data/output/`).

**Apply chain** ("I want to apply to…"):
1. `score` → share the fit score and the top 2–3 strengths and gaps
2. "Want a tailored resume?" → `resume`
3. "A cover letter too?" → `cover-letter`
4. "Shall I log it as applying?" → `track`

**Interview chain** ("I got an interview at X"):
1. **Stage:** infer it from the user's words: "phone screen" or "recruiter call" → `recruiter_screen`; "hiring manager" → `hm_screen`; "technical", "coding" or "system design" → `technical_screen`; "onsite", "loop", "final" or "panel" → `in_loop`. If the words don't say, use `recruiter_screen` for a company with no earlier interview row, otherwise the next stage after the tracker's last one. Say which stage you logged so the user can correct it.
2. `track` the stage (plus journal: who, when, which round, if the user said).
3. **Posting:** if `user_data/postings/<slug>/` or the tracker's `job_url` has it, use it. Otherwise ask for the URL or text, together with anything else missing (one combined question). If the user has no posting, prep from the company and role name alone and say the prep is less specific.
4. `research-company`, reused if `user_data/postings/<slug>/company_research.md` is under 30 days old.
5. `prep`: journal facts about rounds and interviewers take precedence over public research.
6. Story gaps from prep → offer `capture-story`.

**Offer chain** ("they made me an offer"):
1. Identify the application from the tracker (the active slug at that company). If the company is unknown, or the user gave no figures, ask once for both: "Congratulations! Which company, and what are the numbers (base, bonus, equity, start date)?"
2. `track` → `offered` by default; `offer_pending` only when the user says it is verbal or still coming. Say which you logged.
3. `prep <posting or user_data/postings/slug> comp` (compensation research only). Without a posting, run it from the company, title and location.
4. `journal` the offer details and deadlines.

**New material chain** ("I added files", or the S3 add-on):
1. `build-kb`
2. `kb-check`
3. If the new evidence touches a role lens, offer `north-star refresh`

## Combined updates

A message with both a status change and narrative ("I'm in standby at Acme, the recruiter said the role was filled") is one `track` call that writes the CSV row **and** the journal entry. Never ask the user to split it. If the role title is missing: with exactly one tracked application at that company, use it; with several, ask which; with none, log it with the title "(not given)", and mention the title can be added later. Don't ask just for the title.
