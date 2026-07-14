#!/usr/bin/env python3
"""Validate the local Agent Skill metadata used by this repository."""

import argparse
import re
from pathlib import Path

import yaml


FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.DOTALL)
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_skill(skill_dir):
    """Return validation errors for one skill distribution."""
    skill_dir = Path(skill_dir)
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return ["SKILL.md is required"]

    text = skill_file.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return ["SKILL.md must start with YAML frontmatter"]

    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return ["frontmatter is invalid YAML: %s" % exc]

    if not isinstance(metadata, dict):
        return ["frontmatter must be a YAML mapping"]

    errors = []
    name = metadata.get("name")
    description = metadata.get("description")
    if not isinstance(name, str) or not name.strip():
        errors.append("name is required")
    elif not SKILL_NAME_RE.fullmatch(name):
        errors.append("name must contain lowercase letters, digits, and hyphens only")
    if not isinstance(description, str) or not description.strip():
        errors.append("description is required")

    platform_metadata = metadata.get("metadata")
    if skill_dir.name == "openclaw":
        if not isinstance(platform_metadata, dict) or not isinstance(platform_metadata.get("openclaw"), dict):
            errors.append("metadata.openclaw is required for the OpenClaw distribution")
    if skill_dir.name == "hermes":
        if not isinstance(platform_metadata, dict) or not isinstance(platform_metadata.get("hermes"), dict):
            errors.append("metadata.hermes is required for the Hermes distribution")
    return errors


def build_parser():
    parser = argparse.ArgumentParser(description="Validate one local skill distribution.")
    parser.add_argument("skill_dir", help="Path containing SKILL.md.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    errors = validate_skill(Path(args.skill_dir))
    if errors:
        for error in errors:
            print("ERROR: %s" % error)
        return 1
    print("Skill is valid!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
