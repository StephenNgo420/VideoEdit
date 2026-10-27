#!/usr/bin/env bash
# Delegate to the repository setup; do not install into system Python.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
bash "$ROOT/scripts/setup.sh"
