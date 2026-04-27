#!/usr/bin/env python3
"""Flask web dashboard per SysMetrics."""

import base64
import io
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
DB_PATH = Path(__file__).parent.parent / "data" / "metrics.db"

HTML = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SysMetrics Dashboard</title>
<style>
  body { font-family: monospace; background:#0d1117; color:#c9d1d9; margin:0; padding:1rem; }
  h1   { color:#58a6ff; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-top:1rem; }
  .card { background:#161b22; border:1px solid #30363d; border-radius:6px; padding:1rem; }
  img  { width:100%; border-radius:4px; }
  .stat { font-size:2rem; color:#3fb950; }
  .label { font-size:.8rem; color:#8b949e; }
  #refresh { font-size:.8rem; color:#8b949e; }
</style>
</head>
<body>
<h1>&#x1f4ca; SysMetrics Dashboard</h1>
<div id="refresh">Auto-refresh ogni 30s</div>

<div class="grid">
  <div class="card">
    <div class="label">CPU medio</div>
    <div class="stat" id="cpu_avg">--</div>
  </div>
  <div class="card">
    <div class="label">RAM usata (ultimo)</div>
    <div class="stat" id="mem_used">--</div>
  </div>
</div>

<div class="grid" style="margin-top:1rem">
  {% for name, img in charts %}
  <div class="card">
    <img src="data:image/png;base64,{{ img }}" alt="{{ name }}">
  </div>
  {% endfor %}
</div>

<script>
async function refreshStats() {
  const r = await fetch('/api/metrics');
  const d = await r.json();
  document.getElementById('cpu_avg').textContent = d.cpu_avg.toFixed(1) + ' %';
  document.getElementById('mem_used').textContent = d.mem_used_mb + ' MB';
}
refreshStats();
setInterval(() => location.reload(), 30000);
</script>
</body>
</html>"""


def load_df() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM metrics ORDER BY timestamp", conn)
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def make_chart(fig: plt.Figure) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def build_charts(df: pd.DataFrame) -> list[tuple[str, str]]:
    charts = []

    # CPU
    fig, ax = plt.subplots(figsize=(6, 3), facecolor="#161b22")
    ax.set_facecolor("#161b22")
    ax.plot(df["timestamp"], df["cpu_pct"], color="#58a6ff", linewidth=1)
    ax.fill_between(df["timestamp"], df["cpu_pct"], alpha=0.15, color="#58a6ff")
    ax.set_title("CPU %", color="#c9d1d9")
    ax.tick_params(colors="#8b949e")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")
    fig.tight_layout()
    charts.append(("CPU", make_chart(fig)))

    # RAM
    fig, ax = plt.subplots(figsize=(6, 3), facecolor="#161b22")
    ax.set_facecolor("#161b22")
    ax.stackplot(df["timestamp"],
                 df["mem_used_mb"], df["mem_total_mb"] - df["mem_used_mb"],
                 colors=["#f78166", "#3fb950"], alpha=0.7)
    ax.set_title("RAM (MB)", color="#c9d1d9")
    ax.tick_params(colors="#8b949e")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")
    fig.tight_layout()
    charts.append(("RAM", make_chart(fig)))

    return charts


@app.route("/")
def index():
    df = load_df()
    charts = build_charts(df) if not df.empty else []
    return render_template_string(HTML, charts=charts)


@app.route("/api/metrics")
def api_metrics():
    df = load_df()
    if df.empty:
        return jsonify({"cpu_avg": 0.0, "mem_used_mb": 0, "samples": 0})
    return jsonify({
        "cpu_avg": float(df["cpu_pct"].mean()),
        "mem_used_mb": int(df["mem_used_mb"].iloc[-1]),
        "samples": len(df),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
