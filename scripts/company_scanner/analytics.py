"""Generate a static HTML audit dashboard from the company-scanner database.

Produces output/analytics/company_scan_{date}.html: a disposition/rejection
breakdown, per-company and location charts, a sync-run history table, and a
sortable/filterable table of every job ever seen (Tabulator.js from CDN — no
extra Python dependencies, same approach as scripts/linkedin/analytics.py).

Usage:
    python scripts/company_scanner/analytics.py [--output PATH]
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

from company_scanner.init_db import DB_PATH

import yaml

PREFS_PATH = _ROOT / "config" / "preferences.yaml"


def _home_city_label() -> str:
    """The home city named in preferences (company_scanner.home_city), or a generic label."""
    try:
        prefs = yaml.safe_load(PREFS_PATH.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return "Home city"
    return str((prefs.get("company_scanner") or {}).get("home_city") or "").strip() or "Home city"

OUTPUT_DIR = _ROOT / "output" / "analytics"

_DISPOSITION_COLORS = {
    "qualified": "#22c55e",
    "rejected_manager_role": "#e85d4a",
    "rejected_location": "#c37d16",
    "rejected_comp_floor": "#9b59b6",
    "rejected_other": "#94a3b8",
}
_PIE_COLORS = [
    "#0a66c2", "#70b5f9", "#c37d16", "#57a55a", "#e85d4a",
    "#9b59b6", "#1abc9c", "#e67e22", "#bdc3c7",
]


def _q(cur: sqlite3.Cursor, sql: str, params: tuple = ()) -> list:
    cur.execute(sql, params)
    return cur.fetchall()


def build_report(con: sqlite3.Connection) -> str:
    cur = con.cursor()

    # ── Overview ────────────────────────────────────────────────────────────
    total_jobs = _q(cur, "SELECT COUNT(*) FROM company_jobs")[0][0]
    still_listed = _q(cur, "SELECT COUNT(*) FROM company_jobs WHERE still_listed=1")[0][0]
    classified = _q(cur, "SELECT COUNT(*) FROM company_job_classifications")[0][0]
    qualified = _q(
        cur, "SELECT COUNT(*) FROM company_job_classifications WHERE disposition='qualified'"
    )[0][0]
    companies_scanned = _q(cur, "SELECT COUNT(DISTINCT source_company) FROM company_jobs")[0][0]
    last_run = _q(cur, "SELECT MAX(run_at) FROM company_scan_runs")[0][0] or "—"

    # ── Disposition breakdown ──────────────────────────────────────────────
    disposition_rows = _q(
        cur,
        "SELECT disposition, COUNT(*) FROM company_job_classifications GROUP BY disposition ORDER BY COUNT(*) DESC",
    )

    # ── Rejection reasons (with a sample note) ─────────────────────────────
    rejection_rows = _q(
        cur,
        """
        SELECT disposition, COUNT(*) as cnt,
               (SELECT notes FROM company_job_classifications c2
                WHERE c2.disposition = c1.disposition AND c2.notes IS NOT NULL LIMIT 1) as sample_note
        FROM company_job_classifications c1
        WHERE disposition != 'qualified'
        GROUP BY disposition ORDER BY cnt DESC
        """,
    )

    # ── Per-company breakdown ──────────────────────────────────────────────
    company_rows = _q(
        cur,
        """
        SELECT j.source_company,
               COUNT(DISTINCT j.job_id) AS total,
               SUM(CASE WHEN j.still_listed=1 THEN 1 ELSE 0 END) AS listed,
               SUM(CASE WHEN c.disposition='qualified' THEN 1 ELSE 0 END) AS qualified,
               SUM(CASE WHEN c.disposition IS NOT NULL AND c.disposition!='qualified' THEN 1 ELSE 0 END) AS rejected
        FROM company_jobs j
        LEFT JOIN company_job_classifications c ON j.job_id = c.job_id
        GROUP BY j.source_company ORDER BY total DESC
        """,
    )

    # ── Location breakdown (top 8 + Other) ─────────────────────────────────
    location_rows = _q(
        cur,
        "SELECT COALESCE(location_raw, 'Unknown'), COUNT(*) FROM company_jobs GROUP BY location_raw ORDER BY COUNT(*) DESC",
    )
    loc_top = location_rows[:8]
    loc_other_count = sum(cnt for _, cnt in location_rows[8:])
    if loc_other_count:
        loc_top = list(loc_top) + [("Other", loc_other_count)]

    # ── Manager vs IC / home city vs remote splits ─────────────────────────
    manager_split = _q(
        cur,
        "SELECT is_manager, COUNT(*) FROM company_job_classifications GROUP BY is_manager",
    )
    manager_counts = {row[0]: row[1] for row in manager_split}
    ic_count = manager_counts.get(0, 0)
    manager_count = manager_counts.get(1, 0)

    chicago_split = _q(
        cur,
        "SELECT chicago_yn, COUNT(*) FROM company_job_classifications WHERE disposition='qualified' GROUP BY chicago_yn",
    )
    home_counts = {row[0]: row[1] for row in chicago_split}  # chicago_yn = legacy column name for "home city"
    home_city_count = home_counts.get(1, 0)
    remote_count = home_counts.get(0, 0)
    home_label = _home_city_label()

    # ── Sync run history (most recent 20) ──────────────────────────────────
    run_rows = _q(
        cur,
        """
        SELECT run_at, company, jobs_found, jobs_added, jobs_updated, jobs_marked_deleted, status
        FROM company_scan_runs ORDER BY run_at DESC LIMIT 20
        """,
    )

    # ── Full records table ──────────────────────────────────────────────────
    record_rows = _q(
        cur,
        """
        SELECT j.job_id, j.source_company, j.title, j.location_raw, j.job_url,
               j.still_listed, j.first_seen_at, j.last_seen_at,
               c.disposition, c.is_manager, c.chicago_yn,
               c.ote_low, c.ote_high, c.base_low, c.base_high, c.equity_yn, c.notes
        FROM company_jobs j
        LEFT JOIN company_job_classifications c ON j.job_id = c.job_id
        ORDER BY j.last_seen_at DESC
        """,
    )
    record_cols = [
        "job_id", "company", "title", "location", "job_url",
        "still_listed", "first_seen_at", "last_seen_at",
        "disposition", "is_manager", "chicago_yn",
        "ote_low", "ote_high", "base_low", "base_high", "equity_yn", "notes",
    ]

    def _comp_range(low, high):
        if low and high:
            return f"${low:,} - ${high:,}"
        if low:
            return f"${low:,}+"
        if high:
            return f"up to ${high:,}"
        return ""

    def _yn(v):
        if v is None:
            return ""
        return "Yes" if v else "No"

    records = []
    for row in record_rows:
        r = dict(zip(record_cols, row))
        records.append({
            "job_id": r["job_id"],
            "company": r["company"],
            "title": r["title"],
            "location": r["location"] or "",
            "job_url": r["job_url"] or "",
            "still_listed": "Listed" if r["still_listed"] else "Delisted",
            "first_seen_at": (r["first_seen_at"] or "")[:10],
            "last_seen_at": (r["last_seen_at"] or "")[:10],
            "disposition": r["disposition"] or "unclassified",
            "manager": _yn(r["is_manager"]),
            "chicago": _yn(r["chicago_yn"]),
            "ote": _comp_range(r["ote_low"], r["ote_high"]),
            "base": _comp_range(r["base_low"], r["base_high"]),
            "equity": _yn(r["equity_yn"]),
            "notes": r["notes"] or "",
        })

    # ── Build HTML ───────────────────────────────────────────────────────────
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    disposition_table_rows = "".join(
        f"<tr><td>{d}</td><td>{c}</td></tr>" for d, c in disposition_rows
    )

    rejection_total = sum(c for _, c, _ in rejection_rows)
    rejection_table_rows = "".join(
        f"<tr><td>{d}</td><td>{c}</td><td>{(n or '')[:120]}</td></tr>"
        for d, c, n in rejection_rows
    )
    rejection_table_rows += (
        f"<tr class='totals-row'><td><strong>Total</strong></td>"
        f"<td><strong>{rejection_total}</strong></td><td></td></tr>"
    )

    company_table_rows = "".join(
        f"<tr><td>{co}</td><td>{tot}</td><td>{listed or 0}</td><td>{q or 0}</td><td>{rej or 0}</td></tr>"
        for co, tot, listed, q, rej in company_rows
    )

    run_table_rows = "".join(
        f"<tr><td>{(ra or '')[:19]}</td><td>{co}</td><td>{jf}</td><td>{ja}</td><td>{ju}</td><td>{jd}</td><td>{st}</td></tr>"
        for ra, co, jf, ja, ju, jd, st in run_rows
    ) or "<tr><td colspan='7' style='text-align:center;color:#94a3b8'>No runs recorded</td></tr>"

    disposition_labels = json.dumps([d for d, _ in disposition_rows])
    disposition_data = json.dumps([c for _, c in disposition_rows])
    disposition_colors = json.dumps(
        [_DISPOSITION_COLORS.get(d, "#94a3b8") for d, _ in disposition_rows]
    )

    company_names = json.dumps([co or "unknown" for co, *_ in company_rows])
    company_qualified = json.dumps([q or 0 for *_, q, _ in company_rows])
    company_rejected = json.dumps([rej or 0 for *_, rej in company_rows])

    loc_labels = json.dumps([loc for loc, _ in loc_top])
    loc_data = json.dumps([cnt for _, cnt in loc_top])
    loc_colors = json.dumps(_PIE_COLORS[: len(loc_top)])

    records_json = json.dumps(records)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Company Scan Analytics — {today}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2/dist/chartjs-plugin-datalabels.min.js"></script>
<link href="https://cdn.jsdelivr.net/npm/tabulator-tables@6/dist/css/tabulator.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/tabulator-tables@6/dist/js/tabulator.min.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 2rem; color: #222; }}
  h1 {{ color: #0a66c2; }}
  h2 {{ color: #444; border-bottom: 1px solid #ddd; padding-bottom: .4rem; margin-top: 2.5rem; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  .card {{ background: #f8f9fa; border-radius: 8px; padding: 1.2rem; }}
  .stat {{ font-size: 2rem; font-weight: 700; color: #0a66c2; }}
  .label {{ font-size: .85rem; color: #666; }}
  canvas {{ max-height: 280px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }}
  th {{ background: #0a66c2; color: #fff; padding: .5rem .8rem; text-align: left; }}
  td {{ padding: .45rem .8rem; border-bottom: 1px solid #eee; }}
  tr:nth-child(even) td {{ background: #f4f6f8; }}
  .totals-row td {{ background: #e8f0fb !important; border-top: 2px solid #0a66c2; }}
  .overview-grid {{ display: grid; grid-template-columns: repeat(6,1fr); gap: 1rem; }}
  #recordsTable {{ margin-top: 1rem; }}
  .tabulator {{ font-size: .85rem; }}
</style>
</head>
<body>
<h1>Company Scan Analytics</h1>
<p style="color:#666">Generated {today} &middot; Last scan run: {last_run}</p>

<h2>Pipeline Overview</h2>
<div class="overview-grid">
  <div class="card"><div class="stat">{total_jobs}</div><div class="label">Total jobs tracked</div></div>
  <div class="card"><div class="stat">{still_listed}</div><div class="label">Still listed</div></div>
  <div class="card"><div class="stat">{classified}</div><div class="label">Classified</div></div>
  <div class="card"><div class="stat">{qualified}</div><div class="label">Qualified</div></div>
  <div class="card"><div class="stat">{companies_scanned}</div><div class="label">Companies scanned</div></div>
  <div class="card"><div class="stat">{manager_count}</div><div class="label">Manager roles (IC: {ic_count})</div></div>
</div>

<h2>Disposition Breakdown</h2>
<div class="grid">
  <div><canvas id="dispositionChart"></canvas></div>
  <div>
    <table>
      <tr><th>Disposition</th><th>Count</th></tr>
      {disposition_table_rows}
    </table>
  </div>
</div>

<h2>Rejection Reasons</h2>
<table>
  <tr><th>Reason</th><th>Count</th><th>Sample note</th></tr>
  {rejection_table_rows}
</table>

<h2>Per-Company Breakdown</h2>
<div style="margin-bottom:1rem"><canvas id="companyChart" style="max-height:220px"></canvas></div>
<table>
  <tr><th>Company</th><th>Total jobs</th><th>Still listed</th><th>Qualified</th><th>Rejected</th></tr>
  {company_table_rows}
</table>

<h2>Location Breakdown</h2>
<div style="max-width:520px; margin:0 auto">
  <canvas id="locationPieChart"></canvas>
</div>

<h2>Location Scope (qualified jobs)</h2>
<div class="overview-grid" style="grid-template-columns: repeat(2,1fr); max-width: 400px;">
  <div class="card"><div class="stat">{home_city_count}</div><div class="label">{home_label}</div></div>
  <div class="card"><div class="stat">{remote_count}</div><div class="label">Remote</div></div>
</div>

<h2>Recent Scan Runs</h2>
<table>
  <tr><th>Run at</th><th>Company</th><th>Found</th><th>Added</th><th>Updated</th><th>Deleted</th><th>Status</th></tr>
  {run_table_rows}
</table>

<h2>All Records</h2>
<p style="color:#666; font-size:.85rem">Click a column header to sort. Use the filter boxes in the header row to narrow results.</p>
<div id="recordsTable"></div>

<script>
Chart.register(ChartDataLabels);
new Chart(document.getElementById('dispositionChart'), {{
  type: 'doughnut',
  data: {{ labels: {disposition_labels}, datasets: [{{ data: {disposition_data}, backgroundColor: {disposition_colors} }}] }},
  options: {{
    plugins: {{
      title: {{ display: true, text: 'Disposition Breakdown' }},
      datalabels: {{
        color: '#fff', font: {{ weight: 'bold', size: 12 }},
        formatter: (v, ctx) => {{
          const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
          const pct = total ? Math.round(v / total * 100) : 0;
          return pct >= 6 ? ctx.chart.data.labels[ctx.dataIndex] + '\\n' + pct + '%' : '';
        }}
      }}
    }}
  }}
}});
new Chart(document.getElementById('companyChart'), {{
  type: 'bar',
  data: {{
    labels: {company_names},
    datasets: [
      {{ label: 'Qualified', data: {company_qualified}, backgroundColor: '#22c55e', stack: 'a' }},
      {{ label: 'Rejected', data: {company_rejected}, backgroundColor: '#e85d4a', stack: 'a' }}
    ]
  }},
  options: {{
    plugins: {{ title: {{ display: true, text: 'Qualified vs. Rejected by Company' }} }},
    scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }}
  }}
}});
new Chart(document.getElementById('locationPieChart'), {{
  type: 'pie',
  data: {{ labels: {loc_labels}, datasets: [{{ data: {loc_data}, backgroundColor: {loc_colors} }}] }},
  options: {{
    plugins: {{
      title: {{ display: true, text: 'Jobs by Location' }},
      legend: {{ position: 'right' }},
      datalabels: {{
        color: '#fff', font: {{ weight: 'bold', size: 12 }},
        formatter: (v, ctx) => {{
          const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
          const pct = total ? Math.round(v / total * 100) : 0;
          return pct >= 8 ? ctx.chart.data.labels[ctx.dataIndex] + '\\n(' + v + ')' : '';
        }}
      }}
    }}
  }}
}});

const recordsData = {records_json};
new Tabulator("#recordsTable", {{
  data: recordsData,
  layout: "fitDataFill",
  pagination: true,
  paginationSize: 25,
  paginationSizeSelector: [25, 50, 100, true],
  columns: [
    {{ title: "Job ID", field: "job_id", headerFilter: "input", formatter: "link",
       formatterParams: {{ url: (cell) => cell.getData().job_url, target: "_blank", label: (cell) => cell.getValue() }} }},
    {{ title: "Company", field: "company", headerFilter: "input", width: 110 }},
    {{ title: "Title", field: "title", headerFilter: "input", width: 220 }},
    {{ title: "Location", field: "location", headerFilter: "input", width: 150 }},
    {{ title: "Disposition", field: "disposition", headerFilter: "input", width: 160 }},
    {{ title: "Manager", field: "manager", headerFilter: "input", width: 90 }},
    {{ title: "Home city", field: "chicago", headerFilter: "input", width: 90 }},
    {{ title: "OTE", field: "ote", headerFilter: "input", width: 140 }},
    {{ title: "Base", field: "base", headerFilter: "input", width: 140 }},
    {{ title: "Equity", field: "equity", headerFilter: "input", width: 80 }},
    {{ title: "Status", field: "still_listed", headerFilter: "input", width: 90 }},
    {{ title: "First Seen", field: "first_seen_at", headerFilter: "input", width: 110 }},
    {{ title: "Last Seen", field: "last_seen_at", headerFilter: "input", width: 110 }},
    {{ title: "Notes", field: "notes", headerFilter: "input", width: 260 }},
  ],
}});
</script>
</body>
</html>
"""
    return html


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HTML analytics report for the company scanner.")
    parser.add_argument("--output", type=str, default=None, help="Override output file path.")
    args = parser.parse_args()

    con = sqlite3.connect(DB_PATH)
    try:
        html = build_report(con)
    finally:
        con.close()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if args.output:
        out_path = Path(args.output)
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / f"company_scan_{today}.html"

    out_path.write_text(html, encoding="utf-8")
    print(f"Company scan analytics report saved to: {out_path}")


if __name__ == "__main__":
    main()
