# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import importlib.util
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
FILTER_PATH = REPO_ROOT / "plugins" / "filter" / "export_filters.py"
SPEC = importlib.util.spec_from_file_location("export_filters_plugin", FILTER_PATH)
EXPORT_FILTERS_PLUGIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORT_FILTERS_PLUGIN)


class TestExportFiltersPlugin(unittest.TestCase):
    def test_filters_registers_expected_names(self):
        registered = EXPORT_FILTERS_PLUGIN.FilterModule().filters()
        expected = {
            "satellite_configuration_export_item_is_locked",
            "satellite_configuration_append_export_search_for_resource",
            "satellite_configuration_append_export_search_to_api_link",
            "satellite_configuration_append_locked_export_search_to_api_link",
            "satellite_configuration_build_export_search_query",
            "satellite_configuration_filter_export_items",
            "satellite_configuration_filters_for_post_api_export",
            "satellite_configuration_filter_export_organizations",
            "satellite_configuration_locked_item_names",
            "satellite_configuration_reject_locked_items",
            "satellite_configuration_reject_orphaned_katello_products",
        }
        self.assertEqual(set(registered), expected)

    def test_filter_wrappers_delegate_to_module_utils(self):
        filters = EXPORT_FILTERS_PLUGIN.FilterModule()
        items = [
            {"name": "locked", "locked": True},
            {"name": "custom", "locked": False},
        ]
        self.assertEqual(
            [item["name"] for item in filters.satellite_configuration_reject_locked_items(items)],
            ["custom"],
        )
        self.assertTrue(filters.satellite_configuration_export_item_is_locked(items[0]))
        query = filters.satellite_configuration_build_export_search_query(
            {"organizations": ["ACME"]},
        )
        self.assertEqual(query, 'organization = "ACME"')


if __name__ == "__main__":
    unittest.main()
