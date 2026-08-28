"""Unit tests for MCP and app-manifest hardening."""

from __future__ import annotations

import unittest

from plugin_policy import (
    EXPECTED_APPS,
    LINEAR_MCP_URL,
    validate_app_ids,
    validate_mcp_config,
    validate_mcp_server,
)


class McpHardeningTests(unittest.TestCase):
    def test_official_linear_remote_config_is_accepted(self) -> None:
        errors = validate_mcp_config(
            {
                "mcpServers": {
                    "linear": {
                        "type": "http",
                        "url": LINEAR_MCP_URL,
                        "oauth_resource": LINEAR_MCP_URL,
                    }
                }
            }
        )
        self.assertEqual(errors, [])

    def test_rejects_stdio_command_and_env_blocks(self) -> None:
        errors = validate_mcp_server(
            "linear",
            {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "from-env"},
            },
        )
        self.assertTrue(any("forbidden fields" in item or "secret fields" in item for item in errors))
        self.assertTrue(any("type must be http" in item for item in errors))

    def test_rejects_non_linear_host_and_embedded_credentials(self) -> None:
        errors = validate_mcp_server(
            "linear",
            {
                "type": "http",
                "url": "https://user:pass@evil.example/mcp?token=1#frag",
                "oauth_resource": "https://evil.example/mcp",
            },
        )
        joined = "\n".join(errors)
        self.assertIn("url must be", joined)
        self.assertIn("without credentials", joined)
        self.assertIn("query or fragment", joined)

    def test_rejects_unexpected_server_name(self) -> None:
        errors = validate_mcp_config(
            {
                "mcpServers": {
                    "github": {"type": "http", "url": LINEAR_MCP_URL},
                    "linear": {"type": "http", "url": LINEAR_MCP_URL},
                }
            }
        )
        self.assertTrue(any("only the linear server" in item for item in errors))

    def test_registered_app_ids_are_pinned(self) -> None:
        self.assertEqual(
            validate_app_ids(
                {
                    "github": {"id": EXPECTED_APPS["github"], "category": "Developer Tools"},
                    "linear": {"id": EXPECTED_APPS["linear"], "category": "Productivity"},
                    "slack": {"id": EXPECTED_APPS["slack"], "category": "Communication"},
                }
            ),
            [],
        )
        errors = validate_app_ids(
            {
                "github": {"id": "connector_other", "category": "Developer Tools"},
                "linear": {"id": EXPECTED_APPS["linear"], "category": "Productivity"},
                "slack": {"id": EXPECTED_APPS["slack"], "category": "Communication"},
            }
        )
        self.assertTrue(any("registered app ids" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
