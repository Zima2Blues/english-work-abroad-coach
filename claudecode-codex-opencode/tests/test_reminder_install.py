import contextlib
import importlib.util
import io
import json
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


class ReminderUninstallTests(unittest.TestCase):
    def _write_units(self, systemd_dir):
        paths = install_reminder.unit_paths(systemd_dir)
        paths["service"].parent.mkdir(parents=True, exist_ok=True)
        paths["service"].write_text("[Unit]\nDescription=test\n", encoding="utf-8")
        paths["timer"].write_text("[Unit]\nDescription=test\n", encoding="utf-8")
        return paths

    def test_uninstall_disables_removes_units_and_reloads_daemon(self):
        with tempfile.TemporaryDirectory() as tmp:
            systemd_dir = Path(tmp) / "systemd"
            unit_names = self._write_units(systemd_dir)
            state_dir = Path(tmp) / "state"
            state_dir.mkdir()
            marker = state_dir / "coach.db"
            marker.write_text("keep", encoding="utf-8")

            with mock.patch.object(install_reminder.subprocess, "run") as run:
                removed = install_reminder.uninstall(
                    Path(tmp), systemd_user_dir=systemd_dir
                )

            commands = [call.args[0] for call in run.call_args_list]
            self.assertIn(
                ["systemctl", "--user", "disable", "--now",
                 "english-work-abroad-coach.timer"],
                commands,
            )
            self.assertIn(["systemctl", "--user", "daemon-reload"], commands)
            self.assertEqual(removed, sorted(unit_names.values()))
            self.assertFalse(unit_names["service"].exists())
            self.assertFalse(unit_names["timer"].exists())
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_uninstall_dry_run_keeps_units_and_does_not_call_systemctl(self):
        with tempfile.TemporaryDirectory() as tmp:
            systemd_dir = Path(tmp) / "systemd"
            unit_names = self._write_units(systemd_dir)
            output = io.StringIO()

            with mock.patch.object(install_reminder.subprocess, "run") as run:
                with contextlib.redirect_stdout(output):
                    result = install_reminder.main(
                        ["--uninstall", "--dry-run",
                         "--systemd-user-dir", str(systemd_dir)]
                    )

            self.assertEqual(result, 0)
            run.assert_not_called()
            self.assertTrue(unit_names["service"].exists())
            self.assertTrue(unit_names["timer"].exists())

    def test_uninstall_tolerates_missing_unit_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            systemd_dir = Path(tmp) / "systemd"
            with mock.patch.object(install_reminder.subprocess, "run"):
                removed = install_reminder.uninstall(
                    Path(tmp), systemd_user_dir=systemd_dir
                )
            self.assertEqual(removed, [])


class ReminderRunnerDisabledTests(unittest.TestCase):
    def test_runner_skips_notification_when_reminders_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / "state"
            english_coach = reminder_runner.load_english_coach()
            english_coach.store_for(state_dir).set_reminders_enabled(False)
            output = io.StringIO()

            with mock.patch.object(reminder_runner, "notify") as notify:
                with contextlib.redirect_stdout(output):
                    reminder_runner.main(
                        [
                            "--root",
                            str(ROOT),
                            "--state-dir",
                            str(state_dir),
                            "--date",
                            "2026-07-13",
                            "--json",
                        ]
                    )

            payload = json.loads(output.getvalue())
            notify.assert_not_called()
            self.assertFalse(payload["notification"]["sent"])
            self.assertTrue(payload["notification"]["disabled"])
            log_lines = (state_dir / "reminder.log").read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertTrue(
                any(
                    json.loads(line)["reason"] == "disabled"
                    for line in log_lines
                )
            )


if __name__ == "__main__":
    unittest.main()
