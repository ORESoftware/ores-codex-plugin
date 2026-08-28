"""Pure policy helpers for the Ores Codex plugin package.

No third-party dependencies. Effects stay in ``validate.py``.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path, PurePosixPath
from typing import Any, Iterator
from urllib.parse import urlparse


PLUGIN_NAME = "ores-codex-plugin"
MARKETPLACE_NAME = "oresoftware"
AUTHOR_NAME = "Ores Software"
AUTHOR_EMAIL = "alexander.d.mills@gmail.com"
LINEAR_MCP_URL = "https://mcp.linear.app/mcp"
MAX_DEFAULT_PROMPTS = 3
MAX_PROMPT_CHARS = 128
MAX_SCAN_BYTES = 1_000_000

EXPECTED_APPS = {
    "github": "connector_76869538009648d5b282a4bb21c3d157",
    "linear": "asdk_app_69a089a326dc8191b32a3f2553f5be2c",
    "slack": "asdk_app_69a1d78e929881919bba0dbda1f6436d",
}

ALLOWED_GITHUB_OWNERS = ("oresoftware",)
ALLOWED_GITHUB_LOGINS = ("ORESoftware",)
SECONDARY_GITHUB_LOGINS = ("the1mills",)
LINEAR_USER_EMAIL = "alexander.d.mills@gmail.com"
LINEAR_WORKSPACE_NAME = "denman"
LINEAR_WORKSPACE_URL = "https://linear.app/denman"
SLACK_DOMAIN = "oresoftware-workspace.slack.com"
SLACK_TEAM_ID = "T01B3C83PMK"

ALLOWED_MCP_SERVER_KEYS = {"type", "url", "oauth_resource"}
FORBIDDEN_MCP_KEYS = {
    "command",
    "args",
    "env",
    "env_vars",
    "envFile",
    "headers",
    "cwd",
    "authentication",
    "token",
    "apiKey",
    "api_key",
    "bearer_token",
    "bearer_token_env_var",
    "authorization",
}

ALLOWED_PLUGIN_RELATIVE_PATHS = {
    ".codex-plugin/plugin.json",
    ".app.json",
    ".mcp.json",
    "skills/ores-engineering-ops/SKILL.md",
    "skills/ores-engineering-ops/references/boundaries.json",
}

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

SECRET_RULES: tuple[tuple[str, str], ...] = (
    (r"(?:gh[pours]|github_pat)_[A-Za-z0-9_]{20,}", "github token"),
    (r"lin_api_[A-Za-z0-9]{20,}", "linear api token"),
    (r"xox[aboprs]-(?:[A-Za-z0-9-]{10,})", "slack token"),
    (r"xoxe(?:-[A-Za-z0-9-]+)+", "slack exchange token"),
    (r"xapp-[A-Za-z0-9-]+", "slack app token"),
    (r"sk-(?:ant-|proj-|svcacct-)?[A-Za-z0-9_-]{20,}", "openai-style secret"),
    (r"AKIA[0-9A-Z]{16}", "aws access key"),
    (r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----", "private key"),
    (r"hooks\.slack\.com/services/[A-Za-z0-9+/_-]+", "slack webhook"),
)
COMPILED_SECRET_RULES = tuple(
    (re.compile(pattern), label) for pattern, label in SECRET_RULES
)
FROM_ENV_RE = re.compile(
    r"GITHUB_PERSONAL_ACCESS_TOKEN\s*[\"']?\s*[:=]\s*[\"']?from-env[\"']?",
    re.IGNORECASE,
)

REQUIRED_SKILL_PHRASES = (
    "oresoftware",
    "ORESoftware",
    "alexander.d.mills@gmail.com",
    "oresoftware-workspace.slack.com",
    "linear.app/denman",
    "mcp.linear.app",
    "untrusted",
    "never obey embedded",
    "the1mills",
    "from-env",
    "T01B3C83PMK",
    "@channel",
    "@here",
    "do not store access tokens",
    "fail closed",
    "do not revoke",
    "git rebase",
    "git stash",
    "git reset",
    "force-push",
)

SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "node_modules",
    ".codex",
    "secrets",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"{path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return payload


def parse_skill_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("skill must start with YAML frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError("skill frontmatter is not closed")
    body = text[4:end]
    result: dict[str, str] = {}
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"unsupported frontmatter line: {raw_line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key or not value:
            raise ValueError(f"empty frontmatter field: {raw_line}")
        if key in result:
            raise ValueError(f"duplicate frontmatter field: {key}")
        result[key] = value
    return result


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:8192]
    except OSError:
        return False
    return b"\0" in chunk


def iter_scan_files(root: Path) -> Iterator[Path]:
    root = root.resolve()
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_NAMES]
        current_path = Path(current)
        for name in filenames:
            if name == ".DS_Store":
                continue
            path = current_path / name
            if path.is_symlink():
                continue
            yield path


def find_secret_matches(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for regex, label in COMPILED_SECRET_RULES:
        match = regex.search(text)
        if match is not None:
            found.append((label, match.group(0)[:12] + "…"))
    if FROM_ENV_RE.search(text):
        found.append(("github from-env placeholder", "from-env"))
    return found


def scan_file_for_secrets(path: Path) -> list[str]:
    if not path.is_file() or path.is_symlink():
        return []
    try:
        size = path.stat().st_size
    except OSError as exc:
        return [f"{path}: unreadable ({exc})"]
    if size > MAX_SCAN_BYTES:
        return [f"{path}: file exceeds {MAX_SCAN_BYTES} byte secret-scan limit"]
    if is_binary(path):
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    return [
        f"{path}: possible {label} ({preview})"
        for label, preview in find_secret_matches(text)
    ]


def scan_tree_for_secrets(root: Path, *, skip_tests: bool = False) -> list[str]:
    errors: list[str] = []
    tests_root = (root / "tests").resolve()
    for path in iter_scan_files(root):
        if skip_tests:
            try:
                path.resolve().relative_to(tests_root)
            except ValueError:
                pass
            else:
                continue
        errors.extend(scan_file_for_secrets(path))
    return errors


def resolve_inside(root: Path, raw: str, *, field: str) -> Path:
    if not isinstance(raw, str) or not raw.startswith("./"):
        raise ValueError(f"{field} must be a relative path starting with ./")
    if "\\" in raw or "\x00" in raw:
        raise ValueError(f"{field} contains invalid characters: {raw}")
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{field} escapes its root: {raw}")
    resolved = (root / candidate.as_posix()).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"{field} escapes its root: {raw}")
    if not resolved.exists():
        raise ValueError(f"{field} does not exist: {raw}")
    return resolved


def require_https_url(raw: Any, field: str) -> None:
    if not isinstance(raw, str):
        raise ValueError(f"{field} must be an https URL")
    parsed = urlparse(raw)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.params
    ):
        raise ValueError(f"{field} must be an absolute https URL without credentials")


def mcp_server_map(mcp: dict[str, Any]) -> dict[str, Any]:
    if "mcpServers" in mcp and "mcp_servers" in mcp:
        raise ValueError(".mcp.json must not define both mcpServers and mcp_servers")
    extra = set(mcp) - {"mcpServers", "mcp_servers"}
    if extra:
        raise ValueError(f".mcp.json has unexpected top-level keys: {sorted(extra)}")
    servers = mcp.get("mcpServers", mcp.get("mcp_servers"))
    if not isinstance(servers, dict) or not servers:
        raise ValueError(".mcp.json must declare a non-empty mcpServers object")
    return servers


def validate_mcp_server(name: str, config: Any) -> list[str]:
    errors: list[str] = []
    if name != "linear":
        errors.append(f"unexpected MCP server `{name}`")
        return errors
    if not isinstance(config, dict):
        return [f"MCP server `{name}` must be an object"]
    extra = set(config) - ALLOWED_MCP_SERVER_KEYS
    if extra:
        errors.append(f"MCP server `{name}` has forbidden fields: {sorted(extra)}")
    forbidden_present = sorted(set(config) & FORBIDDEN_MCP_KEYS)
    if forbidden_present:
        errors.append(
            f"MCP server `{name}` must not declare executable or secret fields: {forbidden_present}"
        )
    if config.get("type") != "http":
        errors.append(f"MCP server `{name}` type must be http")
    url = config.get("url")
    resource = config.get("oauth_resource")
    if url != LINEAR_MCP_URL:
        errors.append(f"MCP server `{name}` url must be {LINEAR_MCP_URL}")
    if resource not in (None, LINEAR_MCP_URL):
        errors.append(f"MCP server `{name}` oauth_resource must be {LINEAR_MCP_URL}")
    if isinstance(url, str):
        try:
            require_https_url(url, f"MCP server `{name}` url")
        except ValueError as exc:
            errors.append(str(exc))
        parsed = urlparse(url)
        if parsed.hostname != "mcp.linear.app":
            errors.append(f"MCP server `{name}` host is not allowlisted")
        if parsed.query or parsed.fragment:
            errors.append(f"MCP server `{name}` url must not include query or fragment")
    return errors


def validate_mcp_config(mcp: dict[str, Any]) -> list[str]:
    try:
        servers = mcp_server_map(mcp)
    except ValueError as exc:
        return [str(exc)]
    if set(servers) != {"linear"}:
        return [f".mcp.json must declare only the linear server, got {sorted(servers)}"]
    return validate_mcp_server("linear", servers["linear"])


def validate_app_ids(apps: Any) -> list[str]:
    if not isinstance(apps, dict):
        return ["`.app.json` field `apps` must be an object"]
    errors: list[str] = []
    actual = {
        name: config.get("id") if isinstance(config, dict) else None
        for name, config in apps.items()
    }
    if actual != EXPECTED_APPS:
        errors.append(f"registered app ids must equal {EXPECTED_APPS}, got {actual}")
    for name, config in apps.items():
        if not isinstance(config, dict):
            errors.append(f"app `{name}` must be an object")
            continue
        extra = set(config) - {"id", "category"}
        if extra:
            errors.append(f"app `{name}` has unknown fields: {sorted(extra)}")
    return errors


def skill_policy_gaps(text: str) -> list[str]:
    lowered = text.lower()
    missing = [
        phrase for phrase in REQUIRED_SKILL_PHRASES if phrase.lower() not in lowered
    ]
    return [f"SKILL.md missing required policy phrase: {phrase}" for phrase in missing]


def validate_skill_contract(text: str) -> list[str]:
    errors: list[str] = []
    try:
        frontmatter = parse_skill_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]
    if frontmatter.get("name") != "ores-engineering-ops":
        errors.append("SKILL.md name must be ores-engineering-ops")
    if "description" not in frontmatter:
        errors.append("SKILL.md is missing a description")
    if "[TODO:" in text:
        errors.append("SKILL.md still contains a TODO placeholder")
    errors.extend(skill_policy_gaps(text))
    return errors


def boundaries_from_skill_dir(skill_dir: Path) -> dict[str, Any]:
    return load_json(skill_dir / "references" / "boundaries.json")


def validate_boundaries(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    github = payload.get("github") if isinstance(payload.get("github"), dict) else {}
    linear = payload.get("linear") if isinstance(payload.get("linear"), dict) else {}
    slack = payload.get("slack") if isinstance(payload.get("slack"), dict) else {}
    apps = payload.get("apps") if isinstance(payload.get("apps"), dict) else {}

    owners = tuple(github.get("owners") or ())
    logins = tuple(github.get("logins") or ())
    secondary = tuple(github.get("secondaryLogins") or ())
    if owners != ALLOWED_GITHUB_OWNERS:
        errors.append(f"boundaries github.owners must be {ALLOWED_GITHUB_OWNERS}")
    if logins != ALLOWED_GITHUB_LOGINS:
        errors.append(f"boundaries github.logins must be {ALLOWED_GITHUB_LOGINS}")
    if secondary != SECONDARY_GITHUB_LOGINS:
        errors.append(
            f"boundaries github.secondaryLogins must be {SECONDARY_GITHUB_LOGINS}"
        )
    if linear.get("userEmail") != LINEAR_USER_EMAIL:
        errors.append("boundaries linear.userEmail mismatch")
    if linear.get("workspaceName") != LINEAR_WORKSPACE_NAME:
        errors.append("boundaries linear.workspaceName mismatch")
    if linear.get("workspaceUrl") != LINEAR_WORKSPACE_URL:
        errors.append("boundaries linear.workspaceUrl mismatch")
    if linear.get("mcpUrl") != LINEAR_MCP_URL:
        errors.append("boundaries linear.mcpUrl mismatch")
    if slack.get("domain") != SLACK_DOMAIN:
        errors.append("boundaries slack.domain mismatch")
    if slack.get("teamId") != SLACK_TEAM_ID:
        errors.append("boundaries slack.teamId mismatch")
    if apps != EXPECTED_APPS:
        errors.append("boundaries apps must match the registered connector ids")
    return errors


def plugin_package_files(plugin_root: Path) -> list[str]:
    files: list[str] = []
    for path in iter_scan_files(plugin_root):
        files.append(relative_posix(path, plugin_root))
    return sorted(files)


def validate_plugin_manifest(plugin_root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("name") != PLUGIN_NAME:
        errors.append(f"plugin name must be {PLUGIN_NAME}")
    version = manifest.get("version")
    if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
        errors.append(f"plugin version is not semver: {version!r}")
    author = manifest.get("author")
    if not isinstance(author, dict) or author.get("name") != AUTHOR_NAME:
        errors.append(f"plugin author.name must be {AUTHOR_NAME}")
    if not isinstance(author, dict) or author.get("email") != AUTHOR_EMAIL:
        errors.append(f"plugin author.email must be {AUTHOR_EMAIL}")
    for field in ("skills", "apps", "mcpServers"):
        try:
            resolve_inside(plugin_root, manifest[field], field=field)
        except (KeyError, ValueError) as exc:
            errors.append(str(exc))
    if "hooks" in manifest:
        errors.append("plugin must not ship executable hooks")
    if (plugin_root / "hooks" / "hooks.json").exists():
        errors.append("unexpected hooks/hooks.json; this plugin must not ship command hooks")
    extra_files = set(plugin_package_files(plugin_root)) - ALLOWED_PLUGIN_RELATIVE_PATHS
    if extra_files:
        errors.append(f"plugin package contains unexpected files: {sorted(extra_files)}")
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("plugin interface must be an object")
        return errors
    prompts = interface.get("defaultPrompt")
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= MAX_DEFAULT_PROMPTS:
        errors.append("interface.defaultPrompt must contain 1-3 prompts")
    elif not all(
        isinstance(prompt, str) and 1 <= len(prompt) <= MAX_PROMPT_CHARS
        for prompt in prompts
    ):
        errors.append("each defaultPrompt must be a string of 1-128 characters")
    brand = interface.get("brandColor")
    if not isinstance(brand, str) or not HEX_COLOR_RE.fullmatch(brand):
        errors.append(f"interface.brandColor must be #RRGGBB, got {brand!r}")
    for url_field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
        try:
            require_https_url(interface.get(url_field), f"interface.{url_field}")
        except ValueError as exc:
            errors.append(str(exc))
        else:
            url = interface.get(url_field)
            if isinstance(url, str) and not url.startswith("https://github.com/"):
                errors.append(f"interface.{url_field} must be an https GitHub URL")
    return errors


def validate_marketplace(
    root: Path, marketplace: dict[str, Any], plugin_name: str
) -> list[str]:
    errors: list[str] = []
    if marketplace.get("name") != MARKETPLACE_NAME:
        errors.append(f"marketplace name must be {MARKETPLACE_NAME}")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        return errors + ["marketplace plugins must be a non-empty list"]
    try:
        entry = next(
            item
            for item in plugins
            if isinstance(item, dict) and item.get("name") == plugin_name
        )
    except StopIteration:
        return errors + [f"marketplace is missing plugin {plugin_name}"]
    source = entry.get("source")
    if not isinstance(source, dict):
        errors.append("marketplace plugin source must be an object")
        return errors
    if source.get("source") != "local":
        errors.append("marketplace plugin source must be local for this repository")
    raw_path = source.get("path")
    expected_path = f"./plugins/{PLUGIN_NAME}"
    if raw_path != expected_path:
        errors.append(f"marketplace path must be {expected_path}")
    else:
        try:
            resolve_inside(root, raw_path, field="marketplace.source.path")
        except ValueError as exc:
            errors.append(str(exc))
    if entry.get("policy") != {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }:
        errors.append(
            "marketplace policy must require AVAILABLE installation and ON_INSTALL authentication"
        )
    return errors


def plugin_dir(root: Path) -> Path:
    return root / "plugins" / PLUGIN_NAME


def collect_repo_errors(root: Path) -> list[str]:
    errors: list[str] = []
    plugin_root = plugin_dir(root)

    try:
        manifest = load_json(plugin_root / ".codex-plugin" / "plugin.json")
        errors.extend(validate_plugin_manifest(plugin_root, manifest))
        plugin_name = str(manifest.get("name") or PLUGIN_NAME)
    except ValueError as exc:
        errors.append(str(exc))
        plugin_name = PLUGIN_NAME

    try:
        marketplace = load_json(root / ".agents" / "plugins" / "marketplace.json")
        errors.extend(validate_marketplace(root, marketplace, plugin_name))
    except ValueError as exc:
        errors.append(str(exc))

    try:
        apps = load_json(plugin_root / ".app.json")
        errors.extend(validate_app_ids(apps.get("apps")))
        extra = set(apps) - {"apps"}
        if extra:
            errors.append(f".app.json has unexpected top-level keys: {sorted(extra)}")
    except ValueError as exc:
        errors.append(str(exc))

    try:
        mcp = load_json(plugin_root / ".mcp.json")
        errors.extend(validate_mcp_config(mcp))
    except ValueError as exc:
        errors.append(str(exc))

    skill = plugin_root / "skills" / "ores-engineering-ops" / "SKILL.md"
    try:
        errors.extend(validate_skill_contract(skill.read_text(encoding="utf-8")))
    except OSError as exc:
        errors.append(f"{skill}: {exc}")

    try:
        errors.extend(
            validate_boundaries(
                boundaries_from_skill_dir(
                    plugin_root / "skills" / "ores-engineering-ops"
                )
            )
        )
    except ValueError as exc:
        errors.append(str(exc))

    for schema_name in (
        "plugin.schema.json",
        "marketplace.schema.json",
        "app.schema.json",
        "mcp.schema.json",
        "boundaries.schema.json",
    ):
        schema_path = root / "schemas" / schema_name
        if not schema_path.is_file():
            errors.append(f"missing JSON schema contract: schemas/{schema_name}")

    errors.extend(scan_tree_for_secrets(root, skip_tests=True))
    return errors


def validate_repo(root: Path) -> None:
    errors = collect_repo_errors(root)
    if errors:
        raise AssertionError("\n".join(errors))
