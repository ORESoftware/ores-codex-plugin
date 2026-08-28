"""End-to-end checks that unsafe plugin packages fail closed."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests import PLUGIN, ROOT

from plugin_policy import collect_repo_errors


def _copy_live_repo(dest: Path) -> None:
    shutil.copytree(ROOT / ".agents", dest / ".agents")
    shutil.copytree(PLUGIN, dest / "plugins" / "ores-codex-plugin")
    for name in ("SECURITY.md", "PRIVACY.md", "TERMS.md", "README.md"):
        shutil.copy2(ROOT / name, dest / name)


class UnsafePackageE2ETests(unittest.TestCase):
    def test_stdio_mcp_with_env_token_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_live_repo(root)
            mcp_path = root / "plugins" / "ores-codex-plugin" / ".mcp.json"
            mcp_path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "linear": {
                                "type": "stdio",
                                "command": "npx",
                                "args": ["-y", "@modelcontextprotocol/server-github"],
                                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "from-env"},
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            errors = "\n".join(collect_repo_errors(root))
            self.assertIn("forbidden fields", errors)
            self.assertIn("from-env", errors)

    def test_path_escape_in_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_live_repo(root)
            manifest_path = (
                root / "plugins" / "ores-codex-plugin" / ".codex-plugin" / "plugin.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["skills"] = "./skills/../../secrets/"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = "\n".join(collect_repo_errors(root))
            self.assertIn("escapes its root", errors)

    def test_wrong_linear_workspace_in_boundaries_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_live_repo(root)
            boundaries_path = (
                root
                / "plugins"
                / "ores-codex-plugin"
                / "skills"
                / "ores-engineering-ops"
                / "references"
                / "boundaries.json"
            )
            payload = json.loads(boundaries_path.read_text(encoding="utf-8"))
            payload["linear"]["workspaceName"] = "someone-elses-workspace"
            boundaries_path.write_text(json.dumps(payload), encoding="utf-8")
            errors = "\n".join(collect_repo_errors(root))
            self.assertIn("workspaceName", errors)

    def test_committed_github_token_in_plugin_package_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_live_repo(root)
            leaked = root / "plugins" / "ores-codex-plugin" / "skills" / "ores-engineering-ops" / "SKILL.md"
            original = leaked.read_text(encoding="utf-8")
            leaked.write_text(original + "\n" + "ghp_" + ("Z" * 36) + "\n", encoding="utf-8")
            errors = "\n".join(collect_repo_errors(root))
            self.assertIn("github token", errors)

    def test_undeclared_hook_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _copy_live_repo(root)
            hooks = root / "plugins" / "ores-codex-plugin" / "hooks"
            hooks.mkdir()
            (hooks / "hooks.json").write_text(
                json.dumps({"hooks": {"SessionStart": []}}),
                encoding="utf-8",
            )
            errors = "\n".join(collect_repo_errors(root))
            self.assertTrue(
                "hooks/hooks.json" in errors or "unexpected files" in errors,
                errors,
            )


if __name__ == "__main__":
    unittest.main()
