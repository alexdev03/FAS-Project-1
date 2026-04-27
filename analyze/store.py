#!/usr/bin/env python3
"""Legge l'output CSV di collect.sh e parse_logs.sh e lo inserisce in SQLite."""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path


SCHEMA_METRICS = """
CREATE TABLE IF NOT EXISTS metrics (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    cpu_pct   REAL,
    mem_used_mb  INTEGER,
    mem_total_mb INTEGER,
    disk_used_pct INTEGER,
    net_rx_bytes  INTEGER,
    net_tx_bytes  INTEGER
);
"""

SCHEMA_LOGS = """
CREATE TABLE IF NOT EXISTS log_events (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    level     TEXT,
    unit      TEXT,
    message   TEXT
);
"""


def init_db(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA_METRICS)
    conn.execute(SCHEMA_LOGS)
    conn.commit()
    return conn


def store_metrics(conn: sqlite3.Connection, csv_path: str) -> int:
    rows = 0
    with open(csv_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) != 7:
                continue
            ts, cpu, mem_used, mem_total, disk, rx, tx = parts
            conn.execute(
                "INSERT INTO metrics VALUES (NULL,?,?,?,?,?,?,?)",
                (ts, float(cpu), int(mem_used), int(mem_total),
                 int(disk), int(rx), int(tx)),
            )
            rows += 1
    conn.commit()
    return rows


def store_logs(conn: sqlite3.Connection, csv_path: str) -> int:
    rows = 0
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute(
                "INSERT INTO log_events VALUES (NULL,?,?,?,?)",
                (row["timestamp"], row["level"], row["unit"], row["message"]),
            )
            rows += 1
    conn.commit()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa dati in SQLite")
    parser.add_argument("--db", default="data/metrics.db", help="Percorso database SQLite")
    parser.add_argument("--metrics", help="CSV da collect.sh")
    parser.add_argument("--logs", help="CSV da parse_logs.sh")
    args = parser.parse_args()

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    conn = init_db(args.db)

    if args.metrics:
        n = store_metrics(conn, args.metrics)
        print(f"[store] {n} righe metriche inserite")

    if args.logs:
        n = store_logs(conn, args.logs)
        print(f"[store] {n} eventi log inseriti")

    if not args.metrics and not args.logs:
        parser.print_help()
        sys.exit(1)

    conn.close()


if __name__ == "__main__":
    main()
