#!/usr/bin/env python3
"""Interroga il DB SQLite e stampa statistiche + anomalie."""

import argparse
import sqlite3
import sys

import pandas as pd


def load_metrics(conn: sqlite3.Connection, from_ts: str | None, to_ts: str | None) -> pd.DataFrame:
    query = "SELECT * FROM metrics WHERE 1=1"
    params: list = []
    if from_ts:
        query += " AND timestamp >= ?"
        params.append(from_ts)
    if to_ts:
        query += " AND timestamp <= ?"
        params.append(to_ts)
    query += " ORDER BY timestamp"
    return pd.read_sql_query(query, conn, params=params)


def detect_anomalies(df: pd.DataFrame, column: str, threshold: float = 2.0) -> pd.DataFrame:
    """Rileva valori oltre threshold deviazioni standard dalla media mobile (finestra 10)."""
    rolling_mean = df[column].rolling(window=10, min_periods=1).mean()
    rolling_std = df[column].rolling(window=10, min_periods=1).std().fillna(0)
    z_score = (df[column] - rolling_mean) / (rolling_std + 1e-9)
    return df[z_score.abs() > threshold]


def main() -> None:
    parser = argparse.ArgumentParser(description="Analisi metriche di sistema")
    parser.add_argument("--db", default="data/metrics.db")
    parser.add_argument("--from", dest="from_ts", metavar="TIMESTAMP")
    parser.add_argument("--to",   dest="to_ts",   metavar="TIMESTAMP")
    parser.add_argument("--metric", default="cpu_pct",
                        choices=["cpu_pct", "mem_used_mb", "disk_used_pct"])
    parser.add_argument("--anomaly", action="store_true",
                        help="Mostra solo i valori anomali")
    args = parser.parse_args()

    try:
        conn = sqlite3.connect(args.db)
    except Exception as e:
        print(f"Errore apertura DB: {e}", file=sys.stderr)
        sys.exit(1)

    df = load_metrics(conn, args.from_ts, args.to_ts)
    conn.close()

    if df.empty:
        print("Nessun dato trovato.")
        sys.exit(0)

    print(f"\n=== Statistiche '{args.metric}' ({len(df)} campioni) ===")
    stats = df[args.metric].describe()
    print(stats.to_string())

    if args.anomaly:
        anomalies = detect_anomalies(df, args.metric)
        print(f"\n=== Anomalie rilevate: {len(anomalies)} ===")
        if not anomalies.empty:
            print(anomalies[["timestamp", args.metric]].to_string(index=False))


if __name__ == "__main__":
    main()
