"""
SmartTraffic Vision - Dashboard Module (Flask)

Serves a web dashboard to view:
  - Summary violation statistics
  - Violation log with filters
  - Evidence images / video paths
  - Vehicle IDs and timestamps

Run:
    python dashboard.py
Then open: http://127.0.0.1:5000
"""

from flask import Flask, render_template_string, request, jsonify
from database import create_tables, query_violations, get_summary_stats, get_cameras

app = Flask(__name__)

# ------------------------------------------------------------------
# HTML template (inline for portability — no separate templates dir)
# ------------------------------------------------------------------
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>SmartTraffic Vision — Dashboard</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Segoe UI', sans-serif;
      background: #0d0f14;
      color: #e2e6f0;
      min-height: 100vh;
    }

    /* ---------- Top nav ---------- */
    header {
      background: #161a24;
      border-bottom: 1px solid #2a2e3d;
      padding: 0 2rem;
      height: 56px;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    header .logo {
      font-size: 16px;
      font-weight: 700;
      color: #4f8ef7;
      letter-spacing: 0.5px;
    }
    header .tagline { font-size: 12px; color: #6b7280; }

    /* ---------- Layout ---------- */
    .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }

    /* ---------- Stat cards ---------- */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 2rem;
    }
    .stat-card {
      background: #161a24;
      border: 1px solid #2a2e3d;
      border-radius: 10px;
      padding: 1.2rem 1.4rem;
    }
    .stat-card .label { font-size: 12px; color: #6b7280; margin-bottom: 6px; }
    .stat-card .value { font-size: 28px; font-weight: 700; color: #4f8ef7; }
    .stat-card .value.red   { color: #f7694f; }
    .stat-card .value.green { color: #34c78a; }
    .stat-card .value.amber { color: #f4b942; }

    /* ---------- Table section ---------- */
    .section-title {
      font-size: 14px;
      font-weight: 600;
      color: #9ca3af;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 12px;
    }

    .filter-bar {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }
    .filter-bar select,
    .filter-bar input {
      background: #161a24;
      border: 1px solid #2a2e3d;
      border-radius: 6px;
      color: #e2e6f0;
      padding: 6px 10px;
      font-size: 13px;
    }
    .filter-bar button {
      background: #4f8ef7;
      color: #fff;
      border: none;
      border-radius: 6px;
      padding: 6px 16px;
      font-size: 13px;
      cursor: pointer;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    thead th {
      background: #1e2230;
      color: #9ca3af;
      text-align: left;
      padding: 10px 14px;
      font-weight: 500;
      border-bottom: 1px solid #2a2e3d;
    }
    tbody tr { border-bottom: 1px solid #1e2230; }
    tbody tr:hover { background: #1c2030; }
    tbody td { padding: 10px 14px; color: #d1d5db; }

    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
    }
    .badge-signal  { background: #7c3aed22; color: #a78bfa; border: 1px solid #7c3aed55; }
    .badge-wrong   { background: #dc262622; color: #f87171; border: 1px solid #dc262655; }

    .evidence-link {
      color: #4f8ef7;
      text-decoration: none;
      font-size: 12px;
    }
    .evidence-link:hover { text-decoration: underline; }

    .no-data {
      text-align: center;
      color: #6b7280;
      padding: 3rem;
      font-size: 14px;
    }
  </style>
</head>
<body>

<header>
  <div class="logo">SmartTraffic Vision</div>
  <div class="tagline">AI-Powered Traffic Violation Detection</div>
</header>

<div class="container">

  <!-- Summary stats -->
  <div class="stats-grid" id="stats-grid">
    <div class="stat-card">
      <div class="label">Total Violations</div>
      <div class="value" id="stat-total">—</div>
    </div>
    <div class="stat-card">
      <div class="label">Signal Jumping</div>
      <div class="value amber" id="stat-signal">—</div>
    </div>
    <div class="stat-card">
      <div class="label">Wrong-Way Driving</div>
      <div class="value red" id="stat-wrong">—</div>
    </div>
    <div class="stat-card">
      <div class="label">Active Cameras</div>
      <div class="value green" id="stat-cameras">—</div>
    </div>
  </div>

  <!-- Violations table -->
  <div class="section-title">Violation Log</div>

  <div class="filter-bar">
    <select id="filter-type">
      <option value="">All Types</option>
      <option value="signal_jumping">Signal Jumping</option>
      <option value="wrong_way_driving">Wrong-Way Driving</option>
    </select>
    <input type="date" id="filter-start" placeholder="Start date" />
    <input type="date" id="filter-end"   placeholder="End date" />
    <button onclick="loadViolations()">Apply</button>
  </div>

  <table id="violations-table">
    <thead>
      <tr>
        <th>#</th>
        <th>Timestamp</th>
        <th>Violation Type</th>
        <th>Vehicle ID</th>
        <th>Camera ID</th>
        <th>Location</th>
        <th>Evidence</th>
      </tr>
    </thead>
    <tbody id="violations-body">
      <tr><td colspan="7" class="no-data">Loading...</td></tr>
    </tbody>
  </table>

</div>

<script>
  async function loadStats() {
    const res  = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('stat-total').textContent   = data.total_violations;
    document.getElementById('stat-signal').textContent  = data.signal_jumping;
    document.getElementById('stat-wrong').textContent   = data.wrong_way_driving;
    document.getElementById('stat-cameras').textContent = data.active_cameras;
  }

  async function loadViolations() {
    const type  = document.getElementById('filter-type').value;
    const start = document.getElementById('filter-start').value;
    const end   = document.getElementById('filter-end').value;

    let url = `/api/violations?limit=100`;
    if (type)  url += `&type=${type}`;
    if (start) url += `&start=${start}`;
    if (end)   url += `&end=${end}`;

    const res  = await fetch(url);
    const rows = await res.json();
    const tbody = document.getElementById('violations-body');

    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="no-data">No violations found.</td></tr>';
      return;
    }

    tbody.innerHTML = rows.map(r => {
      const badgeClass = r.violation_type === 'signal_jumping' ? 'badge-signal' : 'badge-wrong';
      const typeLabel  = r.violation_type === 'signal_jumping' ? 'Signal Jumping' : 'Wrong-Way Driving';
      const evidence   = r.evidence_path
        ? `<a class="evidence-link" href="/evidence/${r.evidence_path}" target="_blank">View</a>`
        : '<span style="color:#4b5563">—</span>';

      return `<tr>
        <td>${r.violation_id}</td>
        <td>${r.timestamp}</td>
        <td><span class="badge ${badgeClass}">${typeLabel}</span></td>
        <td>${r.vehicle_id}</td>
        <td>${r.camera_id}</td>
        <td>${r.location}</td>
        <td>${evidence}</td>
      </tr>`;
    }).join('');
  }

  loadStats();
  loadViolations();
</script>
</body>
</html>
"""


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/stats")
def api_stats():
    """Return summary statistics as JSON."""
    return jsonify(get_summary_stats())


@app.route("/api/violations")
def api_violations():
    """Return filtered violation records as JSON."""
    vtype  = request.args.get("type")
    cam_id = request.args.get("camera_id", type=int)
    start  = request.args.get("start")
    end    = request.args.get("end")
    limit  = request.args.get("limit", 50, type=int)

    rows = query_violations(
        limit=limit,
        violation_type=vtype,
        camera_id=cam_id,
        start_date=start,
        end_date=end,
    )
    return jsonify(rows)


@app.route("/api/cameras")
def api_cameras():
    """Return all camera records as JSON."""
    return jsonify(get_cameras())


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    create_tables()          # ensure DB schema exists on startup
    print("[Dashboard] Starting SmartTraffic Vision dashboard...")
    print("[Dashboard] Open: http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
