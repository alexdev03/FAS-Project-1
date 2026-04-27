#!/usr/bin/env python3

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

# il db è nella cartella data/ rispetto alla root del progetto
DB_PATH = Path(__file__).parent.parent / "data" / "metrics.db"

HTML = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>SysMetrics</title>
<style>
  body { font-family: monospace; background: #0d1117; color: #c9d1d9; padding: 1rem; }
  h1 { color: #58a6ff; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 1rem; }
  img { width: 100%; }
  .big { font-size: 2rem; color: #3fb950; }
  small { color: #8b949e; }
</style>
</head>
<body>
<h1>SysMetrics Dashboard</h1>
<small>auto-refresh ogni 30s</small>

<div class="grid">
  <div class="card"><small>CPU medio</small><div class="big" id="cpu">--</div></div>
  <div class="card"><small>RAM usata (ultimo)</small><div class="big" id="mem">--</div></div>
</div>

<div class="grid" style="margin-top:1rem">
  {% for titolo, img in grafici %}
  <div class="card"><img src="data:image/png;base64,{{ img }}" alt="{{ titolo }}"></div>
  {% endfor %}
</div>

<script>
async function aggiorna() {
  const r = await fetch('/api/metrics');
  const d = await r.json();
  document.getElementById('cpu').textContent = d.cpu_avg.toFixed(1) + ' %';
  document.getElementById('mem').textContent = d.mem_mb + ' MB';
}
aggiorna();
setInterval(() => location.reload(), 30000);
</script>
</body>
</html>"""


def carica_df():
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM metrics ORDER BY timestamp", conn)
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def build_grafici(df):
    grafici = []

    # CPU
    fig, ax = plt.subplots(figsize=(6, 3), facecolor="#161b22")
    ax.set_facecolor("#161b22")
    ax.plot(df["timestamp"], df["cpu_pct"], color="#58a6ff", linewidth=1)
    ax.fill_between(df["timestamp"], df["cpu_pct"], alpha=0.15, color="#58a6ff")
    ax.set_title("CPU %", color="#c9d1d9")
    ax.tick_params(colors="#8b949e")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    for s in ax.spines.values():
        s.set_edgecolor("#30363d")
    fig.tight_layout()
    grafici.append(("CPU", fig_to_b64(fig)))

    # RAM
    fig, ax = plt.subplots(figsize=(6, 3), facecolor="#161b22")
    ax.set_facecolor("#161b22")
    libera = df["mem_total_mb"] - df["mem_used_mb"]
    ax.stackplot(df["timestamp"], df["mem_used_mb"], libera,
                 colors=["#f78166", "#3fb950"], alpha=0.7)
    ax.set_title("RAM (MB)", color="#c9d1d9")
    ax.tick_params(colors="#8b949e")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    for s in ax.spines.values():
        s.set_edgecolor("#30363d")
    fig.tight_layout()
    grafici.append(("RAM", fig_to_b64(fig)))

    return grafici


@app.route("/")
def index():
    df = carica_df()
    grafici = build_grafici(df) if not df.empty else []
    return render_template_string(HTML, grafici=grafici)


@app.route("/api/metrics")
def api_metrics():
    df = carica_df()
    if df.empty:
        return jsonify({"cpu_avg": 0.0, "mem_mb": 0, "campioni": 0})
    return jsonify({
        "cpu_avg": float(df["cpu_pct"].mean()),
        "mem_mb":  int(df["mem_used_mb"].iloc[-1]),
        "campioni": len(df),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
