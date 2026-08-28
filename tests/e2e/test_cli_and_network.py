"""CLI and network end-to-end checks."""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from tests import PLUGIN, ROOT, SCRIPTS

from plugin_policy import LINEAR_MCP_URL


def _copy_validatable_repo(dest: Path) -> Path:
    shutil.copytree(ROOT / ".agents", dest / ".agents")
    shutil.copytree(PLUGIN, dest / "plugins" / "ores-codex-plugin")
    shutil.copytree(ROOT / "schemas", dest / "schemas")
    for name in ("SECURITY.md", "PRIVACY.md", "TERMS.md", "README.md"):
        shutil.copy2(ROOT / name, dest / name)
    return dest


def _run_validate(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "validate.py"), *args],
        cwd=cwd or ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


class ValidateCliE2ETests(unittest.TestCase):
    def test_cli_passes_the_live_checkout(self) -> None:
        completed = _run_validate()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Validation passed", completed.stdout)

    def test_cli_fails_on_mutated_mcp_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _copy_validatable_repo(Path(tmp) / "repo")
            mcp_path = repo / "plugins" / "ores-codex-plugin" / ".mcp.json"
            payload = json.loads(mcp_path.read_text(encoding="utf-8"))
            payload["mcpServers"]["linear"]["url"] = "https://evil.example/mcp"
            mcp_path.write_text(json.dumps(payload), encoding="utf-8")
            completed = _run_validate("--root", str(repo))
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Validation failed", completed.stderr)
            self.assertIn("url must be", completed.stderr)

    def test_cli_fails_on_injected_stdio_github_server(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = _copy_validatable_repo(Path(tmp) / "repo")
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
                    }
                ),
                encoding="utf-8",
            )
            completed = _run_validate("--root", str(repo))
            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue(
                "only the linear server" in completed.stderr
                or "unexpected MCP" in completed.stderr,
                completed.stderr,
            )

    def test_cli_help_does_not_validate(self) -> None:
        completed = _run_validate("--help")
        self.assertEqual(completed.returncode, 0)
        self.assertIn("--root", completed.stdout)


class LinearMcpNetworkE2ETests(unittest.TestCase):
    def test_linear_mcp_host_resolves(self) -> None:
        try:
            infos = socket.getaddrinfo("mcp.linear.app", 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            self.skipTest(f"dns unavailable: {exc}")
        self.assertTrue(infos)

    def test_linear_mcp_https_endpoint_responds(self) -> None:
        request = urllib.request.Request(
            LINEAR_MCP_URL,
            method="GET",
            headers={
                "Accept": "application/json, text/event-stream",
                "User-Agent": "ores-codex-plugin-tests",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status = response.status
        except urllib.error.HTTPError as exc:
            status = exc.code
            exc.close()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            self.skipTest(f"network unavailable: {exc}")
        self.assertGreaterEqual(status, 200)
        self.assertLess(status, 600)

    def test_plugin_does_not_ship_cleartext_linear_url(self) -> None:
        mcp = (PLUGIN / ".mcp.json").read_text(encoding="utf-8")
        self.assertNotIn("http://mcp.linear.app", mcp)
        self.assertIn(LINEAR_MCP_URL, mcp)


if __name__ == "__main__":
    unittest.main()
