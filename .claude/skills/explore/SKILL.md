---
name: explore
description: >
  Research which roles in today's market best fit the candidate, with real example postings,
  compensation ranges and work-life balance data. Use for "what roles fit me?", "what should I
  target?", "what else could I do with my background?".
argument-hint: "[optional focus, e.g. 'startup roles only' or 'find 6 roles']"
context: fork
agent: career-explorer
background: false
---
Analyze the candidate's profile and produce the career exploration report.

Start from the north star's ranked role lenses when user_data/knowledge_base/north_star.md exists; synthesize 2-3 archetypes only if it is missing. Identify 5-8 role categories (core fit, lateral, growth), research each with real postings, compensation data and work-life balance data, ground every fit claim in specific KB achievements, and save the report per .claude/reference/output-naming.md.

Optional focus or constraints from the user: $ARGUMENTS
