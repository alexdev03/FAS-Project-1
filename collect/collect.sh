#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Raccoglie CPU%, RAM%, disco% e rete da /proc e comandi standard.
# Output: una riga CSV su stdout con timestamp.
# Formato: timestamp,cpu_pct,mem_used_mb,mem_total_mb,disk_used_pct,net_rx_bytes,net_tx_bytes

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# --- CPU (media su 1s tramite /proc/stat) ---
read_cpu() {
    local line1 line2
    line1=$(grep '^cpu ' /proc/stat)
    sleep 1
    line2=$(grep '^cpu ' /proc/stat)

    local idle1 total1 idle2 total2
    idle1=$(echo "$line1" | awk '{print $5}')
    total1=$(echo "$line1" | awk '{for(i=2;i<=NF;i++) s+=$i; print s}')
    idle2=$(echo "$line2" | awk '{print $5}')
    total2=$(echo "$line2" | awk '{for(i=2;i<=NF;i++) s+=$i; print s}')

    local d_idle d_total
    d_idle=$(( idle2 - idle1 ))
    d_total=$(( total2 - total1 ))

    awk "BEGIN { printf \"%.1f\", (1 - $d_idle/$d_total) * 100 }"
}

CPU_PCT=$(read_cpu)

# --- RAM (da /proc/meminfo) ---
MEM_TOTAL_KB=$(grep '^MemTotal:' /proc/meminfo | awk '{print $2}')
MEM_AVAIL_KB=$(grep '^MemAvailable:' /proc/meminfo | awk '{print $2}')
MEM_USED_MB=$(( (MEM_TOTAL_KB - MEM_AVAIL_KB) / 1024 ))
MEM_TOTAL_MB=$(( MEM_TOTAL_KB / 1024 ))

# --- Disco (partizione root %) ---
DISK_USED_PCT=$(df / | awk 'NR==2 {gsub(/%/,"",$5); print $5}')

# --- Rete (prima interfaccia non-loopback da /proc/net/dev) ---
NET_LINE=$(awk 'NR>2 && !/lo:/ {print; exit}' /proc/net/dev)
NET_RX=$(echo "$NET_LINE" | awk '{print $2}')
NET_TX=$(echo "$NET_LINE" | awk '{print $10}')

echo "${TIMESTAMP},${CPU_PCT},${MEM_USED_MB},${MEM_TOTAL_MB},${DISK_USED_PCT},${NET_RX},${NET_TX}"
