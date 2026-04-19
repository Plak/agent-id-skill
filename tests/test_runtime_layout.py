from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]


class RuntimeLayoutTests(unittest.TestCase):
    def test_spec_exists(self):
        self.assertTrue((REPO / "docs/specs/runtime-variants.md").is_file())

    def test_runtime_directories_exist(self):
        for path in [
            REPO / "openclaw/agent-id-io",
            REPO / "claude/agent-id-io",
            REPO / "openai/agent-id-io",
        ]:
            with self.subTest(path=path):
                self.assertTrue(path.is_dir())

    def test_openclaw_variant_has_skill_file(self):
        self.assertTrue((REPO / "openclaw/agent-id-io/SKILL.md").is_file())

    def test_claude_variant_has_expected_files(self):
        base = REPO / "claude/agent-id-io"
        for rel in [
            "README.md",
            "CLAUDE.md",
            "references/api.md",
            "requirements.txt",
            "scripts/keygen.py",
            "scripts/authenticate.py",
        ]:
            with self.subTest(rel=rel):
                self.assertTrue((base / rel).is_file())

    def test_openai_variant_has_expected_files(self):
        base = REPO / "openai/agent-id-io"
        for rel in [
            "README.md",
            "AGENTS.md",
            "CHATGPT.md",
            "references/api.md",
            "requirements.txt",
            "scripts/keygen.py",
            "scripts/authenticate.py",
        ]:
            with self.subTest(rel=rel):
                self.assertTrue((base / rel).is_file())

    def test_root_readme_mentions_all_runtimes(self):
        readme = (REPO / "README.md").read_text()
        for token in ["openclaw/agent-id-io", "claude/agent-id-io", "openai/agent-id-io"]:
            with self.subTest(token=token):
                self.assertIn(token, readme)

    def test_runtime_entrypoints_contain_verification_bias(self):
        checks = {
            REPO / "claude/agent-id-io/CLAUDE.md": ["verify", "state-changing", "references/api.md"],
            REPO / "openai/agent-id-io/AGENTS.md": ["Verify", "mutating", "references/api.md"],
            REPO / "openai/agent-id-io/CHATGPT.md": ["verify", "mutating", "references/api.md"],
        }
        for path, tokens in checks.items():
            text = path.read_text()
            for token in tokens:
                with self.subTest(path=path, token=token):
                    self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
