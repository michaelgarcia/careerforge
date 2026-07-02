"""Generate a condensed candidate context file for the company-scanner agent.

The company-scanner agent only needs enough candidate context to judge
IC-vs-manager fit and location/comp scope — not the full knowledge base.
This script derives a short (~1500-2000 token) summary from the existing
candidate_profile.yaml / candidate_narrative.md so the agent's context stays
small and fast.

Every fact in the output traces back to the KB (personal.summary + a flat
skill list) per the project's no-fabrication rule. The only feature-specific
content not derived from the KB is the explicit filter criteria for this
feature (Chicago/Remote-US, IC-only, $220k floor), which is hardcoded below
because it's a property of this feature, not the candidate's profile.

Usage:
    python scripts/company_scanner/generate_candidate_summary.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = _ROOT / "knowledge_base"
PROFILE_PATH = KB_DIR / "candidate_profile.yaml"
NARRATIVE_PATH = KB_DIR / "candidate_narrative.md"
OUTPUT_PATH = KB_DIR / "candidate_summary_compact.md"

MAX_SKILLS = 12

# Feature-specific filter criteria — not derived from the KB, fixed for this
# feature. If these ever need to vary, move them into config/company_targets.yaml.
FILTER_CRITERIA = """
## Filter Criteria (this feature only)

- **Location:** Chicago, IL OR Remote USA. Anything else is out of scope.
- **Role type:** Individual Contributor only. Any people-management role
  (titles/descriptions implying direct reports, team leadership, "Manager",
  "Head of", "Director" with org-leadership scope, etc.) is out of scope.
- **Compensation floor:** $220,000 total target compensation (OTE or base+
  bonus+equity combined, whichever the posting states). If a posting does
  not state comp, do not reject for missing data — leave comp fields blank
  and judge fit on location/role-type alone.
"""


def _flat_skills(profile: dict) -> list[str]:
    skills = profile.get("skills") or {}
    ordered: list[str] = []
    for category in ("technical", "domains", "frameworks", "tools"):
        for s in skills.get(category) or []:
            if s not in ordered:
                ordered.append(s)
    return ordered[:MAX_SKILLS]


def generate() -> None:
    if not PROFILE_PATH.exists():
        print(
            f"Error: {PROFILE_PATH} does not exist. Build the knowledge base first "
            f"(run /build-kb) before generating the compact summary.",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(PROFILE_PATH, encoding="utf-8") as f:
        profile = yaml.safe_load(f) or {}

    personal = profile.get("personal") or {}
    summary = personal.get("summary", "").strip()
    if not summary or summary == "A 2-3 sentence professional summary highlighting your core expertise and career focus.":
        print(
            f"Error: {PROFILE_PATH} has no real personal.summary yet (still template content). "
            f"Build/finish the knowledge base first.",
            file=sys.stderr,
        )
        sys.exit(1)

    skills = _flat_skills(profile)

    lines = [
        "# Candidate Summary (Compact)",
        "",
        "_Generated from `candidate_profile.yaml`. Scoped for company-scanner "
        "classification only — resume and cover letter generation must still "
        "use the full knowledge base, not this file._",
        "",
        "## Summary",
        "",
        summary,
        "",
        "## Top Skills",
        "",
        *(f"- {s}" for s in skills),
        "",
        FILTER_CRITERIA.strip(),
        "",
    ]

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    generate()
