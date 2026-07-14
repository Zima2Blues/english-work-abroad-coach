import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(test_case, name, relative_path):
    path = ROOT / relative_path
    test_case.assertTrue(path.exists(), "Missing implementation: %s" % relative_path)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerifyProjectTests(unittest.TestCase):
    def test_verification_plan_covers_all_distributions(self):
        verify_project = load_module(self, "verify_project", "tools/verify_project.py")

        plan = verify_project.build_verification_plan(ROOT)

        self.assertIn("project_tests", plan)
        self.assertEqual(plan["project_tests"], ROOT / "tests")
        self.assertEqual(
            [item["name"] for item in plan["tests"]],
            ["claudecode-codex-opencode", "openclaw", "hermes"],
        )
        self.assertEqual(len(plan["skill_validation"]), 3)
        self.assertIn("sync", plan)

    def test_local_validator_accepts_valid_skill(self):
        validate_skill = load_module(self, "validate_skill", "tools/validate_skill.py")
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "valid-skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\n"
                "name: valid-skill\n"
                "description: Use when a valid test skill is needed.\n"
                "---\n\n"
                "# Valid Skill\n",
                encoding="utf-8",
            )

            errors = validate_skill.validate_skill(skill)

        self.assertEqual(errors, [])

    def test_local_validator_rejects_missing_description(self):
        validate_skill = load_module(self, "validate_skill_invalid", "tools/validate_skill.py")
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "invalid-skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: invalid-skill\n---\n\n# Invalid Skill\n",
                encoding="utf-8",
            )

            errors = validate_skill.validate_skill(skill)

        self.assertIn("description is required", errors)

    def test_missing_external_validator_is_reported_as_skipped(self):
        verify_project = load_module(self, "verify_project_skip", "tools/verify_project.py")
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            result = verify_project.run_external_validation(ROOT, validator=None)

        self.assertEqual(result, 0)
        self.assertIn("SKIP: external skill validator not configured", output.getvalue())


if __name__ == "__main__":
    unittest.main()
