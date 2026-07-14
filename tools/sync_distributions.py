#!/usr/bin/env python3
"""Check or synchronize files shared by all skill distributions."""

import argparse
import shutil
from pathlib import Path


CANONICAL_DISTRIBUTION = "claudecode-codex-opencode"
TARGET_DISTRIBUTIONS = ("openclaw", "hermes")
SHARED_PATHS = (
    "requirements-dev.txt",
    "scripts/bootstrap.py",
    "scripts/english_coach.py",
    "scripts/reminder_runner.py",
    "references/learning-science.md",
    "references/material-sources.md",
    "references/plan-system.md",
    "tests/test_runtime_smoke.py",
)


def find_mismatches(root):
    """Return shared files whose bytes differ from the canonical version."""
    root = Path(root).resolve()
    mismatches = []
    for distribution in TARGET_DISTRIBUTIONS:
        for relative in SHARED_PATHS:
            source = root / CANONICAL_DISTRIBUTION / relative
            target = root / distribution / relative
            if not source.is_file():
                raise FileNotFoundError("Missing canonical shared file: %s" % source)
            if not target.is_file() or target.read_bytes() != source.read_bytes():
                mismatches.append("%s/%s" % (distribution, relative))
    return mismatches


def synchronize(root):
    """Copy canonical shared files to platform distributions."""
    root = Path(root).resolve()
    copied = []
    for distribution in TARGET_DISTRIBUTIONS:
        for relative in SHARED_PATHS:
            source = root / CANONICAL_DISTRIBUTION / relative
            target = root / distribution / relative
            if not source.is_file():
                raise FileNotFoundError("Missing canonical shared file: %s" % source)
            if not target.is_file() or target.read_bytes() != source.read_bytes():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(str(source), str(target))
                copied.append(target)
    return copied


def build_parser():
    parser = argparse.ArgumentParser(description="Synchronize shared skill distribution files.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Report drift without writing files.")
    mode.add_argument("--write", action="store_true", help="Copy canonical files to each target.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    if args.check:
        mismatches = find_mismatches(root)
        if mismatches:
            for relative in mismatches:
                print("DRIFT: %s" % relative)
            return 1
        print("Shared files are synchronized.")
        return 0

    copied = synchronize(root)
    for path in copied:
        print("COPIED: %s" % path.relative_to(root.resolve()))
    print("Synchronized %s shared files." % len(copied))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
