#!/usr/bin/env bash
set -euo pipefail

# collect system metrics and log errors, write to daily CSV
python3 "$(dirname "$0")/process.py"
