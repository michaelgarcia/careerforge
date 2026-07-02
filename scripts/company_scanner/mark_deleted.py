"""Flag jobs no longer listed on a company's careers site as still_listed=0.

A job is "no longer listed" if it was not touched by that company's most
recent sync run (i.e. last_seen_run != the latest company_scan_runs.id for
that company). This must run after fetch_*.sync_company for the same
company in the same overall sync, since it relies on the just-completed
run already being recorded in company_scan_runs.

Does not touch company_job_classifications or Excel — write_trackers.py is
responsible for translating still_listed=0 into a "Deleted" status, and for
respecting the rule that a row already marked "Applied" is never touched.

Usage:
    python scripts/company_scanner/mark_deleted.py [--company <name>] [--dry-run]
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # adds scripts/ to path

from company_scanner.init_db import DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def mark_deleted(con: sqlite3.Connection, company: str, dry_run: bool = False) -> int:
    """Mark still_listed=0 for jobs not touched by `company`'s latest run.

    Returns the number of jobs newly marked deleted. No-ops if the company
    has no recorded scan runs yet (nothing to compare against).
    """
    cur = con.cursor()
    cur.execute(
        "SELECT MAX(id) FROM company_scan_runs WHERE company = ? AND status = 'success'",
        (company,),
    )
    latest_run = cur.fetchone()[0]
    if latest_run is None:
        logger.warning("Company '%s': no successful scan run found, skipping mark_deleted.", company)
        return 0

    cur.execute(
        """
        SELECT job_id FROM company_jobs
        WHERE source_company = ? AND still_listed = 1
          AND (last_seen_run IS NULL OR last_seen_run != ?)
        """,
        (company, latest_run),
    )
    stale_ids = [row[0] for row in cur.fetchall()]

    if dry_run:
        logger.info("[DRY-RUN] Company '%s': %d job(s) would be marked still_listed=0", company, len(stale_ids))
        return len(stale_ids)

    if stale_ids:
        cur.executemany(
            "UPDATE company_jobs SET still_listed = 0 WHERE job_id = ?",
            [(jid,) for jid in stale_ids],
        )
        con.commit()

    logger.info("Company '%s': %d job(s) marked still_listed=0", company, len(stale_ids))
    return len(stale_ids)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mark stale company_jobs rows as no longer listed.")
    parser.add_argument("--company", type=str, default=None, help="Run only this named company.")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing.")
    args = parser.parse_args()

    con = sqlite3.connect(DB_PATH)
    try:
        if args.company:
            companies = [args.company]
        else:
            cur = con.cursor()
            cur.execute("SELECT DISTINCT source_company FROM company_jobs")
            companies = [row[0] for row in cur.fetchall()]

        total = 0
        for company in companies:
            total += mark_deleted(con, company, args.dry_run)

        label = "[DRY-RUN] " if args.dry_run else ""
        print(f"\n{label}mark_deleted complete: {len(companies)} compan{'y' if len(companies) == 1 else 'ies'}, "
              f"{total} job(s) marked no-longer-listed.")
    finally:
        con.close()


if __name__ == "__main__":
    main()
