#!/usr/bin/env python3

import configparser
import csv
import os
import re
import subprocess
import sys
from datetime import datetime, timezone


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")
DATA_DIR    = os.path.join(os.path.dirname(__file__), "data")


def load_config():
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_PATH)
    return cfg


def collect_metrics():
    script = os.path.join(os.path.dirname(__file__), "collect", "collect.sh")
    result = subprocess.run(["bash", script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"collect.sh error: {result.stderr}", file=sys.stderr)
        return None
    return result.stdout.strip()


def collect_log_errors(regex_str, n_lines):
    pattern = re.compile(regex_str, re.IGNORECASE)

    # try journalctl first, fall back to /var/log/syslog
    try:
        out = subprocess.run(
            ["journalctl", "-n", str(n_lines), "--no-pager", "-o", "short"],
            capture_output=True, text=True
        )
        lines = out.stdout.splitlines()
    except FileNotFoundError:
        try:
            with open("/var/log/syslog") as f:
                lines = f.readlines()[-n_lines:]
        except FileNotFoundError:
            print("no log source found", file=sys.stderr)
            return []

    matches = []
    for line in lines:
        if pattern.search(line):
            parts = line.split(None, 4)
            if len(parts) >= 5:
                ts  = " ".join(parts[:3])
                msg = parts[4].strip()
            else:
                ts  = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                msg = line.strip()
            matches.append((ts, msg))

    return matches


def write_metrics(csv_line):
    today = datetime.now().strftime("%Y-%m-%d")
    path  = os.path.join(DATA_DIR, f"{today}.csv")
    os.makedirs(DATA_DIR, exist_ok=True)

    is_new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["timestamp", "cpu_pct", "mem_used_mb", "mem_total_mb",
                        "disk_pct", "net_rx_bytes", "net_tx_bytes"])
        w.writerow(csv_line.split(","))


def write_errors(errors):
    today = datetime.now().strftime("%Y-%m-%d")
    path  = os.path.join(DATA_DIR, f"{today}_errors.csv")
    os.makedirs(DATA_DIR, exist_ok=True)

    is_new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["timestamp", "message"])
        for ts, msg in errors:
            w.writerow([ts, msg])


def main():
    cfg     = load_config()
    regex   = cfg.get("log", "regex",  fallback="error|failed")
    n_lines = cfg.getint("log", "lines", fallback=500)

    metrics = collect_metrics()
    if metrics:
        write_metrics(metrics)
        print(f"metrics: {metrics}")

    errors = collect_log_errors(regex, n_lines)
    if errors:
        write_errors(errors)
        print(f"errors found: {len(errors)}")
    else:
        print("no errors matched the regex")


if __name__ == "__main__":
    main()
