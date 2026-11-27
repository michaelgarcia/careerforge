---
name: research-company
description: >
  Research a company's mission and values, recent news, products, culture and engineering
  practices, and save it for reuse by resumes, cover letters and interview prep. Use for
  "research X", "tell me about X before my call", "what do you know about X?".
argument-hint: "[company name, or a posting URL / user_data/postings/<slug>]"
context: fork
agent: interview-prep
background: false
---
task_type: company_research

Research the company in: $ARGUMENTS

Use the "Company Research Format" section of `.claude/reference/interview-prep-formats.md`. Save the result to `user_data/postings/<slug>/company_research.md` (slug per `.claude/reference/output-naming.md`; if only a company name is given, use the company name as the slug). No `output_dir` copy is needed. Do not read KB files for this task.
