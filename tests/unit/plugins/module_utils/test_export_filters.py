# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import importlib.util
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
EXPORT_FILTERS_PATH = REPO_ROOT / "plugins" / "module_utils" / "export_filters.py"
SPEC = importlib.util.spec_from_file_location("export_filters", EXPORT_FILTERS_PATH)
EXPORT_FILTERS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORT_FILTERS)

FACTORY_PROVISIONING_TEMPLATES = [
    {"id": 1, "name": "Kickstart default", "locked": True},
    {"id": 2, "name": "Kickstart default PXEGrub", "locked": True},
    {"id": 3, "name": "custom-kickstart", "locked": False},
]

FACTORY_PARTITION_TABLES = [
    {"id": 10, "name": "Preseed default LVM", "locked": True},
    {"id": 11, "name": "site-custom-lvm", "locked": False},
]


class TestExportFilters(unittest.TestCase):
    def test_reject_locked_items_skips_factory_defaults(self):
        filtered = EXPORT_FILTERS.reject_locked_items(FACTORY_PROVISIONING_TEMPLATES)
        self.assertEqual([item["name"] for item in filtered], ["custom-kickstart"])

    def test_reject_locked_items_keeps_all_when_disabled(self):
        self.assertEqual(
            EXPORT_FILTERS.reject_locked_items(FACTORY_PROVISIONING_TEMPLATES, skip_locked=False),
            FACTORY_PROVISIONING_TEMPLATES,
        )

    def test_locked_item_names_returns_skipped_labels(self):
        self.assertEqual(
            EXPORT_FILTERS.locked_item_names(FACTORY_PARTITION_TABLES),
            ["Preseed default LVM"],
        )

    def test_is_locked_handles_string_truth_values(self):
        self.assertTrue(EXPORT_FILTERS.is_locked({"name": "locked-string", "locked": "true"}))
        self.assertFalse(EXPORT_FILTERS.is_locked({"name": "unlocked", "locked": "false"}))


if __name__ == "__main__":
    unittest.main()
