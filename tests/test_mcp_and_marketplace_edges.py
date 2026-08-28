"""Additional negative cases for MCP wrapping and marketplace sources."""

from __future__ import annotations

import unittest

from tests import ROOT

from plugin_policy import (
    LINEAR_MCP_URL,
    validate_app_ids,
    validate_marketplace,
    validate_mcp_config,
    validate_mcp_server,
)


class McpEdgeTests(unittest.TestCase):
    def test_accepts_mcp_servers_snake_case_alias(self) -> None:
        errors = validate_mcp_config(
            {
                "mcp_servers": {
                    "linear": {
                        "type": "http",
                        "url": LINEAR_MCP_URL,
                        "oauth_resource": LINEAR_MCP_URL,
                    }
                }
            }
        )
        self.assertEqual(errors, [])

    def test_rejects_both_mcp_key_spellings(self) -> None:
        errors = validate_mcp_config(
            {
                "mcpServers": {"linear": {"type": "http", "url": LINEAR_MCP_URL}},
                "mcp_servers": {"linear": {"type": "http", "url": LINEAR_MCP_URL}},
            }
        )
        self.assertTrue(any("both mcpServers and mcp_servers" in item for item in errors))

    def test_rejects_empty_and_non_object_servers(self) -> None:
        self.assertTrue(validate_mcp_config({"mcpServers": {}}))
        self.assertTrue(validate_mcp_config({"mcpServers": []}))
        errors = validate_mcp_server("linear", "https://mcp.linear.app/mcp")
        self.assertTrue(any("must be an object" in item for item in errors))

    def test_rejects_http_cleartext_and_headers(self) -> None:
        errors = validate_mcp_server(
            "linear",
            {
                "type": "http",
                "url": "http://mcp.linear.app/mcp",
                "headers": {"Authorization": "Bearer x"},
            },
        )
        joined = "\n".join(errors)
        self.assertIn("url must be", joined)
        self.assertTrue("https URL" in joined or "forbidden fields" in joined)
        self.assertIn("secret fields", joined)

    def test_rejects_app_unknown_fields_and_non_objects(self) -> None:
        errors = validate_app_ids("nope")
        self.assertTrue(any("must be an object" in item for item in errors))
        errors = validate_app_ids(
            {
                "github": {"id": "x", "category": "Developer Tools", "token": "n"},
            }
        )
        self.assertTrue(any("unknown fields" in item or "registered app ids" in item for item in errors))


class MarketplaceEdgeTests(unittest.TestCase):
    def test_rejects_git_and_npm_remote_sources(self) -> None:
        errors = validate_marketplace(
            ROOT,
            {
                "name": "oresoftware",
                "plugins": [
                    {
                        "name": "ores-codex-plugin",
                        "source": {
                            "source": "git-subdir",
                            "url": "https://github.com/example/plugins.git",
                            "path": "./plugins/ores-codex-plugin",
                        },
                        "policy": {
                            "installation": "AVAILABLE",
                            "authentication": "ON_INSTALL",
                        },
                    }
                ],
            },
            "ores-codex-plugin",
        )
        self.assertTrue(any("must be local" in item for item in errors), errors)

    def test_rejects_missing_plugin_entry_and_wrong_marketplace_name(self) -> None:
        errors = validate_marketplace(
            ROOT,
            {"name": "personal", "plugins": []},
            "ores-codex-plugin",
        )
        self.assertTrue(any("oresoftware" in item or "non-empty" in item for item in errors))
        errors = validate_marketplace(
            ROOT,
            {
                "name": "oresoftware",
                "plugins": [{"name": "other", "source": {"source": "local", "path": "./x"}}],
            },
            "ores-codex-plugin",
        )
        self.assertTrue(any("missing plugin" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
