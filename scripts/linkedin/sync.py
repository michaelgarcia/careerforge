"""Sync LinkedIn job postings to the local SQLite database.

Loads enabled search scopes from config/search_scopes.yaml, runs each scope
through the LinkedIn Guest API, and stores results with global deduplication.

Usage:
    python scripts/linkedin/sync.py [--scope <name>] [--dry-run] [--days N]

    --scope <name>   Run only the named scope (for testing).
    --dry-run        Fetch and parse results but do not write to the database.
    --days N         Override the date filter for all scopes:
                       1     → past-24h
                       2–7   → past-week
                       8–30  → past-month
                       >30   → any-time
                     Omit to use each scope's configured date_posted.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Ensure tools/ is on the path for linkedin_job_search imports
_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "tools"))

from linkedin_job_search.client import LinkedInJobSearch
from linkedin_job_search.models import (
    DatePosted,
    EnrichedJob,
    ExperienceLevel,
    WorkModel,
)

_SCRIPTS_LINKEDIN = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_LINKEDIN.parent))  # adds scripts/ to path

from linkedin.init_db import DB_PATH, init_db
from linkedin.map_preferences import (
    build_from_preferences_scope,
    get_target_companies,
    load_preferences,
)

SCOPES_PATH = _ROOT / "config" / "search_scopes.yaml"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Enum name → model value mappings ────────────────────────────────────────

_EXP_LEVEL_MAP: dict[str, ExperienceLevel] = {
    "internship": ExperienceLevel.INTERNSHIP,
    "entry-level": ExperienceLevel.ENTRY_LEVEL,
    "associate": ExperienceLevel.ASSOCIATE,
    "mid-senior": ExperienceLevel.MID_SENIOR,
    "director": ExperienceLevel.DIRECTOR,
    "executive": ExperienceLevel.EXECUTIVE,
}

_WORK_MODEL_MAP: dict[str, WorkModel] = {
    "on-site": WorkModel.ON_SITE,
    "remote": WorkModel.REMOTE,
    "hybrid": WorkModel.HYBRID,
}

_DATE_POSTED_MAP: dict[str, DatePosted] = {
    "past-24h": DatePosted.PAST_24H,
    "past-week": DatePosted.PAST_WEEK,
    "past-month": DatePosted.PAST_MONTH,
    "any-time": DatePosted.ANY_TIME,
}


def load_scopes(path: Path = SCOPES_PATH) -> list[dict[str, Any]]:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("scopes", [])


def _days_to_date_posted(days: int) -> str:
    if days <= 1:
        return "past-24h"
    elif days <= 7:
        return "past-week"
    elif days <= 30:
        return "past-month"
    else:
        return "any-time"


def run_scope(
    client: LinkedInJobSearch,
    scope: dict[str, Any],
    con: sqlite3.Connection,
    dry_run: bool,
    days_override: int | None = None,
) -> tuple[int, int, int]:
    """Run one search scope. Returns (jobs_found, jobs_added, jobs_skipped)."""
    name = scope["name"]
    keywords = scope.get("keywords") or None
    exp_level_names: list[str] = scope.get("experience_levels") or []
    default_work_model_name: str | None = scope.get("work_model")
    if days_override is not None:
        date_posted_name = _days_to_date_posted(days_override)
    else:
        date_posted_name = scope.get("date_posted") or "past-week"
    limit: int = scope.get("limit", 50)

    # Map string values to enum instances
    exp_levels = [_EXP_LEVEL_MAP[n] for n in exp_level_names if n in _EXP_LEVEL_MAP]
    date_posted = _DATE_POSTED_MAP.get(date_posted_name, DatePosted.PAST_WEEK)

    # Build list of (geo_id, work_model) pairs to search.
    # Prefer geo_searches (precise numeric geoId) over legacy locations (text string).
    # LinkedIn's text location parameter is not reliably enforced; geoId is.
    geo_searches: list[dict] = scope.get("geo_searches") or []
    if geo_searches:
        search_targets = [
            {
                "geo_id": entry["geo_id"],
                "work_model_name": entry.get("work_model") or default_work_model_name,
            }
            for entry in geo_searches
        ]
    else:
        # Legacy fallback: use location text strings (less reliable)
        locations: list[str] = scope.get("locations") or []
        if locations:
            search_targets = [
                {"location": loc, "work_model_name": default_work_model_name}
                for loc in locations
            ]
        else:
            search_targets = [{"work_model_name": default_work_model_name}]

    all_results: list[EnrichedJob] = []
    for target in search_targets:
        geo_id = target.get("geo_id")
        location = target.get("location")
        work_model = _WORK_MODEL_MAP.get(target["work_model_name"]) if target["work_model_name"] else None
        logger.info(
            "Scope '%s' — geo_id=%s location=%s work_model=%s",
            name,
            geo_id or "(none)",
            location or "(none)",
            target["work_model_name"] or "(any)",
        )
        results = client.search(
            keywords=keywords,
            location=location,
            geo_id=geo_id,
            experience_level=exp_levels if exp_levels else None,
            work_model=work_model,
            date_posted=date_posted,
            enrich=True,
            limit=limit,
        )
        all_results.extend(results)  # type: ignore[arg-type]

    jobs_found = len(all_results)

    if dry_run:
        logger.info("[DRY-RUN] Scope '%s': %d jobs found (not written)", name, jobs_found)
        return jobs_found, 0, 0

    # Insert into DB with global dedup via INSERT OR IGNORE
    run_at = datetime.now(timezone.utc).isoformat()
    cur = con.cursor()

    # Log the search run first
    cur.execute(
        "INSERT INTO search_runs (scope_name, run_at, jobs_found, jobs_added, jobs_skipped, status) "
        "VALUES (?, ?, ?, 0, 0, 'running')",
        (name, run_at, jobs_found),
    )
    run_id = cur.lastrowid
    con.commit()

    jobs_added = 0
    jobs_skipped = 0

    for job in all_results:
        enriched_at = job.enriched_at.isoformat() if job.enriched_at else None
        collected_at = job.collected_at.isoformat() if job.collected_at else None

        cur.execute(
            """
            INSERT OR IGNORE INTO jobs
                (job_id, title, company_name, location, job_url, posted_time,
                 collected_at, full_description, seniority_level, employment_type,
                 job_function, industries, salary_info, enriched_at, source_scope,
                 first_seen_run)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                job.job_id,
                job.title,
                job.company_name,
                job.location,
                job.job_url,
                job.posted_time,
                collected_at,
                job.full_description,
                job.seniority_level,
                job.employment_type,
                job.job_function,
                job.industries,
                job.salary_info,
                enriched_at,
                name,
                run_id,
            ),
        )
        if cur.rowcount > 0:
            jobs_added += 1
        else:
            jobs_skipped += 1

    # Update run record
    cur.execute(
        "UPDATE search_runs SET jobs_added=?, jobs_skipped=?, status='success' WHERE id=?",
        (jobs_added, jobs_skipped, run_id),
    )
    con.commit()

    logger.info(
        "Scope '%s': %d found, %d added, %d skipped (duplicates)",
        name,
        jobs_found,
        jobs_added,
        jobs_skipped,
    )
    return jobs_found, jobs_added, jobs_skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync LinkedIn jobs to SQLite.")
    parser.add_argument("--scope", type=str, default=None, help="Run only this named scope.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but do not write to DB.")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        metavar="N",
        help="Override date filter: 1=past-24h, 2-7=past-week, 8-30=past-month, >30=any-time.",
    )
    args = parser.parse_args()

    # Ensure DB exists
    if not args.dry_run:
        init_db()

    # Load scopes
    scopes = load_scopes()

    # Inject preferences-derived scope + target_companies
    prefs = load_preferences()
    pref_scope = build_from_preferences_scope(prefs)
    target_companies = get_target_companies(prefs)

    # Inject target companies into the 'target_companies' scope
    for s in scopes:
        if s.get("name") == "target_companies" and s.get("enabled"):
            s["companies"] = target_companies

    # Append the auto-generated preferences scope
    scopes.append(pref_scope)

    # Filter to requested scope
    if args.scope:
        scopes = [s for s in scopes if s.get("name") == args.scope]
        if not scopes:
            logger.error("No scope named '%s' found in search_scopes.yaml", args.scope)
            sys.exit(1)
    else:
        scopes = [s for s in scopes if s.get("enabled", True)]

    logger.info("Running %d scope(s)%s", len(scopes), " [DRY-RUN]" if args.dry_run else "")

    con = sqlite3.connect(DB_PATH) if not args.dry_run else None  # type: ignore[assignment]
    client = LinkedInJobSearch(request_delay=1.5)

    total_found = total_added = total_skipped = 0

    try:
        for scope in scopes:
            found, added, skipped = run_scope(client, scope, con, args.dry_run, args.days)
            total_found += found
            total_added += added
            total_skipped += skipped
    finally:
        client.close()
        if con:
            con.close()

    print(
        f"\nSync complete: {len(scopes)} scope(s), "
        f"{total_found} found, {total_added} added, {total_skipped} skipped."
    )


if __name__ == "__main__":
    main()
