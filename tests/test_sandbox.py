"""Unit tests for the path-locked filesystem sandbox."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sandbox import SandboxError, list_resources, read_resource, resolve


class TestSandbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "root"
        self.root.mkdir()
        (self.root / "hello.txt").write_text("hello sandbox\n")
        (self.root / "sub").mkdir()
        (self.root / "sub" / "nested.txt").write_text("nested\n")
        (self.root / ".hidden.txt").write_text("secret-ish\n")
        (self.root / ".config").mkdir()
        (self.root / ".config" / "inside.txt").write_text("hidden dir\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_traversal_blocked(self):
        with self.assertRaises(SandboxError):
            resolve(self.root, "../outside.txt")
        with self.assertRaises(SandboxError):
            read_resource(self.root, "../outside.txt")
        with self.assertRaises(SandboxError):
            read_resource(self.root, "sub/../../outside.txt")

    def test_symlink_escape_blocked(self):
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("TOP SECRET\n")
        (self.root / "escape.txt").symlink_to(outside)
        with self.assertRaises(SandboxError):
            resolve(self.root, "escape.txt")
        with self.assertRaises(SandboxError):
            read_resource(self.root, "escape.txt")

    def test_symlink_inside_root_allowed(self):
        (self.root / "alias.txt").symlink_to(self.root / "hello.txt")
        self.assertEqual(read_resource(self.root, "alias.txt"), "hello sandbox\n")

    def test_hidden_files_filtered(self):
        resources = list_resources(self.root)
        self.assertNotIn(".hidden.txt", resources)
        self.assertNotIn(".config/inside.txt", resources)
        self.assertIn("hello.txt", resources)
        self.assertIn("sub/nested.txt", resources)

    def test_normal_read_works(self):
        self.assertEqual(read_resource(self.root, "hello.txt"), "hello sandbox\n")
        self.assertEqual(read_resource(self.root, "sub/nested.txt"), "nested\n")

    def test_root_itself_listed(self):
        self.assertEqual(resolve(self.root, "."), self.root.resolve())
        self.assertEqual(
            list_resources(self.root),
            ["hello.txt", "sub/nested.txt"],
        )

    def test_absolute_path_rejected(self):
        with self.assertRaises(SandboxError):
            resolve(self.root, "/etc/passwd")

    def test_missing_file(self):
        with self.assertRaises(SandboxError):
            read_resource(self.root, "nope.txt")

    def test_size_cap(self):
        big = self.root / "big.txt"
        big.write_text("x" * 100)
        with self.assertRaises(SandboxError):
            read_resource(self.root, "big.txt", max_bytes=10)


if __name__ == "__main__":
    unittest.main()
