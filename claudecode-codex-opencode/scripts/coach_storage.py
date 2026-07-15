#!/usr/bin/env python3
"""SQLite-backed user state for the English Work Abroad Coach."""

import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


APPLICATION_DIR = "english-work-abroad-coach"
WINDOWS_APPLICATION_DIR = "EnglishWorkAbroadCoach"
DATABASE_NAME = "coach.db"
SQLITE_TIMEOUT_SECONDS = 5.0
BUSY_TIMEOUT_MILLISECONDS = 5000
LEGACY_MIGRATION_META_KEY = "legacy_migration_completed"


def resolve_state_dir(explicit=None, environ=None, platform=None, home=None) -> Path:
    """Resolve the writable user state directory without touching the filesystem."""
    environment = os.environ if environ is None else environ
    current_platform = sys.platform if platform is None else platform
    user_home = Path.home() if home is None else Path(home)

    if explicit:
        return Path(explicit)
    if environment.get("ENGLISH_COACH_HOME"):
        return Path(environment["ENGLISH_COACH_HOME"])
    if current_platform == "darwin":
        return (
            user_home
            / "Library"
            / "Application Support"
            / WINDOWS_APPLICATION_DIR
        )
    if current_platform.startswith("win"):
        local_app_data = environment.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else user_home / "AppData" / "Local"
        return base / WINDOWS_APPLICATION_DIR

    xdg_state_home = environment.get("XDG_STATE_HOME")
    base = Path(xdg_state_home) if xdg_state_home else user_home / ".local" / "state"
    return base / APPLICATION_DIR


class CoachStore:
    """Persist plans, check-ins, and metadata in one per-user SQLite database."""

    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir)
        self.database_path = self.state_dir / DATABASE_NAME

    def _connect(self):
        connection = sqlite3.connect(
            str(self.database_path), timeout=SQLITE_TIMEOUT_SECONDS
        )
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "PRAGMA busy_timeout = %d" % BUSY_TIMEOUT_MILLISECONDS
        )
        return connection

    def initialize(self) -> None:
        """Create the state directory and schema when they do not exist."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_meta (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value_json TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS checkins (
                        checkin_date TEXT PRIMARY KEY,
                        payload_json TEXT NOT NULL,
                        recorded_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO schema_meta (key, value)
                    VALUES ('schema_version', '1')
                    ON CONFLICT(key) DO NOTHING
                    """
                )
        finally:
            connection.close()

    def load_plan(self, default_plan: dict) -> dict:
        """Return the saved plan or an independent copy of the bundled default."""
        self.initialize()
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT value_json FROM settings WHERE key = 'plan'"
            ).fetchone()
        finally:
            connection.close()
        source = json.loads(row[0]) if row else default_plan
        return json.loads(json.dumps(source))

    def save_plan(self, plan: dict) -> None:
        """Atomically save the current plan."""
        self.initialize()
        serialized = json.dumps(plan, ensure_ascii=False, sort_keys=True)
        updated_at = datetime.now().replace(microsecond=0).isoformat()
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO settings (key, value_json, updated_at)
                    VALUES ('plan', ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value_json = excluded.value_json,
                        updated_at = excluded.updated_at
                    """,
                    (serialized, updated_at),
                )
        finally:
            connection.close()

    def has_saved_plan(self) -> bool:
        """Return whether the user has saved a plan in this state database."""
        self.initialize()
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT 1 FROM settings WHERE key = 'plan'"
            ).fetchone()
        finally:
            connection.close()
        return row is not None

    def list_checkins(self) -> list[dict]:
        """Return all check-ins ordered by ISO date."""
        self.initialize()
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT payload_json FROM checkins ORDER BY checkin_date"
            ).fetchall()
        finally:
            connection.close()
        return [json.loads(row[0]) for row in rows]

    def upsert_checkin(self, entry: dict) -> None:
        """Atomically insert or replace one check-in identified by its date."""
        self.initialize()
        serialized = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        recorded_at = entry.get("recorded_at") or datetime.now().replace(
            microsecond=0
        ).isoformat()
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO checkins (checkin_date, payload_json, recorded_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(checkin_date) DO UPDATE SET
                        payload_json = excluded.payload_json,
                        recorded_at = excluded.recorded_at
                    """,
                    (entry["date"], serialized, recorded_at),
                )
        finally:
            connection.close()

    def get_meta(self, key: str) -> Optional[str]:
        """Return one schema metadata value, or None when it is absent."""
        self.initialize()
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT value FROM schema_meta WHERE key = ?", (key,)
            ).fetchone()
        finally:
            connection.close()
        return row[0] if row else None

    def set_meta(self, key: str, value: str) -> None:
        """Atomically insert or replace one schema metadata value."""
        self.initialize()
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO schema_meta (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, value),
                )
        finally:
            connection.close()


def _legacy_data_dir(legacy_root: Path) -> Path:
    """Return the data directory from a skill root or an explicit data directory."""
    root = Path(legacy_root)
    return root / "data" if (root / "data").is_dir() else root


def migrate_legacy_data(store: CoachStore, legacy_root: Path) -> dict:
    """Copy legacy state once and report imported, skipped, and invalid records."""
    legacy_data = _legacy_data_dir(legacy_root)
    if not legacy_data.is_dir():
        raise FileNotFoundError(
            "legacy data directory does not exist: %s" % legacy_data
        )
    result = {
        "imported_checkins": 0,
        "skipped_checkins": 0,
        "invalid_lines": [],
        "plan_imported": False,
        "log_copied": False,
        "complete": False,
    }
    store.initialize()

    plan_path = legacy_data / "plan.json"
    if plan_path.is_file() and not store.has_saved_plan():
        with plan_path.open("r", encoding="utf-8") as handle:
            store.save_plan(json.load(handle))
        result["plan_imported"] = True

    existing_dates = {entry["date"] for entry in store.list_checkins()}
    checkins_path = legacy_data / "checkins.jsonl"
    if checkins_path.is_file():
        with checkins_path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                if not raw_line.strip():
                    continue
                try:
                    entry = json.loads(raw_line)
                except json.JSONDecodeError:
                    result["invalid_lines"].append(
                        {"line": line_number, "reason": "invalid JSON"}
                    )
                    continue
                if not isinstance(entry, dict) or not entry.get("date"):
                    result["invalid_lines"].append(
                        {"line": line_number, "reason": "missing check-in date"}
                    )
                    continue
                if entry["date"] in existing_dates:
                    result["skipped_checkins"] += 1
                    continue
                store.upsert_checkin(entry)
                existing_dates.add(entry["date"])
                result["imported_checkins"] += 1

    legacy_log = legacy_data / "reminder.log"
    state_log = store.state_dir / "reminder.log"
    if legacy_log.is_file() and not state_log.exists():
        shutil.copyfile(str(legacy_log), str(state_log))
        result["log_copied"] = True

    result["complete"] = not result["invalid_lines"]
    if result["complete"]:
        store.set_meta(LEGACY_MIGRATION_META_KEY, str(Path(legacy_root).resolve()))
    return result
