# Ores Codex Plugin

Installable ChatGPT/Codex plugin. Work in this checkout.

- Plugin package: `plugins/ores-codex-plugin`
- Validator: `python3 scripts/validate.py`
- Tests: `python3 -m unittest discover -s tests -p 'test_*.py' -v`
- Identity allowlist: `plugins/ores-codex-plugin/skills/ores-engineering-ops/references/boundaries.json`

Do not add executable hooks, stdio MCP servers, or credential env vars to the plugin package. Do not commit tokens. Do not revoke live tokens unless a human confirms a leak and asks for rotation.

Primary GitHub identity is `ORESoftware`. Linear workspace is `denman`. Slack workspace is `oresoftware-workspace.slack.com` (`T01B3C83PMK`).

<!-- BEGIN ores-agents-pointer: managed by ORESoftware/my-ai; edit there, not here -->

## Canonical agent instructions

Before doing anything else in this repository, also read:

    .ores/agents/AGENTS.md

That path is a symlink to `~/codes/oresoftware/my-ai/AGENTS.md`, whose canonical copy is
<https://github.com/ORESoftware/my-ai/blob/main/AGENTS.md>.

It exists at a fixed path *inside* the repository because some agents cannot walk up past
the repository root, so machine-wide instructions one or more directories above are
invisible to them. This pointer plus that path make the same file reachable from a working
directory anywhere in the tree.

The symlink is deliberately **not committed**: it names an absolute path that is only valid
on a machine with `~/codes/oresoftware/my-ai` checked out, so committing it would produce a
broken link for everyone else and for CI. `.ores/` is git-ignored for that reason. If
`.ores/agents/AGENTS.md` is missing on your machine, create it with:

    mkdir -p .ores/agents
    ln -sfn "$HOME/codes/oresoftware/my-ai/AGENTS.md" .ores/agents/AGENTS.md

or run `~/codes/oresoftware/my-ai/scripts/link-repo-agents.sh` once to do it for every git
repository under `~/codes`, and `--check` to verify them.

A missing `.ores/agents/AGENTS.md` is a setup gap on the reader's machine, never a reason to
skip the canonical instructions: fetch them from the URL above instead.

<!-- END ores-agents-pointer -->
