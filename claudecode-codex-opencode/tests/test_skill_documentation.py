import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parent
DISTRIBUTIONS = ("claudecode-codex-opencode", "openclaw", "hermes")


def read_frontmatter(skill_file):
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError("%s must start with YAML frontmatter" % skill_file)
    return yaml.safe_load(match.group(1))


class SkillDocumentationTests(unittest.TestCase):
    def test_skill_entrypoints_stay_within_200_lines(self):
        for distribution in DISTRIBUTIONS:
            skill_file = REPOSITORY_ROOT / distribution / "SKILL.md"
            self.assertLessEqual(
                len(skill_file.read_text(encoding="utf-8").splitlines()),
                200,
                skill_file,
            )

    def test_skill_descriptions_cover_core_coaching_triggers(self):
        required_terms = ("plan", "daily", "task", "check-in", "progress", "reminder")

        for distribution in DISTRIBUTIONS:
            frontmatter = read_frontmatter(REPOSITORY_ROOT / distribution / "SKILL.md")
            description = frontmatter["description"].lower()
            for term in required_terms:
                self.assertIn(term, description, "%s description lacks %s" % (distribution, term))

    def test_plan_references_keep_saved_state_outside_skill_folders(self):
        for distribution in DISTRIBUTIONS:
            reference = (
                REPOSITORY_ROOT / distribution / "references" / "plan-system.md"
            )
            text = reference.read_text(encoding="utf-8")

            self.assertNotIn("data/plan.json", text, reference)
            self.assertIn("external SQLite state directory", text, reference)

    def test_openai_default_prompt_uses_current_command_names(self):
        metadata = yaml.safe_load(
            (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        )
        prompt = metadata["interface"]["default_prompt"]

        self.assertIn("$english-work-abroad-coach", prompt)
        for command in ("today", "checkin", "summary", "reminder"):
            self.assertRegex(prompt, r"\b%s\b" % command)


if __name__ == "__main__":
    unittest.main()
