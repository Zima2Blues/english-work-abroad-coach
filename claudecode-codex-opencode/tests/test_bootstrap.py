import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bootstrap.py"
spec = importlib.util.spec_from_file_location("bootstrap", SCRIPT)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def test_requirements_file_declares_yaml_dependency(self):
        requirements = ROOT / "requirements.txt"

        self.assertTrue(requirements.exists())
        text = requirements.read_text(encoding="utf-8")
        self.assertIn("PyYAML", text)

    def test_bootstrap_plan_uses_local_venv_and_requirements(self):
        plan = bootstrap.build_bootstrap_plan(ROOT, sys.executable)

        self.assertEqual(plan["venv_dir"], str(ROOT / ".venv"))
        self.assertEqual(plan["requirements"], str(ROOT / "requirements.txt"))
        self.assertEqual(plan["create_venv"], [sys.executable, "-m", "venv", str(ROOT / ".venv")])
        self.assertIn("venv", plan["create_venv_uv"])
        self.assertIn(str(ROOT / ".venv"), plan["create_venv_uv"])
        self.assertIn("--python", plan["create_venv_uv"])
        self.assertIn(sys.executable, plan["create_venv_uv"])
        self.assertIn("--clear", plan["create_venv_uv"])
        self.assertIn("--seed", plan["create_venv_uv"])
        self.assertIn("-r", plan["install_requirements"])
        self.assertIn(str(ROOT / "requirements.txt"), plan["install_requirements"])
        self.assertEqual(plan["run_tests"][-4:], ["unittest", "discover", "-s", str(ROOT / "tests")])


if __name__ == "__main__":
    unittest.main()
