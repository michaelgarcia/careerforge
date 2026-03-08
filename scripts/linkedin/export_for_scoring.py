"""Export unscored, non-filtered jobs as markdown files for LLM scoring.

Usage:
    python scripts/linkedin/export_for_scoring.py [--output /tmp/jobs/] [--days 7] [--limit 30]

    --output DIR   Directory to write markdown files (default: /tmp/careerforge_scoring/)
    --days N       Include jobs collected within last N days (default: from preferences)
    --limit N      Maximum jobs to export (default: from preferences max_score_per_run)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # adds scripts/ to path

from linkedin.init_db import DB_PATH
from linkedin.map_preferences import (
    get_export_lookback_days,
    get_max_score_per_run,
    load_preferences,
)

DEFAULT_OUTPUT = Path("/tmp/careerforge_scoring")


def export_jobs(
    con: sqlite3.Connection,
    output_dir: Path,
    lookback_days: int,
    limit: int,
) -> int:
    """Export unscored jobs as markdown. Returns count exported."""
    output_dir.mkdir(parents=True, exist_ok=True)

    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()

    cur = con.cursor()
    cur.execute(
        """
        SELECT j.job_id, j.title, j.company_name, j.location, j.job_url,
               j.posted_time, j.full_description, j.seniority_level,
               j.employment_type, j.job_function, j.industries, j.salary_info,
               j.source_scope
        FROM jobs j
        LEFT JOIN job_scores js ON j.job_id = js.job_id
        WHERE j.collected_at >= ?
          AND (js.job_id IS NULL OR (js.score IS NULL AND js.hard_filtered = 0))
        ORDER BY j.collected_at DESC
        LIMIT ?
        """,
        (cutoff, limit),
    )
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]

    for row in rows:
        job = dict(zip(cols, row))
        job_id = job["job_id"]

        lines = [
            f"# {job['title']}",
            f"",
            f"**Company:** {job['company_name'] or 'Unknown'}  ",
            f"**Location:** {job['location'] or 'Unknown'}  ",
            f"**Seniority:** {job['seniority_level'] or 'Unknown'}  ",
            f"**Employment Type:** {job['employment_type'] or 'Unknown'}  ",
            f"**Industries:** {job['industries'] or 'Unknown'}  ",
            f"**Job Function:** {job['job_function'] or 'Unknown'}  ",
        ]

        if job.get("salary_info"):
            lines.append(f"**Salary:** {job['salary_info']}  ")

        lines += [
            f"**Posted:** {job['posted_time'] or 'Unknown'}  ",
            f"**Source Scope:** {job['source_scope'] or 'Unknown'}  ",
            f"**URL:** {job['job_url']}  ",
            f"**Job ID:** {job_id}  ",
            f"",
            f"## Job Description",
            f"",
            job["full_description"] or "_No description available._",
        ]

        md_path = output_dir / f"{job_id}.md"
        md_path.write_text("\n".join(lines), encoding="utf-8")

    # Write a manifest for the agent to consume
    manifest = [{"job_id": dict(zip(cols, r))["job_id"],
                  "title": dict(zip(cols, r))["title"],
                  "company_name": dict(zip(cols, r))["company_name"],
                  "file": f"{dict(zip(cols, r))['job_id']}.md"} for r in rows]
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return len(rows)


def main() -> None:
    prefs = load_preferences()

    parser = argparse.ArgumentParser(description="Export unscored jobs as markdown for LLM scoring.")
    parser.add_argument(
        "--output", type=str, default=str(DEFAULT_OUTPUT),
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--days", type=int, default=get_export_lookback_days(prefs),
        help="Lookback window in days.",
    )
    parser.add_argument(
        "--limit", type=int, default=get_max_score_per_run(prefs),
        help="Maximum jobs to export.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    con = sqlite3.connect(DB_PATH)
    try:
        count = export_jobs(con, output_dir, args.days, args.limit)
    finally:
        con.close()

    print(f"Exported {count} jobs to {output_dir}")
    print(f"Manifest: {output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
