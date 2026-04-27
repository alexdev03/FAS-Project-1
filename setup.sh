#!/usr/bin/env bash
set -euo pipefail

# Provisioning: crea venv Python e installa le dipendenze.

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "[setup] Creo virtualenv in $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

echo "[setup] Installo dipendenze da requirements.txt"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r requirements.txt

echo "[setup] Setup completato. Attiva con: source $VENV_DIR/bin/activate"
