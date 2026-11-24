Use the north-star agent to define or refresh my career north star: the core positioning statement, career narrative, ranked role lenses, not-targeted list, and forward trajectory that anchor every resume, cover letter, and job score.

$ARGUMENTS

Read knowledge_base/candidate_profile.yaml, knowledge_base/candidate_narrative.md, knowledge_base/resume_variants.md, knowledge_base/memories/*.md, and config/preferences.yaml first, plus knowledge_base/north_star.md and output/career_paths/*.md if they exist. These paths are gitignored, so search them with `rg --no-ignore` via Bash rather than the Grep tool. Derive a positioning hypothesis from the evidence, citing the specific achievements behind each role lens and flagging any lens the knowledge base cannot support. Present the hypothesis, then interview me one question at a time to sharpen it. Show the complete draft and wait for my confirmation before writing knowledge_base/north_star.md.

Optional arguments you can pass:
- A brain dump of how you see your own positioning: it will be parsed directly, and the interview will only cover what it left open
- "refresh": re-derive against new knowledge base content, diff against the current file, and propose a version bump
- "lenses only": revise just the role lenses and the not-targeted list, leaving the rest unchanged
