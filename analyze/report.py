#!/usr/bin/env python3

import argparse
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def carica_dati(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM metrics ORDER BY timestamp", conn)
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def grafico_cpu(df, out_dir):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["timestamp"], df["cpu_pct"], color="steelblue", linewidth=1.2)
    ax.fill_between(df["timestamp"], df["cpu_pct"], alpha=0.2, color="steelblue")
    ax.set_title("Utilizzo CPU nel tempo")
    ax.set_ylabel("CPU %")
    ax.set_ylim(0, 100)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "cpu.png", dpi=120)
    plt.close(fig)
    print("salvato cpu.png")


def grafico_ram(df, out_dir):
    libera = df["mem_total_mb"] - df["mem_used_mb"]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.stackplot(df["timestamp"], df["mem_used_mb"], libera,
                 labels=["Usata", "Libera"], colors=["coral", "lightgreen"], alpha=0.8)
    ax.set_title("Utilizzo RAM nel tempo")
    ax.set_ylabel("MB")
    ax.legend(loc="upper left")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "memory.png", dpi=120)
    plt.close(fig)
    print("salvato memory.png")


def grafico_disco(df, out_dir):
    # prendo solo l'ultimo campione per il pie chart
    usato = df["disk_used_pct"].iloc[-1]
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie([usato, 100 - usato],
           labels=["Usato", "Libero"],
           colors=["tomato", "lightgrey"],
           autopct="%1.1f%%",
           startangle=90)
    ax.set_title("Disco / (ultimo campione)")
    fig.savefig(out_dir / "disk.png", dpi=120)
    plt.close(fig)
    print("salvato disk.png")


def grafico_rete(df, out_dir):
    # i contatori in /proc/net/dev sono cumulativi, quindi faccio il diff
    rx = df["net_rx_bytes"].diff().fillna(0).clip(lower=0) / 1024
    tx = df["net_tx_bytes"].diff().fillna(0).clip(lower=0) / 1024

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["timestamp"], rx, label="RX KB", color="mediumseagreen")
    ax.plot(df["timestamp"], tx, label="TX KB", color="darkorange")
    ax.set_title("Traffico di rete")
    ax.set_ylabel("KB per campione")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "network.png", dpi=120)
    plt.close(fig)
    print("salvato network.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/metrics.db")
    parser.add_argument("--out", default="reports")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = carica_dati(args.db)
    if df.empty:
        print("nessun dato nel db, esegui prima 'make collect'")
        sys.exit(0)

    print(f"{len(df)} campioni trovati, genero grafici...")
    grafico_cpu(df, out_dir)
    grafico_ram(df, out_dir)
    grafico_disco(df, out_dir)
    grafico_rete(df, out_dir)


if __name__ == "__main__":
    main()
