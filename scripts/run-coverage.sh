#!/usr/bin/env bash

# This script runs the full Daml test suite, generates a code coverage report,
# and opens the HTML report in the default web browser.

set -euo pipefail

PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd "$PROJECT_ROOT"

# Define the path to the generated coverage report
COVERAGE_REPORT_PATH=".daml/coverage/index.html"

echo "🧹 Cleaning up previous build artifacts..."
daml clean

echo "🧪 Running Daml tests with coverage enabled..."
# The --coverage flag instructs `daml test` to generate the report
daml test --coverage

echo "✅ Tests finished."
echo "📈 Coverage report generated at: $COVERAGE_REPORT_PATH"

# Check if the report file exists
if [ ! -f "$COVERAGE_REPORT_PATH" ]; then
    echo "❌ Error: Coverage report not found at $COVERAGE_REPORT_PATH"
    exit 1
fi

echo "🚀 Opening coverage report in your browser..."

# Use the appropriate command to open the file based on the OS
case "$(uname -s)" in
   Darwin) # macOS
     open "$COVERAGE_REPORT_PATH"
     ;;
   Linux)
     # Check if running under WSL
     if grep -qE "(Microsoft|WSL)" /proc/version &> /dev/null; then
        # Convert the Unix path to a Windows path and use explorer.exe
        explorer.exe "$(wslpath -w "$PWD/$COVERAGE_REPORT_PATH")"
     else # Native Linux
        xdg-open "$COVERAGE_REPORT_PATH"
     fi
     ;;
   CYGWIN*|MINGW*|MSYS*) # Windows (Git Bash, Cygwin, etc.)
     start "$COVERAGE_REPORT_PATH"
     ;;
   *)
     echo "Unsupported OS: $(uname -s)"
     echo "Please open the report manually by navigating to this file in your browser:"
     echo "file://$PWD/$COVERAGE_REPORT_PATH"
     ;;
esac

echo "🎉 Done."