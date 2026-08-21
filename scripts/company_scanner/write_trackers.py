"""Write each company's review tracker as a deterministic .xlsx file.

This is the only script that touches .xlsx files. It contains no AI calls —
it is a pure rule-based upsert reading already-classified rows from SQLite
(company_jobs joined to company_job_classifications). SQLite remains the
source of truth; the spreadsheet is a generated, re-creatable view.

Tracker columns (in order):
    Job ID | Posting status | Manager role | Title | OTE compensation range |
    Base Salary Range | Equity | Chicago | Location | Date created

Rules:
  - disposition != "qualified" -> never written to the sheet, regardless of
    still_listed. (It remains fully visible/auditable in SQLite.)
  - qualified job_id not yet in the sheet -> insert row, Posting status="New",
    Date created=today. Date created is then immutable.
  - qualified job_id already in the sheet, still listed -> refresh Title /
    Manager role / OTE / Base / Equity / Chicago / Location. Posting status
    and Date created are human-owned and never overwritten here.
  - job_id in the sheet whose job is no longer listed (still_listed=0):
      - status == "Applied"      -> leave the entire row untouched (terminal)
      - status in (New,Reviewed) -> flip status to "Deleted" (Date created
                                     unchanged)
      - status == "Deleted"      -> no-op
  - A job_id present in the sheet that has since lost "qualified" status but
    is still_listed=1 is left untouched (no spec for this edge case; erring
    on the side of not silently rewriting a human-reviewed row).

File-lock handling: writes a ".bak" backup before saving, retries a few
times (the file may be open in Excel), and falls back to a ".new" path with
a loud warning if all retries fail rather than crashing the whole pipeline.

Usage:
    python scripts/company_scanner/write_trackers.py [--company <name>] [--output-dir DIR]
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sqlite3
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # adds scripts/ to path

from company_scanner.init_db import DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output" / "company_trackers"

HEADERS = [
    "Job ID",
    "Posting status",
    "Manager role",
    "Title",
    "OTE compensation range",
    "Base Salary Range",
    "Equity",
    "Chicago",
    "Location",
    "Date created",
    # Appended rather than placed next to "Manager role" so existing tracker
    # files keep their column alignment; _ensure_headers backfills the label.
    "Management scope",
]
COL_JOB_ID = 1
COL_STATUS = 2
COL_MANAGER = 3
COL_TITLE = 4
COL_OTE = 5
COL_BASE = 6
COL_EQUITY = 7
COL_CHICAGO = 8
COL_LOCATION = 9
COL_DATE_CREATED = 10
COL_MGMT_SCOPE = 11


def _yn(value: int | None) -> str:
    if value is None:
        return ""
    return "Yes" if value else "No"


def _comp_range(low: int | None, high: int | None) -> str:
    if low and high:
        return f"${low:,} - ${high:,}"
    if low:
        return f"${low:,}+"
    if high:
        return f"up to ${high:,}"
    return ""


def _ensure_headers(ws) -> None:
    """Backfill header labels for columns added after a tracker was first written.

    Only fills empty header cells, so a header the user renamed is left alone.
    """
    for idx, header in enumerate(HEADERS, start=1):
        if ws.cell(row=1, column=idx).value in (None, ""):
            ws.cell(row=1, column=idx).value = header


def _load_or_create(path: Path) -> tuple[Workbook, Any]:
    if path.exists():
        wb = load_workbook(path)
        ws = wb.active
        _ensure_headers(ws)
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "Tracker"
        ws.append(HEADERS)
    return wb, ws


def _row_index(ws) -> dict[str, int]:
    index: dict[str, int] = {}
    for row_num in range(2, ws.max_row + 1):
        job_id = ws.cell(row=row_num, column=COL_JOB_ID).value
        if job_id:
            index[job_id] = row_num
    return index


def _save_safely(wb: Workbook, path: Path, retries: int = 3, delay: float = 1.0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            if path.exists():
                # Best-effort backup — a lock that blocks this also blocks the
                # save attempt below, so don't let a backup failure abort the
                # whole retry loop; just skip the backup for this attempt.
                try:
                    shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
                except PermissionError:
                    pass
            wb.save(path)
            return path
        except PermissionError as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(delay)

    fallback_path = path.with_suffix(path.suffix + ".new")
    wb.save(fallback_path)
    logger.warning(
        "Could not save %s (file may be open elsewhere): %s. Wrote fallback to %s instead.",
        path, last_err, fallback_path,
    )
    return fallback_path


def write_tracker(con: sqlite3.Connection, company: str, output_dir: Path) -> tuple[int, int, int]:
    """Sync one company's tracker. Returns (added, updated, marked_deleted)."""
    cur = con.cursor()
    cur.execute(
        """
        SELECT j.job_id, j.title, j.location_raw, j.still_listed, j.job_url,
               c.is_manager, c.management_scope, c.chicago_yn, c.ote_low, c.ote_high,
               c.base_low, c.base_high, c.equity_yn, c.disposition
        FROM company_jobs j
        JOIN company_job_classifications c ON j.job_id = c.job_id
        WHERE j.source_company = ?
        """,
        (company,),
    )
    cols = [d[0] for d in cur.description]
    jobs = [dict(zip(cols, row)) for row in cur.fetchall()]

    path = output_dir / f"{company}.xlsx"
    wb, ws = _load_or_create(path)
    row_index = _row_index(ws)

    today = date.today().isoformat()
    added = updated = marked_deleted = 0

    for job in jobs:
        job_id = job["job_id"]
        qualified = job["disposition"] == "qualified"
        existing_row = row_index.get(job_id)

        if existing_row is None:
            if qualified and job["still_listed"]:
                ws.append([
                    job_id,
                    "New",
                    _yn(job["is_manager"]),
                    job["title"],
                    _comp_range(job["ote_low"], job["ote_high"]),
                    _comp_range(job["base_low"], job["base_high"]),
                    _yn(job["equity_yn"]),
                    _yn(job["chicago_yn"]),
                    job["location_raw"],
                    today,
                    job["management_scope"] or "",
                ])
                row_index[job_id] = ws.max_row
                if job.get("job_url"):
                    cell = ws.cell(row=ws.max_row, column=COL_JOB_ID)
                    cell.hyperlink = job["job_url"]
                    cell.font = Font(color="0563C1", underline="single")
                added += 1
            continue

        current_status = ws.cell(row=existing_row, column=COL_STATUS).value

        if not job["still_listed"]:
            if current_status == "Applied":
                continue
            if current_status != "Deleted":
                ws.cell(row=existing_row, column=COL_STATUS).value = "Deleted"
                marked_deleted += 1
            continue

        if qualified:
            ws.cell(row=existing_row, column=COL_MANAGER).value = _yn(job["is_manager"])
            ws.cell(row=existing_row, column=COL_TITLE).value = job["title"]
            ws.cell(row=existing_row, column=COL_OTE).value = _comp_range(job["ote_low"], job["ote_high"])
            ws.cell(row=existing_row, column=COL_BASE).value = _comp_range(job["base_low"], job["base_high"])
            ws.cell(row=existing_row, column=COL_EQUITY).value = _yn(job["equity_yn"])
            ws.cell(row=existing_row, column=COL_CHICAGO).value = _yn(job["chicago_yn"])
            ws.cell(row=existing_row, column=COL_LOCATION).value = job["location_raw"]
            ws.cell(row=existing_row, column=COL_MGMT_SCOPE).value = job["management_scope"] or ""
            if job.get("job_url"):
                cell = ws.cell(row=existing_row, column=COL_JOB_ID)
                cell.hyperlink = job["job_url"]
                cell.font = Font(color="0563C1", underline="single")
            updated += 1
        # else: no longer qualified but still listed -> leave row untouched.

    saved_path = _save_safely(wb, path)
    logger.info(
        "Company '%s': %d added, %d updated, %d marked Deleted -> %s",
        company, added, updated, marked_deleted, saved_path,
    )
    return added, updated, marked_deleted


def main() -> None:
    parser = argparse.ArgumentParser(description="Write deterministic Excel trackers from SQLite.")
    parser.add_argument("--company", type=str, default=None, help="Only write this company's tracker.")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Output directory.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    con = sqlite3.connect(DB_PATH)
    try:
        if args.company:
            companies = [args.company]
        else:
            cur = con.cursor()
            cur.execute("SELECT DISTINCT source_company FROM company_jobs")
            companies = [row[0] for row in cur.fetchall()]

        total_added = total_updated = total_deleted = 0
        for company in companies:
            a, u, d = write_tracker(con, company, output_dir)
            total_added += a
            total_updated += u
            total_deleted += d
    finally:
        con.close()

    print(
        f"\nwrite_trackers complete: {len(companies)} compan{'y' if len(companies) == 1 else 'ies'}, "
        f"{total_added} added, {total_updated} updated, {total_deleted} marked Deleted."
    )


if __name__ == "__main__":
    main()
