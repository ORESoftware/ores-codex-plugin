# Ores Codex Plugin

Installable ChatGPT/Codex plugin. Work in this checkout.

- Plugin package: `plugins/ores-codex-plugin`
- Validator: `python3 scripts/validate.py`
- Tests: `python3 -m unittest discover -s tests -p 'test_*.py' -v`
- Identity allowlist: `plugins/ores-codex-plugin/skills/ores-engineering-ops/references/boundaries.json`

Do not add executable hooks, stdio MCP servers, or credential env vars to the plugin package. Do not commit tokens. Do not revoke live tokens unless a human confirms a leak and asks for rotation.

Primary GitHub identity is `ORESoftware`. Linear workspace is `denman`. Slack workspace is `oresoftware-workspace.slack.com` (`T01B3C83PMK`).
