"""CLI entry point for linkedin-job-search."""

from __future__ import annotations

import argparse
import logging
import sys

from .models import DatePosted, ExperienceLevel, JobType, WorkModel


def enum_type(enum_class):
    """Factory that returns an argparse type function for the given Enum class.

    Validates the input against Enum members (case-insensitive, hyphens → underscores)
    and raises ArgumentTypeError listing all valid values on failure.
    """

    def _type(value: str):
        try:
            return enum_class[value.upper().replace("-", "_")]
        except KeyError:
            valid = [e.name.lower().replace("_", "-") for e in enum_class]
            raise argparse.ArgumentTypeError(
                f"Invalid value {value!r}. Valid values: {', '.join(valid)}"
            )

    _type.__name__ = enum_class.__name__
    return _type


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="linkedin-jobs",
        description="Search LinkedIn jobs via the public Guest API.",
    )

    subparsers = parser.add_subparsers(dest="command")

    # ── search ────────────────────────────────────────────────────────────────
    search_parser = subparsers.add_parser(
        "search",
        help="Search for jobs and optionally enrich results.",
    )
    search_parser.add_argument("--keywords", type=str, default=None, help="Search keywords.")
    search_parser.add_argument("--location", type=str, default=None, help="Location string.")
    search_parser.add_argument("--geo-id", type=str, default=None, dest="geo_id", help="LinkedIn geoId.")
    search_parser.add_argument(
        "--experience-level",
        type=enum_type(ExperienceLevel),
        dest="experience_level",
        default=None,
        nargs="+",
        metavar="LEVEL",
        help=(
            "Experience level filter (repeatable). Valid values: "
            + ", ".join(e.name.lower().replace("_", "-") for e in ExperienceLevel)
        ),
    )
    search_parser.add_argument(
        "--job-type",
        type=enum_type(JobType),
        dest="job_type",
        default=None,
        metavar="TYPE",
        help=(
            "Job type filter. Valid values: "
            + ", ".join(e.name.lower().replace("_", "-") for e in JobType)
        ),
    )
    search_parser.add_argument(
        "--work-model",
        type=enum_type(WorkModel),
        dest="work_model",
        default=None,
        metavar="MODEL",
        help=(
            "Work model filter. Valid values: "
            + ", ".join(e.name.lower().replace("_", "-") for e in WorkModel)
        ),
    )
    search_parser.add_argument(
        "--date-posted",
        type=enum_type(DatePosted),
        dest="date_posted",
        default=None,
        metavar="PERIOD",
        help=(
            "Date posted filter. Valid values: "
            + ", ".join(e.name.lower().replace("_", "-") for e in DatePosted)
        ),
    )
    search_parser.add_argument(
        "--easy-apply",
        action="store_true",
        default=False,
        dest="easy_apply",
        help="Filter for Easy Apply jobs only.",
    )
    search_parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum number of jobs to collect (default: 25).",
    )
    search_parser.add_argument(
        "--output",
        type=str,
        default="jobs.jsonl",
        help="Output JSONL file path (default: jobs.jsonl).",
    )
    enrich_group = search_parser.add_mutually_exclusive_group()
    enrich_group.add_argument(
        "--enrich",
        action="store_true",
        default=True,
        dest="enrich",
        help="Enrich results with full job details (default: on).",
    )
    enrich_group.add_argument(
        "--no-enrich",
        action="store_false",
        dest="enrich",
        help="Skip enrichment and store only search result fields.",
    )

    # ── enrich ────────────────────────────────────────────────────────────────
    enrich_parser = subparsers.add_parser(
        "enrich",
        help="Enrich previously collected jobs from a JSONL file.",
    )
    enrich_parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input JSONL file.",
    )
    enrich_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of jobs to enrich.",
    )

    # ── export ────────────────────────────────────────────────────────────────
    export_parser = subparsers.add_parser(
        "export",
        help="Export a JSONL file to CSV.",
    )
    export_parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input JSONL file.",
    )
    export_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of records to export.",
    )

    # ── geo ───────────────────────────────────────────────────────────────────
    geo_parser = subparsers.add_parser(
        "geo",
        help="Resolve a location name to LinkedIn geoIds.",
    )
    geo_parser.add_argument(
        "query",
        type=str,
        help="Location query string (e.g. 'San Francisco').",
    )

    # ── fetch-alerts ──────────────────────────────────────────────────────────
    fetch_parser = subparsers.add_parser(
        "fetch-alerts",
        help="Poll IMAP mailbox for LinkedIn job alert emails and store results.",
    )
    fetch_parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config.ini file (default: config.ini in project root).",
    )
    fetch_parser.add_argument(
        "--output",
        type=str,
        default="jobs.jsonl",
        help="Output JSONL file path (default: jobs.jsonl).",
    )
    fetch_enrich_group = fetch_parser.add_mutually_exclusive_group()
    fetch_enrich_group.add_argument(
        "--enrich",
        action="store_true",
        default=True,
        dest="enrich",
        help="Enrich results with full job details (default: on).",
    )
    fetch_enrich_group.add_argument(
        "--no-enrich",
        action="store_false",
        dest="enrich",
        help="Skip enrichment and store only search result fields.",
    )
    fetch_parser.add_argument(
        "--no-mark-read",
        action="store_true",
        default=False,
        dest="no_mark_read",
        help="Do not mark processed emails as read (useful for testing).",
    )

    # ── parse-eml ─────────────────────────────────────────────────────────────
    parse_eml_parser = subparsers.add_parser(
        "parse-eml",
        help="Parse a local .eml file and store results (no IMAP needed).",
    )
    parse_eml_parser.add_argument(
        "eml_path",
        type=str,
        help="Path to the .eml file to parse.",
    )
    parse_eml_parser.add_argument(
        "--output",
        type=str,
        default="jobs.jsonl",
        help="Output JSONL file path (default: jobs.jsonl).",
    )
    parse_eml_enrich_group = parse_eml_parser.add_mutually_exclusive_group()
    parse_eml_enrich_group.add_argument(
        "--enrich",
        action="store_true",
        default=False,
        dest="enrich",
        help="Enrich results with full job details.",
    )
    parse_eml_enrich_group.add_argument(
        "--no-enrich",
        action="store_false",
        dest="enrich",
        help="Skip enrichment (default for parse-eml).",
    )

    return parser


def cmd_search(args: argparse.Namespace) -> None:
    """Handle the `search` subcommand."""
    from .client import LinkedInJobSearch
    from .storage import JSONLStore

    client = LinkedInJobSearch()
    results = client.search(
        keywords=args.keywords,
        location=args.location,
        geo_id=args.geo_id,
        experience_level=args.experience_level,
        job_type=args.job_type,
        work_model=args.work_model,
        date_posted=args.date_posted,
        easy_apply=args.easy_apply,
        enrich=args.enrich,
        limit=args.limit,
    )

    store = JSONLStore(args.output)
    added, skipped = store.append(results)
    print(f"Collected {added} new jobs, {skipped} skipped (duplicates).")


def cmd_enrich(args: argparse.Namespace) -> None:
    """Handle the `enrich` subcommand."""
    from .client import LinkedInJobSearch
    from .storage import JSONLStore

    store = JSONLStore(args.input)
    unenriched = store.read_unenriched()

    if not unenriched:
        print("No unenriched records found.")
        return

    client = LinkedInJobSearch()
    enriched = client.enrich_jobs(unenriched, limit=args.limit)
    store.replace_records(enriched)
    print(f"Enriched {len(enriched)} jobs.")


def cmd_export(args: argparse.Namespace) -> None:
    """Handle the `export` subcommand."""
    from .storage import JSONLStore

    store = JSONLStore(args.input)
    csv_path = store.export_csv(limit=args.limit)
    print(f"Exported to {csv_path}")


def cmd_geo(args: argparse.Namespace) -> None:
    """Handle the `geo` subcommand."""
    from .client import LinkedInJobSearch

    client = LinkedInJobSearch()
    locations = client.resolve_geo_id(args.query)

    if not locations:
        print("No matching locations found.")
        return

    for loc in locations:
        print(f"{loc.geo_id}\t{loc.display_name}")


def cmd_fetch_alerts(args: argparse.Namespace) -> None:
    """Handle the `fetch-alerts` subcommand."""
    from .client import LinkedInJobSearch
    from .config import load_email_config
    from .email_source import IMAPSource
    from .storage import JSONLStore

    config = load_email_config(args.config)

    with IMAPSource(config) as source:
        jobs = source.fetch_new_jobs(mark_read=not args.no_mark_read)

    if not jobs:
        print("No new jobs found in alert emails.")
        return

    store = JSONLStore(args.output)

    if args.enrich:
        client = LinkedInJobSearch()
        enriched = client.enrich_jobs(jobs)
        added, skipped = store.append(enriched)
    else:
        added, skipped = store.append(jobs)

    print(f"Collected {added} new jobs from email alerts, {skipped} skipped (duplicates).")


def cmd_parse_eml(args: argparse.Namespace) -> None:
    """Handle the `parse-eml` subcommand."""
    from .client import LinkedInJobSearch
    from .email_parser import parse_eml_file
    from .storage import JSONLStore

    jobs = parse_eml_file(args.eml_path)

    if not jobs:
        print("No jobs found in the .eml file.")
        return

    print(f"Parsed {len(jobs)} job(s) from {args.eml_path}")

    store = JSONLStore(args.output)

    if args.enrich:
        client = LinkedInJobSearch()
        enriched = client.enrich_jobs(jobs)
        added, skipped = store.append(enriched)
    else:
        added, skipped = store.append(jobs)

    print(f"Stored {added} new jobs, {skipped} skipped (duplicates).")


def _configure_logging() -> None:
    """Set up basic INFO logging to stdout for CLI usage."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )


def main() -> None:
    """CLI entry point."""
    _configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    # Default to `search` when no subcommand is given
    if args.command is None:
        args = parser.parse_args(["search"] + sys.argv[1:])

    dispatch = {
        "search": cmd_search,
        "enrich": cmd_enrich,
        "export": cmd_export,
        "geo": cmd_geo,
        "fetch-alerts": cmd_fetch_alerts,
        "parse-eml": cmd_parse_eml,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
