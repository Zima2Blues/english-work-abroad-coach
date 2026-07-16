#!/usr/bin/env python3
"""Daily English coach utilities for plans, check-ins, and streaks."""

import argparse
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path


def load_coach_storage():
    """Load the sibling storage module in both script and spec-loaded contexts."""
    script = Path(__file__).resolve().parent / "coach_storage.py"
    spec = importlib.util.spec_from_file_location("english_coach_storage", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


coach_storage = load_coach_storage()
CoachStore = coach_storage.CoachStore
resolve_state_dir = coach_storage.resolve_state_dir


WEEKDAY_KEYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


DEFAULT_PLAN = {
    "start_date": "2026-07-14",
    "weekday_minutes": 30,
    "weekend_minutes": 60,
    "weekly_themes": {
        "monday": "professional self-introduction",
        "tuesday": "current work",
        "wednesday": "project story",
        "thursday": "workplace communication",
        "friday": "interview answer",
        "saturday": "deep practice",
        "sunday": "weekly review",
    },
    "material_sources": [
        {"name": "VOA Learning English", "use_for": "graded listening"},
        {"name": "British Council LearnEnglish", "use_for": "skills practice"},
        {"name": "Cambridge English activities", "use_for": "B1-C1 practice"},
        {"name": "BBC Learning English", "use_for": "workplace phrases"},
    ],
}
EXPORT_FORMAT_VERSION = 1


def parse_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def iso(value):
    return parse_date(value).isoformat()


def validate_minutes(value):
    """Return a supported session duration or raise a stable validation error."""
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        raise ValueError("minutes must be 30 or 60")
    if minutes not in (30, 60):
        raise ValueError("minutes must be 30 or 60")
    return minutes


def validate_summary_days(value):
    """Return a positive summary window length or raise a stable validation error."""
    try:
        days = int(value)
    except (TypeError, ValueError):
        raise ValueError("days must be at least 1")
    if days < 1:
        raise ValueError("days must be at least 1")
    return days


def parse_summary_days(value):
    """Adapt the shared summary validator to argparse's user-facing error format."""
    try:
        return validate_summary_days(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error))


def data_dir(root):
    return Path(root) / "data"


def default_plan_path(root):
    return data_dir(root) / "default-plan.json"


def load_default_plan(root):
    """Load and merge the read-only plan template bundled with the skill."""
    path = default_plan_path(root)
    if not path.exists():
        return dict(DEFAULT_PLAN)
    with path.open("r", encoding="utf-8") as handle:
        plan = json.load(handle)
    merged = dict(DEFAULT_PLAN)
    merged.update(plan)
    merged["weekly_themes"] = dict(DEFAULT_PLAN["weekly_themes"], **plan.get("weekly_themes", {}))
    merged["material_sources"] = plan.get("material_sources", DEFAULT_PLAN["material_sources"])
    return merged


def store_for(state_dir=None):
    """Return a store for an explicit or platform-default user state directory."""
    return CoachStore(resolve_state_dir(explicit=state_dir))


DOCTOR_REQUIRED_CHECKS = (
    "python_supported",
    "skill_root_readable",
    "state_dir_writable",
    "database_ready",
    "systemd_user_available",
)


def state_dir_is_writable(state_dir):
    """Test that the state directory accepts temporary user-owned files."""
    target = Path(state_dir)
    try:
        target.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=str(target)):
            pass
    except OSError:
        return False
    return True


def build_doctor_report(root, state_dir=None, command_exists=None, version_info=None):
    """Report readiness without running systemctl or sending a notification."""
    root = Path(root)
    state_dir = resolve_state_dir(explicit=state_dir)
    commands = command_exists or shutil.which
    version = tuple(version_info or sys.version_info[:3])
    state_writable = state_dir_is_writable(state_dir)
    database_ready = False
    if state_writable:
        try:
            CoachStore(state_dir).initialize()
            database_ready = True
        except (OSError, coach_storage.sqlite3.Error):
            database_ready = False

    notify_available = bool(commands("notify-send"))
    report = {
        "python_supported": version >= (3, 9),
        "skill_root_readable": root.is_dir()
        and os.access(str(root), os.R_OK | os.X_OK),
        "state_dir_writable": state_writable,
        "database_ready": database_ready,
        "notify_send_available": notify_available,
        "systemd_user_available": bool(commands("systemctl")),
        "warnings": [],
    }
    if not notify_available:
        report["warnings"].append(
            "notify-send is unavailable; reminders will only be logged."
        )
    return report


def doctor_exit_code(report):
    """Return failure only when a required diagnostic check is not ready."""
    return 0 if all(report[name] for name in DOCTOR_REQUIRED_CHECKS) else 1


def print_doctor_report(report):
    """Render the doctor report for interactive use."""
    for name in DOCTOR_REQUIRED_CHECKS:
        print("%s: %s" % (name, "ok" if report[name] else "failed"))
    print(
        "notify_send_available: %s"
        % ("ok" if report["notify_send_available"] else "unavailable")
    )
    for warning in report["warnings"]:
        print("WARNING: %s" % warning)


def load_plan(root, state_dir=None):
    """Load the user's plan, falling back to the read-only bundled template."""
    return store_for(state_dir).load_plan(load_default_plan(root))


def save_plan(root, plan, state_dir=None):
    """Save a user plan outside the read-only skill resource directory."""
    store_for(state_dir).save_plan(plan)


def validate_plan(plan):
    """Reject plan documents that cannot support the coach's fixed daily model."""
    if not isinstance(plan, dict):
        raise ValueError("plan must be a JSON object")
    try:
        parse_date(plan.get("start_date"))
    except (TypeError, ValueError):
        raise ValueError("plan start_date must use YYYY-MM-DD")
    for key in ("weekday_minutes", "weekend_minutes"):
        if plan.get(key) not in (30, 60):
            raise ValueError("plan %s must be 30 or 60" % key)
    themes = plan.get("weekly_themes")
    if not isinstance(themes, dict) or set(themes) != set(WEEKDAY_KEYS):
        raise ValueError("plan weekly_themes must define all seven weekdays")
    if any(not isinstance(themes[key], str) or not themes[key].strip() for key in WEEKDAY_KEYS):
        raise ValueError("plan weekly themes must be non-empty text")
    sources = plan.get("material_sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("plan material_sources must be a non-empty list")
    for source in sources:
        if not isinstance(source, dict) or not str(source.get("name", "")).strip() or not str(source.get("use_for", "")).strip():
            raise ValueError("each material source needs name and use_for")
    return plan


def write_json(path, payload):
    """Write a UTF-8 JSON document, creating its parent directory if required."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def export_state(root, state_dir=None):
    """Build a portable snapshot of the effective plan and all check-ins."""
    return {
        "format_version": EXPORT_FORMAT_VERSION,
        "exported_at": datetime.now().replace(microsecond=0).isoformat(),
        "plan": load_plan(root, state_dir),
        "checkins": load_checkins(root, state_dir),
    }


def export_state_to_file(root, output, state_dir=None):
    """Write a portable state snapshot and return its output path."""
    return write_json(output, export_state(root, state_dir))


def _validated_import(document):
    """Validate an import document fully before it changes user state."""
    if not isinstance(document, dict):
        raise ValueError("import file must be a JSON object")
    if document.get("format_version") != EXPORT_FORMAT_VERSION:
        raise ValueError("unsupported import format_version")
    if not document.get("exported_at"):
        raise ValueError("import file is missing exported_at")
    plan = validate_plan(document.get("plan"))
    checkins = document.get("checkins")
    if not isinstance(checkins, list):
        raise ValueError("import file checkins must be a list")
    normalized = []
    for entry in checkins:
        if not isinstance(entry, dict) or not entry.get("date"):
            raise ValueError("each imported check-in needs a date")
        clean = dict(entry)
        clean["date"] = iso(clean["date"])
        normalized.append(clean)
    return plan, normalized


def import_state(root, input_path, state_dir=None, merge=False):
    """Load one portable snapshot, refusing accidental replacement by default."""
    with Path(input_path).open("r", encoding="utf-8") as handle:
        plan, checkins = _validated_import(json.load(handle))
    store = store_for(state_dir)
    store.initialize()
    if not merge and (store.has_saved_plan() or store.list_checkins()):
        raise ValueError("state already contains data; rerun import with --merge")
    store.save_plan(plan)
    for entry in checkins:
        store.upsert_checkin(entry)
    return {"imported_checkins": len(checkins), "merged": bool(merge)}


def initialize_plan(root, state_dir=None, start_date=None, force=False):
    """Save an initial plan, backing up an existing saved plan before reset."""
    store = store_for(state_dir)
    store.initialize()
    backup = None
    if store.has_saved_plan():
        if not force:
            raise ValueError("state already has a plan; rerun init with --force")
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        backup = export_state_to_file(
            root,
            store.state_dir / "backups" / ("before-init-" + timestamp + ".json"),
            store.state_dir,
        )
    plan = json.loads(json.dumps(load_default_plan(root)))
    plan["start_date"] = iso(start_date or date.today())
    store.save_plan(validate_plan(plan))
    return {"plan": plan, "backup": str(backup) if backup else None}


def update_plan(root, input_path, state_dir=None):
    """Validate and save one user-edited plan document."""
    with Path(input_path).open("r", encoding="utf-8") as handle:
        plan = validate_plan(json.load(handle))
    save_plan(root, plan, state_dir)
    return plan


def day_number(plan, target_date):
    start = parse_date(plan["start_date"])
    delta = (parse_date(target_date) - start).days
    return max(1, delta + 1)


def default_minutes(plan, target_date):
    key = "weekend_minutes" if parse_date(target_date).weekday() >= 5 else "weekday_minutes"
    return validate_minutes(plan.get(key, DEFAULT_PLAN[key]))


def phase_for_day(day):
    if day <= 50:
        return "50-day foundation: reactivate CET-6 knowledge and build a daily output habit"
    if day <= 150:
        return "150-day workplace core: explain work, projects, problems, and decisions"
    if day <= 300:
        return "300-day interview and collaboration: meetings, interviews, and async writing"
    return "500-day abroad-readiness: fluent review cycles, realistic materials, and pressure practice"


def blocks_for_minutes(minutes):
    if validate_minutes(minutes) == 30:
        return [
            {"name": "Duolingo warm-up", "minutes": 5},
            {"name": "Comprehensible listening", "minutes": 8},
            {"name": "Shadowing and pronunciation", "minutes": 7},
            {"name": "Recorded speaking output", "minutes": 7},
            {"name": "Retrieval review", "minutes": 3},
        ]
    return [
        {"name": "Duolingo and spaced review", "minutes": 10},
        {"name": "Intensive listening", "minutes": 15},
        {"name": "Shadowing and retelling", "minutes": 15},
        {"name": "Workplace writing", "minutes": 15},
        {"name": "Reflection and next action", "minutes": 5},
    ]


def material_prompt(plan, theme, target_date):
    sources = plan.get("material_sources") or DEFAULT_PLAN["material_sources"]
    source = sources[(day_number(plan, target_date) - 1) % len(sources)]
    return {
        "source": source["name"],
        "use_for": source.get("use_for", "English practice"),
        "search_query": "%s B2 English %s" % (source["name"], theme),
        "fallback": "If web access is unavailable, generate a 120-180 word B2-level workplace passage about %s." % theme,
    }


def generate_today_task(root, target_date=None, minutes=None, state_dir=None):
    target = parse_date(target_date or date.today())
    plan = load_plan(root, state_dir)
    weekday_key = WEEKDAY_KEYS[target.weekday()]
    expected_minutes = validate_minutes(
        default_minutes(plan, target) if minutes is None else minutes
    )
    day = day_number(plan, target)
    cycle_day = ((day - 1) % 50) + 1
    cycle_number = ((day - 1) // 50) + 1
    theme = plan["weekly_themes"].get(weekday_key, "workplace English")
    return {
        "date": target.isoformat(),
        "day_number": day,
        "cycle_50_day": cycle_day,
        "cycle_50_number": cycle_number,
        "goal_500_progress": "%s/500" % min(day, 500),
        "goal_status": "completed" if day > 500 else "in_progress",
        "minutes": expected_minutes,
        "theme": theme,
        "phase": phase_for_day(day),
        "blocks": blocks_for_minutes(expected_minutes),
        "material": material_prompt(plan, theme, target),
        "required_output": [
            "one 1-5 minute speaking recording or transcript",
            "3-5 reusable expressions",
            "one short reflection sentence",
        ],
    }


def normalize_expressions(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not value:
        return []
    raw = str(value).replace("\n", ";").replace(",", ";")
    return [item.strip() for item in raw.split(";") if item.strip()]


def objective_score(entry, expected_minutes):
    minutes = int(entry.get("minutes") or 0)
    expressions = normalize_expressions(entry.get("expressions"))
    score = 0
    score += min(20, int(round((minutes / float(expected_minutes or 30)) * 20)))
    score += 15 if str(entry.get("listening", "")).strip() else 0
    score += 25 if str(entry.get("speaking", "")).strip() else 0
    score += min(20, len(expressions) * 7)
    score += 20 if str(entry.get("reflection", "")).strip() else 0
    return min(100, score)


def load_checkins(root, state_dir=None):
    """Load check-ins from the user's external state database."""
    return store_for(state_dir).list_checkins()


def validate_checkin_date(plan, target_date):
    """Reject check-ins outside the plan's elapsed calendar range."""
    target = parse_date(target_date)
    start = parse_date(plan["start_date"])
    if target < start:
        raise ValueError("check-in date is before the plan start")
    if target > date.today():
        raise ValueError("check-in date cannot be in the future")
    return target


def record_checkin(root, entry, state_dir=None):
    """Normalize and atomically upsert one check-in in user storage."""
    plan = load_plan(root, state_dir)
    clean = dict(entry)
    target = validate_checkin_date(plan, clean["date"])
    clean["date"] = target.isoformat()
    clean["minutes"] = validate_minutes(
        default_minutes(plan, target)
        if clean.get("minutes") is None
        else clean["minutes"]
    )
    clean["duolingo"] = bool(clean.get("duolingo", False))
    clean["expressions"] = normalize_expressions(clean.get("expressions"))
    clean["recorded_at"] = datetime.now().replace(microsecond=0).isoformat()
    task = generate_today_task(
        root, parse_date(clean["date"]), clean["minutes"], state_dir
    )
    clean["day_number"] = task["day_number"]
    clean["cycle_50_day"] = task["cycle_50_day"]
    clean["objective_score"] = objective_score(clean, task["minutes"])

    store_for(state_dir).upsert_checkin(clean)
    return clean


def each_day(start, end):
    cursor = start
    while cursor <= end:
        yield cursor
        cursor += timedelta(days=1)


def longest_streak(completed, start, end):
    longest = 0
    current = 0
    for item in each_day(start, end):
        if item.isoformat() in completed:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def current_streak(completed, start, today):
    streak = 0
    cursor = today
    while cursor >= start:
        if cursor.isoformat() not in completed:
            break
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def build_summary(root, today=None, days=30, state_dir=None):
    target = parse_date(today or date.today())
    days = validate_summary_days(days)
    plan = load_plan(root, state_dir)
    start = parse_date(plan["start_date"])
    if target < start:
        return {
            "date": target.isoformat(),
            "window_days": days,
            "plan_start_date": start.isoformat(),
            "day_number": 0,
            "completed_days": 0,
            "expected_days": 0,
            "missed_dates": [],
            "current_streak": 0,
            "longest_streak": 0,
            "total_minutes": 0,
            "completion_rate": 0.0,
            "status": "not_started",
        }

    window_start = max(start, target - timedelta(days=days - 1))
    entries = load_checkins(root, state_dir)
    completed = {entry["date"] for entry in entries if window_start <= parse_date(entry["date"]) <= target}
    all_completed = {entry["date"] for entry in entries if start <= parse_date(entry["date"]) <= target}
    missed = [item.isoformat() for item in each_day(window_start, target) if item.isoformat() not in completed]
    total_minutes = sum(int(entry.get("minutes") or 0) for entry in entries if window_start <= parse_date(entry["date"]) <= target)
    expected_days = len(list(each_day(window_start, target)))
    current_day = day_number(plan, target)
    return {
        "date": target.isoformat(),
        "window_days": days,
        "plan_start_date": start.isoformat(),
        "day_number": current_day,
        "completed_days": len(completed),
        "expected_days": expected_days,
        "missed_dates": missed,
        "current_streak": current_streak(all_completed, start, target),
        "longest_streak": longest_streak(all_completed, start, target),
        "total_minutes": total_minutes,
        "completion_rate": round((len(completed) / float(expected_days)) * 100, 1),
        "status": "completed" if current_day > 500 else "in_progress",
    }


def print_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def print_task(task):
    print("English task for %s | Day %s | %s minutes" % (task["date"], task["day_number"], task["minutes"]))
    print("Theme: %s" % task["theme"])
    print("Phase: %s" % task["phase"])
    print("50-day cycle: %s day %s | 500-day goal: %s" % (task["cycle_50_number"], task["cycle_50_day"], task["goal_500_progress"]))
    print("Blocks:")
    for block in task["blocks"]:
        print("- %s min: %s" % (block["minutes"], block["name"]))
    print("Material: %s (%s)" % (task["material"]["source"], task["material"]["use_for"]))
    print("Search: %s" % task["material"]["search_query"])
    print("Fallback: %s" % task["material"]["fallback"])
    print("Required output:")
    for item in task["required_output"]:
        print("- %s" % item)


def print_summary(summary):
    print("Progress summary through %s" % summary["date"])
    print("Day: %s | Window: %s days" % (summary["day_number"], summary["window_days"]))
    print("Completed: %s/%s days (%.1f%%)" % (summary["completed_days"], summary["expected_days"], summary["completion_rate"]))
    print("Current streak: %s | Longest streak: %s" % (summary["current_streak"], summary["longest_streak"]))
    print("Total minutes: %s" % summary["total_minutes"])
    if summary["missed_dates"]:
        print("Missed dates: %s" % ", ".join(summary["missed_dates"]))
    else:
        print("Missed dates: none")


def skill_root_from_args(value):
    if value:
        return Path(value).resolve()
    return Path(__file__).resolve().parents[1]


def build_parser():
    parser = argparse.ArgumentParser(description="Manage daily English plan, check-ins, reminders, and streaks.")
    parser.add_argument("--root", help="Read-only skill resource folder. Defaults to this script's parent skill folder.")
    parser.add_argument("--state-dir", help="Writable user state folder. Defaults to the platform user state location.")
    sub = parser.add_subparsers(dest="command", required=True)

    today_parser = sub.add_parser("today", help="Generate today's task.")
    today_parser.add_argument("--date", help="YYYY-MM-DD. Defaults to today.")
    today_parser.add_argument("--minutes", type=int, choices=[30, 60], help="Override 30/60 minute mode.")
    today_parser.add_argument("--json", action="store_true")

    checkin_parser = sub.add_parser("checkin", help="Record or replace a check-in for one date.")
    checkin_parser.add_argument("--date", required=True)
    checkin_parser.add_argument("--minutes", type=int, choices=[30, 60], required=True)
    checkin_parser.add_argument("--theme", required=True)
    checkin_parser.add_argument("--duolingo", choices=["done", "missed"], default="done")
    checkin_parser.add_argument("--listening", default="")
    checkin_parser.add_argument("--speaking", default="")
    checkin_parser.add_argument("--expressions", default="")
    checkin_parser.add_argument("--reflection", default="")
    checkin_parser.add_argument("--json", action="store_true")

    summary_parser = sub.add_parser("summary", help="Summarize progress and missed dates.")
    summary_parser.add_argument("--date", help="YYYY-MM-DD. Defaults to today.")
    summary_parser.add_argument("--days", type=parse_summary_days, default=30)
    summary_parser.add_argument("--json", action="store_true")

    reminder_parser = sub.add_parser("reminder", help="Print today's reminder and whether check-in is missing.")
    reminder_parser.add_argument("--date", help="YYYY-MM-DD. Defaults to today.")
    reminder_parser.add_argument("--json", action="store_true")

    doctor_parser = sub.add_parser("doctor", help="Check Python, state storage, notification, and systemd readiness.")
    doctor_parser.add_argument("--json", action="store_true")

    migrate_parser = sub.add_parser("migrate", help="Copy legacy JSON and JSONL state into the user database.")
    migrate_parser.add_argument("--legacy-root", required=True, help="Legacy skill folder or its data directory.")
    migrate_parser.add_argument("--json", action="store_true")

    export_parser = sub.add_parser("export", help="Write a portable backup of the current state.")
    export_parser.add_argument("--output", required=True)

    import_parser = sub.add_parser("import", help="Restore a portable backup into the current state.")
    import_parser.add_argument("--input", required=True)
    import_parser.add_argument("--merge", action="store_true", help="Allow replacing check-ins with the same date.")

    init_parser = sub.add_parser("init", help="Save the bundled plan as the user's initial plan.")
    init_parser.add_argument("--start-date", help="YYYY-MM-DD. Defaults to today.")
    init_parser.add_argument("--force", action="store_true", help="Back up and replace an existing saved plan.")
    init_parser.add_argument("--json", action="store_true")

    plan_parser = sub.add_parser("plan", help="Show the current plan JSON.")
    plan_parser.add_argument("--json", action="store_true")
    plan_subcommands = plan_parser.add_subparsers(dest="plan_command")
    plan_export_parser = plan_subcommands.add_parser("export", help="Write the current plan to a JSON file.")
    plan_export_parser.add_argument("--output", required=True)
    plan_update_parser = plan_subcommands.add_parser("update", help="Validate and save a plan JSON file.")
    plan_update_parser.add_argument("--input", required=True)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    root = skill_root_from_args(args.root)
    state_dir = resolve_state_dir(explicit=args.state_dir)

    if args.command == "today":
        task = generate_today_task(
            root,
            parse_date(args.date) if args.date else date.today(),
            args.minutes,
            state_dir,
        )
        print_json(task) if args.json else print_task(task)
        return 0

    if args.command == "checkin":
        try:
            entry = record_checkin(
                root,
                {
                    "date": args.date,
                    "minutes": args.minutes,
                    "theme": args.theme,
                    "duolingo": args.duolingo == "done",
                    "listening": args.listening,
                    "speaking": args.speaking,
                    "expressions": args.expressions,
                    "reflection": args.reflection,
                },
                state_dir=state_dir,
            )
        except ValueError as error:
            print("ERROR: %s" % error)
            return 1
        if args.json:
            print_json(entry)
        else:
            print("Recorded %s | score %s/100 | day %s" % (entry["date"], entry["objective_score"], entry["day_number"]))
        return 0

    if args.command == "summary":
        summary = build_summary(
            root,
            parse_date(args.date) if args.date else date.today(),
            args.days,
            state_dir,
        )
        print_json(summary) if args.json else print_summary(summary)
        return 0

    if args.command == "reminder":
        target = parse_date(args.date) if args.date else date.today()
        completed = {entry["date"] for entry in load_checkins(root, state_dir)}
        task = generate_today_task(root, target, state_dir=state_dir)
        result = {"date": target.isoformat(), "checked_in": target.isoformat() in completed, "task": task}
        if args.json:
            print_json(result)
        else:
            status = "already checked in" if result["checked_in"] else "check-in missing"
            print("%s: %s" % (target.isoformat(), status))
            if not result["checked_in"]:
                print_task(task)
        return 0

    if args.command == "doctor":
        report = build_doctor_report(root, state_dir)
        if args.json:
            print_json(report)
        else:
            print_doctor_report(report)
        return doctor_exit_code(report)

    if args.command == "migrate":
        try:
            result = coach_storage.migrate_legacy_data(
                store_for(state_dir), Path(args.legacy_root)
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print("ERROR: %s" % error)
            return 1
        if args.json:
            print_json(result)
        else:
            print(
                "Migrated %s check-ins; skipped %s; invalid lines: %s"
                % (
                    result["imported_checkins"],
                    result["skipped_checkins"],
                    len(result["invalid_lines"]),
                )
            )
        return 0 if result["complete"] else 1

    if args.command == "export":
        output = export_state_to_file(root, args.output, state_dir)
        print("Exported coach state to %s" % output)
        return 0

    if args.command == "import":
        try:
            result = import_state(root, args.input, state_dir, args.merge)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print("ERROR: %s" % error)
            return 1
        print("Imported %s check-ins" % result["imported_checkins"])
        return 0

    if args.command == "init":
        try:
            result = initialize_plan(
                root, state_dir, args.start_date, args.force
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print("ERROR: %s" % error)
            return 1
        if args.json:
            print_json(result)
        else:
            print("Initialized plan starting %s" % result["plan"]["start_date"])
            if result["backup"]:
                print("Backed up existing state to %s" % result["backup"])
        return 0

    if args.command == "plan":
        if args.plan_command == "export":
            output = write_json(args.output, load_plan(root, state_dir))
            print("Exported plan to %s" % output)
            return 0
        if args.plan_command == "update":
            try:
                update_plan(root, args.input, state_dir)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                print("ERROR: %s" % error)
                return 1
            print("Updated plan from %s" % args.input)
            return 0
        plan = load_plan(root, state_dir)
        print_json(plan) if args.json else print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
