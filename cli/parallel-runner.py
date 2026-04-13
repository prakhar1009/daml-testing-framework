#!/usr/bin/env python3
# Copyright (c) 2024 Digital Asset (Switzerland) GmbH and/or its affiliates. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Daml Test Parallel Runner

This script discovers and runs Daml Script tests in parallel, distributing them
across multiple processes to significantly speed up test suite execution.

It provides a summary of test results and detailed output for failed tests.
"""

import argparse
import glob
import multiprocessing
import os
import subprocess
import sys
import time
from typing import List, NamedTuple, Tuple

# --- Constants for colored output ---
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_color(color: str, *args, **kwargs):
    """Prints messages in a specified color."""
    if sys.stdout.isatty():
        print(color, end="")
        print(*args, **kwargs)
        print(Colors.ENDC, end="")
    else:
        print(*args, **kwargs)

# --- Data Structures ---
class TestResult(NamedTuple):
    """Represents the outcome of a single test file execution."""
    file_path: str
    return_code: int
    stdout: str
    stderr: str
    duration: float

# --- Worker Function ---
def run_dpm_test(file_path: str) -> TestResult:
    """
    Executes 'dpm test' for a single Daml file and captures the result.

    Args:
        file_path: The path to the Daml test file.

    Returns:
        A TestResult tuple containing the execution details.
    """
    command = ["dpm", "test", "--files", file_path]
    start_time = time.monotonic()
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            encoding='utf-8'
        )
        duration = time.monotonic() - start_time
        return TestResult(
            file_path=file_path,
            return_code=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
            duration=duration,
        )
    except FileNotFoundError:
        duration = time.monotonic() - start_time
        return TestResult(
            file_path=file_path,
            return_code=1,
            stdout="",
            stderr="Error: 'dpm' command not found. Is DPM installed and in your PATH?",
            duration=duration,
        )
    except Exception as e:
        duration = time.monotonic() - start_time
        return TestResult(
            file_path=file_path,
            return_code=1,
            stdout="",
            stderr=f"An unexpected error occurred while running the test: {e}",
            duration=duration,
        )

# --- Main Application Logic ---
def main():
    """Main entry point for the parallel test runner script."""
    parser = argparse.ArgumentParser(
        description="Run Daml Script tests in parallel.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="daml",
        help="Directory to search for Daml test files (default: 'daml')."
    )
    parser.add_argument(
        "-p", "--pattern",
        default="**/*Test.daml",
        help="Glob pattern to match test files recursively (default: '**/*Test.daml')."
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=multiprocessing.cpu_count(),
        help=f"Number of parallel worker processes to use (default: CPU count = {multiprocessing.cpu_count()})."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print output for all tests, including successful ones."
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output."
    )

    args = parser.parse_args()

    if args.no_color:
        # pylint: disable=redefined-builtin,redefining-built-in
        global print_color
        print_color = print

    # 1. Discover test files
    search_path = os.path.join(args.directory, args.pattern)
    test_files = sorted(glob.glob(search_path, recursive=True))

    if not test_files:
        print_color(Colors.WARNING, f"No test files found matching pattern '{args.pattern}' in directory '{args.directory}'.")
        sys.exit(0)

    num_tests = len(test_files)
    print_color(Colors.HEADER, f"Found {num_tests} test file(s). Running with {args.workers} worker(s).")
    print("-" * 70)

    # 2. Run tests in parallel
    start_time = time.monotonic()
    passed_tests = []
    failed_tests = []

    with multiprocessing.Pool(processes=args.workers) as pool:
        # Use imap_unordered to get results as they complete
        results_iterator = pool.imap_unordered(run_dpm_test, test_files)
        
        for i, result in enumerate(results_iterator):
            if result.return_code == 0:
                passed_tests.append(result)
                print_color(Colors.OKGREEN, f"✓ PASSSED ({result.duration:.2f}s): {result.file_path}")
                if args.verbose:
                    print(result.stdout)
                    print(result.stderr)
            else:
                failed_tests.append(result)
                print_color(Colors.FAIL, f"✗ FAILED  ({result.duration:.2f}s): {result.file_path}")

    total_duration = time.monotonic() - start_time

    # 3. Report results
    print("\n" + "=" * 70)
    print_color(Colors.BOLD, "TEST FAILURE DETAILS")
    print("=" * 70)

    if not failed_tests:
        print("All tests passed.")
    else:
        for result in failed_tests:
            print_color(Colors.FAIL, f"\n--- Failure in: {result.file_path} ---")
            if result.stdout:
                print("\n[STDOUT]")
                print(result.stdout.strip())
            if result.stderr:
                print("\n[STDERR]")
                print(result.stderr.strip())
            print_color(Colors.FAIL, "--- End of Failure Report ---")

    print("\n" + "=" * 70)
    print_color(Colors.BOLD, "SUMMARY")
    print("=" * 70)

    num_passed = len(passed_tests)
    num_failed = len(failed_tests)

    print(f"Total tests run: {num_tests}")
    print(f"Total time:      {total_duration:.2f}s")
    print_color(Colors.OKGREEN, f"Passed:          {num_passed}")
    print_color(Colors.FAIL,   f"Failed:          {num_failed}")

    # 4. Exit with appropriate status code
    if failed_tests:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()