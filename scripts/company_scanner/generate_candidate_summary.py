"""Generate a condensed candidate context file for the company-scanner agent.

The company-scanner agent only needs enough candidate context to judge
IC-vs-manager fit and location/comp scope — not the full knowledge base.
This script derives a short (~1500-2000 token) summary from the existing
candidate_profile.yaml / candidate_narrative.md so the agent's context stays
small and fast.

Every fact in the output traces back to the KB (personal.summary + a flat
skill list) per the project's no-fabrication rule. The filter criteria come
from user_data/config/preferences.yaml (gitignored): location from
hard_constraints.location, the comp floor from
hard_constraints.minimum_compensation_usd, and the role and function rules from
the company_scanner block.

Usage:
    python scripts/company_scanner/generate_candidate_summary.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # adds scripts/ to path
from paths import USER_DATA  # noqa: E402

KB_DIR = USER_DATA / "knowledge_base"
PROFILE_PATH = KB_DIR / "candidate_profile.yaml"
PREFS_PATH = USER_DATA / "config" / "preferences.yaml"
OUTPUT_PATH = KB_DIR / "candidate_summary_compact.md"

MAX_SKILLS = 12

def _location_rule(location: dict, home_city: str) -> str:
    acceptable = [str(x) for x in (location.get("acceptable_locations") or [])]
    remote_scope = "United States" if "United States" in acceptable else ""
    cities = [x for x in acceptable if x != "United States"]
    if home_city and home_city not in cities:
        cities.insert(0, home_city)
    parts = cities[:]
    if location.get("remote_only"):
        parts = [f"Remote {remote_scope or 'only'}".strip()]
    elif remote_scope:
        parts.append("Remote USA")
    if not parts:
        return "Any location."
    return " OR ".join(parts) + ". Anything else is out of scope."


def _filter_criteria(prefs: dict) -> str:
    hc = prefs.get("hard_constraints") or {}
    cs = prefs.get("company_scanner") or {}
    home_city = str(cs.get("home_city") or "").strip()
    floor = hc.get("minimum_compensation_usd") or 0
    role_rule = " ".join(str(cs.get("role_rule") or "").split()) or "Any role type."
    function_scope = " ".join(str(cs.get("function_scope") or "").split()) or "Any function."
    comp = (
        f"${floor:,.0f} total target compensation (OTE or base+bonus+equity "
        "combined, whichever the posting states). If a posting does not state comp, "
        "do not reject for missing data — leave comp fields blank and judge fit on "
        "location/role-type alone."
        if floor
        else "None set. Never reject on compensation."
    )
    lines = [
        "## Filter Criteria (this feature only)",
        "",
        f"- **Location:** {_location_rule(hc.get('location') or {}, home_city)}",
    ]
    if home_city:
        lines.append(f"- **Home city** (the `chicago_yn` field — legacy name): true only if {home_city} is explicitly an eligible location.")
    lines += [
        f"- **Role type:** {role_rule}",
        f"- **Function scope:** {function_scope}",
        f"- **Compensation floor:** {comp}",
    ]
    return "\n".join(lines)


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

    if not PREFS_PATH.exists():
        print(
            f"Error: {PREFS_PATH} does not exist. Set up your job search preferences "
            f"first (say \"set up my job filters\").",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(PREFS_PATH, encoding="utf-8") as f:
        prefs = yaml.safe_load(f) or {}

    skills = _flat_skills(profile)

    lines = [
        "# Candidate Summary (Compact)",
        "",
        "_Generated from `candidate_profile.yaml` and `user_data/config/preferences.yaml`. Scoped for company-scanner "
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
        _filter_criteria(prefs),
        "",
    ]

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    generate()
