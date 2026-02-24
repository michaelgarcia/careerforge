# Interview Prep Output Formats

Reference file for interview-prep sub-task output templates. Each sub-task should read only the section it needs.

---

## Process Research Format (`00_interview_process.md`)

```markdown
# Interview Process: [Company] — [Role Title]
Generated: [date]

## Overview
[Brief summary: expected number of rounds, total timeline, any known quirks]

## Rounds

### Round 1: [Name]
- **Format:** [phone/video/onsite/panel]
- **Duration:** [estimated time]
- **Focus:** [what they assess]
- **Typical interviewer(s):** [who]
- **Notes:** [any specifics from research]

### Round 2: [Name]
...

## Sources
[URLs consulted]

<!-- ROUNDS_DATA
[
  {"number": 1, "name": "Recruiter Screen", "slug": "recruiter_screen", "format": "phone", "duration": "30 min", "focus": "culture fit, role overview, salary expectations"},
  {"number": 2, "name": "Hiring Manager", "slug": "hiring_manager", "format": "video", "duration": "45 min", "focus": "experience deep dive, team fit, leadership"},
  ...
]
-->
```

**Critical:** The `<!-- ROUNDS_DATA [...] -->` HTML comment block at the bottom must contain valid JSON. The orchestrator parses this to launch per-round prep agents. The `slug` field is used for the output filename (e.g., `01_recruiter_screen.md`). The `number` field determines the file prefix.

---

## Company Research Format (`company_research.md`)

```markdown
# Company Research: [Company Name]
Generated: [date]

## Mission & Values
[List each value with a brief description]

## Products & Market Position
[What they build, customers, competitive landscape]

## Recent News (Last 3-6 Months)
[Key items: product launches, strategic shifts, acquisitions]

## Engineering Culture
[Blog posts, open source, tech stack, architecture decisions]

## Company Stage & Trajectory
[Headcount, growth, funding, recent milestones]

## Sources
[URLs consulted]
```

---

## Compensation Analysis Format (`compensation_analysis.md`)

```markdown
# Compensation Analysis: [Company] — [Role Title]
Generated: [date]

## Market Range

### [Company Name]
| Component | Low | Mid | High |
|-----------|-----|-----|------|
| Base Salary | | | |
| Bonus/Variable | | | |
| Equity (annual) | | | |
| **Total Comp** | | | |

### Peer Companies
[Table or list of 3-5 comparable roles at peer companies with ranges]

## Candidate Positioning

**Recommended target range:** [range]

**Rationale — why the candidate should target the upper range:**
- [X] years of experience in [relevant domains]
- [N] published patents, [M] pending — demonstrates innovation and IP creation
- [Certifications] — [list relevant ones]
- [Publications/speaking] — recognized thought leader in [domain]
- [Other differentiators from KB]

Each bullet above traces to specific KB data. If a claim cannot be sourced, it is omitted.

## Negotiation Notes
[Practical advice: when to discuss comp, how to frame the ask, what to negotiate beyond base]

## Sources
[URLs consulted]
```

---

## Round Prep Format (`{NN}_{slug}.md`)

```markdown
# Round [N]: [Round Name]
**Format:** [format] | **Duration:** [duration] | **Focus:** [focus]

## [Sub-theme 1]

### Q: [Question text]
> **Your angle:** [2-3 bullet points with key points, KB reference, suggested framing]

### Q: [Question text]
> **Prepare your answer:** [guidance on what to cover, what the interviewer is looking for]

## [Sub-theme 2]
...

## Questions to Ask the Interviewer
- [Question 1]
- [Question 2]
- ...

## Gaps to Prepare
[Only if the KB lacks strong stories for key question areas in this round]
```

---

## Story Bank Format (`story_bank.md`)

```markdown
# Story Bank: [Company] — [Role Title]
Generated: [date]

This file maps your KB achievements to the interview questions they answer.
Use this to practice: for each story, rehearse telling it with different framings
depending on which question it's answering.

## Story: [Achievement description — short title]
**Achievement:** [XYZ summary from KB]
**Source:** [KB source reference]

**Use for these questions:**
- (Round 1: Recruiter Screen) [Question text]
- (Round 3: Behavioral) [Question text]
- (Round 4: Hiring Manager) [Question text]

---

## Story: [Next achievement]
...

## Coverage Summary
- **Total unique stories mapped:** [N]
- **Rounds with strong KB coverage:** [list]
- **Rounds needing more preparation:** [list — where most questions had "Prepare your answer" instead of KB matches]
```
