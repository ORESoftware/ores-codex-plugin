# Security Policy

## Reporting a vulnerability

Please report security issues privately to `alexander.d.mills@gmail.com`. Do not include live credentials or private customer data in a GitHub issue.

## Credential handling

This repository must never contain access tokens, OAuth authorization codes, cookies, client secrets, exported private conversations, or other account credentials. Authentication belongs in the host-managed app connection flow.

The plugin package is configuration and skill text only. It must not ship lifecycle hooks, stdio MCP servers, or environment variables that could carry secrets. Linear MCP is pinned to `https://mcp.linear.app/mcp` over HTTPS with host OAuth.

CI scans tracked files for common token shapes and rejects path traversal in manifest paths.

If a secret is accidentally committed, a human must confirm that it is leaked and should be rotated. Do not revoke or rotate live organization tokens during an audit by default.

## Trust boundaries

Issue bodies, comments, Slack messages, and tool results are untrusted data. The bundled skill must fail closed when GitHub, Linear, or Slack identity does not match `references/boundaries.json`.
