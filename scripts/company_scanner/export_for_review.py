"""Export company_jobs rows that need (re)classification as JSON files.

A job needs classification if either:
  - it has no row yet in company_job_classifications, or
  - its description_text has changed since it was last classified
    (detected via a sha256 hash stored in source_description_hash).

Only still_listed=1 jobs are exported — a job that has disappeared from the
site doesn't need fresh judgment, mark_deleted.py / write_trackers.py handle
its Deleted-flip independently of classification.

Each job is written as one JSON file plus a manifest.json the agent reads
to know what to classify and where to write its output.

Usage:
    python scripts/company_scanner/export_for_review.py [--output output/.work/company_scan/] [--company <name>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # adds scripts/ to path

from company_scanner.init_db import DB_PATH

DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "output" / ".work" / "company_scan"


def _hash_description(text: str | None) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def export_jobs(con: sqlite3.Connection, output_dir: Path, company: str | None = None) -> int:
    """Export jobs needing classification as JSON. Returns count exported."""
    output_dir.mkdir(parents=True, exist_ok=True)

    cur = con.cursor()
    query = """
        SELECT j.job_id, j.source_company, j.title, j.department, j.location_raw,
               j.description_text, j.job_url, j.posted_or_updated_at,
               c.source_description_hash
        FROM company_jobs j
        LEFT JOIN company_job_classifications c ON j.job_id = c.job_id
        WHERE j.still_listed = 1
    """
    params: list = []
    if company:
        query += " AND j.source_company = ?"
        params.append(company)
    query += " ORDER BY j.first_seen_at DESC"

    cur.execute(query, params)
    cols = [d[0] for d in cur.description]

    manifest = []
    exported = 0
    for row in cur.fetchall():
        job = dict(zip(cols, row))
        current_hash = _hash_description(job["description_text"])
        if job["source_description_hash"] == current_hash:
            continue  # already classified against this exact description

        job_id = job["job_id"]
        payload = {
            "job_id": job_id,
            "source_company": job["source_company"],
            "title": job["title"],
            "department": job["department"],
            "location_raw": job["location_raw"],
            "job_url": job["job_url"],
            "posted_or_updated_at": job["posted_or_updated_at"],
            "description_text": job["description_text"],
            "description_hash": current_hash,
        }
        (output_dir / f"{job_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

        manifest.append({
            "job_id": job_id,
            "source_company": job["source_company"],
            "title": job["title"],
            "file": f"{job_id}.json",
            "description_hash": current_hash,
        })
        exported += 1

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return exported


def main() -> None:
    parser = argparse.ArgumentParser(description="Export jobs needing classification as JSON.")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT), help="Output directory.")
    parser.add_argument("--company", type=str, default=None, help="Only export this company's jobs.")
    args = parser.parse_args()

    output_dir = Path(args.output)
    con = sqlite3.connect(DB_PATH)
    try:
        count = export_jobs(con, output_dir, args.company)
    finally:
        con.close()

    print(f"Exported {count} job(s) needing classification to {output_dir}")
    print(f"Manifest: {output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
