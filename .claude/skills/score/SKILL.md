---
name: score
description: >
  Score how well one or more job postings fit the candidate (skills, experience, preferences)
  and recommend apply or skip. Use when the user links or pastes a posting and asks "is this a
  good fit?", "should I apply?", "score this", or "how do these compare?". Works without a
  profile in job-quality mode.
argument-hint: "[posting URL(s), pasted text, or user_data/postings/<slug>]"
context: fork
agent: scorer
background: false
---
Score and evaluate the following job posting(s) against the candidate's profile and preferences:

$ARGUMENTS

Apply hard-constraint filters first, then score with .claude/reference/scoring-rubric.md. Include the minimum-qualification check and tailoring notes. Name the report per .claude/reference/output-naming.md.
