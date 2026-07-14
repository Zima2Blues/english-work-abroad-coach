#!/usr/bin/env python3
"""Create a local virtual environment and install this skill's dependencies."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


MIN_PYTHON = (3, 9)


def skill_root():
    return Path(__file__).resolve().parents[1]


def probe_python_version(python_executable):
    """Return the version tuple reported by a selected Python executable."""
    command = [
        str(python_executable),
        "-c",
        "import sys; print('.'.join(str(part) for part in sys.version_info[:3]))",
    ]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Unable to run selected Python interpreter %s: %s" % (python_executable, exc))
    try:
        return tuple(int(part) for part in completed.stdout.strip().split("."))
    except ValueError:
        raise RuntimeError(
            "Selected Python interpreter %s returned an invalid version: %s"
            % (python_executable, completed.stdout.strip())
        )


def require_supported_python(version_info=None, python_executable=None):
    """Reject interpreters older than the project's supported minimum."""
    version = tuple(version_info or sys.version_info[:3])
    executable = str(python_executable or sys.executable)
    if version < MIN_PYTHON:
        raise RuntimeError(
            "Python 3.9 or newer is required; selected interpreter %s is Python %s. "
            "Run 'uv python install 3.12' and rerun bootstrap with that interpreter."
            % (executable, ".".join(str(part) for part in version))
        )
    return version


def venv_python_path(venv_dir):
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def build_bootstrap_plan(root, python_executable, venv_name=".venv"):
    root = Path(root).resolve()
    venv_dir = root / venv_name
    venv_python = venv_python_path(venv_dir)
    requirements_dev = root / "requirements-dev.txt"
    tests = root / "tests"
    return {
        "root": str(root),
        "python": str(python_executable),
        "venv_dir": str(venv_dir),
        "venv_python": str(venv_python),
        "requirements_dev": str(requirements_dev),
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
        "install_dev_requirements": [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_dev),
        ],
        "run_runtime_tests": [
            str(venv_python),
            "-m",
            "unittest",
            "discover",
            "-s",
            str(tests),
            "-p",
            "test_runtime_smoke.py",
            "-v",
        ],
        "run_dev_tests": [str(venv_python), "-m", "unittest", "discover", "-s", str(tests)],
        "quick_check": [str(venv_python), str(root / "scripts" / "english_coach.py"), "--root", str(root), "today", "--json"],
    }


def run(command, dry_run=False):
    print("+ " + " ".join(command), flush=True)
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


def bootstrap(
    root,
    python_executable,
    venv_name=".venv",
    dry_run=False,
    skip_install=False,
    skip_tests=False,
    dev=False,
):
    root = Path(root).resolve()
    selected_version = probe_python_version(python_executable)
    require_supported_python(selected_version, python_executable)
    plan = build_bootstrap_plan(root, python_executable, venv_name)
    requirements_dev = Path(plan["requirements_dev"])

    if dev and not skip_install and not requirements_dev.exists():
        raise FileNotFoundError("Missing development requirements file: %s" % requirements_dev)

    create_venv(plan, dry_run=dry_run)
    if dev and not skip_install:
        run(plan["install_dev_requirements"], dry_run=dry_run)
    if not skip_tests:
        run(plan["run_runtime_tests"], dry_run=dry_run)
        if dev:
            run(plan["run_dev_tests"], dry_run=dry_run)
        run(plan["quick_check"], dry_run=dry_run)
    plan["python_version"] = ".".join(str(part) for part in selected_version)
    plan["dev"] = bool(dev)
    return plan


def build_parser():
    parser = argparse.ArgumentParser(description="Bootstrap the English Work Abroad Coach skill.")
    parser.add_argument("--root", default=str(skill_root()), help="Skill folder path.")
    parser.add_argument("--python", default=sys.executable, help="Python executable used to create .venv.")
    parser.add_argument("--venv-name", default=".venv", help="Virtual environment folder name under the skill root.")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies and run all tests.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    parser.add_argument("--skip-install", action="store_true", help="With --dev, skip development dependency install.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip self-tests after install.")
    parser.add_argument("--json", action="store_true", help="Print the bootstrap plan as JSON.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        plan = bootstrap(
            args.root,
            args.python,
            venv_name=args.venv_name,
            dry_run=args.dry_run,
            skip_install=args.skip_install,
            skip_tests=args.skip_tests,
            dev=args.dev,
        )
    except RuntimeError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("Bootstrap plan complete. Use %s for this skill." % plan["venv_python"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
