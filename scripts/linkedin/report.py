"""Generate a ranked markdown report of scored LinkedIn jobs above threshold.

Queries jobs that: have been scored, are above the threshold, and have not yet
been presented to the user. Marks presented jobs so they don't repeat.

Usage:
    python scripts/linkedin/report.py [--threshold 65] [--limit 20] [--no-mark]

    --threshold N   Minimum score to include (default: from preferences)
    --limit N       Maximum jobs in report (default: 20)
    --no-mark       Don't mark jobs as presented (useful for re-running)
    --output PATH   Override output file path
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # adds scripts/ to path

from linkedin.init_db import DB_PATH
from linkedin.map_preferences import get_score_threshold, load_preferences

OUTPUT_DIR = _ROOT / "output" / "lead_reports"

_TIER_EMOJI = {
    "tier1": "★★★",
    "tier2": "★★☆",
    "tier3": "★☆☆",
}


def _build_metrics_section(cur: sqlite3.Cursor, threshold: int) -> str:
    """Build a pipeline metrics summary to prepend to the report."""
    # Collection counts
    cur.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM job_scores WHERE hard_filtered=1")
    hard_filtered = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM job_scores WHERE score IS NOT NULL AND hard_filtered=0")
    scored = cur.fetchone()[0]

    eligible = total_jobs - hard_filtered

    # Tier breakdown
    cur.execute(
        "SELECT tier, COUNT(*), ROUND(AVG(score),1) FROM job_scores WHERE score IS NOT NULL GROUP BY tier ORDER BY tier"
    )
    tier_rows = cur.fetchall()

    above_threshold = sum(cnt for tier, cnt, avg in tier_rows if tier in ("tier1", "tier2"))
    # More precise: count directly
    cur.execute("SELECT COUNT(*) FROM job_scores WHERE score >= ? AND hard_filtered=0", (threshold,))
    above_threshold = cur.fetchone()[0]

    # Scope breakdown
    cur.execute("SELECT source_scope, COUNT(*) FROM jobs GROUP BY source_scope ORDER BY COUNT(*) DESC")
    scope_rows = cur.fetchall()

    # Top 5 scored jobs
    cur.execute(
        """
        SELECT j.title, j.company_name, j.location, js.score
        FROM jobs j JOIN job_scores js ON j.job_id = js.job_id
        WHERE js.score IS NOT NULL AND js.hard_filtered=0
        ORDER BY js.score DESC LIMIT 5
        """
    )
    top_rows = cur.fetchall()

    lines = [
        "## Pipeline Summary",
        "",
        "| Metric | Count |",
        "| --- | --- |",
        f"| Total collected | {total_jobs} |",
        f"| Hard-filtered | {hard_filtered} |",
        f"| Eligible (passed filter) | {eligible} |",
        f"| LLM-scored | {scored} |",
        f"| Above threshold (≥{threshold}) | {above_threshold} |",
        "",
    ]

    if tier_rows:
        lines += ["**Score tiers:**", "", "| Tier | Count | Avg Score |", "| --- | --- | --- |"]
        for tier, cnt, avg in tier_rows:
            lines.append(f"| {tier} | {cnt} | {avg} |")
        lines.append("")

    if scope_rows:
        lines += ["**Jobs by scope:**", "", "| Scope | Jobs |", "| --- | --- |"]
        for scope, cnt in scope_rows:
            lines.append(f"| {scope or 'unknown'} | {cnt} |")
        lines.append("")

    if top_rows:
        lines += ["**Top 5 roles:**", "", "| # | Title | Company | Location | Score |", "| --- | --- | --- | --- | --- |"]
        for i, (title, company, location, score) in enumerate(top_rows, 1):
            lines.append(f"| {i} | {title or '—'} | {company or '—'} | {location or '—'} | {score} |")
        lines.append("")

    return "\n".join(lines)


def generate_report(
    con: sqlite3.Connection,
    threshold: int,
    limit: int,
    mark_presented: bool,
) -> tuple[str, int]:
    """Generate markdown report. Returns (markdown_content, job_count)."""
    cur = con.cursor()

    cur.execute(
        """
        SELECT j.job_id, j.title, j.company_name, j.location, j.job_url,
               j.posted_time, j.seniority_level, j.employment_type,
               j.industries, j.salary_info, j.source_scope,
               js.score, js.tier, js.skill_match, js.experience_alignment,
               js.domain_fit, js.growth_potential, js.company_quality,
               js.preference_match, js.notes
        FROM jobs j
        JOIN job_scores js ON j.job_id = js.job_id
        WHERE js.score >= ?
          AND js.hard_filtered = 0
          AND js.presented_at IS NULL
        ORDER BY js.score DESC
        LIMIT ?
        """,
        (threshold, limit),
    )
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# LinkedIn Job Scan — {today}",
        f"",
        f"**Score threshold:** {threshold}  |  **Jobs shown:** {len(rows)}",
        f"",
        _build_metrics_section(cur, threshold),
        "---",
        "",
    ]

    if not rows:
        lines.append("_No new scored jobs above threshold._\n")
        return "\n".join(lines) + "\n", 0

    for row in rows:
        job = dict(zip(cols, row))
        tier = job.get("tier") or "tier3"
        tier_stars = _TIER_EMOJI.get(tier, "")
        score = job["score"]
        title = job["title"]
        company = job["company_name"] or "Unknown"
        location = job["location"] or "Unknown"
        url = job["job_url"]

        lines += [
            f"---",
            f"",
            f"## {tier_stars} {title}",
            f"**{company}** · {location}  ",
            f"**Score:** {score}/100 · **Tier:** {tier}  ",
        ]

        if job.get("salary_info"):
            lines.append(f"**Salary:** {job['salary_info']}  ")

        if job.get("seniority_level"):
            lines.append(f"**Seniority:** {job['seniority_level']}  ")

        if job.get("employment_type"):
            lines.append(f"**Type:** {job['employment_type']}  ")

        lines += [
            f"**Posted:** {job['posted_time'] or 'Unknown'}  ",
            f"**URL:** {url}  ",
            f"",
        ]

        # Score breakdown table
        dim_scores = {
            "Skill Match": job.get("skill_match"),
            "Experience Alignment": job.get("experience_alignment"),
            "Domain Fit": job.get("domain_fit"),
            "Growth Potential": job.get("growth_potential"),
            "Company Quality": job.get("company_quality"),
            "Preference Match": job.get("preference_match"),
        }
        has_dims = any(v is not None for v in dim_scores.values())
        if has_dims:
            lines += ["| Dimension | Score |", "| --- | --- |"]
            for dim, val in dim_scores.items():
                if val is not None:
                    lines.append(f"| {dim} | {val} |")
            lines.append("")

        if job.get("notes"):
            lines += [f"**Notes:** {job['notes']}", ""]

    lines += [
        "---",
        "",
        f"_Generated {today} by CareerForge LinkedIn Scanner_",
    ]

    # Mark as presented
    if mark_presented and rows:
        now_iso = datetime.now(timezone.utc).isoformat()
        job_ids = [dict(zip(cols, r))["job_id"] for r in rows]
        cur.executemany(
            "UPDATE job_scores SET presented_at=? WHERE job_id=?",
            [(now_iso, jid) for jid in job_ids],
        )
        con.commit()

    return "\n".join(lines) + "\n", len(rows)


def main() -> None:
    prefs = load_preferences()

    parser = argparse.ArgumentParser(description="Generate ranked LinkedIn job report.")
    parser.add_argument(
        "--threshold", type=int, default=get_score_threshold(prefs),
        help="Minimum score to include.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Max jobs in report.")
    parser.add_argument("--no-mark", action="store_true", help="Don't mark jobs as presented.")
    parser.add_argument("--output", type=str, default=None, help="Override output file path.")
    args = parser.parse_args()

    con = sqlite3.connect(DB_PATH)
    try:
        content, count = generate_report(con, args.threshold, args.limit, not args.no_mark)
    finally:
        con.close()

    # Determine output path
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if args.output:
        out_path = Path(args.output)
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / f"linkedin_scan_{today}.md"

    out_path.write_text(content, encoding="utf-8")
    print(f"Report saved to: {out_path}")
    print(f"Jobs in report: {count}")


if __name__ == "__main__":
    main()
