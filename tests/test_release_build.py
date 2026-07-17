import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = "english-work-abroad-coach"
RELEASE_PREFLIGHT_ENV = "ENGLISH_COACH_SKIP_RELEASE_PACKAGE_TESTS"
EXPECTED_VERSION = "0.2.0"


def load_module(test_case):
    path = ROOT / "tools" / "build_release.py"
    test_case.assertTrue(path.exists(), "Missing implementation: tools/build_release.py")
    spec = importlib.util.spec_from_file_location("build_release", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipIf(
    os.environ.get(RELEASE_PREFLIGHT_ENV) == "1",
    "release-package tests are excluded from release preflight",
)
class ReleaseBuildTests(unittest.TestCase):
    def test_release_version_is_consistent_across_metadata_readme_and_filenames(self):
        release = load_module(self)

        self.assertEqual(release.RELEASE_VERSION, EXPECTED_VERSION)
        self.assertEqual(
            release.archive_filename("openclaw"),
            "english-work-abroad-coach-0.2.0-openclaw.zip",
        )
        self.assertIn('version: "0.2.0"', (ROOT / "openclaw" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn('version: "0.2.0"', (ROOT / "hermes" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("Release: 0.2.0", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_each_release_archive_is_sanitized_self_contained_and_runnable(self):
        release = load_module(self)
        required_paths = {
            "SKILL.md",
            "scripts/bootstrap.py",
            "scripts/english_coach.py",
            "references/learning-science.md",
            "references/material-sources.md",
            "references/plan-system.md",
            "data/default-plan.json",
        }

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dist"
            for distribution in release.DISTRIBUTIONS:
                with self.subTest(distribution=distribution):
                    archive = release.build_release(ROOT, distribution, output_dir)
                    self.assertEqual(archive.name, release.archive_filename(distribution))

                    with zipfile.ZipFile(archive) as package:
                        names = package.namelist()
                        self.assertTrue(names)
                        self.assertTrue(
                            all(
                                name == PACKAGE_ROOT + "/"
                                or name.startswith(PACKAGE_ROOT + "/")
                                for name in names
                            )
                        )
                        packaged_paths = {
                            name[len(PACKAGE_ROOT) + 1 :]
                            for name in names
                            if name.startswith(PACKAGE_ROOT + "/")
                        }
                        self.assertTrue(required_paths.issubset(packaged_paths))
                        self.assertFalse(
                            any("/tests/" in name for name in names),
                            "release archives must not contain development test fixtures",
                        )
                        self.assertFalse(
                            any(
                                ".venv/" in name
                                or "__pycache__/" in name
                                or ".pytest_cache/" in name
                                or name.endswith("/data/checkins.jsonl")
                                or name.endswith("/data/reminder.log")
                                or name.endswith("/coach.db")
                                or "/coach.db-" in name
                                for name in names
                            )
                        )

                    extraction_root = Path(tmp) / (distribution + "-extracted")
                    with zipfile.ZipFile(archive) as package:
                        package.extractall(extraction_root)
                    installed_skill = extraction_root / PACKAGE_ROOT
                    state_home = Path(tmp) / (distribution + "-state")
                    environment = os.environ.copy()
                    environment["XDG_STATE_HOME"] = str(state_home)
                    completed = subprocess.run(
                        [sys.executable, "scripts/english_coach.py", "today", "--json"],
                        cwd=str(installed_skill),
                        env=environment,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False,
                    )
                    self.assertEqual(
                        completed.returncode,
                        0,
                        completed.stdout + completed.stderr,
                    )
                    self.assertEqual(json.loads(completed.stdout)["minutes"], 30)

    def test_preflight_failure_does_not_create_an_archive(self):
        release = load_module(self)

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "dist"
            with mock.patch.object(release, "run_preflight", return_value=1):
                with self.assertRaisesRegex(RuntimeError, "release preflight failed"):
                    release.build_release(ROOT, "openclaw", output_dir)

            self.assertFalse(output_dir.exists())

    def test_publish_check_requires_an_explicit_license_without_blocking_local_builds(self):
        release = load_module(self)

        with tempfile.TemporaryDirectory() as tmp:
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                result = release.main(["--root", tmp, "--publish-check"])

        self.assertEqual(result, 1)
        self.assertEqual(error.getvalue().strip(), "LICENSE file is required for public release")


if __name__ == "__main__":
    unittest.main()
