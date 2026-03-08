"""JSONL storage with O(1) deduplication via companion .seen_ids file."""

import csv
import json
import logging
from pathlib import Path

from linkedin_job_search.models import EnrichedJob, SearchResult

logger = logging.getLogger(__name__)


class JSONLStore:
    """Append-only JSONL storage with dedup via in-memory set backed by .seen_ids file."""

    def __init__(self, filepath: str | Path) -> None:
        self._filepath = Path(filepath)
        self._seen_ids_path = self._filepath.with_suffix(".seen_ids")

        # Create files if they don't exist
        self._filepath.touch(exist_ok=True)
        self._seen_ids_path.touch(exist_ok=True)

        # Load seen IDs into memory for O(1) lookup
        self._seen_ids: set[str] = self._load_seen_ids()

    def _load_seen_ids(self) -> set[str]:
        """Load job IDs from the .seen_ids file into a set."""
        ids: set[str] = set()
        text = self._seen_ids_path.read_text()
        for line in text.splitlines():
            stripped = line.strip()
            if stripped:
                ids.add(stripped)
        return ids

    def _append_seen_id(self, job_id: str) -> None:
        """Append a single job ID to the .seen_ids file."""
        with open(self._seen_ids_path, "a") as f:
            f.write(job_id + "\n")

    def append(self, records: list[SearchResult | EnrichedJob]) -> tuple[int, int]:
        """Append records, skipping duplicates. Returns (added_count, skipped_count)."""
        added = 0
        skipped = 0

        with open(self._filepath, "a") as jsonl_f, open(self._seen_ids_path, "a") as ids_f:
            for record in records:
                if record.job_id in self._seen_ids:
                    skipped += 1
                    continue

                jsonl_f.write(record.model_dump_json() + "\n")
                ids_f.write(record.job_id + "\n")
                self._seen_ids.add(record.job_id)
                added += 1

        return added, skipped

    def read_all(self) -> list[dict]:
        """Read all records from the JSONL file as dicts."""
        records: list[dict] = []
        text = self._filepath.read_text()
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError:
                logger.warning("Skipping malformed JSONL line: %s", stripped[:80])
        return records

    def read_unenriched(self) -> list[SearchResult]:
        """Read records where enriched_at is None, returning them as SearchResult."""
        unenriched: list[SearchResult] = []
        text = self._filepath.read_text()
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError:
                logger.warning("Skipping malformed JSONL line: %s", stripped[:80])
                continue
            if data.get("enriched_at") is None:
                unenriched.append(SearchResult.model_validate(data))
        return unenriched

    def replace_records(self, records: list[EnrichedJob]) -> None:
        """Rewrite JSONL, replacing records matching by job_id with enriched versions.

        Non-matching records are kept unchanged. Total record count stays the same.
        """
        # Build lookup of replacements by job_id
        replacements: dict[str, EnrichedJob] = {r.job_id: r for r in records}

        # Read existing lines
        existing_lines = self._filepath.read_text().splitlines()

        new_lines: list[str] = []
        for line in existing_lines:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError:
                logger.warning("Skipping malformed JSONL line: %s", stripped[:80])
                new_lines.append(stripped)
                continue

            job_id = data.get("job_id")
            if job_id in replacements:
                new_lines.append(replacements[job_id].model_dump_json())
            else:
                new_lines.append(stripped)

        # Rewrite the file
        self._filepath.write_text("\n".join(new_lines) + "\n" if new_lines else "")


    def export_csv(self, limit: int | None = None) -> Path:
        """Export JSONL records to a CSV file with model field names as headers.

        Args:
            limit: Maximum number of records to export. None means export all.

        Returns:
            Path to the created CSV file.

        Raises:
            FileNotFoundError: If the JSONL file does not exist.
        """
        if not self._filepath.exists():
            raise FileNotFoundError(f"JSONL file not found: {self._filepath}")

        records = self.read_all()
        if limit is not None:
            records = records[:limit]

        csv_path = self._filepath.with_suffix(".csv")

        # Use EnrichedJob field names as headers (superset of SearchResult)
        fieldnames = list(EnrichedJob.model_fields.keys())

        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for record in records:
                writer.writerow(record)

        return csv_path

