#!/usr/bin/env python3
"""Generate HTML test report from JSON results."""
import json, sys, argparse
from pathlib import Path
from datetime import datetime

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Daml Test Report</title>
  <style>
    body {{ font-family: Inter, sans-serif; margin: 32px; color: #1e293b; }}
    h1   {{ font-size: 22px; }}
    .summary {{ display: flex; gap: 24px; margin: 16px 0; }}
    .card {{ padding: 12px 20px; border-radius: 8px; min-width: 100px; text-align: center; }}
    .pass {{ background: #dcfce7; color: #166534; }}
    .fail {{ background: #fee2e2; color: #991b1b; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th    {{ text-align: left; padding: 8px 12px; background: #f8fafc; font-size: 13px; }}
    td    {{ padding: 8px 12px; border-top: 1px solid #e2e8f0; font-size: 13px; }}
    .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
  </style>
</head>
<body>
  <h1>Daml Test Report</h1>
  <p style="color:#64748b">Generated: {date}</p>
  <div class="summary">
    <div class="card pass">✅ {passed} Passed</div>
    <div class="card fail">❌ {failed} Failed</div>
  </div>
  <table>
    <tr><th>Script</th><th>Result</th></tr>
    {rows}
  </table>
</body>
</html>"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results_json")
    parser.add_argument("--out", default="report.html")
    args = parser.parse_args()

    results = json.loads(Path(args.results_json).read_text())
    passed  = sum(1 for r in results if r["passed"])
    failed  = len(results) - passed

    rows = "".join(
        f'<tr><td><code>{r["script"]}</code></td>'
        f'<td><span class="badge" style="background:{"#dcfce7" if r["passed"] else "#fee2e2"};'
        f'color:{"#166534" if r["passed"] else "#991b1b"}">'
        f'{"PASS" if r["passed"] else "FAIL"}</span></td></tr>'
        for r in results
    )

    html = HTML.format(date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                       passed=passed, failed=failed, rows=rows)
    Path(args.out).write_text(html)
    print(f"Report written to {args.out}")

if __name__ == "__main__":
    main()
