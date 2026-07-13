#!/usr/bin/env python3
"""Install a user-level systemd timer for daily English reminders."""

import argparse
import re
import subprocess
from pathlib import Path


UNIT_NAME = "english-work-abroad-coach"


def skill_root():
    return Path(__file__).resolve().parents[1]


def validate_time(value):
    if not re.match(r"^[0-2][0-9]:[0-5][0-9]$", value):
        raise ValueError("Time must be HH:MM, for example 21:00")
    hour, minute = [int(part) for part in value.split(":")]
    if hour > 23 or minute > 59:
        raise ValueError("Time must be a valid 24-hour HH:MM value")
    return value


def build_systemd_units(root, reminder_time):
    root = Path(root).resolve()
    reminder_time = validate_time(reminder_time)
    python = root / ".venv" / "bin" / "python"
    runner = root / "scripts" / "reminder_runner.py"
    service = """[Unit]
Description=English Work Abroad Coach reminder

[Service]
Type=oneshot
WorkingDirectory=%s
ExecStart=%s %s --root %s
""" % (root, python, runner, root)
    timer = """[Unit]
Description=Daily English Work Abroad Coach reminder

[Timer]
OnCalendar=*-*-* %s:00
Persistent=true

[Install]
WantedBy=timers.target
""" % reminder_time
    return {"service": service, "timer": timer}


def unit_paths(systemd_user_dir):
    base = Path(systemd_user_dir).expanduser()
    return {
        "service": base / ("%s.service" % UNIT_NAME),
        "timer": base / ("%s.timer" % UNIT_NAME),
    }


def write_units(root, reminder_time, systemd_user_dir):
    paths = unit_paths(systemd_user_dir)
    units = build_systemd_units(root, reminder_time)
    paths["service"].parent.mkdir(parents=True, exist_ok=True)
    paths["service"].write_text(units["service"], encoding="utf-8")
    paths["timer"].write_text(units["timer"], encoding="utf-8")
    return paths


def run(command, dry_run=False):
    print("+ " + " ".join(command))
    if not dry_run:
        subprocess.run(command, check=True)


def install(root, reminder_time="21:00", dry_run=False, systemd_user_dir=None, enable=True):
    root = Path(root).resolve()
    if not (root / ".venv" / "bin" / "python").exists():
        raise FileNotFoundError("Missing .venv. Run scripts/bootstrap.py first.")
    systemd_dir = Path(systemd_user_dir).expanduser() if systemd_user_dir else Path.home() / ".config" / "systemd" / "user"
    paths = write_units(root, reminder_time, systemd_dir)
    if enable:
        run(["systemctl", "--user", "daemon-reload"], dry_run=dry_run)
        run(["systemctl", "--user", "enable", "--now", "%s.timer" % UNIT_NAME], dry_run=dry_run)
    return paths


def build_parser():
    parser = argparse.ArgumentParser(description="Install a daily user-level systemd reminder timer.")
    parser.add_argument("--root", default=str(skill_root()))
    parser.add_argument("--time", default="21:00", help="Daily reminder time in HH:MM. Default: 21:00.")
    parser.add_argument("--systemd-user-dir", help="Override unit output directory for testing.")
    parser.add_argument("--dry-run", action="store_true", help="Write unit files but do not enable the timer.")
    parser.add_argument("--no-enable", action="store_true", help="Write unit files but do not run systemctl.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    paths = install(
        args.root,
        args.time,
        dry_run=args.dry_run,
        systemd_user_dir=args.systemd_user_dir,
        enable=not args.no_enable,
    )
    print("Installed %s" % paths["service"])
    print("Installed %s" % paths["timer"])
    if args.no_enable:
        print("Timer not enabled because --no-enable was passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
