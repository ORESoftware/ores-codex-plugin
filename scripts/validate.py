#!/usr/bin/env python3
"""Validate the repository's marketplace and plugin package without dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "ores-codex-plugin"
MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
APP_MANIFEST = PLUGIN / ".app.json"
MCP_MANIFEST = PLUGIN / ".mcp.json"
SKILL = PLUGIN / "skills" / "ores-engineering-ops" / "SKILL.md"


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError(f"{path.relative_to(ROOT)}: {exc}") from exc


def check_relative_path(raw: str) -> None:
    assert raw.startswith("./"), f"manifest path must start with ./: {raw}"
    resolved = (PLUGIN / raw).resolve()
    assert resolved.is_relative_to(PLUGIN.resolve()), f"path escapes plugin root: {raw}"
    assert resolved.exists(), f"manifest path does not exist: {raw}"


def main() -> int:
    manifest = load_json(MANIFEST)
    marketplace = load_json(MARKETPLACE)
    apps = load_json(APP_MANIFEST)
    mcp = load_json(MCP_MANIFEST)

    assert manifest["name"] == "ores-codex-plugin"
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", manifest["version"])
    assert manifest["author"]["name"] == "Ores Software"
    for field in ("skills", "apps", "mcpServers"):
        check_relative_path(manifest[field])

    prompts = manifest["interface"]["defaultPrompt"]
    assert isinstance(prompts, list) and 1 <= len(prompts) <= 3
    assert all(isinstance(prompt, str) and len(prompt) <= 128 for prompt in prompts)

    expected_apps = {
        "github": "connector_76869538009648d5b282a4bb21c3d157",
        "linear": "asdk_app_69a089a326dc8191b32a3f2553f5be2c",
        "slack": "asdk_app_69a1d78e929881919bba0dbda1f6436d",
    }
    assert {name: config.get("id") for name, config in apps["apps"].items()} == expected_apps
    assert mcp["mcpServers"]["linear"]["url"] == "https://mcp.linear.app/mcp"

    assert marketplace["name"] == "oresoftware"
    entry = next(item for item in marketplace["plugins"] if item["name"] == manifest["name"])
    assert entry["source"]["path"] == "./plugins/ores-codex-plugin"
    assert entry["policy"] == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}

    skill_text = SKILL.read_text()
    assert skill_text.startswith("---\n") and "[TODO:" not in skill_text

    tracked_text = "\n".join(
        path.read_text(errors="ignore")
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )
    assert not re.search(r"(?:ghp|github_pat|xox[baprs]|lin_api)_[A-Za-z0-9_-]{12,}", tracked_text)

    print("Validation passed: marketplace, plugin manifest, apps, MCP, skill, and secret scan")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, StopIteration) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
