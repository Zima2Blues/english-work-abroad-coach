import importlib.util
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


if __name__ == "__main__":
    unittest.main()
