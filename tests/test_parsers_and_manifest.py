"""Unit tests for parsers, URL rules, and plugin.json contracts."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests import PLUGIN

from plugin_policy import (
    AUTHOR_EMAIL,
    AUTHOR_NAME,
    MAX_SCAN_BYTES,
    PLUGIN_NAME,
    find_secret_matches,
    load_json,
    parse_skill_frontmatter,
    require_https_url,
    scan_file_for_secrets,
    validate_plugin_manifest,
)


def _live_manifest() -> dict:
    return json.loads(
        (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )


class ParserTests(unittest.TestCase):
    def test_load_json_rejects_arrays_and_invalid_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            array_path = root / "array.json"
            array_path.write_text("[1, 2]\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_json(array_path)
            bad = root / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_json(bad)
            missing = root / "nope.json"
            with self.assertRaises(ValueError):
                load_json(missing)

    def test_frontmatter_rejects_unclosed_duplicate_and_empty_fields(self) -> None:
        with self.assertRaises(ValueError):
            parse_skill_frontmatter("no frontmatter\n")
        with self.assertRaises(ValueError):
            parse_skill_frontmatter("---\nname: x\n")
        with self.assertRaises(ValueError):
            parse_skill_frontmatter("---\nname: a\nname: b\n---\n")
        with self.assertRaises(ValueError):
            parse_skill_frontmatter("---\nname:\n---\n")
        parsed = parse_skill_frontmatter(
            '---\nname: ores-engineering-ops\ndescription: "ok"\n---\n\nbody\n'
        )
        self.assertEqual(parsed["name"], "ores-engineering-ops")
        self.assertEqual(parsed["description"], "ok")

    def test_https_url_rejects_http_and_userinfo(self) -> None:
        require_https_url("https://github.com/oresoftware", "ok")
        with self.assertRaises(ValueError):
            require_https_url("http://github.com/oresoftware", "field")
        with self.assertRaises(ValueError):
            require_https_url("https://user:pass@github.com/oresoftware", "field")
        with self.assertRaises(ValueError):
            require_https_url("/relative", "field")


class ExtraSecretShapeTests(unittest.TestCase):
    def test_detects_additional_github_slack_and_openai_shapes(self) -> None:
        blob = "\n".join(
            [
                "gho_" + ("A" * 36),
                "github_pat_" + ("B" * 22),
                "xoxe-1-" + ("C" * 12),
                "xapp-1-" + ("D" * 12),
                "sk-proj-" + ("E" * 24),
                "https://hooks.slack.com/services/" + ("F" * 16),
            ]
        )
        labels = {label for label, _preview in find_secret_matches(blob)}
        self.assertIn("github token", labels)
        self.assertIn("slack exchange token", labels)
        self.assertIn("slack app token", labels)
        self.assertIn("openai-style secret", labels)
        self.assertIn("slack webhook", labels)

    def test_binary_files_are_not_scanned_as_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "blob.bin"
            path.write_bytes(b"\0" + ("ghp_" + ("A" * 36)).encode("ascii"))
            self.assertEqual(scan_file_for_secrets(path), [])

    def test_oversize_file_is_rejected_without_reading_as_a_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "huge.txt"
            path.write_bytes(b"x" * (MAX_SCAN_BYTES + 1))
            errors = scan_file_for_secrets(path)
            self.assertTrue(any("secret-scan limit" in item for item in errors), errors)


class ManifestContractTests(unittest.TestCase):
    def test_live_manifest_is_accepted(self) -> None:
        self.assertEqual(validate_plugin_manifest(PLUGIN, _live_manifest()), [])

    def test_rejects_hooks_bad_semver_and_oversized_prompts(self) -> None:
        manifest = _live_manifest()
        manifest["hooks"] = "./hooks/hooks.json"
        manifest["version"] = "1.2"
        manifest["interface"]["defaultPrompt"] = ["x" * 129]
        manifest["interface"]["brandColor"] = "#fff"
        manifest["interface"]["privacyPolicyURL"] = "http://example.com/privacy"
        errors = "\n".join(validate_plugin_manifest(PLUGIN, manifest))
        self.assertIn("must not ship executable hooks", errors)
        self.assertIn("is not semver", errors)
        self.assertIn("1-128 characters", errors)
        self.assertIn("brandColor", errors)
        self.assertIn("https URL", errors)

    def test_rejects_non_github_legal_urls_and_wrong_author(self) -> None:
        manifest = _live_manifest()
        manifest["author"] = {"name": "Other", "email": "other@example.com"}
        manifest["interface"]["termsOfServiceURL"] = "https://example.com/terms"
        errors = "\n".join(validate_plugin_manifest(PLUGIN, manifest))
        self.assertIn(AUTHOR_NAME, errors)
        self.assertIn(AUTHOR_EMAIL, errors)
        self.assertIn("https GitHub URL", errors)

    def test_rejects_unexpected_package_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Copy is unnecessary: extra file next to a fake plugin root that
            # still contains the live files via symlink would follow. Write a
            # stub tree instead and reuse live relative layout.
            plugin = Path(tmp) / "plugin"
            plugin.mkdir()
            (plugin / ".codex-plugin").mkdir()
            (plugin / "skills" / "ores-engineering-ops" / "references").mkdir(
                parents=True
            )
            for rel in (
                ".codex-plugin/plugin.json",
                ".app.json",
                ".mcp.json",
                "skills/ores-engineering-ops/SKILL.md",
                "skills/ores-engineering-ops/references/boundaries.json",
            ):
                src = PLUGIN / rel
                dest = plugin / rel
                dest.write_bytes(src.read_bytes())
            (plugin / "extra.sh").write_text("echo hi\n", encoding="utf-8")
            errors = "\n".join(validate_plugin_manifest(plugin, _live_manifest()))
            self.assertIn("unexpected files", errors)
            self.assertIn("extra.sh", errors)

    def test_plugin_name_must_match(self) -> None:
        manifest = _live_manifest()
        manifest["name"] = "other-plugin"
        errors = "\n".join(validate_plugin_manifest(PLUGIN, manifest))
        self.assertIn(PLUGIN_NAME, errors)


if __name__ == "__main__":
    unittest.main()
