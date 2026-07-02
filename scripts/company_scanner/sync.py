"""Sync job postings from all enabled companies in config/company_targets.yaml.

Dispatches each company to the right fetcher based on its `fetch_method`:
    api        -> fetch_greenhouse.sync_company (Greenhouse public board API)
    playwright -> fetch_google.sync_company (Phase 2 — not yet implemented)

Usage:
    python scripts/company_scanner/sync.py [--company <name>] [--dry-run]
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # adds scripts/ to path

from company_scanner import fetch_greenhouse
from company_scanner.init_db import DB_PATH, init_db

TARGETS_PATH = _ROOT / "config" / "company_targets.yaml"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_companies(path: Path = TARGETS_PATH) -> list[dict]:
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("companies", [])


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync company career-page jobs into SQLite.")
    parser.add_argument("--company", type=str, default=None, help="Run only this named company.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but do not write to DB.")
    args = parser.parse_args()

    if not args.dry_run:
        init_db()

    companies = load_companies()
    companies = [c for c in companies if c.get("enabled", True)]
    if args.company:
        companies = [c for c in companies if c.get("name") == args.company]
        if not companies:
            logger.error("No enabled company named '%s' found in company_targets.yaml", args.company)
            sys.exit(1)

    logger.info("Running %d compan%s%s", len(companies), "y" if len(companies) == 1 else "ies", " [DRY-RUN]" if args.dry_run else "")

    con = sqlite3.connect(DB_PATH) if not args.dry_run else None

    total_found = total_added = total_updated = 0
    try:
        for company in companies:
            method = company.get("fetch_method")
            if method == "api":
                found, added, updated = fetch_greenhouse.sync_company(con, company, args.dry_run)
            elif method == "playwright":
                logger.error(
                    "Company '%s' uses fetch_method=playwright, which is Phase 2 and not yet "
                    "implemented (scripts/company_scanner/fetch_google.py does not exist). Skipping.",
                    company["name"],
                )
                continue
            else:
                logger.error("Company '%s' has unknown fetch_method=%r. Skipping.", company["name"], method)
                continue
            total_found += found
            total_added += added
            total_updated += updated
    finally:
        if con:
            con.close()

    label = "[DRY-RUN] " if args.dry_run else ""
    print(f"\n{label}Sync complete: {len(companies)} compan{'y' if len(companies) == 1 else 'ies'}, "
          f"{total_found} found, {total_added} added, {total_updated} updated.")


if __name__ == "__main__":
    main()
