#!/usr/bin/env python3
"""Run one English study reminder and optionally send a desktop notification."""

import argparse
import importlib.util
import json
import shutil
import subprocess
from datetime import date
from pathlib import Path


def load_english_coach():
    script = Path(__file__).resolve().parent / "english_coach.py"
    spec = importlib.util.spec_from_file_location("english_coach", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_reminder_result(root, target_date=None):
    english_coach = load_english_coach()
    target = english_coach.parse_date(target_date or date.today())
    completed = {entry["date"] for entry in english_coach.load_checkins(root)}
    return {
        "date": target.isoformat(),
        "checked_in": target.isoformat() in completed,
        "task": english_coach.generate_today_task(root, target),
    }


def build_notification(result):
    task = result["task"]
    if result["checked_in"]:
        return (
            "English check-in completed",
            "Day %s is already checked in." % task["day_number"],
        )
    return (
        "English check-in missing",
        "Day %s: %s min, %s. Finish listening, speaking, expressions, and reflection."
        % (task["day_number"], task["minutes"], task["theme"]),
    )


def append_log(root, result, title, body):
    log_path = Path(root) / "data" / "reminder.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "date": result["date"],
        "checked_in": result["checked_in"],
        "title": title,
        "body": body,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n")


def notify(title, body):
    notify_send = shutil.which("notify-send")
    if not notify_send:
        return False
    subprocess.run([notify_send, title, body], check=False)
    return True


def build_parser():
    parser = argparse.ArgumentParser(description="Run one English Work Abroad Coach reminder.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--date", help="YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--notify-completed", action="store_true", help="Also notify when already checked in.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    result = build_reminder_result(root, args.date)
    title, body = build_notification(result)
    append_log(root, result, title, body)
    notified = False
    if not result["checked_in"] or args.notify_completed:
        notified = notify(title, body)
    output = dict(result)
    output["notification"] = {"title": title, "body": body, "sent": notified}
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("%s: %s" % (title, body))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
