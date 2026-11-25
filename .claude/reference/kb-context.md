# Knowledge base context (shared by every agent and skill)

Read this before touching the knowledge base or producing a deliverable. It is the single definition of what the KB files are, how to tell whether the KB is ready, and how to search it.

## Evidence versus framing

| File | Role | May supply facts? |
|---|---|---|
| `knowledge_base/candidate_profile.yaml` | Structured evidence (schema: `docs/profile_schema.md`) | **Yes** |
| `knowledge_base/candidate_narrative.md` | Narrative evidence, voice | **Yes** |
| `knowledge_base/north_star.md` | Positioning, ranked role lenses, not-targeted list, "How to apply" | No: framing only |
| `knowledge_base/resume_variants.md` | Maps lenses to resume variants (selection, ordering, skill grouping, certification rule) | No: framing only |
| `knowledge_base/memories/*.md` | Candidate-specific wording, naming and confidentiality rules | No: framing only |
| `config/preferences.yaml` | Hard constraints (absolute filters) and soft preferences (emphasis) | No: preferences, not evidence |
| `postings/journal/<company>.md` | What recruiters and interviewers actually said | Facts about the process, never about the candidate's record |

Framing decides selection, ordering, emphasis and wording. A claim that appears only in a framing file does not get made.

## Readiness gate

The KB is **ready** when `knowledge_base/candidate_profile.yaml` exists and `personal.name` is not `"Your Name"`. Otherwise it is **missing**. Each agent's own gate decides what happens next (stop, or run a degraded mode).

## What every deliverable reads

1. Profile and narrative (evidence), unless the agent's own instructions say to skip the narrative.
2. `north_star.md` if it exists: pick the role lens; respect the not-targeted list (if a posting matches it, say so before doing any work).
3. **Every file in `knowledge_base/memories/`**, if the folder exists. Apply each rule to every sentence you write. An empty or missing folder is fine.
4. `config/preferences.yaml` when the task involves fit, filtering or emphasis.

## Searching gitignored paths

`knowledge_base/`, `config/preferences.yaml`, `config/search_scopes.yaml`, `config/company_targets.yaml`, `postings/`, `output/` and `data/` are gitignored. The Grep tool inherits ripgrep's gitignore behavior and returns "No matches found" with no warning. Search them with Bash instead:

```bash
rg --no-ignore -n -i "pattern" knowledge_base/
```

Treat a zero-match Grep result inside a gitignored path as unproven, not as a negative.
