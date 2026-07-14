import contextlib
import importlib.util
import io
import sys
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bootstrap.py"
spec = importlib.util.spec_from_file_location("bootstrap", SCRIPT)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def test_development_requirements_declare_yaml_dependency(self):
        requirements = ROOT / "requirements-dev.txt"

        self.assertTrue(requirements.exists())
        text = requirements.read_text(encoding="utf-8")
        self.assertIn("PyYAML", text)
        self.assertFalse((ROOT / "requirements.txt").exists())

    def test_require_supported_python_rejects_python_37(self):
        self.assertTrue(hasattr(bootstrap, "require_supported_python"))

        with self.assertRaisesRegex(RuntimeError, "Python 3.9 or newer") as raised:
            bootstrap.require_supported_python((3, 7, 3), "/usr/bin/python3.7")

        self.assertIn("/usr/bin/python3.7", str(raised.exception))
        self.assertIn("3.7.3", str(raised.exception))
        self.assertIn("uv python install 3.12", str(raised.exception))

    def test_require_supported_python_accepts_python_312(self):
        self.assertTrue(hasattr(bootstrap, "require_supported_python"))

        version = bootstrap.require_supported_python((3, 12, 0), "/opt/python3.12")

        self.assertEqual(version, (3, 12, 0))

    def test_probe_python_version_reads_selected_interpreter(self):
        self.assertTrue(hasattr(bootstrap, "probe_python_version"))

        version = bootstrap.probe_python_version(sys.executable)

        self.assertEqual(version[:2], sys.version_info[:2])

    def test_main_reports_unsupported_interpreter_without_traceback(self):
        error = io.StringIO()
        with mock.patch.object(bootstrap, "probe_python_version", return_value=(3, 7, 3)):
            with contextlib.redirect_stderr(error):
                try:
                    result = bootstrap.main(["--python", "/usr/bin/python3.7", "--dry-run"])
                except RuntimeError as exc:
                    self.fail("main leaked RuntimeError instead of returning 1: %s" % exc)

        self.assertEqual(result, 1)
        self.assertIn("ERROR: Python 3.9 or newer is required", error.getvalue())
        self.assertNotIn("Traceback", error.getvalue())

    def test_bootstrap_plan_uses_local_venv_and_requirements(self):
        plan = bootstrap.build_bootstrap_plan(ROOT, sys.executable)

        self.assertEqual(plan["venv_dir"], str(ROOT / ".venv"))
        self.assertIn("requirements_dev", plan)
        self.assertEqual(plan["requirements_dev"], str(ROOT / "requirements-dev.txt"))
        self.assertEqual(plan["create_venv"], [sys.executable, "-m", "venv", str(ROOT / ".venv")])
        self.assertIn("venv", plan["create_venv_uv"])
        self.assertIn(str(ROOT / ".venv"), plan["create_venv_uv"])
        self.assertIn("--python", plan["create_venv_uv"])
        self.assertIn(sys.executable, plan["create_venv_uv"])
        self.assertIn("--clear", plan["create_venv_uv"])
        self.assertIn("--seed", plan["create_venv_uv"])
        self.assertNotIn("upgrade_pip", plan)
        self.assertIn("install_dev_requirements", plan)
        self.assertIn("-r", plan["install_dev_requirements"])
        self.assertIn(str(ROOT / "requirements-dev.txt"), plan["install_dev_requirements"])
        self.assertIn("run_runtime_tests", plan)
        self.assertEqual(plan["run_runtime_tests"][-3:], ["-p", "test_runtime_smoke.py", "-v"])
        self.assertIn("run_dev_tests", plan)
        self.assertEqual(plan["run_dev_tests"][-4:], ["unittest", "discover", "-s", str(ROOT / "tests")])


if __name__ == "__main__":
    unittest.main()
