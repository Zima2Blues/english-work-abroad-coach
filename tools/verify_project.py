#!/usr/bin/env python3
"""Run repository tests and skill metadata validation."""

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Optional


DISTRIBUTIONS = ("claudecode-codex-opencode", "openclaw", "hermes")


def build_verification_plan(root):
    """Return deterministic project checks configured for the current milestone."""
    root = Path(root).resolve()
    tests = [
        {"name": name, "path": root / name / "tests"}
        for name in DISTRIBUTIONS
    ]
    skill_validation = [root / name for name in DISTRIBUTIONS]
    sync_script = root / "tools" / "sync_distributions.py"
    sync = [[str(sync_script), "--check"]] if sync_script.is_file() else []
    return {
        "project_tests": root / "tests",
        "tests": tests,
        "skill_validation": skill_validation,
        "sync": sync,
    }


def run_command(command, cwd):
    """Run one command and return its exit status."""
    print("+ %s" % shlex.join([str(part) for part in command]), flush=True)
    completed = subprocess.run([str(part) for part in command], cwd=str(cwd), check=False)
    return completed.returncode


def run_external_validation(root, validator, python=None):
    """Run an optional external validator for every distribution."""
    if validator is None:
        print("SKIP: external skill validator not configured")
        return 0

    root = Path(root).resolve()
    python = python or sys.executable
    for name in DISTRIBUTIONS:
        result = run_command([python, validator, root / name], cwd=root)
        if result:
            return result
    return 0


def run_verification(root, python, validator: Optional[Path] = None):
    """Run every configured check and stop after the first failure."""
    root = Path(root).resolve()
    python = str(python)
    plan = build_verification_plan(root)

    result = run_command(
        [python, "-m", "unittest", "discover", "-s", plan["project_tests"], "-v"],
        cwd=root,
    )
    if result:
        return result

    for item in plan["tests"]:
        result = run_command(
            [python, "-m", "unittest", "discover", "-s", item["path"], "-v"],
            cwd=root,
        )
        if result:
            return result

    local_validator = root / "tools" / "validate_skill.py"
    for skill_dir in plan["skill_validation"]:
        result = run_command([python, local_validator, skill_dir], cwd=root)
        if result:
            return result

    for sync_command in plan["sync"]:
        result = run_command([python] + sync_command, cwd=root)
        if result:
            return result

    return run_external_validation(root, validator, python=python)


def build_parser():
    parser = argparse.ArgumentParser(description="Run all English coach project checks.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--validator", type=Path, help="Optional external quick_validate.py path.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return run_verification(args.root, args.python, validator=args.validator)


if __name__ == "__main__":
    raise SystemExit(main())
