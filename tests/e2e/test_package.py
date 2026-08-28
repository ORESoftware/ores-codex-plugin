"""End-to-end checks against the real plugin repository."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from tests import PLUGIN, ROOT, SCRIPTS

from plugin_policy import collect_repo_errors


class LivePackageTests(unittest.TestCase):
    def test_repository_validator_is_clean(self) -> None:
        self.assertEqual(collect_repo_errors(ROOT), [])

    def test_plugin_package_contains_only_allowlisted_files(self) -> None:
        allowed = {
            ".codex-plugin/plugin.json",
            ".app.json",
            ".mcp.json",
            "skills/ores-engineering-ops/SKILL.md",
            "skills/ores-engineering-ops/references/boundaries.json",
        }
        found: set[str] = set()
        for current, dirnames, filenames in os.walk(PLUGIN, followlinks=False):
            dirnames[:] = [name for name in dirnames if name != "__pycache__"]
            for name in filenames:
                path = Path(current) / name
                found.add(path.relative_to(PLUGIN).as_posix())
        self.assertEqual(found, allowed)

    def test_codex_plugin_dir_contains_only_plugin_json(self) -> None:
        names = sorted(
            path.name
            for path in (PLUGIN / ".codex-plugin").iterdir()
            if not path.name.startswith(".")
        )
        self.assertEqual(names, ["plugin.json"])

    def test_cli_validate_exits_zero(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate.py")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Validation passed", completed.stdout)

    def test_json_contracts_exist_and_parse(self) -> None:
        for name in (
            "plugin.schema.json",
            "marketplace.schema.json",
            "app.schema.json",
            "mcp.schema.json",
            "boundaries.schema.json",
        ):
            path = ROOT / "schemas" / name
            self.assertTrue(path.is_file(), name)
            json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
