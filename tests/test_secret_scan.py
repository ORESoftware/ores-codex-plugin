"""Unit tests for secret scanning and path containment."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from plugin_policy import (
    find_secret_matches,
    resolve_inside,
    scan_file_for_secrets,
    scan_tree_for_secrets,
)


class SecretScanTests(unittest.TestCase):
    def test_detects_github_linear_slack_and_cloud_secrets(self) -> None:
        github = "ghp_" + ("A" * 36)
        linear = "lin_api_" + ("B" * 32)
        slack = "xoxb-" + ("C" * 20)
        aws = "AKIA" + ("D" * 16)
        blob = "\n".join([github, linear, slack, aws, "-----BEGIN PRIVATE KEY-----"])
        labels = {label for label, _preview in find_secret_matches(blob)}
        self.assertIn("github token", labels)
        self.assertIn("linear api token", labels)
        self.assertIn("slack token", labels)
        self.assertIn("aws access key", labels)
        self.assertIn("private key", labels)

    def test_detects_from_env_github_placeholder(self) -> None:
        key = "GITHUB_PERSONAL_ACCESS_TOKEN"
        placeholder = "from-env"
        text = f'{key}: "{placeholder}"'
        labels = {label for label, _preview in find_secret_matches(text)}
        self.assertIn("github from-env placeholder", labels)

    def test_documentation_prefixes_without_bodies_are_clean(self) -> None:
        self.assertEqual(find_secret_matches("never commit a ghp_ or lin_api_ prefix"), [])


class PathSafetyTests(unittest.TestCase):
    def test_relative_paths_must_stay_inside_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills").mkdir()
            inside = resolve_inside(root, "./skills/", field="skills")
            self.assertTrue(inside.is_relative_to(root.resolve()))
            with self.assertRaises(ValueError):
                resolve_inside(root, "../outside", field="skills")
            with self.assertRaises(ValueError):
                resolve_inside(root, "./skills/../../etc/passwd", field="skills")
            with self.assertRaises(ValueError):
                resolve_inside(root, "/etc/passwd", field="skills")
            with self.assertRaises(ValueError):
                resolve_inside(root, ".\\skills", field="skills")

    def test_secret_scan_skips_tests_directory_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "plugin.txt").write_text("ok", encoding="utf-8")
            tests = root / "tests"
            tests.mkdir()
            (tests / "fixture.txt").write_text("ghp_" + ("A" * 36), encoding="utf-8")
            self.assertEqual(scan_tree_for_secrets(root, skip_tests=True), [])
            leaked = scan_tree_for_secrets(root, skip_tests=False)
            self.assertTrue(any("github token" in item for item in leaked))

    def test_scan_file_ignores_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "secret.txt"
            target.write_text("ghp_" + ("A" * 36), encoding="utf-8")
            link = root / "alias.txt"
            link.symlink_to(target)
            self.assertEqual(scan_file_for_secrets(link), [])


if __name__ == "__main__":
    unittest.main()
