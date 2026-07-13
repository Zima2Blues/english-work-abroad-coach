#!/usr/bin/env python3
"""Create a local virtual environment and install this skill's dependencies."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def skill_root():
    return Path(__file__).resolve().parents[1]


def venv_python_path(venv_dir):
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def build_bootstrap_plan(root, python_executable, venv_name=".venv"):
    root = Path(root).resolve()
    venv_dir = root / venv_name
    venv_python = venv_python_path(venv_dir)
    requirements = root / "requirements.txt"
    tests = root / "tests"
    return {
        "root": str(root),
        "python": str(python_executable),
        "venv_dir": str(venv_dir),
        "venv_python": str(venv_python),
        "requirements": str(requirements),
        "create_venv": [str(python_executable), "-m", "venv", str(venv_dir)],
        "create_venv_uv": [
            shutil.which("uv") or "uv",
            "venv",
            str(venv_dir),
            "--python",
            str(python_executable),
            "--clear",
            "--seed",
        ],
        "upgrade_pip": [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
        "install_requirements": [str(venv_python), "-m", "pip", "install", "-r", str(requirements)],
        "run_tests": [str(venv_python), "-m", "unittest", "discover", "-s", str(tests)],
        "quick_check": [str(venv_python), str(root / "scripts" / "english_coach.py"), "--root", str(root), "today", "--json"],
    }


def run(command, dry_run=False):
    print("+ " + " ".join(command))
    if dry_run:
        return
    subprocess.run(command, check=True)


def create_venv(plan, dry_run=False):
    try:
        run(plan["create_venv"], dry_run=dry_run)
    except subprocess.CalledProcessError as exc:
        if not shutil.which("uv"):
            raise
        print("Standard venv failed with exit code %s; retrying with uv." % exc.returncode)
        run(plan["create_venv_uv"], dry_run=dry_run)


def bootstrap(root, python_executable, venv_name=".venv", dry_run=False, skip_install=False, skip_tests=False):
    root = Path(root).resolve()
    plan = build_bootstrap_plan(root, python_executable, venv_name)
    requirements = Path(plan["requirements"])

    if not requirements.exists():
        raise FileNotFoundError("Missing requirements file: %s" % requirements)

    create_venv(plan, dry_run=dry_run)
    if not skip_install:
        run(plan["upgrade_pip"], dry_run=dry_run)
        run(plan["install_requirements"], dry_run=dry_run)
    if not skip_tests:
        run(plan["run_tests"], dry_run=dry_run)
        run(plan["quick_check"], dry_run=dry_run)
    return plan


def build_parser():
    parser = argparse.ArgumentParser(description="Bootstrap the English Work Abroad Coach skill.")
    parser.add_argument("--root", default=str(skill_root()), help="Skill folder path.")
    parser.add_argument("--python", default=sys.executable, help="Python executable used to create .venv.")
    parser.add_argument("--venv-name", default=".venv", help="Virtual environment folder name under the skill root.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    parser.add_argument("--skip-install", action="store_true", help="Create the venv but skip pip install.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip self-tests after install.")
    parser.add_argument("--json", action="store_true", help="Print the bootstrap plan as JSON.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    plan = bootstrap(
        args.root,
        args.python,
        venv_name=args.venv_name,
        dry_run=args.dry_run,
        skip_install=args.skip_install,
        skip_tests=args.skip_tests,
    )
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("Bootstrap plan complete. Use %s for this skill." % plan["venv_python"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
