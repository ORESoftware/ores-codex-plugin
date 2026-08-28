"""Unit tests for skill and marketplace contracts."""

from __future__ import annotations

import unittest

from tests import PLUGIN, ROOT

from plugin_policy import (
    parse_skill_frontmatter,
    skill_policy_gaps,
    validate_boundaries,
    validate_marketplace,
    validate_skill_contract,
    boundaries_from_skill_dir,
    load_json,
)


class SkillContractTests(unittest.TestCase):
    def test_live_skill_satisfies_frontmatter_and_policy_phrases(self) -> None:
        text = (PLUGIN / "skills" / "ores-engineering-ops" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        frontmatter = parse_skill_frontmatter(text)
        self.assertEqual(frontmatter["name"], "ores-engineering-ops")
        self.assertEqual(validate_skill_contract(text), [])
        self.assertEqual(skill_policy_gaps(text), [])

    def test_missing_fail_closed_and_workspace_markers_are_reported(self) -> None:
        thin = "---\nname: ores-engineering-ops\ndescription: thin\n---\n\nhello\n"
        errors = validate_skill_contract(thin)
        self.assertTrue(any("fail closed" in item for item in errors))
        self.assertTrue(any("linear.app/denman" in item for item in errors))


class MarketplaceAndBoundaryTests(unittest.TestCase):
    def test_live_marketplace_requires_on_install_auth(self) -> None:
        marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
        self.assertEqual(
            validate_marketplace(ROOT, marketplace, "ores-codex-plugin"),
            [],
        )

    def test_rejects_marketplace_path_escape_and_wrong_policy(self) -> None:
        errors = validate_marketplace(
            ROOT,
            {
                "name": "oresoftware",
                "plugins": [
                    {
                        "name": "ores-codex-plugin",
                        "source": {"source": "local", "path": "./../etc"},
                        "policy": {
                            "installation": "INSTALLED_BY_DEFAULT",
                            "authentication": "ON_USE",
                        },
                    }
                ],
            },
            "ores-codex-plugin",
        )
        joined = "\n".join(errors)
        self.assertIn("marketplace path must be", joined)
        self.assertIn("ON_INSTALL", joined)

    def test_live_boundaries_json_matches_pinned_identities(self) -> None:
        payload = boundaries_from_skill_dir(
            PLUGIN / "skills" / "ores-engineering-ops"
        )
        self.assertEqual(validate_boundaries(payload), [])
        mutated = dict(payload)
        mutated["github"] = dict(payload["github"], logins=["the1mills"])
        errors = validate_boundaries(mutated)
        self.assertTrue(any("github.logins" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
