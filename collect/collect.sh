#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# collect system metrics and print one CSV line to stdout
# format: timestamp,cpu_pct,mem_used_mb,mem_total_mb,disk_pct,net_rx_bytes,net_tx_bytes

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# CPU: read /proc/stat twice one second apart
# counters are cumulative so the diff gives usage over that interval
read_cpu() {
    local r1 r2

    r1=$(grep '^cpu ' /proc/stat)
    sleep 1
    r2=$(grep '^cpu ' /proc/stat)

    local idle1 tot1 idle2 tot2
    idle1=$(echo "$r1" | awk '{print $5}')
    tot1=$(echo "$r1"  | awk '{for(i=2;i<=NF;i++) s+=$i; print s}')
    idle2=$(echo "$r2" | awk '{print $5}')
    tot2=$(echo "$r2"  | awk '{for(i=2;i<=NF;i++) s+=$i; print s}')

    local d_idle=$(( idle2 - idle1 ))
    local d_tot=$(( tot2 - tot1 ))

    awk "BEGIN { printf \"%.1f\", (1 - $d_idle/$d_tot) * 100 }"
}

CPU_PCT=$(read_cpu)

# RAM from /proc/meminfo (in KB, convert to MB)
MEM_TOTAL=$(grep '^MemTotal:'     /proc/meminfo | awk '{print $2}')
MEM_AVAIL=$(grep '^MemAvailable:' /proc/meminfo | awk '{print $2}')
MEM_USED_MB=$(( (MEM_TOTAL - MEM_AVAIL) / 1024 ))
MEM_TOTAL_MB=$(( MEM_TOTAL / 1024 ))

# disk usage on /
DISK_PCT=$(df / | awk 'NR==2 {gsub(/%/,"",$5); print $5}')

# network: first non-loopback interface from /proc/net/dev
# column 2 = rx bytes, column 10 = tx bytes
NET_LINE=$(awk 'NR>2 && !/lo:/ {print; exit}' /proc/net/dev)
NET_RX=$(echo "$NET_LINE" | awk '{print $2}')
NET_TX=$(echo "$NET_LINE" | awk '{print $10}')

echo "${TIMESTAMP},${CPU_PCT},${MEM_USED_MB},${MEM_TOTAL_MB},${DISK_PCT},${NET_RX},${NET_TX}"
