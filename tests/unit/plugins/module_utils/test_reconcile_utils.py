# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import importlib.util
import pathlib
import tempfile
import unittest

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
UTILS_PATH = REPO_ROOT / "plugins" / "module_utils" / "reconcile_utils.py"
SPEC = importlib.util.spec_from_file_location("reconcile_utils", UTILS_PATH)
RECONCILE_UTILS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECONCILE_UTILS)


class TestReconcileUtils(unittest.TestCase):
    def test_present_entry_clears_live_only_scalar_fields(self):
        entry = RECONCILE_UTILS.build_present_entry(
            {"name": "red_ribbon_new", "label": "x", "title": "x"},
            {
                "name": "red_ribbon_new",
                "label": "x",
                "title": "x",
                "description": "test description",
            },
            RECONCILE_UTILS.DEFAULT_IGNORE_KEYS,
        )

        self.assertEqual(entry["state"], "present")
        self.assertEqual(entry["description"], "")
        self.assertEqual(entry["name"], "red_ribbon_new")

    def test_present_entry_clears_live_only_nested_fields(self):
        entry = RECONCILE_UTILS.build_present_entry(
            {"name": "hostgroup", "parameters": {"keep": "value"}},
            {
                "name": "hostgroup",
                "parameters": {"keep": "value", "manual": "change"},
            },
            RECONCILE_UTILS.DEFAULT_IGNORE_KEYS,
        )

        self.assertEqual(entry["parameters"]["keep"], "value")
        self.assertEqual(entry["parameters"]["manual"], "")

    def test_absent_entry_copies_full_live_object(self):
        live_object = {
            "name": "remove_me",
            "template": "kickstart content",
            "organizations": ["Default Organization"],
            "id": 42,
            "created_at": "2026-01-01",
        }
        entry = RECONCILE_UTILS.build_absent_entry(
            live_object,
            RECONCILE_UTILS.DEFAULT_IGNORE_KEYS,
        )

        self.assertEqual(entry["state"], "absent")
        self.assertEqual(entry["name"], "remove_me")
        self.assertEqual(entry["template"], "kickstart content")
        self.assertEqual(entry["organizations"], ["Default Organization"])
        self.assertNotIn("id", entry)
        self.assertNotIn("created_at", entry)

    def test_detects_absent_present_and_changed_entries(self):
        live_index = {
            "keep": {"name": "keep", "description": "same"},
            "remove": {
                "name": "remove",
                "organization": "Default Organization",
                "description": "live-only field",
            },
            "drift": {"name": "drift", "description": "live"},
        }
        cac_index = {
            "keep": {"name": "keep", "description": "same"},
            "create": {"name": "create", "description": "new"},
            "drift": {"name": "drift", "description": "cac"},
        }

        diff_items, stats = RECONCILE_UTILS.compute_diff_items(
            live_index,
            cac_index,
            RECONCILE_UTILS.DEFAULT_IGNORE_KEYS,
        )

        self.assertEqual(stats["absent"], 1)
        self.assertEqual(stats["present_new"], 1)
        self.assertEqual(stats["present_changed"], 1)
        self.assertEqual(len(diff_items), 3)

        absent_entry = next(item for item in diff_items if item["name"] == "remove")
        self.assertEqual(absent_entry["state"], "absent")
        self.assertEqual(absent_entry["organization"], "Default Organization")
        self.assertEqual(absent_entry["description"], "live-only field")

        present_entry = next(item for item in diff_items if item["name"] == "create")
        self.assertEqual(present_entry["state"], "present")
        self.assertEqual(present_entry["description"], "new")

        changed_entry = next(item for item in diff_items if item["name"] == "drift")
        self.assertEqual(changed_entry["state"], "present")
        self.assertEqual(changed_entry["description"], "cac")

    def test_reconcile_directories_ignores_formatting_only_differences(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cac_path = pathlib.Path(temp_dir) / "cac" / "satellite_organizations.d"
            live_path = pathlib.Path(temp_dir) / "live" / "satellite_organizations.d"
            cac_path.mkdir(parents=True)
            live_path.mkdir(parents=True)
            document = {
                "satellite_organizations": [
                    {"name": "example", "label": "Example", "title": "Example"},
                ]
            }
            (cac_path / "satellite_organizations.yaml").write_text(
                yaml.dump(document, default_flow_style=False),
                encoding="utf-8",
            )
            live_content = """\
---
satellite_organizations:
  - name: example
    label: Example

    title: Example
"""
            (live_path / "satellite_organizations.yaml").write_text(
                live_content,
                encoding="utf-8",
            )

            diff_items, stats = RECONCILE_UTILS.reconcile_directories(
                str(cac_path),
                str(live_path),
                "satellite_organizations",
                "name",
                RECONCILE_UTILS.DEFAULT_IGNORE_KEYS,
            )

            self.assertEqual(diff_items, [])
            self.assertEqual(stats["absent"], 0)
            self.assertEqual(stats["present_new"], 0)
            self.assertEqual(stats["present_changed"], 0)

    def test_reconcile_directories_only_marks_extra_live_objects_absent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            cac_dir = temp_path / "cac" / "satellite_organizations.d"
            live_dir = temp_path / "live" / "satellite_organizations.d"
            cac_dir.mkdir(parents=True)
            live_dir.mkdir(parents=True)

            shared = [
                {"label": "Red_Ribbon", "name": "red_ribbon", "title": "red_ribbon"},
                {"label": "datacenter", "name": "datacenter", "title": "datacenter"},
            ]
            (cac_dir / "satellite_organizations.yaml").write_text(
                yaml.dump({"satellite_organizations": shared}, default_flow_style=False),
                encoding="utf-8",
            )
            live_items = shared + [
                {
                    "label": "test_org_to_be_deleted",
                    "name": "test_org_to_be_deleted",
                    "title": "test_org_to_be_deleted",
                    "description": "filetree_reconcile should remove that new organization",
                }
            ]
            (live_dir / "satellite_organizations.yaml").write_text(
                yaml.dump({"satellite_organizations": live_items}, default_flow_style=False),
                encoding="utf-8",
            )

            diff_items, stats = RECONCILE_UTILS.reconcile_directories(
                str(cac_dir),
                str(live_dir),
                "satellite_organizations",
                "name",
                RECONCILE_UTILS.DEFAULT_IGNORE_KEYS,
            )

            self.assertEqual(stats["absent"], 1)
            self.assertEqual(stats["present_new"], 0)
            self.assertEqual(stats["present_changed"], 0)
            self.assertEqual([item["name"] for item in diff_items], ["test_org_to_be_deleted"])
            self.assertEqual(diff_items[0]["state"], "absent")
            self.assertEqual(
                diff_items[0]["description"],
                "filetree_reconcile should remove that new organization",
            )

    def test_reconcile_directories_refuses_absent_when_cac_directory_is_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            cac_dir = temp_path / "cac" / "satellite_organizations.d"
            live_dir = temp_path / "live" / "satellite_organizations.d"
            cac_dir.mkdir(parents=True)
            live_dir.mkdir(parents=True)
            (live_dir / "satellite_organizations.yaml").write_text(
                yaml.dump(
                    {"satellite_organizations": [{"name": "only_live", "label": "only_live"}]},
                    default_flow_style=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaises(RECONCILE_UTILS.ReconcileCompareError):
                RECONCILE_UTILS.reconcile_directories(
                    str(cac_dir),
                    str(live_dir),
                    "satellite_organizations",
                    "name",
                    RECONCILE_UTILS.DEFAULT_IGNORE_KEYS,
                )

    def test_reconcile_directories_ignores_cac_objects_outside_scope_filters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            cac_dir = temp_path / "cac" / "satellite_organizations.d"
            live_dir = temp_path / "live" / "satellite_organizations.d"
            cac_dir.mkdir(parents=True)
            live_dir.mkdir(parents=True)
            shared = {"label": "red_ribbon", "name": "red_ribbon", "title": "red_ribbon"}
            (cac_dir / "satellite_organizations.yaml").write_text(
                yaml.dump(
                    {
                        "satellite_organizations": [
                            shared,
                            {
                                "label": "out_of_scope",
                                "name": "out_of_scope",
                                "title": "out_of_scope",
                            },
                        ]
                    },
                    default_flow_style=False,
                ),
                encoding="utf-8",
            )
            (live_dir / "satellite_organizations.yaml").write_text(
                yaml.dump({"satellite_organizations": [shared]}, default_flow_style=False),
                encoding="utf-8",
            )

            diff_items, stats = RECONCILE_UTILS.reconcile_directories(
                str(cac_dir),
                str(live_dir),
                "satellite_organizations",
                "name",
                RECONCILE_UTILS.DEFAULT_IGNORE_KEYS,
                {"organizations": ["red_ribbon"]},
            )

            self.assertEqual(diff_items, [])
            self.assertEqual(stats["present_new"], 0)

    def test_reconcile_directories_ignores_live_objects_outside_scope_filters(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            cac_dir = temp_path / "cac" / "satellite_organizations.d"
            live_dir = temp_path / "live" / "satellite_organizations.d"
            cac_dir.mkdir(parents=True)
            live_dir.mkdir(parents=True)
            shared = {"label": "red_ribbon", "name": "red_ribbon", "title": "red_ribbon"}
            (cac_dir / "satellite_organizations.yaml").write_text(
                yaml.dump({"satellite_organizations": [shared]}, default_flow_style=False),
                encoding="utf-8",
            )
            (live_dir / "satellite_organizations.yaml").write_text(
                yaml.dump(
                    {
                        "satellite_organizations": [
                            shared,
                            {
                                "label": "live_only_out_of_scope",
                                "name": "live_only_out_of_scope",
                                "title": "live_only_out_of_scope",
                            },
                        ]
                    },
                    default_flow_style=False,
                ),
                encoding="utf-8",
            )

            diff_items, stats = RECONCILE_UTILS.reconcile_directories(
                str(cac_dir),
                str(live_dir),
                "satellite_organizations",
                "name",
                RECONCILE_UTILS.DEFAULT_IGNORE_KEYS,
                {"organizations": ["red_ribbon"]},
            )

            self.assertEqual(diff_items, [])
            self.assertEqual(stats["absent"], 0)

    def test_reconcile_directories_without_scope_filters_matches_legacy_behavior(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            cac_dir = temp_path / "cac" / "satellite_organizations.d"
            live_dir = temp_path / "live" / "satellite_organizations.d"
            cac_dir.mkdir(parents=True)
            live_dir.mkdir(parents=True)
            shared = [
                {"label": "red_ribbon", "name": "red_ribbon", "title": "red_ribbon"},
                {"label": "datacenter", "name": "datacenter", "title": "datacenter"},
            ]
            (cac_dir / "satellite_organizations.yaml").write_text(
                yaml.dump({"satellite_organizations": shared}, default_flow_style=False),
                encoding="utf-8",
            )
            live_items = shared + [
                {
                    "label": "test_org_to_be_deleted",
                    "name": "test_org_to_be_deleted",
                    "title": "test_org_to_be_deleted",
                }
            ]
            (live_dir / "satellite_organizations.yaml").write_text(
                yaml.dump({"satellite_organizations": live_items}, default_flow_style=False),
                encoding="utf-8",
            )

            diff_items, stats = RECONCILE_UTILS.reconcile_directories(
                str(cac_dir),
                str(live_dir),
                "satellite_organizations",
                "name",
                RECONCILE_UTILS.DEFAULT_IGNORE_KEYS,
                None,
            )

            self.assertEqual(stats["absent"], 1)
            self.assertEqual([item["name"] for item in diff_items], ["test_org_to_be_deleted"])


if __name__ == "__main__":
    unittest.main()
