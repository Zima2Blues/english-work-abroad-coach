import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "english_coach.py"
spec = importlib.util.spec_from_file_location("english_coach", SCRIPT)
english_coach = importlib.util.module_from_spec(spec)
spec.loader.exec_module(english_coach)

REMINDER_SCRIPT = SCRIPT.with_name("reminder_runner.py")
reminder_spec = importlib.util.spec_from_file_location(
    "reminder_runner", REMINDER_SCRIPT
)
reminder_runner = importlib.util.module_from_spec(reminder_spec)
reminder_spec.loader.exec_module(reminder_runner)


def write_plan(root: Path) -> None:
    data = root / "data"
    data.mkdir(parents=True)
    (data / "default-plan.json").write_text(
        json.dumps(
            {
                "start_date": "2026-07-13",
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
                ],
            }
        ),
        encoding="utf-8",
    )


class EnglishCoachTests(unittest.TestCase):
    def run_cli(self, arguments):
        """Run the command entrypoint and return its exit code and JSON output."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = english_coach.main(arguments)
        return result, output.getvalue()

    def assert_cli_parse_error(self, arguments, expected_message):
        """Assert argparse rejects invalid command arguments before command handling."""
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            with self.assertRaises(SystemExit) as raised:
                english_coach.main(arguments)
        self.assertEqual(raised.exception.code, 2)
        self.assertIn(expected_message, error.getvalue())

    def test_today_uses_weekday_and_weekend_default_minutes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            state_dir = Path(tmp) / "state"
            write_plan(root)

            monday = english_coach.generate_today_task(
                root, date(2026, 7, 13), state_dir=state_dir
            )
            saturday = english_coach.generate_today_task(
                root, date(2026, 7, 18), state_dir=state_dir
            )

            self.assertEqual(monday["day_number"], 1)
            self.assertEqual(monday["minutes"], 30)
            self.assertEqual(monday["theme"], "professional self-introduction")
            self.assertEqual([block["minutes"] for block in monday["blocks"]], [5, 8, 7, 7, 3])
            self.assertEqual(saturday["day_number"], 6)
            self.assertEqual(saturday["minutes"], 60)
            self.assertEqual(saturday["theme"], "deep practice")

    def test_summary_before_plan_start_returns_not_started(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            state_dir = Path(tmp) / "state"
            write_plan(root)

            summary = english_coach.build_summary(
                root, date(2026, 7, 12), days=30, state_dir=state_dir
            )

            self.assertEqual(summary["status"], "not_started")
            self.assertEqual(summary["expected_days"], 0)
            self.assertEqual(summary["completion_rate"], 0.0)

    def test_cli_rejects_invalid_today_minutes(self):
        self.assert_cli_parse_error(
            ["today", "--minutes", "45"], "invalid choice: 45"
        )

    def test_cli_rejects_invalid_checkin_minutes(self):
        self.assert_cli_parse_error(
            [
                "checkin",
                "--date",
                "2026-07-14",
                "--minutes",
                "45",
                "--theme",
                "current work",
            ],
            "invalid choice: 45",
        )

    def test_library_rejects_invalid_minutes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            state_dir = Path(tmp) / "state"
            write_plan(root)

            with self.assertRaisesRegex(ValueError, "^minutes must be 30 or 60$"):
                english_coach.generate_today_task(
                    root, date(2026, 7, 13), minutes=45, state_dir=state_dir
                )
            with self.assertRaisesRegex(ValueError, "^minutes must be 30 or 60$"):
                english_coach.record_checkin(
                    root,
                    {
                        "date": "2026-07-13",
                        "minutes": 45,
                        "theme": "professional self-introduction",
                    },
                    state_dir=state_dir,
                )

    def test_checkin_rejects_dates_before_plan_start_and_after_today(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            state_dir = Path(tmp) / "state"
            write_plan(root)

            with self.assertRaisesRegex(ValueError, "^check-in date is before the plan start$"):
                english_coach.record_checkin(
                    root,
                    {"date": "2026-07-12", "minutes": 30, "theme": "pre-plan"},
                    state_dir=state_dir,
                )
            with self.assertRaisesRegex(ValueError, "^check-in date cannot be in the future$"):
                english_coach.record_checkin(
                    root,
                    {
                        "date": (date.today() + timedelta(days=1)).isoformat(),
                        "minutes": 30,
                        "theme": "future",
                    },
                    state_dir=state_dir,
                )

    def test_summary_rejects_nonpositive_days(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            state_dir = Path(tmp) / "state"
            write_plan(root)

            with self.assertRaisesRegex(ValueError, "^days must be at least 1$"):
                english_coach.build_summary(
                    root, date(2026, 7, 13), days=0, state_dir=state_dir
                )
            self.assert_cli_parse_error(
                ["summary", "--days", "0"], "days must be at least 1"
            )

    def test_day_501_reports_completed_goal_without_exceeding_goal_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            state_dir = Path(tmp) / "state"
            write_plan(root)

            task = english_coach.generate_today_task(
                root, date(2026, 7, 13) + timedelta(days=500), state_dir=state_dir
            )

            self.assertEqual(task["day_number"], 501)
            self.assertEqual(task["goal_status"], "completed")
            self.assertEqual(task["goal_500_progress"], "500/500")

    def test_checkin_records_entry_and_summary_counts_streak(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            state_dir = Path(tmp) / "state"
            write_plan(root)

            english_coach.record_checkin(
                root,
                {
                    "date": "2026-07-13",
                    "minutes": 30,
                    "theme": "professional self-introduction",
                    "duolingo": True,
                    "listening": "VOA 2 minute clip",
                    "speaking": "I currently work as a backend developer.",
                    "expressions": ["I currently work as", "main responsibility", "work abroad"],
                    "reflection": "I paused when explaining details.",
                },
                state_dir=state_dir,
            )
            english_coach.record_checkin(
                root,
                {
                    "date": "2026-07-14",
                    "minutes": 30,
                    "theme": "current work",
                    "duolingo": True,
                    "listening": "British Council work video",
                    "speaking": "My main responsibility is building APIs.",
                    "expressions": ["main responsibility", "build APIs", "sync progress"],
                    "reflection": "Need smoother verbs.",
                },
                state_dir=state_dir,
            )

            summary = english_coach.build_summary(
                root, date(2026, 7, 14), days=7, state_dir=state_dir
            )

            self.assertEqual(summary["completed_days"], 2)
            self.assertEqual(summary["current_streak"], 2)
            self.assertEqual(summary["longest_streak"], 2)
            self.assertEqual(summary["missed_dates"], [])
            self.assertEqual(summary["total_minutes"], 60)

    def test_summary_reports_missing_dates_without_breaking_longest_streak(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            state_dir = Path(tmp) / "state"
            write_plan(root)

            english_coach.record_checkin(
                root,
                {
                    "date": "2026-07-13",
                    "minutes": 30,
                    "theme": "professional self-introduction",
                    "duolingo": True,
                    "listening": "VOA",
                    "speaking": "Hello.",
                    "expressions": ["currently", "responsibility", "abroad"],
                    "reflection": "Done.",
                },
                state_dir=state_dir,
            )
            english_coach.record_checkin(
                root,
                {
                    "date": "2026-07-15",
                    "minutes": 30,
                    "theme": "project story",
                    "duolingo": True,
                    "listening": "VOA",
                    "speaking": "One project I worked on was a dashboard.",
                    "expressions": ["worked on", "challenge", "result"],
                    "reflection": "Need better structure.",
                },
                state_dir=state_dir,
            )

            summary = english_coach.build_summary(
                root, date(2026, 7, 15), days=3, state_dir=state_dir
            )

            self.assertEqual(summary["completed_days"], 2)
            self.assertEqual(summary["current_streak"], 1)
            self.assertEqual(summary["longest_streak"], 1)
            self.assertEqual(summary["missed_dates"], ["2026-07-14"])

    def test_cli_uses_writable_state_without_modifying_read_only_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            state_dir = Path(tmp) / "state"
            write_plan(root)
            default_plan = root / "data" / "default-plan.json"
            original_files = {
                path.relative_to(root): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            default_plan.chmod(0o444)
            (root / "data").chmod(0o555)
            root.chmod(0o555)

            try:
                checkin_output = io.StringIO()
                with contextlib.redirect_stdout(checkin_output):
                    result = english_coach.main(
                        [
                            "--root",
                            str(root),
                            "--state-dir",
                            str(state_dir),
                            "checkin",
                            "--date",
                            "2026-07-14",
                            "--minutes",
                            "30",
                            "--theme",
                            "current work",
                            "--listening",
                            "VOA",
                            "--speaking",
                            "I build APIs.",
                            "--expressions",
                            "build APIs;main responsibility;work abroad",
                            "--reflection",
                            "Done.",
                            "--json",
                        ]
                    )
                self.assertEqual(result, 0)
                self.assertEqual(json.loads(checkin_output.getvalue())["minutes"], 30)

                summary_output = io.StringIO()
                with contextlib.redirect_stdout(summary_output):
                    result = english_coach.main(
                        [
                            "--root",
                            str(root),
                            "--state-dir",
                            str(state_dir),
                            "summary",
                            "--date",
                            "2026-07-14",
                            "--days",
                            "7",
                            "--json",
                        ]
                    )
                self.assertEqual(result, 0)
                self.assertEqual(json.loads(summary_output.getvalue())["completed_days"], 1)

                reminder_output = io.StringIO()
                with contextlib.redirect_stdout(reminder_output):
                    result = reminder_runner.main(
                        [
                            "--root",
                            str(root),
                            "--state-dir",
                            str(state_dir),
                            "--date",
                            "2026-07-14",
                            "--json",
                        ]
                    )
                self.assertEqual(result, 0)
                self.assertTrue(json.loads(reminder_output.getvalue())["checked_in"])
            finally:
                root.chmod(0o755)
                (root / "data").chmod(0o755)
                default_plan.chmod(0o644)

            current_files = {
                path.relative_to(root): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(current_files, original_files)
            self.assertTrue((state_dir / "coach.db").is_file())
            self.assertTrue((state_dir / "reminder.log").is_file())

    def test_migrate_command_returns_nonzero_for_malformed_legacy_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            root = workspace / "skill"
            state_dir = workspace / "state"
            legacy_root = workspace / "legacy"
            write_plan(root)
            legacy_data = legacy_root / "data"
            legacy_data.mkdir(parents=True)
            (legacy_data / "checkins.jsonl").write_text(
                '{"date": "2026-07-14", "minutes": 30}\n{broken\n',
                encoding="utf-8",
            )

            result, output = self.run_cli(
                [
                    "--root",
                    str(root),
                    "--state-dir",
                    str(state_dir),
                    "migrate",
                    "--legacy-root",
                    str(legacy_root),
                    "--json",
                ]
            )

            migration = json.loads(output)
            self.assertEqual(result, 1)
            self.assertEqual(migration["imported_checkins"], 1)
            self.assertEqual(
                migration["invalid_lines"], [{"line": 2, "reason": "invalid JSON"}]
            )
            self.assertFalse(migration["complete"])

    def test_migrate_command_rejects_a_missing_legacy_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            root = workspace / "skill"
            write_plan(root)

            result, output = self.run_cli(
                [
                    "--root",
                    str(root),
                    "--state-dir",
                    str(workspace / "state"),
                    "migrate",
                    "--legacy-root",
                    str(workspace / "missing-legacy"),
                ]
            )

            self.assertEqual(result, 1)
            self.assertIn("legacy data directory does not exist", output)

    def test_export_import_rejects_nonempty_state_unless_merge_overwrites_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            root = workspace / "skill"
            source_state = workspace / "source-state"
            target_state = workspace / "target-state"
            backup = workspace / "english-coach-backup.json"
            write_plan(root)
            source_plan = english_coach.load_default_plan(root)
            source_plan["start_date"] = "2026-07-14"
            english_coach.save_plan(root, source_plan, source_state)
            english_coach.store_for(source_state).upsert_checkin(
                {"date": "2026-07-14", "minutes": 30}
            )

            result, _ = self.run_cli(
                [
                    "--root",
                    str(root),
                    "--state-dir",
                    str(source_state),
                    "export",
                    "--output",
                    str(backup),
                ]
            )

            self.assertEqual(result, 0)
            exported = json.loads(backup.read_text(encoding="utf-8"))
            self.assertEqual(exported["format_version"], 1)
            self.assertIn("exported_at", exported)
            self.assertEqual(exported["plan"], source_plan)
            self.assertEqual(exported["checkins"], [{"date": "2026-07-14", "minutes": 30}])

            target_plan = dict(source_plan, start_date="2026-08-01")
            english_coach.save_plan(root, target_plan, target_state)
            english_coach.store_for(target_state).upsert_checkin(
                {"date": "2026-07-14", "minutes": 60}
            )
            result, _ = self.run_cli(
                [
                    "--root",
                    str(root),
                    "--state-dir",
                    str(target_state),
                    "import",
                    "--input",
                    str(backup),
                ]
            )

            self.assertEqual(result, 1)
            self.assertEqual(english_coach.load_plan(root, target_state), target_plan)
            self.assertEqual(
                english_coach.load_checkins(root, target_state),
                [{"date": "2026-07-14", "minutes": 60}],
            )

            result, _ = self.run_cli(
                [
                    "--root",
                    str(root),
                    "--state-dir",
                    str(target_state),
                    "import",
                    "--input",
                    str(backup),
                    "--merge",
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(english_coach.load_plan(root, target_state), source_plan)
            self.assertEqual(
                english_coach.load_checkins(root, target_state),
                [{"date": "2026-07-14", "minutes": 30}],
            )

    def test_init_and_plan_commands_protect_existing_plan_and_validate_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            root = workspace / "skill"
            state_dir = workspace / "state"
            plan_file = workspace / "my-plan.json"
            write_plan(root)

            result, output = self.run_cli(
                [
                    "--root",
                    str(root),
                    "--state-dir",
                    str(state_dir),
                    "init",
                    "--start-date",
                    "2026-08-01",
                    "--json",
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(json.loads(output)["plan"]["start_date"], "2026-08-01")

            result, _ = self.run_cli(
                [
                    "--root",
                    str(root),
                    "--state-dir",
                    str(state_dir),
                    "init",
                ]
            )
            self.assertEqual(result, 1)

            result, output = self.run_cli(
                [
                    "--root",
                    str(root),
                    "--state-dir",
                    str(state_dir),
                    "init",
                    "--start-date",
                    "2026-09-01",
                    "--force",
                    "--json",
                ]
            )

            self.assertEqual(result, 0)
            forced_init = json.loads(output)
            self.assertTrue(Path(forced_init["backup"]).is_file())
            self.assertEqual(forced_init["plan"]["start_date"], "2026-09-01")

            result, _ = self.run_cli(
                [
                    "--root",
                    str(root),
                    "--state-dir",
                    str(state_dir),
                    "plan",
                    "export",
                    "--output",
                    str(plan_file),
                ]
            )
            self.assertEqual(result, 0)

            invalid_plan = json.loads(plan_file.read_text(encoding="utf-8"))
            invalid_plan["weekday_minutes"] = 45
            plan_file.write_text(json.dumps(invalid_plan), encoding="utf-8")
            result, _ = self.run_cli(
                [
                    "--root",
                    str(root),
                    "--state-dir",
                    str(state_dir),
                    "plan",
                    "update",
                    "--input",
                    str(plan_file),
                ]
            )

            self.assertEqual(result, 1)
            self.assertEqual(
                english_coach.load_plan(root, state_dir)["start_date"], "2026-09-01"
            )

            valid_plan = english_coach.load_plan(root, state_dir)
            valid_plan["start_date"] = "2026-10-01"
            plan_file.write_text(json.dumps(valid_plan), encoding="utf-8")
            result, _ = self.run_cli(
                [
                    "--root",
                    str(root),
                    "--state-dir",
                    str(state_dir),
                    "plan",
                    "update",
                    "--input",
                    str(plan_file),
                ]
            )

            self.assertEqual(result, 0)
            self.assertEqual(
                english_coach.load_plan(root, state_dir)["start_date"], "2026-10-01"
            )


if __name__ == "__main__":
    unittest.main()
