"""End-to-end checks against the live Codex plugin package."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests import PLUGIN, ROOT

from plugin_policy import (
    ALLOWED_PLUGIN_RELATIVE_PATHS,
    LINEAR_MCP_URL,
    collect_repo_errors,
    load_json,
    parse_skill_frontmatter,
    plugin_package_files,
    validate_repo,
)


class LivePackageE2ETests(unittest.TestCase):
    def test_validate_repo_accepts_the_checked_out_tree(self) -> None:
        validate_repo(ROOT)
        self.assertEqual(collect_repo_errors(ROOT), [])

    def test_codex_ingest_layout_matches_official_path_rules(self) -> None:
        manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["apps"], "./.app.json")
        self.assertEqual(manifest["mcpServers"], "./.mcp.json")
        self.assertTrue((PLUGIN / ".codex-plugin" / "plugin.json").is_file())
        self.assertTrue((PLUGIN / "skills" / "ores-engineering-ops" / "SKILL.md").is_file())
        self.assertFalse((PLUGIN / "hooks" / "hooks.json").exists())
        self.assertNotIn("hooks", manifest)
        shipped = set(plugin_package_files(PLUGIN))
        self.assertEqual(shipped, ALLOWED_PLUGIN_RELATIVE_PATHS)

    def test_mcp_is_remote_https_only_and_apps_are_oauth_connectors(self) -> None:
        mcp = load_json(PLUGIN / ".mcp.json")
        linear = mcp["mcpServers"]["linear"]
        self.assertEqual(linear["type"], "http")
        self.assertEqual(linear["url"], LINEAR_MCP_URL)
        self.assertNotIn("command", linear)
        self.assertNotIn("env", linear)
        apps = load_json(PLUGIN / ".app.json")["apps"]
        self.assertEqual(set(apps), {"github", "linear", "slack"})
        self.assertTrue(str(apps["github"]["id"]).startswith("connector_"))
        self.assertTrue(str(apps["linear"]["id"]).startswith("asdk_app_"))
        self.assertTrue(str(apps["slack"]["id"]).startswith("asdk_app_"))

    def test_skill_frontmatter_and_boundaries_are_installable(self) -> None:
        skill = (PLUGIN / "skills" / "ores-engineering-ops" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        frontmatter = parse_skill_frontmatter(skill)
        self.assertEqual(frontmatter["name"], "ores-engineering-ops")
        self.assertIn("GitHub", frontmatter["description"])
        boundaries = json.loads(
            (
                PLUGIN
                / "skills"
                / "ores-engineering-ops"
                / "references"
                / "boundaries.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(boundaries["linear"]["workspaceName"], "denman")
        self.assertEqual(boundaries["github"]["logins"], ["ORESoftware"])

    def test_marketplace_entry_points_at_the_plugin_folder(self) -> None:
        marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
        entry = marketplace["plugins"][0]
        resolved = (ROOT / entry["source"]["path"]).resolve()
        self.assertEqual(resolved, PLUGIN.resolve())
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")

    def test_legal_and_security_docs_are_linked(self) -> None:
        manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
        interface = manifest["interface"]
        for field, filename in (
            ("privacyPolicyURL", "PRIVACY.md"),
            ("termsOfServiceURL", "TERMS.md"),
        ):
            self.assertTrue(interface[field].endswith(filename))
            self.assertTrue((ROOT / filename).is_file())
        self.assertTrue((ROOT / "SECURITY.md").is_file())
        self.assertIn("mcp.linear.app", Path(ROOT / "SECURITY.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
