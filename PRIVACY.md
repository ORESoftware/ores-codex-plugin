# Privacy

Ores Codex Plugin is a configuration and workflow package. This repository does not operate a server, collect credentials, or persist GitHub, Linear, or Slack content.

When the plugin is installed, ChatGPT or Codex connects to the selected third-party accounts through registered app integrations and, for Linear, its remote MCP endpoint at `https://mcp.linear.app/mcp`. Data handling is therefore also governed by the policies of OpenAI, GitHub, Linear, Slack, and the organization that administers the connected accounts. The intended Linear workspace is `denman`.

Do not commit tokens, OAuth codes, cookies, private exports, or other credentials to this repository. To revoke access, disconnect the corresponding app in ChatGPT or Codex and revoke its authorization with the service provider.

Privacy questions may be sent to `alexander.d.mills@gmail.com`.
