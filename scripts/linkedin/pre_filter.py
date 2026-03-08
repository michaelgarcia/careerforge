"""Rule-based hard filter for LinkedIn jobs stored in SQLite.

Marks jobs that clearly fail hard constraints with hard_filtered=1 and a
filter_reason. Runs in milliseconds with zero LLM cost.

Usage:
    python scripts/linkedin/pre_filter.py [--days 14]

    --days N    Only process jobs collected within the last N days (default: 14).
    --reset     Clear all existing hard_filtered flags and re-run filter.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # adds scripts/ to path

from linkedin.init_db import DB_PATH

PREFS_PATH = _ROOT / "config" / "preferences.yaml"

# Title keywords that indicate clearly under-level roles
_JUNIOR_TITLE_KEYWORDS = {
    "intern",
    "internship",
    "junior",
    "associate engineer",
    "coordinator",
    "assistant",
    "entry level",
    "entry-level",
    "graduate",
    "new grad",
    "apprentice",
}

# Employment types that are NOT full-time
_NON_FULLTIME_TYPES = {"part-time", "contract", "temporary", "volunteer", "internship", "other"}


def load_prefs() -> dict:
    with open(PREFS_PATH) as f:
        return yaml.safe_load(f)


def title_is_junior(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in _JUNIOR_TITLE_KEYWORDS)


def employment_type_invalid(employment_type: str | None) -> bool:
    if not employment_type:
        return False
    return employment_type.lower().strip() in _NON_FULLTIME_TYPES


def location_invalid(location: str | None, acceptable_locations: list[str], include_hybrid: bool) -> bool:
    """Return True only when location is clearly wrong AND we have strong signal."""
    if not location or not acceptable_locations:
        return False
    loc_lower = location.lower()
    # If the job says "remote" anywhere it's acceptable
    if "remote" in loc_lower:
        return False
    # If include_hybrid and job mentions hybrid
    if include_hybrid and "hybrid" in loc_lower:
        return False
    # Check against acceptable_locations list
    for acceptable in acceptable_locations:
        if acceptable.lower() in loc_lower or loc_lower in acceptable.lower():
            return False
    # Location doesn't match anything — filter it
    return True


def run_filter(con: sqlite3.Connection, lookback_days: int, reset: bool) -> tuple[int, int]:
    """Apply hard filter rules. Returns (checked, filtered)."""
    prefs = load_prefs()
    hc = prefs.get("hard_constraints", {})
    loc_cfg = hc.get("location", {})
    remote_only: bool = loc_cfg.get("remote_only", False)
    acceptable_locations: list[str] = loc_cfg.get("acceptable_locations") or []
    include_hybrid: bool = loc_cfg.get("include_hybrid", True)

    cur = con.cursor()

    if reset:
        cur.execute("UPDATE job_scores SET hard_filtered=0, filter_reason=NULL")
        con.commit()
        print("Reset all hard_filtered flags.")

    # Cutoff date
    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()

    # Find jobs not yet scored/filtered
    cur.execute(
        """
        SELECT j.job_id, j.title, j.company_name, j.location, j.employment_type
        FROM jobs j
        LEFT JOIN job_scores js ON j.job_id = js.job_id
        WHERE j.collected_at >= ?
          AND (js.job_id IS NULL OR (js.hard_filtered = 0 AND js.score IS NULL))
        """,
        (cutoff,),
    )
    rows = cur.fetchall()

    checked = len(rows)
    filtered = 0

    now_iso = datetime.now(timezone.utc).isoformat()

    for job_id, title, company_name, location, employment_type in rows:
        reason: str | None = None

        if title and title_is_junior(title):
            reason = f"Title indicates under-level role: '{title}'"
        elif employment_type_invalid(employment_type):
            reason = f"Employment type not full-time: '{employment_type}'"
        elif not remote_only and acceptable_locations and location_invalid(
            location, acceptable_locations, include_hybrid
        ):
            reason = f"Location not in acceptable list: '{location}'"

        if reason:
            # Upsert into job_scores
            cur.execute(
                """
                INSERT INTO job_scores (job_id, hard_filtered, filter_reason, scored_at)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    hard_filtered=1,
                    filter_reason=excluded.filter_reason,
                    scored_at=excluded.scored_at
                """,
                (job_id, reason, now_iso),
            )
            filtered += 1

    con.commit()
    return checked, filtered


def main() -> None:
    parser = argparse.ArgumentParser(description="Rule-based hard filter for LinkedIn jobs.")
    parser.add_argument("--days", type=int, default=14, help="Lookback window in days (default: 14).")
    parser.add_argument("--reset", action="store_true", help="Clear existing flags before re-running.")
    args = parser.parse_args()

    con = sqlite3.connect(DB_PATH)
    try:
        checked, filtered = run_filter(con, args.days, args.reset)
    finally:
        con.close()

    print(f"Pre-filter complete: {checked} jobs checked, {filtered} hard-filtered.")


if __name__ == "__main__":
    main()
