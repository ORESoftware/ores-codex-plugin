# Security Policy

## Reporting a vulnerability

Please report security issues privately to `alexander.d.mills@gmail.com`. Do not include live credentials or private customer data in a GitHub issue.

## Credential handling

This repository must never contain access tokens, OAuth authorization codes, cookies, client secrets, exported private conversations, or other account credentials. Authentication belongs in the host-managed app connection flow.

If a secret is accidentally committed, revoke it with the service provider immediately and then remove it from Git history.
