# Candidate Profile YAML Schema

The `candidate_profile.yaml` follows this schema:

```yaml
personal:
  name: ""
  title: ""
  location: ""
  email: ""
  phone: ""
  linkedin: ""
  github: ""
  website: ""
  summary: ""

skills:
  technical: [""]
  tools: [""]
  frameworks: [""]
  languages: [""]
  soft_skills: [""]
  domains: [""]

experience:
  - company: ""
    title: ""
    start_date: ""
    end_date: ""
    location: ""
    summary: ""
    achievements:
      - description: ""
        impact: ""
        metrics: ""
        skills_used: [""]
        source: ""

education:
  - institution: ""
    degree: ""
    field: ""
    graduation_date: ""
    gpa: ""
    honors: [""]

certifications:
  - name: ""
    issuer: ""
    date: ""
    expiration: ""
    credential_id: ""

publications:
  - title: ""
    venue: ""
    date: ""
    url: ""
    summary: ""

awards:
  - name: ""
    issuer: ""
    date: ""
    description: ""

speaking:
  - title: ""
    event: ""
    date: ""
    url: ""
    description: ""

projects:
  - name: ""
    description: ""
    technologies: [""]
    url: ""
    highlights: [""]
```

The `candidate_reviews.yaml` follows this schema:

```yaml
performance_history:
  - year: ""
    rating: ""
    leadership_principles_rating: ""
    manager_summary: ""
    key_themes: [""]
    source: ""

peer_endorsements:
  - quote: ""
    attribute: ""
    relationship: "peer | manager | customer | skip-level"
    year: ""
    context: ""
    source: ""

growth_areas:
  - theme: ""
    frequency: "one-time | recurring"
    years_cited: [""]
    context: ""
    source: ""
```
