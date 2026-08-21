"""Write the classification agent's judgments back into SQLite.

Reads a JSON array produced by the company-scanner agent (one entry per job
exported by export_for_review.py) and upserts each into
company_job_classifications. Never touches Excel — write_trackers.py reads
this table separately and is the only script that writes .xlsx files.

Input format:
    [
      {
        "job_id": "gh_1234567",
        "is_manager": false,
        "management_scope": "none",
        "in_location_scope": true,
        "chicago_yn": false,
        "ote_low": 220000,
        "ote_high": 260000,
        "base_low": null,
        "base_high": null,
        "equity_yn": true,
        "disposition": "qualified",
        "notes": "Remote-US eligible IC role, OTE stated in posting.",
        "description_hash": "<sha256 from the exported job JSON>"
      },
      ...
    ]

disposition must be one of: qualified, rejected_manager_role,
rejected_location, rejected_comp_floor, rejected_other.

management_scope must be one of: none, small team, org (or null). It records
how much people-leadership a role carries, so the candidate can judge headcount
per posting. It is descriptive only and never drives a rejection on its own —
rejected_manager_role is reserved for roles whose mandate is running an
engineering organization rather than directing AI or technical work.

Usage:
    python scripts/company_scanner/apply_classifications.py --input /tmp/classifications.json
    python scripts/company_scanner/apply_classifications.py --input /tmp/classifications.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # adds scripts/ to path

from company_scanner.init_db import DB_PATH

_VALID_DISPOSITIONS = {
    "qualified",
    "rejected_manager_role",
    "rejected_location",
    "rejected_comp_floor",
    "rejected_other",
}

# Descriptive only — records how much people-leadership a qualified role carries.
# Never drives a rejection on its own.
_VALID_MANAGEMENT_SCOPES = {"none", "small team", "org"}


def validate_record(record: dict) -> str | None:
    """Return an error message if the record is invalid, else None."""
    if not record.get("job_id"):
        return "Missing job_id"
    if not record.get("description_hash"):
        return "Missing description_hash"
    disposition = record.get("disposition")
    if disposition not in _VALID_DISPOSITIONS:
        return f"Invalid disposition: {disposition!r} (must be one of {_VALID_DISPOSITIONS})"
    for bool_field in ("is_manager", "in_location_scope", "chicago_yn", "equity_yn"):
        val = record.get(bool_field)
        if val is not None and not isinstance(val, bool):
            return f"Invalid {bool_field}: {val!r} (must be true/false/null)"
    scope = record.get("management_scope")
    if scope is not None and scope not in _VALID_MANAGEMENT_SCOPES:
        return f"Invalid management_scope: {scope!r} (must be one of {_VALID_MANAGEMENT_SCOPES} or null)"
    return None


def apply_classifications(con: sqlite3.Connection, records: list[dict], dry_run: bool) -> tuple[int, int, int]:
    """Upsert classification records. Returns (updated, skipped_invalid, skipped_unknown_job)."""
    cur = con.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()

    updated = 0
    skipped_invalid = 0
    skipped_unknown = 0

    for record in records:
        err = validate_record(record)
        if err:
            print(f"  [SKIP invalid] {record.get('job_id', '?')}: {err}", file=sys.stderr)
            skipped_invalid += 1
            continue

        job_id = record["job_id"]

        cur.execute("SELECT 1 FROM company_jobs WHERE job_id=?", (job_id,))
        if not cur.fetchone():
            print(f"  [SKIP unknown] job_id={job_id} not in company_jobs", file=sys.stderr)
            skipped_unknown += 1
            continue

        if dry_run:
            print(f"  [DRY-RUN] Would classify job_id={job_id} disposition={record['disposition']}")
            updated += 1
            continue

        cur.execute(
            """
            INSERT INTO company_job_classifications
                (job_id, is_manager, management_scope, in_location_scope, chicago_yn,
                 ote_low, ote_high, base_low, base_high, equity_yn,
                 disposition, notes, classified_at, source_description_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                is_manager=excluded.is_manager,
                management_scope=excluded.management_scope,
                in_location_scope=excluded.in_location_scope,
                chicago_yn=excluded.chicago_yn,
                ote_low=excluded.ote_low,
                ote_high=excluded.ote_high,
                base_low=excluded.base_low,
                base_high=excluded.base_high,
                equity_yn=excluded.equity_yn,
                disposition=excluded.disposition,
                notes=excluded.notes,
                classified_at=excluded.classified_at,
                source_description_hash=excluded.source_description_hash
            """,
            (
                job_id,
                record.get("is_manager"),
                record.get("management_scope"),
                record.get("in_location_scope"),
                record.get("chicago_yn"),
                record.get("ote_low"),
                record.get("ote_high"),
                record.get("base_low"),
                record.get("base_high"),
                record.get("equity_yn"),
                record["disposition"],
                record.get("notes"),
                now_iso,
                record["description_hash"],
            ),
        )
        updated += 1

    if not dry_run:
        con.commit()

    return updated, skipped_invalid, skipped_unknown


def main() -> None:
    parser = argparse.ArgumentParser(description="Write classification judgments back to SQLite.")
    parser.add_argument("--input", required=True, help="Path to JSON classifications file.")
    parser.add_argument("--dry-run", action="store_true", help="Validate but do not write.")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        print("Error: JSON file must contain an array of classification records.", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(DB_PATH)
    try:
        updated, invalid, unknown = apply_classifications(con, records, args.dry_run)
    finally:
        con.close()

    label = "[DRY-RUN] " if args.dry_run else ""
    print(f"{label}apply_classifications: {updated} updated, {invalid} invalid, {unknown} unknown job IDs.")


if __name__ == "__main__":
    main()
