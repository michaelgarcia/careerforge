# Candidate Profile Schema

**This is the only definition of `knowledge_base/candidate_profile.yaml`.** The kb-builder agent, the `capture-story` skill and every reader follow it. `templates/candidate_profile.template.yaml` is an example that conforms to it, not a second definition.

Conventions:
- **Required** fields are marked `# required`. Everything else is optional. Omit an optional field rather than writing an empty value when the source doesn't support it.
- **Provenance:** `source` is a path relative to `knowledge_base/sources/` (for example `"Resumes and mind maps/resume_2025.pdf"`), or `"unverified"`. Never invent one. Older story captures use `story-capture-session-YYYY-MM-DD`; new ones point to a file under `sources/Stories/`.
- **Dates** are `YYYY-MM` (or `YYYY`); `end_date` may be `"Present"`.
- Field semantics for achievements (XYZ, leadership scope, wording): `.claude/reference/achievement-format.md`.

```yaml
personal:
  name: ""                 # required. "Your Name" means the profile is still the template
  title: ""
  location: ""
  email: ""
  phone: ""
  linkedin: ""
  github: ""
  website: ""
  summary: ""
  languages_spoken: [""]

skills:                    # each a list of strings
  technical: [""]
  tools: [""]
  frameworks: [""]
  languages: [""]          # programming languages
  soft_skills: [""]
  domains: [""]

experience:                # most recent first
  - company: ""            # required
    title: ""              # required
    start_date: ""         # required
    end_date: ""           # required ("Present" if current)
    location: ""
    summary: ""
    achievements:
      - id: ""             # stable key: "ach-<company>-<short-slug>", unique, never reused
        description: ""    # required. X: what was accomplished
        metrics: ""        # required. Y: how it was measured, or "(unquantified)"
        impact: ""         # required. Z: what was done
        leadership:        # include when the achievement involved leading people
          team_size: ""    # e.g. "8 direct, 30 cross-functional"
          scope: ""        # team | cross-functional | org | company
          formal: true     # true = title-based; false = tech lead / program lead
          budget: ""       # if stated
        tags: [""]         # free-form themes, used to match role lenses and interview questions
        skills_used: [""]
        source: ""         # required

education:
  - institution: ""
    degree: ""
    field: ""
    graduation_date: ""
    gpa: ""
    honors: [""]
    source: ""

certifications:
  - name: ""
    issuer: ""
    date: ""
    expiration: ""
    credential_id: ""
    source: ""

publications:              # patents go here too: title, number in `venue`, one-line summary
  - title: ""
    venue: ""
    date: ""
    url: ""
    summary: ""
    source: ""

awards:
  - name: ""
    issuer: ""
    date: ""
    description: ""
    source: ""

speaking:
  - title: ""
    event: ""
    date: ""
    url: ""
    description: ""
    source: ""

projects:
  - name: ""
    description: ""
    technologies: [""]
    url: ""
    highlights: [""]
    source: ""
```

## Performance reviews

There is no separate reviews section. Quantified accomplishments from reviews become achievements under the matching `experience` entry. Quotes, growth themes and progression signals go into `candidate_narrative.md`. The old `candidate_reviews.yaml` is archived in `knowledge_base/archive/`, and no agent reads it.

## Growing the schema

1. Add the field here first, as **optional**, with a one-line comment.
2. Then update the kb-builder agent (and `capture-story` if it writes that section).
3. Never back-fill invented values. Existing entries gain the field the next time a source supports it.
4. Never rename or remove a field without migrating every reader in the same change.
