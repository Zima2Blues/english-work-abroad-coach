import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "english_coach.py"
spec = importlib.util.spec_from_file_location("english_coach", SCRIPT)
english_coach = importlib.util.module_from_spec(spec)
spec.loader.exec_module(english_coach)


def write_plan(root: Path) -> None:
    data = root / "data"
    data.mkdir()
    (data / "plan.json").write_text(
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
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_plan(root)

            monday = english_coach.generate_today_task(root, date(2026, 7, 13))
            saturday = english_coach.generate_today_task(root, date(2026, 7, 18))

            self.assertEqual(monday["day_number"], 1)
            self.assertEqual(monday["minutes"], 30)
            self.assertEqual(monday["theme"], "professional self-introduction")
            self.assertEqual([block["minutes"] for block in monday["blocks"]], [5, 8, 7, 7, 3])
            self.assertEqual(saturday["day_number"], 6)
            self.assertEqual(saturday["minutes"], 60)
            self.assertEqual(saturday["theme"], "deep practice")

    def test_checkin_records_entry_and_summary_counts_streak(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
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
            )

            summary = english_coach.build_summary(root, date(2026, 7, 14), days=7)

            self.assertEqual(summary["completed_days"], 2)
            self.assertEqual(summary["current_streak"], 2)
            self.assertEqual(summary["longest_streak"], 2)
            self.assertEqual(summary["missed_dates"], [])
            self.assertEqual(summary["total_minutes"], 60)

    def test_summary_reports_missing_dates_without_breaking_longest_streak(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
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
            )

            summary = english_coach.build_summary(root, date(2026, 7, 15), days=3)

            self.assertEqual(summary["completed_days"], 2)
            self.assertEqual(summary["current_streak"], 1)
            self.assertEqual(summary["longest_streak"], 1)
            self.assertEqual(summary["missed_dates"], ["2026-07-14"])


if __name__ == "__main__":
    unittest.main()
