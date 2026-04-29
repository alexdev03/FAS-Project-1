#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGS_DIR="$ROOT/data"

# load .env for the token (never tracked by git)
if [ -f "$ROOT/.env" ]; then
    # shellcheck disable=SC2046
    export $(grep -v '^#' "$ROOT/.env" | xargs)
else
    echo "missing .env — copy .env.example to .env and set GITHUB_TOKEN"
    exit 1
fi

# read a key from config.ini
get_config() {
    grep "^$1" "$ROOT/config.ini" | sed 's/.*= *//' | tr -d '[:space:]'
}

REPO=$(get_config "repo")
INTERVAL=$(get_config "interval")
INTERVAL="${INTERVAL:-600}"
TOKEN="${GITHUB_TOKEN:-}"

if [ "$REPO" = "utente/nome-repo" ] || [ -z "$TOKEN" ]; then
    echo "set repo in config.ini and GITHUB_TOKEN in .env"
    exit 1
fi

REMOTE="https://x-access-token:${TOKEN}@github.com/${REPO}.git"

# initialise a separate git repo inside data/ if not already done
mkdir -p "$LOGS_DIR"
if [ ! -d "$LOGS_DIR/.git" ]; then
    git -C "$LOGS_DIR" init
    git -C "$LOGS_DIR" remote add origin "$REMOTE"
    # pull existing history if the remote already has content
    git -C "$LOGS_DIR" pull origin master 2>/dev/null || true
    echo "initialised logs repo in $LOGS_DIR"
else
    git -C "$LOGS_DIR" remote set-url origin "$REMOTE"
fi

run_cycle() {
    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    bash "$ROOT/collect.sh"

    git -C "$LOGS_DIR" add .

    # skip commit if nothing changed
    if git -C "$LOGS_DIR" diff --cached --quiet; then
        echo "[$ts] no changes, skipping"
        return
    fi

    git -C "$LOGS_DIR" \
        -c user.email="fas-project-1@unitn.it" \
        -c user.name="alex" \
        commit -m "data: update CSV [$ts]"

    git -C "$LOGS_DIR" push origin master
    echo "[$ts] pushed"
}

echo "starting loop every ${INTERVAL}s — Ctrl+C to stop"
while true; do
    run_cycle
    sleep "$INTERVAL"
done
