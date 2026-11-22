#!/usr/bin/env bash
set -euo pipefail

file=$(jq -r '.tool_input.file_path // empty')
[[ "$file" == *.py && -f "$file" ]] || exit 0

cd "$(dirname "$file")"
uv run --quiet --no-sync ruff format --quiet "$file" 2>/dev/null || true
