#!/usr/bin/env python3
"""Validate the marketplace, plugin package, skill policy, and secret scan."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from plugin_policy import collect_repo_errors


ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root to validate (default: this checkout)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    errors = collect_repo_errors(args.root.expanduser().resolve())
    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        "Validation passed: marketplace, plugin manifest, apps, MCP allowlist, "
        "skill policy, package layout, and secret scan"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
