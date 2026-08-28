import sys
from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "scripts" / "plugin_policy.py").is_file():
            return parent
    raise RuntimeError("could not locate ores-codex-plugin repository root")


ROOT = repo_root()
PLUGIN = ROOT / "plugins" / "ores-codex-plugin"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
