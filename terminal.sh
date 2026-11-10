#!/usr/bin/env bash
# Launch the AI Red Team Blue-Green Deployment backend in interactive terminal mode.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

export PYTHONPATH="$SCRIPT_DIR/backend"
exec "$SCRIPT_DIR/backend/venv/bin/python" -m app.cli

