import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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
    def test_build_systemd_units_quote_paths_and_pass_explicit_state_dir(self):
        root = Path("/tmp/English Coach")
        state_dir = Path("/tmp/English Coach State")
        units = install_reminder.build_systemd_units(root, "21:00", state_dir)

        self.assertIn("WorkingDirectory=/tmp/English\\x20Coach", units["service"])
        self.assertIn(
            'ExecStart="/tmp/English Coach/.venv/bin/python"',
            units["service"],
        )
        self.assertIn(
            '"/tmp/English Coach/scripts/reminder_runner.py"',
            units["service"],
        )
        self.assertIn('--root "/tmp/English Coach"', units["service"])
        self.assertIn('--state-dir "/tmp/English Coach State"', units["service"])
        self.assertIn("OnCalendar=*-*-* 21:00:00", units["timer"])
        self.assertIn("Persistent=true", units["timer"])
        self.assertIn("WantedBy=timers.target", units["timer"])

    def test_quote_systemd_value_escapes_percent_backslash_and_double_quote(self):
        value = '/tmp/English Coach % "quoted"\\tail/${HOME}'

        quoted = install_reminder.quote_systemd_value(value)

        self.assertEqual(
            quoted,
            '"/tmp/English Coach %% \\"quoted\\"\\\\tail/$${HOME}"',
        )

    def test_escape_systemd_path_encodes_path_directive_characters(self):
        value = '/tmp/English Coach % "quoted"\\tail'

        escaped = install_reminder.escape_systemd_path(value)

        self.assertEqual(
            escaped,
            "/tmp/English\\x20Coach\\x20%%\\x20\\x22quoted\\x22\\x5ctail",
        )

    def test_dry_run_writes_quoted_units_without_calling_systemctl(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "English Coach"
            python = root / ".venv" / "bin" / "python"
            python.parent.mkdir(parents=True)
            python.touch()
            state_dir = Path(tmp) / "English Coach State"
            systemd_dir = Path(tmp) / "systemd"
            output = io.StringIO()

            with mock.patch.object(install_reminder.subprocess, "run") as run:
                with contextlib.redirect_stdout(output):
                    result = install_reminder.main(
                        [
                            "--root",
                            str(root),
                            "--state-dir",
                            str(state_dir),
                            "--time",
                            "21:00",
                            "--dry-run",
                            "--systemd-user-dir",
                            str(systemd_dir),
                        ]
                    )

            service = (systemd_dir / "english-work-abroad-coach.service").read_text(
                encoding="utf-8"
            )
            self.assertEqual(result, 0)
            run.assert_not_called()
            self.assertIn(
                'ExecStart="%s"' % (root / ".venv" / "bin" / "python"),
                service,
            )
            self.assertIn('--state-dir "%s"' % state_dir, service)

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
