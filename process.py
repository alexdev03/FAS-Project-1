#!/usr/bin/env python3

import configparser
import csv
import os
import re
import subprocess
from datetime import datetime, timezone

CONFIG = os.path.join(os.path.dirname(__file__), "config.ini")
DATA   = os.path.join(os.path.dirname(__file__), "data")


def load_config():
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG)
    return cfg


# --- metrics -----------------------------------------------------------------

def sh(cmd):
    r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
    return r.stdout.strip()


def cpu_load():
    # 1-minute load average from /proc/loadavg
    return sh("cat /proc/loadavg").split()[0]


def ram_usage():
    # grep MemTotal and MemAvailable from /proc/meminfo
    out = sh("grep -E 'MemTotal|MemAvailable' /proc/meminfo")
    info = {}
    for line in out.splitlines():
        key, val = line.split(":")
        info[key.strip()] = int(val.strip().split()[0])  # kB

    total = info["MemTotal"] // 1024
    used  = (info["MemTotal"] - info["MemAvailable"]) // 1024
    return used, total


def disk_usage():
    out = sh("df / --output=pcent")
    return int(out.splitlines()[-1].strip().replace("%", ""))


# --- log errors --------------------------------------------------------------

def grep_errors(regex, n_lines):
    r = subprocess.run(
        ["bash", "-c", f"journalctl -n {n_lines} --no-pager"],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        return []

    pattern = re.compile(regex, re.IGNORECASE)
    matches = []
    for line in r.stdout.splitlines():
        if pattern.search(line):
            parts = line.split(None, 4)
            ts  = " ".join(parts[:3]) if len(parts) >= 3 else ""
            msg = parts[4].strip()   if len(parts) >= 5 else line.strip()
            matches.append((ts, msg))

    return matches


# --- CSV writers -------------------------------------------------------------

def append_metrics(ts, load, mem_used, mem_total, disk_pct):
    os.makedirs(DATA, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    path  = os.path.join(DATA, f"{today}.csv")

    write_header = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["timestamp", "load_avg", "mem_used_mb", "mem_total_mb", "disk_pct"])
        w.writerow([ts, load, mem_used, mem_total, disk_pct])


def append_errors(errors):
    os.makedirs(DATA, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    path  = os.path.join(DATA, f"{today}_errors.csv")

    write_header = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["timestamp", "message"])
        w.writerows(errors)


# -----------------------------------------------------------------------------

def main():
    cfg     = load_config()
    regex   = cfg.get("log", "regex",  fallback="error|failed|critical")
    n_lines = cfg.getint("log", "lines", fallback=500)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    load            = cpu_load()
    mem_used, mem_total = ram_usage()
    disk            = disk_usage()

    append_metrics(ts, load, mem_used, mem_total, disk)
    print(f"[{ts}] load={load} mem={mem_used}/{mem_total}MB disk={disk}%")

    errors = grep_errors(regex, n_lines)
    if errors:
        append_errors(errors)
        print(f"[{ts}] {len(errors)} errors matched '{regex}'")


if __name__ == "__main__":
    main()
