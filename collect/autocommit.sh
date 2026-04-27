#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Raccoglie metriche, le salva nel DB, committa e pusha su GitHub.
# Legge configurazione da .env nella root del progetto.
#
# Uso:
#   bash collect/autocommit.sh          # singola esecuzione
#   bash collect/autocommit.sh --loop   # loop continuo (usa COLLECT_INTERVAL da .env)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# carica .env se esiste
if [ -f "$ROOT_DIR/.env" ]; then
    # shellcheck disable=SC2046
    export $(grep -v '^#' "$ROOT_DIR/.env" | grep -v '^$' | xargs)
else
    echo "errore: .env non trovato in $ROOT_DIR"
    echo "copia .env.example in .env e compila i valori"
    exit 1
fi

: "${GITHUB_REPO:?variabile GITHUB_REPO mancante nel .env}"
: "${GITHUB_TOKEN:?variabile GITHUB_TOKEN mancante nel .env}"
INTERVAL="${COLLECT_INTERVAL:-60}"

VENV="$ROOT_DIR/.venv/bin/python"
DB="$ROOT_DIR/data/metrics.db"
CSV_METRICS="$ROOT_DIR/data/collect_latest.csv"
CSV_LOGS="$ROOT_DIR/data/logs_latest.csv"

# configura git per usare il token (HTTPS)
# formato: https://x-access-token:TOKEN@github.com/UTENTE/REPO.git
REMOTE_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"

git -C "$ROOT_DIR" remote set-url origin "$REMOTE_URL" 2>/dev/null || \
    git -C "$ROOT_DIR" remote add origin "$REMOTE_URL"

esegui_ciclo() {
    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    echo "[$ts] raccolta metriche..."
    bash "$ROOT_DIR/collect/collect.sh" >> "$CSV_METRICS"

    echo "[$ts] parsing log..."
    bash "$ROOT_DIR/collect/parse_logs.sh" > "$CSV_LOGS"

    echo "[$ts] import nel db..."
    "$VENV" "$ROOT_DIR/analyze/store.py" \
        --db "$DB" \
        --metrics "$CSV_METRICS" \
        --logs "$CSV_LOGS"

    # genero i grafici aggiornati
    "$VENV" "$ROOT_DIR/analyze/report.py" --db "$DB" --out "$ROOT_DIR/reports"

    # commit e push dei PNG aggiornati
    git -C "$ROOT_DIR" add reports/ 2>/dev/null || true
    git -C "$ROOT_DIR" diff --cached --quiet && {
        echo "[$ts] nessuna modifica da committare"
        return
    }

    git -C "$ROOT_DIR" \
        -c user.email="sysmetrics@localhost" \
        -c user.name="SysMetrics" \
        commit -m "data: aggiorno grafici [$ts]"

    git -C "$ROOT_DIR" push origin master
    echo "[$ts] push completato"
}

if [ "${1:-}" = "--loop" ]; then
    echo "avvio loop ogni ${INTERVAL}s (Ctrl+C per fermare)"
    while true; do
        esegui_ciclo
        sleep "$INTERVAL"
    done
else
    esegui_ciclo
fi
