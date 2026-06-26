"""
Application pipeline analytics — reads postings/applications.csv and generates
a self-contained HTML dashboard at output/analytics/application_pipeline_YYYY-MM-DD.html
"""

import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "postings" / "applications.csv"
OUTPUT_DIR = ROOT / "output" / "analytics"

STATUS_ORDER = [
    "discovered", "saved", "researching", "applying", "applied",
    "recruiter_screen", "hm_screen", "technical_screen",
    "in_loop", "loop_completed",
    "offer_pending", "offered", "negotiating", "accepted",
    "rejected", "withdrawn", "on_hold", "standby", "ghosted", "closed",
]

TERMINAL_POSITIVE = {"accepted"}
TERMINAL_NEGATIVE = {"rejected", "withdrawn", "ghosted", "closed"}
TERMINAL = TERMINAL_POSITIVE | TERMINAL_NEGATIVE
HOLDING = {"on_hold", "standby"}


def load_events():
    if not CSV_PATH.exists():
        print(f"No applications.csv found at {CSV_PATH}", file=sys.stderr)
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_applications(events):
    """Group events by slug; return dict of slug -> sorted list of events."""
    by_slug = defaultdict(list)
    for e in events:
        by_slug[e["slug"]].append(e)
    for slug in by_slug:
        by_slug[slug].sort(key=lambda e: e["timestamp"])
    return dict(by_slug)


def current_status(event_list):
    return event_list[-1]["status"]


def days_since(ts_str):
    try:
        ts = datetime.fromisoformat(ts_str)
        return (datetime.now() - ts).days
    except Exception:
        return 0


def stage_velocity(apps):
    """Return {status: avg_days} for each stage that has at least one exit."""
    stage_days = defaultdict(list)
    for events in apps.values():
        for i in range(len(events) - 1):
            status = events[i]["status"]
            try:
                t0 = datetime.fromisoformat(events[i]["timestamp"])
                t1 = datetime.fromisoformat(events[i + 1]["timestamp"])
                delta = (t1 - t0).days
                if delta >= 0:
                    stage_days[status].append(delta)
            except Exception:
                pass
    return {s: round(sum(v) / len(v), 1) for s, v in stage_days.items() if v}


def active_pipeline(apps):
    rows = []
    for slug, events in apps.items():
        status = current_status(events)
        if status in TERMINAL:
            continue
        last_event = events[-1]
        rows.append({
            "slug": slug,
            "company": last_event["company"],
            "title": last_event["title"],
            "status": status,
            "days_in_status": days_since(last_event["timestamp"]),
            "note": last_event.get("note", ""),
        })
    rows.sort(key=lambda r: r["days_in_status"], reverse=True)
    return rows


def status_counts(apps):
    counts = defaultdict(int)
    for events in apps.values():
        counts[current_status(events)] += 1
    return dict(counts)


def outcome_summary(apps):
    outcomes = defaultdict(int)
    for events in apps.values():
        s = current_status(events)
        if s in TERMINAL or s in HOLDING:
            outcomes[s] += 1
    return dict(outcomes)


def generate_html(events, apps):
    today = date.today().isoformat()
    active = active_pipeline(apps)
    counts = status_counts(apps)
    velocity = stage_velocity(apps)
    outcomes = outcome_summary(apps)
    total = len(apps)

    # Chart data
    funnel_labels = [s for s in STATUS_ORDER if s in counts]
    funnel_data = [counts.get(s, 0) for s in funnel_labels]
    funnel_colors = []
    for s in funnel_labels:
        if s in TERMINAL_POSITIVE:
            funnel_colors.append("#22c55e")
        elif s in TERMINAL_NEGATIVE:
            funnel_colors.append("#ef4444")
        elif s in HOLDING:
            funnel_colors.append("#f59e0b")
        elif s in {"in_loop", "loop_completed", "offered", "negotiating"}:
            funnel_colors.append("#3b82f6")
        else:
            funnel_colors.append("#94a3b8")

    velocity_rows = "".join(
        f"<tr><td>{s}</td><td>{d}</td></tr>"
        for s, d in sorted(velocity.items(), key=lambda x: STATUS_ORDER.index(x[0]) if x[0] in STATUS_ORDER else 99)
    )

    active_rows = "".join(
        f"""<tr class="{'stale' if r['days_in_status'] > 14 else ''}">
            <td>{r['company']}</td>
            <td>{r['title']}</td>
            <td><span class="badge badge-{r['status']}">{r['status']}</span></td>
            <td>{r['days_in_status']}d</td>
            <td>{r['note']}</td>
        </tr>"""
        for r in active
    ) or "<tr><td colspan='5' style='text-align:center;color:#94a3b8'>No active applications</td></tr>"

    outcome_rows = "".join(
        f"<tr><td>{s}</td><td>{n}</td><td>{round(n/total*100) if total else 0}%</td></tr>"
        for s, n in sorted(outcomes.items(), key=lambda x: x[1], reverse=True)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Application Pipeline — {today}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 24px; }}
  h1 {{ font-size: 1.5rem; font-weight: 700; color: #f1f5f9; margin-bottom: 4px; }}
  .subtitle {{ color: #64748b; font-size: 0.85rem; margin-bottom: 28px; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; margin-bottom: 28px; }}
  .card {{ background: #1e293b; border-radius: 10px; padding: 16px; }}
  .card .label {{ color: #64748b; font-size: 0.75rem; text-transform: uppercase; letter-spacing: .05em; }}
  .card .value {{ font-size: 2rem; font-weight: 700; color: #f1f5f9; margin-top: 4px; }}
  .card.green .value {{ color: #22c55e; }}
  .card.red .value {{ color: #ef4444; }}
  .card.amber .value {{ color: #f59e0b; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 28px; }}
  .panel {{ background: #1e293b; border-radius: 10px; padding: 20px; }}
  .panel h2 {{ font-size: 0.9rem; font-weight: 600; color: #94a3b8; text-transform: uppercase;
               letter-spacing: .05em; margin-bottom: 16px; }}
  .panel-full {{ background: #1e293b; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th {{ color: #64748b; font-weight: 500; text-align: left; padding: 6px 8px;
        border-bottom: 1px solid #334155; }}
  td {{ padding: 8px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }}
  tr.stale td {{ color: #f59e0b; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px;
            font-size: 0.75rem; font-weight: 600; background: #334155; color: #94a3b8; }}
  .badge-in_loop, .badge-loop_completed {{ background: #1d4ed8; color: #93c5fd; }}
  .badge-offered, .badge-negotiating {{ background: #065f46; color: #6ee7b7; }}
  .badge-accepted {{ background: #14532d; color: #22c55e; }}
  .badge-rejected, .badge-ghosted {{ background: #7f1d1d; color: #fca5a5; }}
  .badge-standby, .badge-on_hold {{ background: #78350f; color: #fcd34d; }}
  .badge-recruiter_screen, .badge-hm_screen, .badge-technical_screen {{ background: #312e81; color: #a5b4fc; }}
  @media (max-width: 700px) {{ .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<h1>Application Pipeline</h1>
<p class="subtitle">Generated {today} &nbsp;·&nbsp; {total} total applications &nbsp;·&nbsp; {len(active)} active</p>

<div class="cards">
  <div class="card"><div class="label">Total</div><div class="value">{total}</div></div>
  <div class="card"><div class="label">Active</div><div class="value">{len(active)}</div></div>
  <div class="card green"><div class="label">Accepted</div><div class="value">{outcomes.get('accepted', 0)}</div></div>
  <div class="card red"><div class="label">Rejected</div><div class="value">{outcomes.get('rejected', 0)}</div></div>
  <div class="card amber"><div class="label">Standby</div><div class="value">{outcomes.get('standby', 0)}</div></div>
  <div class="card amber"><div class="label">Ghosted</div><div class="value">{outcomes.get('ghosted', 0)}</div></div>
</div>

<div class="panel-full">
  <h2>Active Pipeline</h2>
  <table>
    <thead><tr><th>Company</th><th>Role</th><th>Status</th><th>Days</th><th>Note</th></tr></thead>
    <tbody>{active_rows}</tbody>
  </table>
  <p style="font-size:0.75rem;color:#64748b;margin-top:8px">Rows in amber = no activity for 14+ days</p>
</div>

<div class="grid">
  <div class="panel">
    <h2>Status Distribution</h2>
    <canvas id="funnelChart" height="220"></canvas>
  </div>
  <div class="panel">
    <h2>Stage Velocity (avg days)</h2>
    <table>
      <thead><tr><th>Stage</th><th>Avg Days</th></tr></thead>
      <tbody>{velocity_rows or '<tr><td colspan="2" style="color:#64748b">Not enough data yet</td></tr>'}</tbody>
    </table>
  </div>
</div>

<div class="panel-full">
  <h2>Terminal Outcomes</h2>
  <table>
    <thead><tr><th>Outcome</th><th>Count</th><th>Rate</th></tr></thead>
    <tbody>{outcome_rows or '<tr><td colspan="3" style="color:#64748b">No terminal outcomes yet</td></tr>'}</tbody>
  </table>
</div>

<script>
new Chart(document.getElementById('funnelChart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(funnel_labels)},
    datasets: [{{
      data: {json.dumps(funnel_data)},
      backgroundColor: {json.dumps(funnel_colors)},
      borderRadius: 4,
    }}]
  }},
  options: {{
    indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }} }},
      y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }}
    }}
  }}
}});
</script>
</body>
</html>
"""


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    events = load_events()
    if not events:
        print("No events to report.")
        return
    apps = build_applications(events)
    html = generate_html(events, apps)
    out = OUTPUT_DIR / f"application_pipeline_{date.today().isoformat()}.html"
    out.write_text(html, encoding="utf-8")
    print(f"Report written to {out}")


if __name__ == "__main__":
    main()
