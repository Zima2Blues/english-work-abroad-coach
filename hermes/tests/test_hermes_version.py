import importlib.util
import json
import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_frontmatter():
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError("SKILL.md must start with YAML frontmatter")
    return yaml.safe_load(match.group(1))


class HermesVersionTests(unittest.TestCase):
    def test_skill_frontmatter_declares_hermes_metadata(self):
        frontmatter = read_frontmatter()

        self.assertEqual(frontmatter["name"], "english-work-abroad-coach")
        self.assertIn("Hermes", frontmatter["description"])
        self.assertNotIn("hermes", frontmatter)
        self.assertIn("metadata", frontmatter)
        self.assertIn("hermes", frontmatter["metadata"])
        hermes = frontmatter["metadata"]["hermes"]
        self.assertEqual(hermes["displayName"], "English Work Abroad Coach")
        self.assertEqual(hermes["version"], "0.2.0")
        self.assertIn("daily-coach", hermes["tags"])
        self.assertEqual(hermes["requires"]["anyBins"], ["python3", "python", "uv"])

    def test_hermes_blueprint_defines_daily_reminder(self):
        hermes = read_frontmatter()["metadata"]["hermes"]
        blueprint = hermes["blueprint"]

        self.assertEqual(blueprint["id"], "daily-english-reminder")
        self.assertEqual(blueprint["schedule"]["cron"], "0 21 * * *")
        self.assertEqual(blueprint["schedule"]["timezone"], "local")
        self.assertIn("reminder_runner.py", blueprint["command"])
        self.assertIn("today's study task", blueprint["prompt"])

    def test_hermes_files_are_self_contained(self):
        expected = [
            "SKILL.md",
            "requirements-dev.txt",
            "scripts/bootstrap.py",
            "scripts/english_coach.py",
            "scripts/reminder_runner.py",
            "references/learning-science.md",
            "references/material-sources.md",
            "references/plan-system.md",
            "data/default-plan.json",
            "tests/test_runtime_smoke.py",
        ]

        for relative in expected:
            self.assertTrue((ROOT / relative).exists(), relative)

        self.assertFalse((ROOT / "README.md").exists())
        self.assertFalse((ROOT / "scripts" / "install_reminder.py").exists())

    def test_default_plan_identifies_hermes_version_without_runtime_templates(self):
        plan = json.loads(
            (ROOT / "data" / "default-plan.json").read_text(encoding="utf-8")
        )

        self.assertEqual(plan["distribution"], "hermes")
        self.assertEqual(plan["goals"]["goal_500_days"], "Reach work-abroad readiness through ten 50-day cycles.")
        self.assertFalse((ROOT / "data" / "plan.json").exists())
        self.assertFalse((ROOT / "data" / "progress.json").exists())

    def test_english_coach_script_imports_from_hermes_folder(self):
        script = ROOT / "scripts" / "english_coach.py"
        spec = importlib.util.spec_from_file_location("english_coach_hermes", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        task = module.generate_today_task(ROOT, module.parse_date("2026-07-14"))

        self.assertEqual(task["day_number"], 1)
        self.assertEqual(task["minutes"], 30)
        self.assertEqual(task["theme"], "current work")


if __name__ == "__main__":
    unittest.main()
