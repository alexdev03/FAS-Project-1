#!/usr/bin/env python3

import argparse
import csv
import sqlite3
import sys
from pathlib import Path


def init_db(path):
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cpu_pct REAL,
            mem_used_mb INTEGER,
            mem_total_mb INTEGER,
            disk_used_pct INTEGER,
            net_rx_bytes INTEGER,
            net_tx_bytes INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS log_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            level TEXT,
            unit TEXT,
            message TEXT
        )
    """)
    conn.commit()
    return conn


def importa_metriche(conn, csv_path):
    n = 0
    with open(csv_path) as f:
        for riga in f:
            riga = riga.strip()
            if not riga:
                continue
            campi = riga.split(",")
            if len(campi) != 7:
                continue
            ts, cpu, mem_used, mem_total, disk, rx, tx = campi
            conn.execute(
                "INSERT INTO metrics VALUES (NULL,?,?,?,?,?,?,?)",
                (ts, float(cpu), int(mem_used), int(mem_total), int(disk), int(rx), int(tx))
            )
            n += 1
    conn.commit()
    return n


def importa_log(conn, csv_path):
    n = 0
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conn.execute(
                "INSERT INTO log_events VALUES (NULL,?,?,?,?)",
                (row["timestamp"], row["level"], row["unit"], row["message"])
            )
            n += 1
    conn.commit()
    return n


def main():
    parser = argparse.ArgumentParser(description="importa CSV nel database")
    parser.add_argument("--db", default="data/metrics.db")
    parser.add_argument("--metrics", help="output di collect.sh")
    parser.add_argument("--logs",    help="output di parse_logs.sh")
    args = parser.parse_args()

    if not args.metrics and not args.logs:
        parser.print_help()
        sys.exit(1)

    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    conn = init_db(args.db)

    if args.metrics:
        n = importa_metriche(conn, args.metrics)
        print(f"metriche inserite: {n}")

    if args.logs:
        n = importa_log(conn, args.logs)
        print(f"eventi log inseriti: {n}")

    conn.close()


if __name__ == "__main__":
    main()
