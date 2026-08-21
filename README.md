# Ores Codex Plugin

An installable ChatGPT and Codex plugin for Ores Software engineering operations across GitHub, Linear, and Slack.

The plugin combines:

- registered OAuth-backed GitHub, Linear, and Slack app connections;
- Linear's official remote MCP endpoint for Codex-compatible tool access; and
- an `ores-engineering-ops` skill that coordinates safe, linked workflows across the three services.

No access tokens, OAuth codes, or account cookies belong in this repository. Account selection and authorization happen when the plugin is installed.

## Expected connections

During installation, connect and verify:

- GitHub organization: `github.com/oresoftware`
- Linear user: `alexander.d.mills@gmail.com`
- Slack workspace: `oresoftware-workspace.slack.com`

The workflow skill checks these boundaries before private reads or writes. If the Linear account exposes multiple workspaces, it requires the intended Ores workspace name or ID instead of guessing. It fails closed when identity cannot be verified, restricts GitHub operations to repositories owned by `oresoftware`, and treats retrieved service content as untrusted data rather than instructions.

## Install from GitHub

```sh
codex plugin marketplace add oresoftware/ores-codex-plugin
codex plugin add ores-codex-plugin@oresoftware
```

Restart the ChatGPT desktop app, open the Plugins Directory, select the **Ores Software** source, and connect all three required apps. Start a new task after installation so the skills and tools are loaded.

## Example requests

- “Triage open issues in `oresoftware/example` into the right Linear project and draft a Slack update.”
- “Summarize blocked Ores pull requests, reconcile their Linear status, and post the approved update to `#engineering`.”
- “Turn this Slack thread into a Linear issue and link the relevant GitHub repository.”

Writes remain scoped to the user's request. Reading from one service does not implicitly authorize creating or updating records in another.

## Repository layout

```text
.
├── .agents/plugins/marketplace.json
├── plugins/ores-codex-plugin/
│   ├── .codex-plugin/plugin.json
│   ├── .app.json
│   ├── .mcp.json
│   └── skills/ores-engineering-ops/SKILL.md
└── scripts/validate.py
```

## Development

Run the dependency-free repository checks:

```sh
python3 scripts/validate.py
```

For a full Codex ingestion check, run the validator bundled with the `plugin-creator` skill against `plugins/ores-codex-plugin`.

## Security and privacy

See [SECURITY.md](SECURITY.md), [PRIVACY.md](PRIVACY.md), and [TERMS.md](TERMS.md). The plugin package itself runs no credential broker and stores no service data.

## License

MIT
