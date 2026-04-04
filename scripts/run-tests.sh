#!/usr/bin/env bash
set -euo pipefail

DAR="${1:-.daml/dist/$(ls .daml/dist/*.dar 2>/dev/null | head -1 | xargs basename)}"
WORKERS="${WORKERS:-4}"
TIMEOUT="${TIMEOUT:-120}"
OUT="test-results.json"
REPORT="test-report.html"

echo "Daml Testing Framework"
echo "======================"
echo "DAR:     $DAR"
echo "Workers: $WORKERS"
echo ""

daml build

python3 dtf/runner.py "$DAR" \
  --workers "$WORKERS" \
  --timeout "$TIMEOUT" \
  --json \
  --out "$OUT"

python3 dtf/reporter.py "$OUT" --out "$REPORT"
echo "HTML report: $REPORT"
