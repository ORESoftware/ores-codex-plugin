# Codex evented PR review integration

Driver: `ORESoftware/ores-gh-bots#9`

This is a bounded review contract for an independently mergeable slice of the driver issue. It does not claim full rollout or implementation.

## Invariants

- Review one immutable PR head and invalidate results after synchronize/head change.
- Keep prompt/context inputs bounded and exclude secrets or decrypted configuration.
- Return review evidence in a deterministic form that the review bot can bind to head SHA.
- Plugin failure must leave the merge gate pending/fail-closed rather than synthesizing approval.

## Verification

- Bind evidence to the exact PR/source revision.
- Add or retain fail-closed negative coverage around untrusted inputs.
- Keep credentials and sensitive payloads out of fixtures, logs, and review text.
- Treat missing or zero-step CI as missing evidence.

## Non-goals

This contract does not bypass branch protection or create new secret-delivery channels.
