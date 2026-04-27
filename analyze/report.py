#!/usr/bin/env python3
"""Genera grafici PNG a partire dai dati nel DB SQLite."""

import argparse
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def load_df(db_path: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM metrics ORDER BY timestamp", conn)
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def plot_cpu(df: pd.DataFrame, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["timestamp"], df["cpu_pct"], linewidth=1.2, color="steelblue")
    ax.fill_between(df["timestamp"], df["cpu_pct"], alpha=0.2, color="steelblue")
    ax.set_title("Utilizzo CPU nel tempo")
    ax.set_ylabel("CPU %")
    ax.set_xlabel("Timestamp")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "cpu.png", dpi=120)
    plt.close(fig)
    print(f"[report] Salvato {out_dir}/cpu.png")


def plot_memory(df: pd.DataFrame, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.stackplot(
        df["timestamp"],
        df["mem_used_mb"],
        df["mem_total_mb"] - df["mem_used_mb"],
        labels=["Usata", "Libera"],
        colors=["coral", "lightgreen"],
        alpha=0.8,
    )
    ax.set_title("Utilizzo RAM nel tempo")
    ax.set_ylabel("MB")
    ax.set_xlabel("Timestamp")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "memory.png", dpi=120)
    plt.close(fig)
    print(f"[report] Salvato {out_dir}/memory.png")


def plot_disk(df: pd.DataFrame, out_dir: Path) -> None:
    last = df.iloc[-1]
    used = last["disk_used_pct"]
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(
        [used, 100 - used],
        labels=["Usato", "Libero"],
        colors=["tomato", "lightgrey"],
        autopct="%1.1f%%",
        startangle=90,
    )
    ax.set_title("Disco (root) — campione più recente")
    fig.tight_layout()
    fig.savefig(out_dir / "disk.png", dpi=120)
    plt.close(fig)
    print(f"[report] Salvato {out_dir}/disk.png")


def plot_network(df: pd.DataFrame, out_dir: Path) -> None:
    # Converti contatori cumulativi in delta per campione
    rx_delta = df["net_rx_bytes"].diff().fillna(0).clip(lower=0) / 1024
    tx_delta = df["net_tx_bytes"].diff().fillna(0).clip(lower=0) / 1024

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["timestamp"], rx_delta, label="RX (KB/s)", color="mediumseagreen")
    ax.plot(df["timestamp"], tx_delta, label="TX (KB/s)", color="darkorange")
    ax.set_title("Traffico di rete nel tempo")
    ax.set_ylabel("KB per campione")
    ax.set_xlabel("Timestamp")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "network.png", dpi=120)
    plt.close(fig)
    print(f"[report] Salvato {out_dir}/network.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera report grafici")
    parser.add_argument("--db", default="data/metrics.db")
    parser.add_argument("--out", default="reports", help="Directory output PNG")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        df = load_df(args.db)
    except Exception as e:
        print(f"Errore lettura DB: {e}", file=sys.stderr)
        sys.exit(1)

    if df.empty:
        print("Nessun dato nel DB.")
        sys.exit(0)

    plot_cpu(df, out_dir)
    plot_memory(df, out_dir)
    plot_disk(df, out_dir)
    plot_network(df, out_dir)
    print(f"[report] {len(df)} campioni, {len(df.columns)} metriche → 4 grafici generati")


if __name__ == "__main__":
    main()
