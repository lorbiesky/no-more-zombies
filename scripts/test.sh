#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(CDPATH="" cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
exec "$PYTHON_BIN" "$ROOT_DIR/scripts/test.py" "$@"
