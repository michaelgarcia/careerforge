"""Fetch jobs from a Greenhouse-hosted careers board's public API.

No browser automation needed — Greenhouse exposes a public JSON endpoint per
board. The `team=` query parameter in a company's saved careers-page URL is
the Greenhouse department ID directly (verified for Anthropic:
team=4079949008 -> department "Applied AI").

Every job returned by the API for a configured department_id is upserted
into company_jobs, regardless of whether it will later qualify for the
Excel tracker — company_jobs is meant to be a complete, traceable record of
everything ever seen on the site.

Usage:
    python scripts/company_scanner/fetch_greenhouse.py --company anthropic [--dry-run]
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

GREENHOUSE_API_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"


def _strip_html(html: str | None) -> str:
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(separator="\n").strip()


def _matches_department(job: dict[str, Any], department_ids: set[int]) -> bool:
    return any(d.get("id") in department_ids for d in job.get("departments") or [])


def _location_raw(job: dict[str, Any]) -> str:
    # Greenhouse's `location.name` is sometimes itself a composite string
    # (e.g. "San Francisco, CA | New York City, NY") that overlaps with the
    # individually-listed `offices`. Split every candidate on the same
    # separator before de-duping so we don't end up with repeated tokens.
    candidates: list[str] = []
    loc = job.get("location") or {}
    if loc.get("name"):
        candidates.extend(p.strip() for p in loc["name"].split("|"))
    for office in job.get("offices") or []:
        name = office.get("name")
        if name:
            candidates.extend(p.strip() for p in name.split("|"))
    return " | ".join(dict.fromkeys(c for c in candidates if c))


def fetch_jobs(board_token: str, timeout: float = 30.0) -> list[dict[str, Any]]:
    """Fetch the full job list for a Greenhouse board (all departments)."""
    url = GREENHOUSE_API_URL.format(board_token=board_token)
    resp = httpx.get(url, params={"content": "true"}, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data.get("jobs", [])


def sync_company(
    con: sqlite3.Connection | None,
    company: dict[str, Any],
    dry_run: bool,
) -> tuple[int, int, int]:
    """Sync one Greenhouse-backed company. Returns (jobs_found, jobs_added, jobs_updated)."""
    name = company["name"]
    board_token = company["board_token"]
    department_ids = set(company.get("department_ids") or [])

    all_jobs = fetch_jobs(board_token)

    # Warn loudly if a configured department_id matches zero jobs — catches a
    # wrong/stale ID immediately instead of silently returning nothing for it.
    observed_ids: set[int] = set()
    for job in all_jobs:
        for d in job.get("departments") or []:
            if d.get("id") is not None:
                observed_ids.add(d["id"])
    for dep_id in department_ids:
        if dep_id not in observed_ids:
            logger.warning(
                "Company '%s': configured department_id %s matched 0 jobs on the live board "
                "(board has %d total jobs). Verify this ID is correct.",
                name, dep_id, len(all_jobs),
            )

    matched = [j for j in all_jobs if _matches_department(j, department_ids)]
    jobs_found = len(matched)

    if dry_run:
        logger.info("[DRY-RUN] Company '%s': %d jobs matched configured departments (not written)", name, jobs_found)
        return jobs_found, 0, 0

    now_iso = datetime.now(timezone.utc).isoformat()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO company_scan_runs (company, run_at, jobs_found, jobs_added, jobs_updated, jobs_marked_deleted, status) "
        "VALUES (?, ?, ?, 0, 0, 0, 'running')",
        (name, now_iso, jobs_found),
    )
    run_id = cur.lastrowid
    con.commit()

    jobs_added = 0
    jobs_updated = 0

    for job in matched:
        job_id = f"gh_{job['id']}"
        dept_names = ", ".join(d.get("name", "") for d in job.get("departments") or [])
        location_raw = _location_raw(job)
        description_text = _strip_html(job.get("content"))
        job_url = job.get("absolute_url")
        posted_or_updated_at = job.get("updated_at")
        raw_json = json.dumps(job)

        cur.execute("SELECT 1 FROM company_jobs WHERE job_id = ?", (job_id,))
        exists = cur.fetchone() is not None

        cur.execute(
            """
            INSERT INTO company_jobs
                (job_id, source_company, title, department, location_raw, description_text,
                 job_url, posted_or_updated_at, first_seen_at, last_seen_at, still_listed,
                 raw_json, first_seen_run, last_seen_run)
            VALUES (?,?,?,?,?,?,?,?,?,?,1,?,?,?)
            ON CONFLICT(job_id) DO UPDATE SET
                title=excluded.title,
                department=excluded.department,
                location_raw=excluded.location_raw,
                description_text=excluded.description_text,
                job_url=excluded.job_url,
                posted_or_updated_at=excluded.posted_or_updated_at,
                last_seen_at=excluded.last_seen_at,
                still_listed=1,
                raw_json=excluded.raw_json,
                last_seen_run=excluded.last_seen_run
            """,
            (
                job_id, name, job.get("title"), dept_names, location_raw, description_text,
                job_url, posted_or_updated_at, now_iso, now_iso,
                raw_json, run_id, run_id,
            ),
        )
        if exists:
            jobs_updated += 1
        else:
            jobs_added += 1

    cur.execute(
        "UPDATE company_scan_runs SET jobs_added=?, jobs_updated=?, status='success' WHERE id=?",
        (jobs_added, jobs_updated, run_id),
    )
    con.commit()

    logger.info(
        "Company '%s': %d found, %d added, %d updated",
        name, jobs_found, jobs_added, jobs_updated,
    )
    return jobs_found, jobs_added, jobs_updated
