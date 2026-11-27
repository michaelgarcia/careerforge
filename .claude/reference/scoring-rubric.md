# Job fit scoring rubric (shared)

The single rubric for every fit score: `/score` (scorer agent) and `/scan` (job-scanner agent). The dimension keys match what `scripts/linkedin/update_scores.py` stores. Do not rename them.

## Before scoring

1. **Hard constraints** from `user_data/config/preferences.yaml` (location, comp floor when stated, role type, sponsorship, dealbreakers) are absolute filters. A posting that fails one is **FILTERED OUT** with the reason. Never filter for comp that isn't disclosed; note "comp undisclosed" instead.
2. **Not-targeted check:** if `user_data/knowledge_base/north_star.md` exists and the posting's mandate matches its not-targeted list, mark it **NOT TARGETED: <which entry>**. Still score it, but recommend SKIP and say why in one line.

## Dimensions (each 0–100)

| Key | Weight | What to evaluate |
|---|---|---|
| `skill_match` | **30%** | Share of required skills evidenced in the profile; bonus for preferred skills. Weight most heavily the skills behind the north star's first-ranked lens and `preferences.yaml` `soft_preferences.preferred_tech`. |
| `experience_alignment` | **20%** | Seniority, years and scope. **MQ check:** list every stated minimum qualification and whether the KB meets it. Failing 2+ MQs caps this dimension at 40. |
| `preference_match` | **20%** | Fit with soft preferences: domains, company stage, work style, remote or hybrid, career goals. |
| `domain_fit` | **10%** | The posting's industry and domain vs. the candidate's domain experience and `preferred_domains`. |
| `growth_potential` | **10%** | Movement toward `career_goals` and the north star's "Where this goes": scope, stretch, trajectory. |
| `company_quality` | **10%** | Use the guide below. |

**Overall score** = 0.30·skill_match + 0.20·experience_alignment + 0.20·preference_match + 0.10·domain_fit + 0.10·growth_potential + 0.10·company_quality, rounded to an integer.

## Tiers and recommendations

| Score | Tier key | Label | Recommendation |
|---|---|---|---|
| 75–100 | `tier1` | Strong fit | APPLY NOW |
| 60–74 | `tier2` | Good fit | WORTH APPLYING |
| 45–59 | `tier3` | Borderline | APPLY IF TIME |
| 0–44 | `filtered` | Weak fit | SKIP |

These cutoffs match the analytics dashboard legend (`scripts/linkedin/analytics.py`). Change both together, or neither.

Per-dimension anchors: 90–100 exceptional, 70–89 strong, 50–69 moderate (could do the job, not ideal), 30–49 weak (significant gaps), 0–29 poor.

## Company quality guide

| Score | Band |
|---|---|
| 88–100 | Companies in `preferences.yaml` `search_config.target_companies`, or recognized frontier AI/ML leaders |
| 75–87 | Large, highly regarded tech or cloud companies with strong AI/ML investment |
| 60–74 | Well-funded, reputable mid-to-large tech or tech-forward companies |
| 40–59 | Established non-tech enterprises with real tech investment, or small AI boutiques with genuine technical credibility |
| 20–39 | IT staffing, offshore consulting or body-shop firms, regardless of size or title (unless preferences say otherwise) |
| 0–19 | Unknown or low signal: no web presence, temp agency, clear red flags |

- `company_quality` is one dimension of six. A great company with a poor-fit role still scores low overall.
- When a company is ambiguous, look for funding, an engineering blog, open-source work and AI patent activity.

## Evidence

Every "why this fits" point and every MQ marked MET cites a specific KB achievement or skill. Never infer a skill the profile doesn't list. Be honest about gaps.
