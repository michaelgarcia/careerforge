# CareerForge — Project Instructions

## Project Context

This is a multi-agent job search system for a single candidate. Six specialized agents work from a shared knowledge base to cover the full job search lifecycle.

## Directory Layout

- `knowledge_base/` — The candidate's structured profile and raw source materials. This is the single source of truth.
  - `candidate_profile.json` — Structured data: skills, roles, achievements, certifications, publications, awards
  - `candidate_narrative.md` — Long-form narrative version of the candidate's background for LLM consumption
  - `source_index.md` — Provenance log mapping every KB fact to its source document
  - `sources/` — Raw input materials (resumes, transcripts, articles, etc.)
- `config/preferences.yaml` — Job search hard filters and soft preferences (location, comp, role type, etc.)
- `config/resume_style.yaml` — Resume formatting preferences
- `templates/` — Optional custom .docx templates
- `postings/` — Job postings under consideration, organized as `postings/[company_role]/job_description.md`. Transient inputs, not part of the candidate's permanent profile.
- `output/` — All generated deliverables, organized by type
- `scripts/generate_docx.js` — Node.js helper for .docx generation using docx-js

## Global Rules

1. **Always read the knowledge base before generating any deliverable.** Never fabricate achievements, skills, or experiences. Every claim must trace to `candidate_profile.json` or `candidate_narrative.md`.

2. **Never overwrite existing outputs without confirmation.** Use timestamped or descriptive filenames (e.g., `resume_stripe_sr_ml_engineer_2026-02-13.docx`).

3. **Log every action.** When ingesting sources, updating the KB, or generating deliverables, append a log entry to the relevant index or output folder.

4. **Prefer structured data for querying, narrative for generation.** Use `candidate_profile.json` when you need to match skills/keywords. Use `candidate_narrative.md` when you need to write compelling prose about the candidate's experience.

5. **Respect the preferences config.** The `config/preferences.yaml` file defines the candidate's hard constraints (e.g., "remote only", "minimum $200k") and soft preferences (e.g., "prefers ML/AI roles"). Lead gen must respect hard constraints as absolute filters. Resume and cover letter agents should weight soft preferences.

6. **Use web search for company context.** When writing cover letters or scoring job fit, search for recent company news, mission statements, and culture signals. Cite what you find.

7. **Output .docx for resumes and cover letters.** Use the `scripts/generate_docx.js` helper or the `docx` npm package via bash. Never output resumes as plain text or markdown — they must be properly formatted Word documents.

8. **Use the XYZ achievement formula.** When writing, extracting, or evaluating achievements, follow the pattern: "Accomplished [X] as measured by [Y], by doing [Z]." This maps directly to the achievement schema fields: `description` = X (what was accomplished), `metrics` = Y (how success was measured), `impact` = Z (what actions were taken). All agents should apply this formula when writing achievement bullets, extracting achievements from sources, or evaluating candidate-job fit. For leadership achievements, always include team size and scope of responsibility.

## Candidate Profile Schema

The `candidate_profile.json` follows this schema:

```json
{
  "personal": {
    "name": "",
    "title": "",
    "location": "",
    "email": "",
    "phone": "",
    "linkedin": "",
    "github": "",
    "website": "",
    "summary": ""
  },
  "skills": {
    "technical": [""],
    "tools": [""],
    "frameworks": [""],
    "languages": [""],
    "soft_skills": [""],
    "domains": [""]
  },
  "experience": [
    {
      "company": "",
      "title": "",
      "start_date": "",
      "end_date": "",
      "location": "",
      "summary": "",
      "achievements": [
        {
          "description": "",
          "impact": "",
          "metrics": "",
          "skills_used": [""],
          "source": ""
        }
      ]
    }
  ],
  "education": [
    {
      "institution": "",
      "degree": "",
      "field": "",
      "graduation_date": "",
      "gpa": "",
      "honors": [""]
    }
  ],
  "certifications": [
    {
      "name": "",
      "issuer": "",
      "date": "",
      "expiration": "",
      "credential_id": ""
    }
  ],
  "publications": [
    {
      "title": "",
      "venue": "",
      "date": "",
      "url": "",
      "summary": ""
    }
  ],
  "awards": [
    {
      "name": "",
      "issuer": "",
      "date": "",
      "description": ""
    }
  ],
  "speaking": [
    {
      "title": "",
      "event": "",
      "date": "",
      "url": "",
      "description": ""
    }
  ],
  "projects": [
    {
      "name": "",
      "description": "",
      "technologies": [""],
      "url": "",
      "highlights": [""]
    }
  ]
}
```
