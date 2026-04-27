#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# legge metriche di sistema e stampa una riga CSV su stdout
# formato: timestamp,cpu_pct,mem_used_mb,mem_total_mb,disk_pct,net_rx,net_tx

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# CPU: leggo /proc/stat due volte a distanza di 1 secondo e calcolo la %
# (la prima lettura da sola non è significativa perché i contatori sono cumulativi)
leggi_cpu() {
    local r1 r2 idle1 idle2 tot1 tot2

    r1=$(grep '^cpu ' /proc/stat)
    sleep 1
    r2=$(grep '^cpu ' /proc/stat)

    idle1=$(echo "$r1" | awk '{print $5}')
    tot1=$(echo "$r1"  | awk '{for(i=2;i<=NF;i++) s+=$i; print s}')
    idle2=$(echo "$r2" | awk '{print $5}')
    tot2=$(echo "$r2"  | awk '{for(i=2;i<=NF;i++) s+=$i; print s}')

    local d_idle d_tot
    d_idle=$(( idle2 - idle1 ))
    d_tot=$(( tot2 - tot1 ))

    awk "BEGIN { printf \"%.1f\", (1 - $d_idle/$d_tot) * 100 }"
}

CPU_PCT=$(leggi_cpu)

# RAM da /proc/meminfo
MEM_TOTAL=$(grep '^MemTotal:'     /proc/meminfo | awk '{print $2}')
MEM_AVAIL=$(grep '^MemAvailable:' /proc/meminfo | awk '{print $2}')
MEM_USED_MB=$(( (MEM_TOTAL - MEM_AVAIL) / 1024 ))
MEM_TOTAL_MB=$(( MEM_TOTAL / 1024 ))

# Disco: percentuale usata su /
DISK_PCT=$(df / | awk 'NR==2 {gsub(/%/,"",$5); print $5}')

# Rete: prima interfaccia non-loopback da /proc/net/dev
# colonna 2 = rx bytes, colonna 10 = tx bytes
NET_LINE=$(awk 'NR>2 && !/lo:/ {print; exit}' /proc/net/dev)
NET_RX=$(echo "$NET_LINE" | awk '{print $2}')
NET_TX=$(echo "$NET_LINE" | awk '{print $10}')

echo "${TIMESTAMP},${CPU_PCT},${MEM_USED_MB},${MEM_TOTAL_MB},${DISK_PCT},${NET_RX},${NET_TX}"
