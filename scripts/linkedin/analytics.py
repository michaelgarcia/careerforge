"""Generate a static HTML analytics report from the LinkedIn jobs database.

Produces output/analytics/analytics_{date}.html with Chart.js charts
(loaded from CDN — no extra dependencies).

Usage:
    python scripts/linkedin/analytics.py [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from linkedin.init_db import DB_PATH

OUTPUT_DIR = _ROOT / "output" / "analytics"


def _q(cur: sqlite3.Cursor, sql: str, params: tuple = ()) -> list:
    cur.execute(sql, params)
    return cur.fetchall()


def build_report(con: sqlite3.Connection) -> str:
    cur = con.cursor()

    # ── Pipeline overview ──────────────────────────────────────────────────
    total_jobs = _q(cur, "SELECT COUNT(*) FROM jobs")[0][0]
    hard_filtered = _q(cur, "SELECT COUNT(*) FROM job_scores WHERE hard_filtered=1")[0][0]
    eligible = total_jobs - hard_filtered
    scored = _q(cur, "SELECT COUNT(*) FROM job_scores WHERE score IS NOT NULL AND hard_filtered=0")[0][0]

    filter_reasons = _q(
        cur,
        """
        SELECT filter_reason, COUNT(*) as cnt
        FROM job_scores WHERE hard_filtered=1 AND filter_reason IS NOT NULL
        GROUP BY filter_reason ORDER BY cnt DESC LIMIT 10
        """,
    )

    # ── Scope performance ──────────────────────────────────────────────────
    scope_perf = _q(
        cur,
        """
        SELECT j.source_scope,
               COUNT(DISTINCT j.job_id) AS total,
               COUNT(DISTINCT js.job_id) AS scored_count,
               ROUND(AVG(js.score), 1) AS avg_score,
               SUM(CASE WHEN js.tier='tier1' THEN 1 ELSE 0 END) AS t1,
               SUM(CASE WHEN js.tier='tier2' THEN 1 ELSE 0 END) AS t2,
               SUM(CASE WHEN js.tier='tier3' THEN 1 ELSE 0 END) AS t3
        FROM jobs j
        LEFT JOIN job_scores js ON j.job_id = js.job_id AND js.hard_filtered=0
        GROUP BY j.source_scope ORDER BY total DESC
        """,
    )

    # ── Score distribution ─────────────────────────────────────────────────
    buckets = {"0-49": 0, "50-59": 0, "60-69": 0, "70-79": 0, "80-100": 0}
    score_rows = _q(cur, "SELECT score FROM job_scores WHERE score IS NOT NULL AND hard_filtered=0")
    for (s,) in score_rows:
        if s < 50:
            buckets["0-49"] += 1
        elif s < 60:
            buckets["50-59"] += 1
        elif s < 70:
            buckets["60-69"] += 1
        elif s < 80:
            buckets["70-79"] += 1
        else:
            buckets["80-100"] += 1

    tier_counts = _q(
        cur,
        "SELECT tier, COUNT(*) FROM job_scores WHERE score IS NOT NULL GROUP BY tier ORDER BY tier",
    )

    # ── Location breakdown ─────────────────────────────────────────────────
    location_rows = _q(
        cur,
        "SELECT location, COUNT(*) FROM jobs GROUP BY location ORDER BY COUNT(*) DESC LIMIT 15",
    )

    # ── Seniority breakdown ────────────────────────────────────────────────
    seniority_rows = _q(
        cur,
        """
        SELECT COALESCE(seniority_level, 'Unknown'), COUNT(*)
        FROM jobs GROUP BY seniority_level ORDER BY COUNT(*) DESC
        """,
    )

    # ── Threshold sensitivity ──────────────────────────────────────────────
    sensitivity = []
    for t in [60, 65, 70, 75, 80]:
        cnt = _q(cur, "SELECT COUNT(*) FROM job_scores WHERE score >= ? AND hard_filtered=0", (t,))[0][0]
        sensitivity.append((t, cnt))

    # ── Build HTML ─────────────────────────────────────────────────────────
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Scope table with grand totals
    scope_total_collected = sum(r[1] for r in scope_perf)
    scope_total_scored = sum(r[2] or 0 for r in scope_perf)
    scope_total_t1 = sum(r[4] or 0 for r in scope_perf)
    scope_total_t2 = sum(r[5] or 0 for r in scope_perf)
    scope_total_t3 = sum(r[6] or 0 for r in scope_perf)
    scope_scored_avgs = [float(r[3]) for r in scope_perf if r[3] is not None]
    scope_grand_avg = f"{sum(scope_scored_avgs) / len(scope_scored_avgs):.1f}" if scope_scored_avgs else "—"

    scope_table_rows = "".join(
        f"<tr><td>{s or 'unknown'}</td><td>{tot}</td><td>{sc or 0}</td>"
        f"<td>{avg or '—'}</td><td>{t1 or 0}</td><td>{t2 or 0}</td><td>{t3 or 0}</td></tr>"
        for s, tot, sc, avg, t1, t2, t3 in scope_perf
    )
    scope_table_rows += (
        f"<tr class='totals-row'><td><strong>Total</strong></td>"
        f"<td><strong>{scope_total_collected}</strong></td>"
        f"<td><strong>{scope_total_scored}</strong></td>"
        f"<td><strong>{scope_grand_avg}</strong></td>"
        f"<td><strong>{scope_total_t1}</strong></td>"
        f"<td><strong>{scope_total_t2}</strong></td>"
        f"<td><strong>{scope_total_t3}</strong></td></tr>"
    )

    # Filter reasons table with grand total
    filter_total = sum(c for _, c in filter_reasons)
    filter_table_rows = "".join(
        f"<tr><td>{r}</td><td>{c}</td></tr>" for r, c in filter_reasons
    )
    filter_table_rows += (
        f"<tr class='totals-row'><td><strong>Total</strong></td>"
        f"<td><strong>{filter_total}</strong></td></tr>"
    )

    # Location pie chart data (top 8, rest → Other)
    loc_top = location_rows[:8]
    loc_other_count = sum(cnt for _, cnt in location_rows[8:])
    if loc_other_count:
        loc_top = list(loc_top) + [("Other", loc_other_count)]
    loc_labels = json.dumps([loc or "Unknown" for loc, _ in loc_top])
    loc_data = json.dumps([cnt for _, cnt in loc_top])
    _PIE_COLORS = [
        "#0a66c2", "#70b5f9", "#c37d16", "#57a55a", "#e85d4a",
        "#9b59b6", "#1abc9c", "#e67e22", "#bdc3c7",
    ]
    loc_colors = json.dumps(_PIE_COLORS[:len(loc_top)])

    seniority_table_rows = "".join(
        f"<tr><td>{lvl}</td><td>{cnt}</td></tr>"
        for lvl, cnt in seniority_rows
    )

    sensitivity_table_rows = "".join(
        f"<tr><td>≥{t}</td><td>{cnt}</td></tr>" for t, cnt in sensitivity
    )

    # Chart data
    bucket_labels = json.dumps(list(buckets.keys()))
    bucket_data = json.dumps(list(buckets.values()))
    tier_labels = json.dumps([r[0] for r in tier_counts])
    tier_data = json.dumps([r[1] for r in tier_counts])
    scope_names = json.dumps([r[0] or "unknown" for r in scope_perf])
    scope_totals = json.dumps([r[1] for r in scope_perf])
    scope_avgs = json.dumps([float(r[3]) if r[3] else 0 for r in scope_perf])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LinkedIn Analytics — {today}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2/dist/chartjs-plugin-datalabels.min.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 1100px; margin: 0 auto; padding: 2rem; color: #222; }}
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
  .overview-grid {{ display: grid; grid-template-columns: repeat(5,1fr); gap: 1rem; }}
  .tier-legend {{ display: flex; gap: 1.5rem; flex-wrap: wrap; margin: .8rem 0 1.2rem; font-size: .9rem; }}
  .tier-legend span {{ display: flex; align-items: center; gap: .4rem; }}
  .tier-dot {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; }}
</style>
</head>
<body>
<h1>LinkedIn Job Analytics</h1>
<p style="color:#666">Generated {today}</p>

<h2>Pipeline Overview</h2>
<div class="overview-grid">
  <div class="card"><div class="stat">{total_jobs}</div><div class="label">Total collected</div></div>
  <div class="card"><div class="stat">{hard_filtered}</div><div class="label">Hard-filtered</div></div>
  <div class="card"><div class="stat">{eligible}</div><div class="label">Eligible</div></div>
  <div class="card"><div class="stat">{scored}</div><div class="label">LLM-scored</div></div>
  <div class="card"><div class="stat">{sensitivity[3][1]}</div><div class="label">Above threshold (≥75)</div></div>
</div>

<h2>Score Distribution</h2>
<div class="tier-legend">
  <span><span class="tier-dot" style="background:#0a66c2"></span><strong>Tier 1</strong> — score ≥ 75 (strong fit, pursue immediately)</span>
  <span><span class="tier-dot" style="background:#70b5f9"></span><strong>Tier 2</strong> — score 60–74 (good fit, worth considering)</span>
  <span><span class="tier-dot" style="background:#cce4ff"></span><strong>Tier 3</strong> — score 45–59 (borderline, monitor)</span>
  <span><span class="tier-dot" style="background:#e8e8e8; border:1px solid #ccc"></span><strong>Filtered</strong> — score &lt; 45 (not recommended)</span>
</div>
<div class="grid">
  <div><canvas id="scoreHistChart"></canvas></div>
  <div><canvas id="tierChart"></canvas></div>
</div>

<h2>Scope Performance</h2>
<div style="margin-bottom:1rem"><canvas id="scopeChart" style="max-height:220px"></canvas></div>
<table>
  <tr><th>Scope</th><th>Collected jobs</th><th>Scored jobs</th><th>Avg Score</th><th>Tier 1</th><th>Tier 2</th><th>Tier 3</th></tr>
  {scope_table_rows}
</table>

<h2>Hard Filter Reasons</h2>
<table>
  <tr><th>Reason</th><th>Count</th></tr>
  {filter_table_rows}
</table>

<h2>Location Breakdown</h2>
<div style="max-width:520px; margin:0 auto">
  <canvas id="locationPieChart"></canvas>
</div>

<div class="grid" style="margin-top:2rem">
  <div>
    <h2>Seniority Breakdown</h2>
    <table>
      <tr><th>Level</th><th>Jobs</th></tr>
      {seniority_table_rows}
    </table>
  </div>
  <div>
    <h2>Threshold Sensitivity</h2>
    <table>
      <tr><th>Min Score</th><th>Jobs Surfaced</th></tr>
      {sensitivity_table_rows}
    </table>
  </div>
</div>

<script>
Chart.register(ChartDataLabels);
new Chart(document.getElementById('scoreHistChart'), {{
  type: 'bar',
  data: {{ labels: {bucket_labels}, datasets: [{{ label: 'Jobs', data: {bucket_data},
    backgroundColor: ['#e8e8e8','#cce4ff','#cce4ff','#70b5f9','#0a66c2'] }}] }},
  options: {{
    plugins: {{ legend: {{ display: false }}, title: {{ display: true, text: 'Score Distribution' }},
      datalabels: {{ anchor: 'end', align: 'top', color: '#444', font: {{ size: 11 }},
        formatter: v => v > 0 ? v : '' }} }},
    scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }}
  }}
}});
new Chart(document.getElementById('tierChart'), {{
  type: 'doughnut',
  data: {{ labels: {tier_labels}, datasets: [{{ data: {tier_data},
    backgroundColor: ['#0a66c2','#70b5f9','#cce4ff','#e8e8e8'] }}] }},
  options: {{
    plugins: {{
      title: {{ display: true, text: 'Tier Breakdown' }},
      datalabels: {{
        color: '#fff',
        font: {{ weight: 'bold', size: 12 }},
        formatter: (v, ctx) => {{
          const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
          const pct = Math.round(v / total * 100);
          return pct >= 8 ? ctx.chart.data.labels[ctx.dataIndex] + '\\n' + pct + '%' : '';
        }}
      }}
    }}
  }}
}});
new Chart(document.getElementById('scopeChart'), {{
  type: 'bar',
  data: {{
    labels: {scope_names},
    datasets: [
      {{ label: 'Total Jobs', data: {scope_totals}, backgroundColor: '#70b5f9', yAxisID: 'y', order: 2 }},
      {{ label: 'Avg Score', data: {scope_avgs}, type: 'line', borderColor: '#c37d16',
        backgroundColor: 'transparent', borderWidth: 2.5, pointRadius: 5,
        yAxisID: 'y2', order: 1 }}
    ]
  }},
  options: {{
    plugins: {{ title: {{ display: true, text: 'Jobs & Avg Score by Scope' }} }},
    scales: {{
      y: {{
        beginAtZero: true, ticks: {{ precision: 0 }},
        title: {{ display: true, text: 'Total Jobs' }}
      }},
      y2: {{
        position: 'right', beginAtZero: true, max: 100,
        grid: {{ drawOnChartArea: false }},
        title: {{ display: true, text: 'Avg Score (0–100)' }}
      }}
    }}
  }}
}});
new Chart(document.getElementById('locationPieChart'), {{
  type: 'pie',
  data: {{
    labels: {loc_labels},
    datasets: [{{ data: {loc_data}, backgroundColor: {loc_colors} }}]
  }},
  options: {{
    plugins: {{
      title: {{ display: true, text: 'Jobs by Location' }},
      legend: {{ position: 'right' }},
      datalabels: {{
        color: '#fff',
        font: {{ weight: 'bold', size: 12 }},
        formatter: (v, ctx) => {{
          const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
          const pct = Math.round(v / total * 100);
          return pct >= 8 ? ctx.chart.data.labels[ctx.dataIndex] + '\\n(' + v + ')' : '';
        }}
      }}
    }}
  }}
}});
</script>
</body>
</html>
"""
    return html


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HTML analytics report.")
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
        out_path = OUTPUT_DIR / f"analytics_{today}.html"

    out_path.write_text(html, encoding="utf-8")
    print(f"Analytics report saved to: {out_path}")


if __name__ == "__main__":
    main()
