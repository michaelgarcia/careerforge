---
name: resume
description: >
  Tailor a resume (.docx + .pdf) to a specific job posting, grounded only in the knowledge base.
  Use when the user wants a resume for a role, pastes a posting and says "tailor", "apply",
  "update my resume for this", or asks for the resume step of a full application.
argument-hint: "[posting URL, pasted text, or user_data/postings/<slug>]"
context: fork
agent: resume-writer
background: false
---
Create a tailored resume for the following job posting:

$ARGUMENTS

Follow your workflow from Step 0 (variant selection from north_star.md and resume_variants.md), honour every file in user_data/knowledge_base/memories/, check the resume style (user_data/config/resume_style.yaml if present, else templates/resume_style.yaml), name the output per .claude/reference/output-naming.md, and report minimum-qualification coverage and gaps.
