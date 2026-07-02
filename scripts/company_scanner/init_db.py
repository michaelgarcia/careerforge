"""Initialize the company-scanner tables in the shared SQLite jobs database.

Adds company_jobs / company_job_classifications / company_scan_runs to the
same data/jobs.db used by the LinkedIn scanner. Fully namespaced — does not
read or modify the LinkedIn scanner's jobs/job_scores/search_runs tables.

Run once before first use:
    python scripts/company_scanner/init_db.py

Safe to re-run — uses CREATE TABLE IF NOT EXISTS.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # adds scripts/ to path

from linkedin.init_db import DB_PATH  # noqa: E402  (shared DB file with the LinkedIn scanner)


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS company_scan_runs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            company      TEXT    NOT NULL,
            run_at       TEXT    NOT NULL,
            jobs_found   INTEGER,
            jobs_added   INTEGER,
            jobs_updated INTEGER,
            jobs_marked_deleted INTEGER,
            status       TEXT
        );

        CREATE TABLE IF NOT EXISTS company_jobs (
            job_id            TEXT PRIMARY KEY,
            source_company    TEXT NOT NULL,
            title             TEXT,
            department        TEXT,
            location_raw      TEXT,
            description_text  TEXT,
            job_url           TEXT,
            posted_or_updated_at TEXT,
            first_seen_at     TEXT NOT NULL,
            last_seen_at      TEXT NOT NULL,
            still_listed      INTEGER DEFAULT 1,
            raw_json          TEXT,
            first_seen_run    INTEGER REFERENCES company_scan_runs(id),
            last_seen_run     INTEGER REFERENCES company_scan_runs(id)
        );

        CREATE TABLE IF NOT EXISTS company_job_classifications (
            job_id             TEXT PRIMARY KEY REFERENCES company_jobs(job_id),
            is_manager         INTEGER,
            in_location_scope  INTEGER,
            chicago_yn         INTEGER,
            ote_low            INTEGER,
            ote_high           INTEGER,
            base_low           INTEGER,
            base_high          INTEGER,
            equity_yn          INTEGER,
            disposition        TEXT,
            notes              TEXT,
            classified_at      TEXT,
            source_description_hash TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_company_jobs_source     ON company_jobs(source_company);
        CREATE INDEX IF NOT EXISTS idx_company_jobs_still_listed ON company_jobs(still_listed);
        CREATE INDEX IF NOT EXISTS idx_company_classif_disposition ON company_job_classifications(disposition);
    """)

    # Migration: add last_seen_run if this table predates the column.
    existing_cols = {row[1] for row in cur.execute("PRAGMA table_info(company_jobs)")}
    if "last_seen_run" not in existing_cols:
        cur.execute("ALTER TABLE company_jobs ADD COLUMN last_seen_run INTEGER")

    con.commit()
    con.close()
    print(f"Company-scanner tables ready in: {db_path}")


if __name__ == "__main__":
    init_db()
