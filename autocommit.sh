#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ROOT="$(cd "$(dirname "$0")" && pwd)"

# read a key from config.ini
get_config() {
    grep "^$1" "$ROOT/config.ini" | sed 's/.*= *//' | tr -d '[:space:]'
}

REPO=$(get_config "repo")
TOKEN=$(get_config "token")
INTERVAL=$(get_config "intervallo")
INTERVAL="${INTERVAL:-600}"

if [ "$REPO" = "utente/nome-repo" ] || [ -z "$TOKEN" ]; then
    echo "set repo and token in config.ini before running autocommit"
    exit 1
fi

REMOTE="https://x-access-token:${TOKEN}@github.com/${REPO}.git"
git -C "$ROOT" remote set-url origin "$REMOTE" 2>/dev/null || \
    git -C "$ROOT" remote add origin "$REMOTE"

run_cycle() {
    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    python3 "$ROOT/process.py"

    git -C "$ROOT" add data/

    # skip commit if nothing changed
    if git -C "$ROOT" diff --cached --quiet; then
        echo "[$ts] no changes, skipping"
        return
    fi

    git -C "$ROOT" \
        -c user.email="sysmetrics@localhost" \
        -c user.name="sysmetrics" \
        commit -m "data: update CSV [$ts]"

    git -C "$ROOT" push origin master
    echo "[$ts] pushed"
}

echo "starting loop every ${INTERVAL}s — Ctrl+C to stop"
while true; do
    run_cycle
    sleep "$INTERVAL"
done
