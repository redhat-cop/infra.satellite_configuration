# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import importlib.util
import pathlib
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
MODULE_PATH = REPO_ROOT / "plugins" / "modules" / "filetree_reconcile_diff.py"
SPEC = importlib.util.spec_from_file_location("filetree_reconcile_diff", MODULE_PATH)
FILETREE_RECONCILE_DIFF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FILETREE_RECONCILE_DIFF)


class TestWriteReconcileDiffFile(unittest.TestCase):
    def test_writes_new_diff_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file, changed = FILETREE_RECONCILE_DIFF.write_reconcile_diff_file(
                temp_dir,
                "satellite_domains.yaml",
                "satellite_domains",
                [{"name": "example.com", "state": "absent"}],
            )

            self.assertTrue(changed)
            self.assertTrue(pathlib.Path(output_file).is_file())
            content = pathlib.Path(output_file).read_text(encoding="utf-8")
            self.assertIn("satellite_domains:", content)
            self.assertIn("example.com", content)
            self.assertIn("state: absent", content)

    def test_reports_unchanged_when_content_matches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            diff_items = [{"name": "example.com", "state": "present", "fullname": "example.com"}]
            output_file, first_changed = FILETREE_RECONCILE_DIFF.write_reconcile_diff_file(
                temp_dir,
                "satellite_domains.yaml",
                "satellite_domains",
                diff_items,
            )
            self.assertTrue(first_changed)

            second_path, second_changed = FILETREE_RECONCILE_DIFF.write_reconcile_diff_file(
                temp_dir,
                "satellite_domains.yaml",
                "satellite_domains",
                diff_items,
            )
            self.assertFalse(second_changed)
            self.assertEqual(second_path, output_file)
            self.assertTrue(pathlib.Path(output_file).is_file())


if __name__ == "__main__":
    unittest.main()
