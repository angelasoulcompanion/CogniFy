#!/usr/bin/env python3
"""
CogniFy Test Runner
Comprehensive test execution with detailed reporting

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run unit tests only
    python run_tests.py --api              # Run API tests only
    python run_tests.py --e2e              # Run E2E tests only
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --verbose          # Verbose output
    python run_tests.py --fast             # Skip slow tests

Created with love by Angela & David - 3 January 2026
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path


# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a styled header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_section(text: str):
    """Print a section header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}>>> {text}{Colors.ENDC}")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")


def run_command(cmd: list, description: str) -> tuple[int, str]:
    """Run a command and return exit code and output"""
    print_section(description)
    print(f"{Colors.BLUE}$ {' '.join(cmd)}{Colors.ENDC}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            cwd=Path(__file__).parent
        )
        return result.returncode, ""
    except Exception as e:
        return 1, str(e)


def check_prerequisites():
    """Check if all prerequisites are met"""
    print_section("Checking Prerequisites")

    issues = []

    # Check Python version
    if sys.version_info < (3, 10):
        issues.append(f"Python 3.10+ required, found {sys.version}")

    # Check pytest
    try:
        import pytest
        print_success(f"pytest {pytest.__version__} found")
    except ImportError:
        issues.append("pytest not installed. Run: pip install pytest pytest-asyncio")

    # Check httpx
    try:
        import httpx
        print_success(f"httpx found")
    except ImportError:
        issues.append("httpx not installed. Run: pip install httpx")

    # Check pytest-asyncio
    try:
        import pytest_asyncio
        print_success(f"pytest-asyncio found")
    except ImportError:
        issues.append("pytest-asyncio not installed. Run: pip install pytest-asyncio")

    # Check if tests directory exists
    tests_dir = Path(__file__).parent / "tests"
    if tests_dir.exists():
        test_files = list(tests_dir.glob("test_*.py"))
        print_success(f"Found {len(test_files)} test files")
    else:
        issues.append("tests/ directory not found")

    return issues


def count_tests():
    """Count total number of tests"""
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q", "tests/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        # Parse output to count tests
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'test' in line.lower() and 'selected' in line.lower():
                return line
        return "Unknown number of tests"
    except:
        return "Could not count tests"


def main():
    parser = argparse.ArgumentParser(description="CogniFy Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--e2e", action="store_true", help="Run E2E tests only")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--file", "-f", type=str, help="Run specific test file")

    args = parser.parse_args()

    # Print header
    print_header("CogniFy Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check prerequisites
    issues = check_prerequisites()
    if issues:
        print_error("Prerequisites check failed:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)

    # Count tests
    print_section("Test Summary")
    print(count_tests())

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test path
    if args.file:
        cmd.append(f"tests/{args.file}")
    elif args.unit:
        cmd.extend(["tests/test_security.py", "tests/test_entities.py"])
    elif args.api:
        cmd.extend([
            "tests/test_api_auth.py",
            "tests/test_api_documents.py",
            "tests/test_api_chat.py",
            "tests/test_api_search.py",
            "tests/test_api_connectors.py",
            "tests/test_api_admin.py",
            "tests/test_api_prompts.py"
        ])
    elif args.e2e:
        cmd.append("tests/test_e2e_workflow.py")
    else:
        cmd.append("tests/")

    # Add options
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-v")  # Always show some verbosity

    if args.fast:
        cmd.extend(["-m", "not slow"])

    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])

    if args.html:
        cmd.extend(["--html=test_report.html", "--self-contained-html"])

    # Add useful options
    cmd.extend([
        "--tb=short",           # Shorter tracebacks
        "--strict-markers",     # Strict marker checking
        "-x",                   # Stop on first failure (optional)
        "--color=yes"           # Color output
    ])

    # Remove -x if running all tests
    if not args.file:
        cmd.remove("-x")

    # Run tests
    print_header("Running Tests")
    exit_code, error = run_command(cmd, "Executing pytest")

    # Print summary
    print_header("Test Results Summary")

    if exit_code == 0:
        print_success("All tests passed!")
    elif exit_code == 1:
        print_error("Some tests failed")
    elif exit_code == 2:
        print_error("Test execution was interrupted")
    elif exit_code == 3:
        print_error("Internal error during test collection")
    elif exit_code == 4:
        print_error("pytest command line usage error")
    elif exit_code == 5:
        print_warning("No tests were collected")
    else:
        print_error(f"Tests finished with exit code: {exit_code}")

    if error:
        print_error(f"Error: {error}")

    # Print next steps
    print_section("Next Steps")
    if exit_code != 0:
        print("1. Review failed tests above")
        print("2. Fix the issues in your code")
        print("3. Run tests again: python run_tests.py")
    else:
        print("All tests passed! You can:")
        print("1. Run with coverage: python run_tests.py --coverage")
        print("2. Generate HTML report: python run_tests.py --html")
        print("3. Run E2E tests: python run_tests.py --e2e")

    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
