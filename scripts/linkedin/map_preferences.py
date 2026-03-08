"""Map config/preferences.yaml fields to LinkedIn search parameters.

Used by sync.py at runtime to build a synthetic 'from_preferences' scope
and to inject target_companies into the 'target_companies' scope.

Usage (standalone — prints the generated scope as YAML):
    python scripts/linkedin/map_preferences.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PREFS_PATH = Path(__file__).resolve().parents[2] / "config" / "preferences.yaml"

# Mapping from preferences role_types → LinkedIn experience_level names
_ROLE_TO_EXP_LEVEL: dict[str, list[str]] = {
    "Individual Contributor": ["mid-senior"],
    "Technical Lead": ["mid-senior", "director"],
    "Staff Architect": ["mid-senior", "director"],
    "Principal Architect": ["director"],
    "Director": ["director"],
    "VP": ["executive"],
    "C-Level": ["executive"],
}


def load_preferences(path: Path = PREFS_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def build_from_preferences_scope(prefs: dict) -> dict[str, Any]:
    """Generate a synthetic search scope from preferences.yaml fields."""
    hc = prefs.get("hard_constraints", {})
    sc = prefs.get("search_config", {})

    # --- locations ---
    loc_cfg = hc.get("location", {})
    if loc_cfg.get("remote_only"):
        locations = ["Remote"]
        work_model = "remote"
    else:
        locations = [str(l) for l in (loc_cfg.get("acceptable_locations") or [])]
        work_model = "hybrid" if loc_cfg.get("include_hybrid") else "on-site"

    # --- experience levels ---
    role_types = hc.get("role_types") or []
    exp_levels: list[str] = []
    for rt in role_types:
        for lvl in _ROLE_TO_EXP_LEVEL.get(rt, []):
            if lvl not in exp_levels:
                exp_levels.append(lvl)

    # --- keywords (titles + keywords) ---
    titles = [str(t) for t in (sc.get("target_titles") or [])]
    kws = [str(k) for k in (sc.get("keywords") or [])]
    # Deduplicate while preserving order
    seen: set[str] = set()
    all_terms: list[str] = []
    for term in titles + kws:
        if term not in seen:
            seen.add(term)
            all_terms.append(term)
    keywords_str = " ".join(all_terms[:8])  # LinkedIn keyword string has practical length limit

    return {
        "name": "from_preferences",
        "description": "Auto-generated scope from config/preferences.yaml",
        "keywords": keywords_str,
        "locations": locations,
        "experience_levels": exp_levels,
        "work_model": work_model,
        "date_posted": "past-week",
        "limit": 75,
        "enabled": True,
    }


def get_target_companies(prefs: dict) -> list[str]:
    """Return target companies list from search_config."""
    return [str(c) for c in (prefs.get("search_config", {}).get("target_companies") or [])]


def get_score_threshold(prefs: dict) -> int:
    """Return the lead_score_threshold (default 65)."""
    return int(prefs.get("linkedin_scanner", {}).get("lead_score_threshold", 65))


def get_max_score_per_run(prefs: dict) -> int:
    """Return the max_score_per_run (default 30)."""
    return int(prefs.get("linkedin_scanner", {}).get("max_score_per_run", 30))


def get_export_lookback_days(prefs: dict) -> int:
    """Return the export_lookback_days (default 7)."""
    return int(prefs.get("linkedin_scanner", {}).get("export_lookback_days", 7))


if __name__ == "__main__":
    prefs = load_preferences()
    scope = build_from_preferences_scope(prefs)
    companies = get_target_companies(prefs)
    print("Generated 'from_preferences' scope:")
    print(yaml.dump(scope, default_flow_style=False))
    print(f"Target companies ({len(companies)}): {companies}")
