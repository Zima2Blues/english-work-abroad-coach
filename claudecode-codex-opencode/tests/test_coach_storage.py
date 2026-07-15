import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "coach_storage.py"
spec = importlib.util.spec_from_file_location("coach_storage", SCRIPT)
coach_storage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coach_storage)


class StateDirectoryTests(unittest.TestCase):
    def test_explicit_state_dir_wins_over_environment(self):
        resolved = coach_storage.resolve_state_dir(
            explicit="/tmp/explicit",
            environ={"ENGLISH_COACH_HOME": "/tmp/environment"},
            platform="linux",
            home=Path("/home/tester"),
        )

        self.assertEqual(resolved, Path("/tmp/explicit"))

    def test_environment_state_dir_wins_over_platform_default(self):
        resolved = coach_storage.resolve_state_dir(
            environ={"ENGLISH_COACH_HOME": "/tmp/environment"},
            platform="linux",
            home=Path("/home/tester"),
        )

        self.assertEqual(resolved, Path("/tmp/environment"))

    def test_linux_uses_xdg_state_home_when_set(self):
        resolved = coach_storage.resolve_state_dir(
            environ={"XDG_STATE_HOME": "/state"},
            platform="linux",
            home=Path("/home/tester"),
        )

        self.assertEqual(resolved, Path("/state/english-work-abroad-coach"))

    def test_linux_defaults_below_home_local_state(self):
        home = Path("/home/tester")

        resolved = coach_storage.resolve_state_dir(
            environ={}, platform="linux", home=home
        )

        self.assertEqual(
            resolved, home / ".local" / "state" / "english-work-abroad-coach"
        )

    def test_macos_defaults_below_application_support(self):
        home = Path("/Users/tester")

        resolved = coach_storage.resolve_state_dir(
            environ={}, platform="darwin", home=home
        )

        self.assertEqual(
            resolved,
            home / "Library" / "Application Support" / "EnglishWorkAbroadCoach",
        )

    def test_windows_uses_local_app_data(self):
        resolved = coach_storage.resolve_state_dir(
            environ={"LOCALAPPDATA": "C:/Users/tester/AppData/Local"},
            platform="win32",
            home=Path("C:/Users/tester"),
        )

        self.assertEqual(
            resolved,
            Path("C:/Users/tester/AppData/Local/EnglishWorkAbroadCoach"),
        )


class CoachStoreTests(unittest.TestCase):
    def test_initialize_uses_planned_settings_and_checkins_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = coach_storage.CoachStore(Path(tmp))
            store.initialize()

            connection = sqlite3.connect(str(store.database_path))
            try:
                settings = connection.execute(
                    "PRAGMA table_info(settings)"
                ).fetchall()
                checkins = connection.execute(
                    "PRAGMA table_info(checkins)"
                ).fetchall()
            finally:
                connection.close()

            self.assertEqual(
                [row[1] for row in settings],
                ["key", "value_json", "updated_at"],
            )
            self.assertEqual(
                [row[1] for row in checkins],
                ["checkin_date", "payload_json", "recorded_at"],
            )

    def test_initialize_records_schema_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = coach_storage.CoachStore(Path(tmp))

            store.initialize()

            self.assertEqual(store.get_meta("schema_version"), "1")

    def test_plan_uses_default_until_saved_and_then_persists(self):
        default_plan = {"start_date": "2026-07-14", "weekday_minutes": 30}
        saved_plan = {"start_date": "2026-07-15", "weekday_minutes": 60}
        with tempfile.TemporaryDirectory() as tmp:
            store = coach_storage.CoachStore(Path(tmp))

            self.assertEqual(store.load_plan(default_plan), default_plan)
            store.save_plan(saved_plan)

            self.assertEqual(store.load_plan(default_plan), saved_plan)

    def test_upsert_replaces_one_date_without_duplicate_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = coach_storage.CoachStore(Path(tmp))

            store.upsert_checkin({"date": "2026-07-14", "minutes": 30})
            store.upsert_checkin({"date": "2026-07-14", "minutes": 60})

            self.assertEqual(
                store.list_checkins(),
                [{"date": "2026-07-14", "minutes": 60}],
            )

    def test_upsert_uses_entry_recorded_at_for_database_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = coach_storage.CoachStore(Path(tmp))
            store.upsert_checkin(
                {
                    "date": "2026-07-14",
                    "minutes": 30,
                    "recorded_at": "2026-07-14T21:00:00",
                }
            )

            connection = sqlite3.connect(str(store.database_path))
            try:
                row = connection.execute(
                    "SELECT checkin_date, recorded_at FROM checkins"
                ).fetchone()
            finally:
                connection.close()

            self.assertEqual(row, ("2026-07-14", "2026-07-14T21:00:00"))

    def test_two_store_connections_preserve_consecutive_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            first = coach_storage.CoachStore(state_dir)
            second = coach_storage.CoachStore(state_dir)

            first.upsert_checkin({"date": "2026-07-14", "minutes": 30})
            second.upsert_checkin({"date": "2026-07-15", "minutes": 60})

            self.assertEqual(
                first.list_checkins(),
                [
                    {"date": "2026-07-14", "minutes": 30},
                    {"date": "2026-07-15", "minutes": 60},
                ],
            )

    def test_meta_value_can_be_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = coach_storage.CoachStore(Path(tmp))

            store.set_meta("last_reminder", "2026-07-14")
            store.set_meta("last_reminder", "2026-07-15")

            self.assertEqual(store.get_meta("last_reminder"), "2026-07-15")


class LegacyMigrationTests(unittest.TestCase):
    def create_legacy_data(self, root, checkin_lines):
        """Create a representative pre-SQLite skill data directory."""
        data = root / "data"
        data.mkdir(parents=True)
        plan = {
            "start_date": "2026-07-14",
            "weekday_minutes": 30,
            "weekend_minutes": 60,
            "weekly_themes": {"monday": "current work"},
        }
        (data / "plan.json").write_text(
            json.dumps(plan), encoding="utf-8"
        )
        (data / "progress.json").write_text(
            json.dumps({"completed_days": 2}), encoding="utf-8"
        )
        (data / "checkins.jsonl").write_text(
            "\n".join(checkin_lines) + "\n", encoding="utf-8"
        )
        (data / "reminder.log").write_text(
            "2026-07-14: check-in missing\n", encoding="utf-8"
        )
        return data

    def test_migration_imports_legacy_state_once_without_changing_source_files(self):
        checkins = [
            json.dumps({"date": "2026-07-14", "minutes": 30}),
            json.dumps({"date": "2026-07-15", "minutes": 60}),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            legacy_root = workspace / "legacy"
            legacy_data = self.create_legacy_data(legacy_root, checkins)
            source_files = {
                path.name: path.read_bytes() for path in legacy_data.iterdir()
            }
            store = coach_storage.CoachStore(workspace / "state")

            first = coach_storage.migrate_legacy_data(store, legacy_root)

            self.assertEqual(first["imported_checkins"], 2)
            self.assertEqual(first["skipped_checkins"], 0)
            self.assertEqual(first["invalid_lines"], [])
            self.assertTrue(first["plan_imported"])
            self.assertTrue(first["log_copied"])
            self.assertTrue(first["complete"])
            self.assertEqual(store.load_plan({}), json.loads((legacy_data / "plan.json").read_text(encoding="utf-8")))
            self.assertEqual(
                store.list_checkins(),
                [
                    {"date": "2026-07-14", "minutes": 30},
                    {"date": "2026-07-15", "minutes": 60},
                ],
            )
            self.assertEqual(
                (workspace / "state" / "reminder.log").read_text(encoding="utf-8"),
                "2026-07-14: check-in missing\n",
            )
            self.assertEqual(
                {path.name: path.read_bytes() for path in legacy_data.iterdir()},
                source_files,
            )

            second = coach_storage.migrate_legacy_data(store, legacy_root)

            self.assertEqual(second["imported_checkins"], 0)
            self.assertEqual(second["skipped_checkins"], 2)
            self.assertEqual(second["invalid_lines"], [])
            self.assertFalse(second["plan_imported"])
            self.assertFalse(second["log_copied"])
            self.assertTrue(second["complete"])
            self.assertEqual(len(store.list_checkins()), 2)

    def test_migration_reports_malformed_jsonl_lines_without_rewriting_legacy_data(self):
        valid = json.dumps({"date": "2026-07-14", "minutes": 30})
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            legacy_root = workspace / "legacy"
            legacy_data = self.create_legacy_data(
                legacy_root, [valid, "{not valid json"]
            )
            original_checkins = (legacy_data / "checkins.jsonl").read_bytes()
            store = coach_storage.CoachStore(workspace / "state")

            result = coach_storage.migrate_legacy_data(store, legacy_root)

            self.assertEqual(result["imported_checkins"], 1)
            self.assertEqual(result["skipped_checkins"], 0)
            self.assertEqual(result["invalid_lines"], [{"line": 2, "reason": "invalid JSON"}])
            self.assertTrue(result["plan_imported"])
            self.assertTrue(result["log_copied"])
            self.assertFalse(result["complete"])
            self.assertEqual(
                store.list_checkins(), [{"date": "2026-07-14", "minutes": 30}]
            )
            self.assertEqual(
                (legacy_data / "checkins.jsonl").read_bytes(), original_checkins
            )

    def test_migration_accepts_the_repository_legacy_plan_shape(self):
        repository_plan = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "legacy-data"
            / "plan.json"
        )
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            legacy_data = workspace / "legacy" / "data"
            legacy_data.mkdir(parents=True)
            legacy_data.joinpath("plan.json").write_bytes(
                repository_plan.read_bytes()
            )
            legacy_data.joinpath("checkins.jsonl").write_text(
                '{"date": "2026-07-14", "minutes": 30}\n',
                encoding="utf-8",
            )
            store = coach_storage.CoachStore(workspace / "state")

            result = coach_storage.migrate_legacy_data(store, legacy_data)

            self.assertTrue(result["complete"])
            self.assertTrue(result["plan_imported"])
            self.assertEqual(result["imported_checkins"], 1)
            self.assertEqual(
                store.load_plan({}),
                json.loads(repository_plan.read_text(encoding="utf-8")),
            )


if __name__ == "__main__":
    unittest.main()
