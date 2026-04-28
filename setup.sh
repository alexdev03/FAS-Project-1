#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "creating virtualenv in $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

echo "installing dependencies"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r requirements.txt

echo "done — activate with: source $VENV_DIR/bin/activate"
