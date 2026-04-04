# CI Integration Guide

## GitHub Actions
The framework ships with a ready-to-use workflow:

```yaml
- name: Run Daml Tests
  run: |
    daml build
    python3 -m dtf run .daml/dist/myapp.dar --workers 4 \
      --json --out results.json

- name: Upload Test Report
  uses: actions/upload-artifact@v4
  with:
    name: test-report
    path: results.json
```

## Parallel Execution
Use `--workers N` to run N scripts concurrently.
Recommended: 4 workers for small suites, 8 for large.

## Timeout Configuration
Set `--timeout 60` to kill scripts that hang after 60 seconds.
Default is 120 seconds.
