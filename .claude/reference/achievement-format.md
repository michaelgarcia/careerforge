# Achievement format (shared)

The single definition of how achievements are stored in the KB and phrased in deliverables.

## XYZ formula

"Accomplished **[X]** as measured by **[Y]**, by doing **[Z]**."

| KB field | Formula part | Content |
|---|---|---|
| `description` | X | What was accomplished (the outcome) |
| `metrics` | Y | How it was measured: %, $, time, scale, users, team size |
| `impact` | Z | What was done: the approach, technology or method |

- No number in the source? Record `metrics: "(unquantified)"` and flag it as a gap for story capture. Never invent or estimate a number on the candidate's behalf.
- Every achievement carries a `source` (a path relative to `user_data/knowledge_base/sources/`, or `"unverified"`).

## Leadership scope

For every leadership achievement, capture team size (direct and total), organizational scope (team, cross-functional, org, company), budget if stated, and whether the role was formal (title) or informal (tech lead, program lead). Store it in the optional `leadership` field (`docs/profile_schema.md`) and keep it visible in the wording: "Led a cross-functional team of 12", not "Led a team".

## Wording in deliverables

- Start bullets with a strong, accurate verb: Led, Architected, Built, Delivered, Designed, Reduced, Increased, Launched.
- **Verb fidelity:** use the KB's verb, not the more impressive neighbor. *Built content delivered by* an executive is not *delivered*; *contributed to* is not *launched*.
- Cut filler: "responsible for", "helped to", "worked on".
- Keep each of these only if the KB already uses it: spearheaded, leveraged, pivotal, intricate, showcasing, synergy, delve, realm, robust, seamless, cutting-edge.
- At least 60% of resume bullets carry a quantified metric, where the KB has one.
