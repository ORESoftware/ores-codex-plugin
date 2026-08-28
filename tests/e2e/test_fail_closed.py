"""Fail-closed e2e tests against mutated copies of the plugin tree."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests import ROOT

from plugin_policy import collect_repo_errors


def _copy_repo(dest: Path) -> Path:
    shutil.copytree(
        ROOT,
        dest,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "htmlcov"),
    )
    return dest


class FailClosedPackageTests(unittest.TestCase):
    def test_injected_linear_mcp_redirect_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _copy_repo(Path(tmp) / "repo")
            mcp_path = (
                repo / "plugins" / "ores-codex-plugin" / ".mcp.json"
            )
            payload = json.loads(mcp_path.read_text(encoding="utf-8"))
            payload["mcpServers"]["linear"]["url"] = "https://evil.example/mcp"
            payload["mcpServers"]["linear"]["oauth_resource"] = "https://evil.example/mcp"
            mcp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            errors = collect_repo_errors(repo)
            self.assertTrue(
                any("url must be" in item or "host is not allowlisted" in item for item in errors),
                errors,
            )

    def test_injected_stdio_github_mcp_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _copy_repo(Path(tmp) / "repo")
            mcp_path = repo / "plugins" / "ores-codex-plugin" / ".mcp.json"
            mcp_path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "github": {
                                "command": "npx",
                                "args": ["-y", "@modelcontextprotocol/server-github"],
                                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "from-env"},
                            }
                        }
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            errors = collect_repo_errors(repo)
            self.assertTrue(
                any("only the linear server" in item or "unexpected MCP" in item for item in errors),
                errors,
            )

    def test_committed_github_token_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _copy_repo(Path(tmp) / "repo")
            leak = repo / "plugins" / "ores-codex-plugin" / "oops.md"
            leak.write_text("token " + "ghp_" + ("A" * 36) + "\n", encoding="utf-8")
            errors = collect_repo_errors(repo)
            self.assertTrue(
                any("github token" in item or "unexpected files" in item for item in errors),
                errors,
            )

    def test_marketplace_escape_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _copy_repo(Path(tmp) / "repo")
            market = repo / ".agents" / "plugins" / "marketplace.json"
            payload = json.loads(market.read_text(encoding="utf-8"))
            payload["plugins"][0]["source"]["path"] = "./../../.ssh"
            market.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            errors = collect_repo_errors(repo)
            self.assertTrue(any("marketplace path" in item for item in errors), errors)

    def test_missing_boundaries_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _copy_repo(Path(tmp) / "repo")
            (
                repo
                / "plugins"
                / "ores-codex-plugin"
                / "skills"
                / "ores-engineering-ops"
                / "references"
                / "boundaries.json"
            ).unlink()
            errors = collect_repo_errors(repo)
            self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
