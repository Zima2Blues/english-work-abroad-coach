import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    script = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


install_reminder = load_script("install_reminder.py")
reminder_runner = load_script("reminder_runner.py")


class ReminderInstallerTests(unittest.TestCase):
    def test_build_systemd_units_use_local_venv_and_default_time(self):
        units = install_reminder.build_systemd_units(ROOT, "21:00")

        self.assertIn(str(ROOT / ".venv" / "bin" / "python"), units["service"])
        self.assertIn(str(ROOT / "scripts" / "reminder_runner.py"), units["service"])
        self.assertIn("--root %s" % ROOT, units["service"])
        self.assertIn("OnCalendar=*-*-* 21:00:00", units["timer"])
        self.assertIn("Persistent=true", units["timer"])
        self.assertIn("WantedBy=timers.target", units["timer"])

    def test_validate_time_accepts_hh_mm_and_rejects_invalid_values(self):
        self.assertEqual(install_reminder.validate_time("09:05"), "09:05")
        self.assertEqual(install_reminder.validate_time("21:00"), "21:00")

        with self.assertRaises(ValueError):
            install_reminder.validate_time("24:00")
        with self.assertRaises(ValueError):
            install_reminder.validate_time("21:60")
        with self.assertRaises(ValueError):
            install_reminder.validate_time("9:5")

    def test_runner_builds_notification_text_from_reminder_result(self):
        result = {
            "date": "2026-07-13",
            "checked_in": False,
            "task": {
                "minutes": 30,
                "theme": "professional self-introduction",
                "day_number": 1,
            },
        }

        title, body = reminder_runner.build_notification(result)

        self.assertEqual(title, "English check-in missing")
        self.assertIn("Day 1", body)
        self.assertIn("30 min", body)
        self.assertIn("professional self-introduction", body)


if __name__ == "__main__":
    unittest.main()
