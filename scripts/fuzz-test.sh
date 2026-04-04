#!/usr/bin/env bash
set -euo pipefail

TEMPLATE="${1:-}"
COUNT="${2:-100}"

[[ -n "$TEMPLATE" ]] || { echo "Usage: $0 <FullyQualifiedTemplate> [count]"; exit 1; }

echo "Fuzz testing: $TEMPLATE ($COUNT runs)"
python3 dtf/fuzzer.py "$TEMPLATE" --count "$COUNT" | python3 -m json.tool
