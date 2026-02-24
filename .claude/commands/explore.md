Use the career-explorer agent to analyze the candidate's profile and generate a deep research report of the best-fit roles in the current job market. The report includes fit analysis grounded in the knowledge base, real job posting examples, compensation estimates, and work-life balance data for each role, ending with a comparison table and recommended next steps.

$ARGUMENTS

Read knowledge_base/candidate_profile.yaml, knowledge_base/candidate_narrative.md, and config/preferences.yaml first. Synthesize 2–3 candidate archetypes, then identify 5–8 role categories (core fit, lateral, and growth). For each role, run WebSearch and WebFetch to gather real job postings, compensation data from Levels.fyi/Glassdoor/LinkedIn Salary, and work-life balance data from Glassdoor/Blind. Ground all fit analysis in specific KB achievements and skills — no fabrication. Save the report to output/career_exploration/career_exploration_[YYYY-MM-DD].md.

Optional arguments you can pass:
- Focus area: e.g., "focus on AI leadership roles" or "include startup-stage roles"
- Number of roles: e.g., "find 6 roles" (default: 5–8)
- Custom constraints: e.g., "exclude roles with more than 20% travel"
