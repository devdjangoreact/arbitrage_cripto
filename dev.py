#!/usr/bin/env python3
"""
Development helper script for the arbitrage crypto project.

This script provides common development tasks like formatting, linting, and testing.
"""

import subprocess
import sys


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n[RUNNING] {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"[OK] {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def format_code():
    """Format code with Black and organize imports with isort."""
    success = True
    success &= run_command(
        ["venv/Scripts/isort.exe", ".", "--profile", "black"],
        "Organizing imports with isort",
    )
    success &= run_command(
        ["venv/Scripts/black.exe", "."], "Formatting code with Black"
    )
    return success


def lint_code():
    """Lint code with Ruff and Pylint."""
    success = True
    success &= run_command(["venv/Scripts/ruff.exe", "check", "."], "Linting with Ruff")
    success &= run_command(
        [
            "venv/Scripts/pylint.exe",
            ".",
        ],
        "Linting with Pylint",
    )
    return success


def type_check():
    """Run type checking with MyPy."""
    return run_command(
        [
            "venv/Scripts/mypy.exe",
            ".",
        ],
        "Type checking with MyPy",
    )


def run_tests():
    """Run tests with pytest."""
    return run_command(
        [
            "venv/Scripts/pytest.exe",
            "tests/",
            "-v",
            "--cov=app",
            "--cov-report=term-missing",
        ],
        "Running tests with pytest",
    )


def run_all_checks():
    """Run all development checks."""
    print("[START] Running all development checks...")
    success = True
    success &= format_code()
    success &= lint_code()
    success &= type_check()
    success &= run_tests()

    if success:
        print("\n[SUCCESS] All checks passed!")
    else:
        print("\n[FAILED] Some checks failed!")
        sys.exit(1)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python dev.py <command>")
        print("Commands:")
        print("  format    - Format code with Black and isort")
        print("  lint      - Lint code with Ruff and Pylint")
        print("  typecheck - Run type checking with MyPy")
        print("  test      - Run tests with pytest")
        print("  all       - Run all checks")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "format":
        format_code()
    elif command == "lint":
        lint_code()
    elif command == "typecheck":
        type_check()
    elif command == "test":
        run_tests()
    elif command == "all":
        run_all_checks()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
