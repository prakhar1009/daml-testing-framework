#!/usr/bin/env python3
"""Daml Testing Framework — scenario test runner with timeout handling."""
import subprocess
import sys
import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

DEFAULT_TIMEOUT = 120  # seconds per script

def run_script(dar: Path, script_name: str, host: str, port: int,
               timeout: int = DEFAULT_TIMEOUT) -> dict:
    cmd = [
        "daml", "script",
        "--dar", str(dar),
        "--script-name", script_name,
        "--ledger-host", host,
        "--ledger-port", str(port),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "script": script_name,
            "passed": result.returncode == 0,
            "output": result.stdout[:2000],
            "error":  result.stderr[:2000],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "script": script_name,
            "passed": False,
            "output": "",
            "error": f"Timed out after {timeout}s",
            "timed_out": True,
        }

def discover_scripts(dar: Path) -> list[str]:
    result = subprocess.run(
        ["daml", "inspect-dar", str(dar), "--json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return []
    data = json.loads(result.stdout)
    return [s for s in data.get("scripts", []) if s.endswith("Test")]

def main():
    parser = argparse.ArgumentParser(description="Daml Testing Framework runner")
    parser.add_argument("dar",  help="Path to the compiled DAR file")
    parser.add_argument("--host",    default="localhost")
    parser.add_argument("--port",    default=6865, type=int)
    parser.add_argument("--workers", default=4, type=int)
    parser.add_argument("--timeout", default=DEFAULT_TIMEOUT, type=int)
    parser.add_argument("--json",    action="store_true")
    parser.add_argument("--out",     default=None)
    args = parser.parse_args()

    dar     = Path(args.dar)
    scripts = discover_scripts(dar)
    if not scripts:
        print("No test scripts found.", file=sys.stderr)
        sys.exit(1)

    print(f"Running {len(scripts)} tests | workers={args.workers} | timeout={args.timeout}s")
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(run_script, dar, s, args.host, args.port, args.timeout): s
            for s in scripts
        }
        for future in as_completed(futures):
            r = future.result()
            results.append(r)
            icon = "✅" if r["passed"] else ("⏱" if r.get("timed_out") else "❌")
            print(f"  {icon} {r['script']}")

    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    print(f"\nResults: {passed} passed, {failed} failed")

    if args.out:
        Path(args.out).write_text(json.dumps(results, indent=2))

    if args.json:
        print(json.dumps(results, indent=2))

    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
