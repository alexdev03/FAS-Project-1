#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Analizza i log di sistema e produce una riga CSV per ogni evento rilevante.
# Sorgente: journalctl (se disponibile) oppure /var/log/syslog.
# Formato output: timestamp,level,unit,message

# Numero di righe recenti da analizzare (default 500)
LINES="${1:-500}"

# Pattern di interesse (grep extended)
PATTERN="error|warning|failed|critical|denied|refused|killed"

emit_csv() {
    local raw_line="$1"
    local ts level unit msg

    # Formato journalctl --no-pager: "Apr 29 10:00:00 host unit[pid]: message"
    ts=$(echo "$raw_line"  | awk '{print $1, $2, $3}')
    unit=$(echo "$raw_line" | awk '{print $5}' | sed 's/\[.*\]//; s/://')
    msg=$(echo "$raw_line"  | cut -d: -f4- | sed 's/^ *//' | tr ',' ';')

    if echo "$raw_line" | grep -qiE "error|critical|failed"; then
        level="ERROR"
    elif echo "$raw_line" | grep -qiE "warning|warn"; then
        level="WARNING"
    else
        level="INFO"
    fi

    printf '"%s","%s","%s","%s"\n' "$ts" "$level" "$unit" "$msg"
}

# Header
echo "timestamp,level,unit,message"

if command -v journalctl &>/dev/null; then
    journalctl --no-pager -n "$LINES" 2>/dev/null \
        | grep -iE "$PATTERN" \
        | while IFS= read -r line; do emit_csv "$line"; done
elif [ -f /var/log/syslog ]; then
    tail -n "$LINES" /var/log/syslog \
        | grep -iE "$PATTERN" \
        | while IFS= read -r line; do emit_csv "$line"; done
else
    echo '"N/A","INFO","parse_logs","No log source available"'
fi
