"""Optional Codex plugin-creator ingestion check."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
import venv
from pathlib import Path

from tests import PLUGIN


PLUGIN_CREATOR = (
    Path.home()
    / ".codex"
    / "skills"
    / ".system"
    / "plugin-creator"
    / "scripts"
    / "validate_plugin.py"
)


class OfficialIngestionTests(unittest.TestCase):
    def test_plugin_creator_validator_when_available(self) -> None:
        if not PLUGIN_CREATOR.is_file():
            self.skipTest("plugin-creator validator is not installed on this machine")

        try:
            import yaml  # noqa: F401
        except ImportError:
            yaml = None  # noqa: F841
        else:
            self._run_official(sys.executable)
            return

        with tempfile.TemporaryDirectory(prefix="ores-codex-pyyaml-") as tmp:
            venv_dir = Path(tmp) / "venv"
            try:
                venv.create(venv_dir, with_pip=True, clear=True)
            except OSError as exc:
                self.skipTest(f"could not create venv for PyYAML: {exc}")
            pip = venv_dir / "bin" / "pip"
            python = venv_dir / "bin" / "python"
            install = subprocess.run(
                [str(pip), "install", "--quiet", "pyyaml"],
                check=False,
                capture_output=True,
                text=True,
            )
            if install.returncode != 0:
                self.skipTest(install.stderr or "pip install pyyaml failed")
            self._run_official(str(python))

    def _run_official(self, python: str) -> None:
        completed = subprocess.run(
            [python, str(PLUGIN_CREATOR), str(PLUGIN)],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": str(PLUGIN_CREATOR.parent)},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
