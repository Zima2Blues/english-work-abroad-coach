import importlib.util
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


def create_distribution_tree(root, shared_paths):
    for distribution in ("claudecode-codex-opencode", "openclaw", "hermes"):
        base = root / distribution
        (base / "SKILL.md").parent.mkdir(parents=True, exist_ok=True)
        (base / "SKILL.md").write_text("platform=%s\n" % distribution, encoding="utf-8")
        for relative in shared_paths:
            path = base / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("shared:%s\n" % relative, encoding="utf-8")


class DistributionSyncTests(unittest.TestCase):
    def test_shared_paths_use_development_requirements_and_runtime_smoke_test(self):
        sync = load_module(self, "sync_distributions_manifest", "tools/sync_distributions.py")

        self.assertIn("requirements-dev.txt", sync.SHARED_PATHS)
        self.assertIn("tests/test_runtime_smoke.py", sync.SHARED_PATHS)
        self.assertNotIn("requirements.txt", sync.SHARED_PATHS)

    def test_repository_shared_files_match_canonical_distribution(self):
        sync = load_module(self, "sync_distributions", "tools/sync_distributions.py")

        self.assertEqual(sync.find_mismatches(ROOT), [])

    def test_find_mismatches_reports_distribution_and_path(self):
        sync = load_module(self, "sync_distributions_mismatch", "tools/sync_distributions.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_distribution_tree(root, sync.SHARED_PATHS)
            changed = root / "openclaw" / "scripts" / "english_coach.py"
            changed.write_text("platform drift\n", encoding="utf-8")

            mismatches = sync.find_mismatches(root)

        self.assertEqual(mismatches, ["openclaw/scripts/english_coach.py"])

    def test_synchronize_repairs_shared_files_without_touching_skill_metadata(self):
        sync = load_module(self, "sync_distributions_write", "tools/sync_distributions.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_distribution_tree(root, sync.SHARED_PATHS)
            changed = root / "hermes" / "scripts" / "bootstrap.py"
            changed.write_text("platform drift\n", encoding="utf-8")
            hermes_skill = root / "hermes" / "SKILL.md"
            original_skill = hermes_skill.read_bytes()

            copied = sync.synchronize(root)

            self.assertEqual(copied, [changed])
            self.assertEqual(sync.find_mismatches(root), [])
            self.assertEqual(hermes_skill.read_bytes(), original_skill)

    def test_project_verification_plan_includes_sync_check(self):
        load_module(self, "sync_distributions_plan", "tools/sync_distributions.py")
        verify = load_module(self, "verify_project_with_sync", "tools/verify_project.py")

        plan = verify.build_verification_plan(ROOT)

        self.assertEqual(len(plan["sync"]), 1)
        self.assertEqual(plan["sync"][0][-1], "--check")


if __name__ == "__main__":
    unittest.main()
