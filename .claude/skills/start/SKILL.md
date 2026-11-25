---
name: start
description: >
  Orient the user in their CareerForge workspace: detect what exists (sources, profile,
  preferences, active applications), say where things stand, and route what they want to the
  right skill. Use on the first message of a session, and for "hi", "help", "where was I?",
  "what can you do?", "how do I get started?", or any request whose intent is unclear.
---

# Start: state-aware orientation and routing

The user never needs to know a skill, agent or command name. Detect the state, open with the line for it, and act on what they asked in the same reply.

## 1. Read the signals

If a `[CareerForge state]` block is in context (from the SessionStart hook), use its values. Otherwise compute the same signals yourself with Glob, Read and Bash (`ls`, `find`). These paths are gitignored, so never use the Grep tool here.

| Signal | Values | How |
|---|---|---|
| `initialized` | yes / no | `knowledge_base/` and `config/` both exist |
| `sources` | count | files under `knowledge_base/sources/`, excluding `.gitkeep` |
| `profile` | ready / template / missing | `knowledge_base/candidate_profile.yaml`; it is the `template` if it contains `Your Name` |
| `sources_not_in_progress_file` | count / `all` | sources whose file name doesn't appear in `knowledge_base/ingestion_progress.yaml`. Compare lowercase letters and digits only, because entries may be stored as `path:` or `file:` with punctuation altered. `all` means the progress file is missing or empty. |
| `progress_unfinished` | count | entries with status `pending`, `modified`, `in_progress` or `error` |
| `sources_modified_since_last_build` | count | sources newer than `ingestion_progress.yaml` (`find … -newer`) |
| `north_star` | current / older_than_profile / missing | compare modification times with the profile |
| `preferences` | filled / empty / missing | `config/preferences.yaml` is **filled** when `minimum_compensation_usd` is above 0 or `target_titles` has at least one uncommented item |
| active pipeline | list | **Always read `postings/applications.csv` yourself.** Group rows by `slug` and take each slug's last row in file order. A slug is active when that row's status is `recruiter_screen`, `hm_screen`, `technical_screen`, `in_loop`, `loop_completed`, `offer_pending`, `offered` or `negotiating`. Its age is today minus that row's `timestamp`. |

## 2. Pick the base state

Exactly one applies:

| Base | When | Opening |
|---|---|---|
| **S0** Not set up | `initialized=no` | "This folder isn't set up for CareerForge yet. Want me to set it up? Type `/cf-init` and it takes about a minute." (`/cf-init` only runs when typed.) |
| **S1** Nothing yet | `profile` is missing or template, and `sources=0` | "No career material yet. Drop your resume, LinkedIn PDF, reviews or project write-ups into `knowledge_base/sources/` and I'll build your profile (best results). If you have a specific job or interview right now, I can start there without a profile." |
| **S2** Sources, no profile | `profile` is missing or template, and `sources>0` | "I can see N file(s) in your sources but no profile yet. Want me to build it now?" If the sources span more than one folder, add: "…or start with just your resume folder (about 2 minutes) and add the rest later." |
| **S5** Profile ready | `profile=ready` | No base line of its own. Use the add-ons below; if none apply, the **ready line**. |

**Ready line:** "Your profile is ready. I can tailor a resume to a posting, research a company, prep you for an interview loop, find and score new roles, or update your tracker. What's going on?"

## 3. Add-ons (only when `profile=ready`; use every one that applies, in this order)

| Add-on | When | Line |
|---|---|---|
| **S3** Profile stale | `sources_not_in_progress_file` > 0 or `all`, or `progress_unfinished` > 0, or `sources_modified_since_last_build` > 0 | "N source files are new or changed since your last profile build. Want me to fold them in first?" (N = the largest of the three counts; when a count is `all`, N is `sources`.) |
| **S3b** North star stale | `north_star=older_than_profile` | "Your profile has changed since your north star was written. Worth a refresh when you have ten minutes." |
| **S4** No filters | `preferences` is missing or empty | "Two minutes on your search filters (location, salary floor, role types) and job scans and scoring get much sharper. Want to do that now?" |
| **S4b** No north star | `north_star=missing` | "Optional: ten minutes on your north star (your positioning and target roles) sharpens every resume and score." At most once per session. |
| **S6** Active pipeline | at least one active slug | "You have N active processes: [company, role, stage, and 'no update in D days' when D ≥ 14]. Want to pick one up?" Name at most three, oldest first. |

Compose, keeping the reply to **one question**:
- Lead with "Your profile is ready", or "Your profile is built" when S3 applies.
- Use at most **two** add-ons, by priority: S6, S3, S4, S3b, S4b. Hold the rest for a later turn when they become relevant (for example S4 when the user asks for a scan).
- Only the last line used asks a question. Turn earlier ones into statements ("N source files are new since your last build."). Drop "What's going on?" whenever an add-on already asks something.
- If no add-ons apply, use the ready line. Never say "everything else works" while S4 applies.

## 4. Help and capability questions

For "help", "what can you do?" or "how does this work?", in **any** state, give the state's opening, then this menu (drop items whose state isn't met, and say what unlocks them):

> - Build or update your profile from your documents
> - Score a job posting, or tailor a resume or cover letter to it
> - Research a company, or prep you for an interview loop, round by round
> - Find and score new roles on LinkedIn, or at your target companies
> - Track applications and notes ("I applied to…", "the recruiter said…")
> - Check your profile for gaps, or sharpen your positioning (north star)
>
> Just say it in your own words.

## 5. Keep it short, and answer the actual message

If the message already states an intent, shrink the opening to one clause and start the work. "I have an interview Tuesday" in S1 becomes: "No profile yet, so I'll prep you from the posting and public research, and we can add your stories after. What's the posting?" Never dump the README. Plain language, one question at a time.

## 6. Route

Use `${CLAUDE_SKILL_DIR}/routing.md`: the intent map, which state each route needs, what to offer when that state is missing, the one-question rule, and the chained workflows. Typed slash commands always win; run them as typed.
