import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import date
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


if __name__ == "__main__":
    unittest.main()
