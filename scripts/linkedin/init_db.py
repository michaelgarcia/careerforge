"""Initialize the SQLite jobs database schema.

Run once before first use:
    python scripts/linkedin/init_db.py

Safe to re-run — uses CREATE TABLE IF NOT EXISTS.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "jobs.db"


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS search_runs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            scope_name   TEXT    NOT NULL,
            run_at       TEXT    NOT NULL,
            jobs_found   INTEGER,
            jobs_added   INTEGER,
            jobs_skipped INTEGER,
            status       TEXT
        );

        CREATE TABLE IF NOT EXISTS jobs (
            job_id           TEXT PRIMARY KEY,
            title            TEXT NOT NULL,
            company_name     TEXT,
            location         TEXT,
            job_url          TEXT,
            posted_time      TEXT,
            collected_at     TEXT,
            full_description TEXT,
            seniority_level  TEXT,
            employment_type  TEXT,
            job_function     TEXT,
            industries       TEXT,
            salary_info      TEXT,
            enriched_at      TEXT,
            source_scope     TEXT,
            first_seen_run   INTEGER REFERENCES search_runs(id)
        );

        CREATE TABLE IF NOT EXISTS job_scores (
            job_id               TEXT PRIMARY KEY REFERENCES jobs(job_id),
            scored_at            TEXT,
            score                INTEGER,
            tier                 TEXT,
            skill_match          INTEGER,
            experience_alignment INTEGER,
            domain_fit           INTEGER,
            growth_potential     INTEGER,
            company_quality      INTEGER,
            preference_match     INTEGER,
            hard_filtered        INTEGER DEFAULT 0,
            filter_reason        TEXT,
            notes                TEXT,
            presented_at         TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_jobs_source_scope   ON jobs(source_scope);
        CREATE INDEX IF NOT EXISTS idx_jobs_collected_at   ON jobs(collected_at);
        CREATE INDEX IF NOT EXISTS idx_scores_score        ON job_scores(score);
        CREATE INDEX IF NOT EXISTS idx_scores_presented_at ON job_scores(presented_at);
        CREATE INDEX IF NOT EXISTS idx_scores_hard_filtered ON job_scores(hard_filtered);
    """)

    con.commit()
    con.close()
    print(f"Database initialised at: {db_path}")


if __name__ == "__main__":
    init_db()
