import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "english_coach.py"
spec = importlib.util.spec_from_file_location("english_coach_runtime", SCRIPT)
english_coach = importlib.util.module_from_spec(spec)
spec.loader.exec_module(english_coach)


class RuntimeSmokeTests(unittest.TestCase):
    def test_today_runs_with_standard_library_only(self):
        task = english_coach.generate_today_task(ROOT, english_coach.parse_date("2026-07-14"))

        self.assertEqual(task["date"], "2026-07-14")
        self.assertEqual(task["minutes"], 30)
        self.assertEqual(task["theme"], "current work")


if __name__ == "__main__":
    unittest.main()
