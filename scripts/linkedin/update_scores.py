"""Write LLM scoring results back to the SQLite job_scores table.

Reads a JSON array produced by the job-scanner agent and upserts each record.

Input format:
    [
      {
        "job_id": "1234567890",
        "score": 78,
        "tier": "tier1",
        "skill_match": 80,
        "experience_alignment": 75,
        "domain_fit": 85,
        "growth_potential": 70,
        "company_quality": 80,
        "preference_match": 75,
        "notes": "Strong GenAI focus, remote-friendly, aligns with Principal Architect track."
      },
      ...
    ]

Usage:
    python scripts/linkedin/update_scores.py --input /tmp/scores.json
    python scripts/linkedin/update_scores.py --input /tmp/scores.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # adds scripts/ to path

from linkedin.init_db import DB_PATH

_VALID_TIERS = {"tier1", "tier2", "tier3", "filtered"}
_DIMENSION_FIELDS = [
    "skill_match",
    "experience_alignment",
    "domain_fit",
    "growth_potential",
    "company_quality",
    "preference_match",
]


def validate_record(record: dict) -> str | None:
    """Return an error message if the record is invalid, else None."""
    if not record.get("job_id"):
        return "Missing job_id"
    score = record.get("score")
    if score is None or not isinstance(score, int) or not (0 <= score <= 100):
        return f"Invalid score: {score!r} (must be int 0-100)"
    tier = record.get("tier")
    if tier not in _VALID_TIERS:
        return f"Invalid tier: {tier!r} (must be one of {_VALID_TIERS})"
    return None


def update_scores(con: sqlite3.Connection, records: list[dict], dry_run: bool) -> tuple[int, int, int]:
    """Upsert scoring records. Returns (updated, skipped_invalid, skipped_unknown_job)."""
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

        # Verify job exists
        cur.execute("SELECT 1 FROM jobs WHERE job_id=?", (job_id,))
        if not cur.fetchone():
            print(f"  [SKIP unknown] job_id={job_id} not in DB", file=sys.stderr)
            skipped_unknown += 1
            continue

        if dry_run:
            print(f"  [DRY-RUN] Would update job_id={job_id} score={record['score']} tier={record['tier']}")
            updated += 1
            continue

        cur.execute(
            """
            INSERT INTO job_scores
                (job_id, scored_at, score, tier,
                 skill_match, experience_alignment, domain_fit,
                 growth_potential, company_quality, preference_match, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                scored_at=excluded.scored_at,
                score=excluded.score,
                tier=excluded.tier,
                skill_match=excluded.skill_match,
                experience_alignment=excluded.experience_alignment,
                domain_fit=excluded.domain_fit,
                growth_potential=excluded.growth_potential,
                company_quality=excluded.company_quality,
                preference_match=excluded.preference_match,
                notes=excluded.notes
            """,
            (
                job_id,
                now_iso,
                record["score"],
                record["tier"],
                record.get("skill_match"),
                record.get("experience_alignment"),
                record.get("domain_fit"),
                record.get("growth_potential"),
                record.get("company_quality"),
                record.get("preference_match"),
                record.get("notes"),
            ),
        )
        updated += 1

    if not dry_run:
        con.commit()

    return updated, skipped_invalid, skipped_unknown


def main() -> None:
    parser = argparse.ArgumentParser(description="Write LLM scores back to SQLite.")
    parser.add_argument("--input", required=True, help="Path to JSON scores file.")
    parser.add_argument("--dry-run", action="store_true", help="Validate but do not write.")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        print("Error: JSON file must contain an array of score records.", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(DB_PATH)
    try:
        updated, invalid, unknown = update_scores(con, records, args.dry_run)
    finally:
        con.close()

    label = "[DRY-RUN] " if args.dry_run else ""
    print(f"{label}update_scores: {updated} updated, {invalid} invalid, {unknown} unknown job IDs.")


if __name__ == "__main__":
    main()
