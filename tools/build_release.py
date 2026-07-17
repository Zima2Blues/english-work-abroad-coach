#!/usr/bin/env python3
"""Build sanitized, self-contained release archives for each skill platform."""

import argparse
import shlex
import subprocess
import sys
import zipfile
from pathlib import Path


DISTRIBUTIONS = ("claudecode-codex-opencode", "openclaw", "hermes")
RELEASE_VERSION = "0.2.0"
PACKAGE_ROOT = "english-work-abroad-coach"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
EXCLUDED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "tests",
    "venv",
}
EXCLUDED_DATA_FILES = {
    Path("data/checkins.jsonl"),
    Path("data/plan.json"),
    Path("data/progress.json"),
    Path("data/reminder.log"),
}


def archive_filename(distribution):
    """Return the versioned filename for one platform archive."""
    return "%s-%s-%s.zip" % (PACKAGE_ROOT, RELEASE_VERSION, distribution)


def release_python(root):
    """Prefer the canonical distribution's local development environment."""
    root = Path(root).resolve()
    candidates = (
        root / "claudecode-codex-opencode" / ".venv" / "bin" / "python",
        root / "claudecode-codex-opencode" / ".venv" / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return Path(sys.executable)


def run_command(command, root, env=None):
    """Run one preflight command and return its exit status."""
    command = [str(part) for part in command]
    print("+ %s" % shlex.join(command), flush=True)
    completed = subprocess.run(command, cwd=str(root), env=env, check=False)
    return completed.returncode


def run_preflight(root):
    """Check synchronization and project health before packaging a distribution."""
    root = Path(root).resolve()
    python = release_python(root)
    commands = (
        [python, root / "tools" / "sync_distributions.py", "--root", root, "--check"],
        [
            python,
            root / "tools" / "verify_project.py",
            "--root",
            root,
            "--python",
            python,
            "--exclude-release-tests",
        ],
    )
    for command in commands:
        if run_command(command, root):
            return 1
    return 0


def should_package(path, source):
    """Return whether a source file is safe to include in a public archive."""
    relative = path.relative_to(source)
    if any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
        return False
    if relative in EXCLUDED_DATA_FILES:
        return False

    name = path.name
    if name in {"coach.db", "checkins.jsonl", "reminder.log"}:
        return False
    if name.startswith("coach.db-"):
        return False
    if path.suffix.lower() in {".db", ".pyc", ".pyo", ".sqlite", ".sqlite3"}:
        return False
    return True


def package_files(source):
    """Return release files in a deterministic archive order."""
    return [
        path
        for path in sorted(source.rglob("*"), key=lambda item: item.relative_to(source).as_posix())
        if path.is_file() and not path.is_symlink() and should_package(path, source)
    ]


def write_directory(archive, name):
    """Write a deterministic root-directory entry to a ZIP archive."""
    info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
    info.create_system = 3
    info.external_attr = (0o40755 << 16) | 0x10
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, b"", compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def write_file(archive, source, path):
    """Write one source file with fixed archive metadata."""
    relative = path.relative_to(source).as_posix()
    info = zipfile.ZipInfo("%s/%s" % (PACKAGE_ROOT, relative), date_time=ZIP_TIMESTAMP)
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(
        info,
        path.read_bytes(),
        compress_type=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    )


def build_release(root: Path, distribution: str, output_dir: Path) -> Path:
    """Build one sanitized, self-contained platform ZIP."""
    root = Path(root).resolve()
    output_dir = Path(output_dir)
    if distribution not in DISTRIBUTIONS:
        raise ValueError("Unknown distribution: %s" % distribution)

    source = root / distribution
    if not source.is_dir():
        raise FileNotFoundError("Distribution directory is required: %s" % source)
    if run_preflight(root):
        raise RuntimeError("release preflight failed")

    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / archive_filename(distribution)
    temporary_archive = output_dir / (archive.name + ".tmp")
    try:
        with zipfile.ZipFile(
            temporary_archive,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as package:
            write_directory(package, PACKAGE_ROOT + "/")
            for path in package_files(source):
                write_file(package, source, path)
        temporary_archive.replace(archive)
    finally:
        temporary_archive.unlink(missing_ok=True)
    return archive


def publish_check(root):
    """Require an explicit repository license before a public release."""
    if not (Path(root).resolve() / "LICENSE").is_file():
        print("LICENSE file is required for public release", file=sys.stderr)
        return 1
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Build English Work Abroad Coach release archives.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output-dir", default="dist")
    parser.add_argument("--distribution", choices=DISTRIBUTIONS)
    parser.add_argument("--all", action="store_true", help="Build every platform archive.")
    parser.add_argument(
        "--publish-check",
        action="store_true",
        help="Require a LICENSE file before a public release.",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    if args.publish_check:
        return publish_check(root)

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    if args.all:
        distributions = DISTRIBUTIONS
    elif args.distribution:
        distributions = (args.distribution,)
    else:
        build_parser().error("select --distribution or --all")

    for distribution in distributions:
        archive = build_release(root, distribution, output_dir)
        print("BUILT: %s" % archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
