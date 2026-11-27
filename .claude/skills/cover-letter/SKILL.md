---
name: cover-letter
description: >
  Write a tailored cover letter (.docx + .pdf) and, if needed, answers to application questions
  for a specific job posting. Use for "write a cover letter", "help me answer the application
  questions", or the cover-letter step of a full application.
argument-hint: "[posting URL, pasted text, or user_data/postings/<slug>]"
context: fork
agent: cover-letter
background: false
---
Write a tailored cover letter for the following job posting:

$ARGUMENTS

Reuse user_data/postings/<slug>/company_research.md if it exists instead of repeating the research. Name the output per .claude/reference/output-naming.md.
