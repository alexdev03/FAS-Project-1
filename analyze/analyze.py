#!/usr/bin/env python3

import argparse
import sqlite3
import sys

import pandas as pd


def carica_metriche(db_path, da=None, a=None):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM metrics ORDER BY timestamp", conn)
    conn.close()

    if da:
        df = df[df["timestamp"] >= da]
    if a:
        df = df[df["timestamp"] <= a]

    return df


def trova_anomalie(df, colonna, soglia=2.0):
    # z-score su finestra mobile: valori molto distanti dalla media recente
    media = df[colonna].rolling(10, min_periods=1).mean()
    std   = df[colonna].rolling(10, min_periods=1).std().fillna(1)
    z = (df[colonna] - media) / std
    return df[z.abs() > soglia]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/metrics.db")
    parser.add_argument("--from", dest="da", metavar="TIMESTAMP")
    parser.add_argument("--to",   dest="a",  metavar="TIMESTAMP")
    parser.add_argument("--metric", default="cpu_pct",
                        choices=["cpu_pct", "mem_used_mb", "disk_used_pct"])
    parser.add_argument("--anomaly", action="store_true")
    args = parser.parse_args()

    df = carica_metriche(args.db, args.da, args.a)

    if df.empty:
        print("nessun dato trovato")
        sys.exit(0)

    print(f"\n--- {args.metric} ({len(df)} campioni) ---")
    print(df[args.metric].describe().to_string())

    if args.anomaly:
        anom = trova_anomalie(df, args.metric)
        print(f"\nanomalie trovate: {len(anom)}")
        if not anom.empty:
            print(anom[["timestamp", args.metric]].to_string(index=False))


if __name__ == "__main__":
    main()
