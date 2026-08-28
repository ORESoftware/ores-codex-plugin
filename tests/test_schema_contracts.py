"""Check live manifests against the checked-in JSON Schema contracts."""

from __future__ import annotations

import json
import unittest
from typing import Any

from tests import PLUGIN, ROOT

from plugin_policy import load_json


def _schema(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def _assert_object_matches_schema(
    test: unittest.TestCase, payload: dict[str, Any], schema: dict[str, Any], label: str
) -> None:
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    for key in required:
        test.assertIn(key, payload, f"{label} missing required {key}")
    extra = set(payload) - set(properties)
    if schema.get("additionalProperties") is False:
        test.assertEqual(extra, set(), f"{label} extra fields: {sorted(extra)}")
    for key, subschema in properties.items():
        if key not in payload:
            continue
        value = payload[key]
        if "const" in subschema:
            test.assertEqual(value, subschema["const"], f"{label}.{key}")
        expected_type = subschema.get("type")
        if expected_type == "string":
            test.assertIsInstance(value, str, label)
            if subschema.get("minLength"):
                test.assertGreaterEqual(len(value), subschema["minLength"], label)
            if "pattern" in subschema:
                import re

                test.assertRegex(value, subschema["pattern"], f"{label}.{key}")
        elif expected_type == "array":
            test.assertIsInstance(value, list, label)
            if "minItems" in subschema:
                test.assertGreaterEqual(len(value), subschema["minItems"], label)
            if "maxItems" in subschema:
                test.assertLessEqual(len(value), subschema["maxItems"], label)
            item_schema = subschema.get("items", {})
            if item_schema.get("type") == "string":
                for item in value:
                    test.assertIsInstance(item, str, label)
                    if "maxLength" in item_schema:
                        test.assertLessEqual(len(item), item_schema["maxLength"], label)
                    if "enum" in item_schema:
                        test.assertIn(item, item_schema["enum"], label)
            elif item_schema.get("type") == "object":
                for item in value:
                    test.assertIsInstance(item, dict, label)
                    _assert_object_matches_schema(
                        test, item, item_schema, f"{label}[]"
                    )
        elif expected_type == "object":
            test.assertIsInstance(value, dict, label)
            _assert_object_matches_schema(test, value, subschema, f"{label}.{key}")


class SchemaContractTests(unittest.TestCase):
    def test_plugin_manifest_matches_schema(self) -> None:
        _assert_object_matches_schema(
            self,
            load_json(PLUGIN / ".codex-plugin" / "plugin.json"),
            _schema("plugin.schema.json"),
            "plugin.json",
        )

    def test_marketplace_matches_schema(self) -> None:
        _assert_object_matches_schema(
            self,
            load_json(ROOT / ".agents" / "plugins" / "marketplace.json"),
            _schema("marketplace.schema.json"),
            "marketplace.json",
        )

    def test_app_mcp_and_boundaries_match_schema(self) -> None:
        _assert_object_matches_schema(
            self,
            load_json(PLUGIN / ".app.json"),
            _schema("app.schema.json"),
            ".app.json",
        )
        _assert_object_matches_schema(
            self,
            load_json(PLUGIN / ".mcp.json"),
            _schema("mcp.schema.json"),
            ".mcp.json",
        )
        _assert_object_matches_schema(
            self,
            load_json(
                PLUGIN
                / "skills"
                / "ores-engineering-ops"
                / "references"
                / "boundaries.json"
            ),
            _schema("boundaries.schema.json"),
            "boundaries.json",
        )

    def test_interface_prompts_fit_codex_limits(self) -> None:
        manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
        prompts = manifest["interface"]["defaultPrompt"]
        self.assertLessEqual(len(prompts), 3)
        for prompt in prompts:
            self.assertLessEqual(len(prompt), 128)
            self.assertGreater(len(prompt), 0)


if __name__ == "__main__":
    unittest.main()
