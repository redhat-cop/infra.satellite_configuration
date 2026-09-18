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

    def test_filter_export_organizations_allowlist(self):
        organizations = [
            {"name": "ACME", "id": 1},
            {"name": "Other", "id": 2},
        ]
        filtered = EXPORT_FILTERS.filter_export_organizations(
            organizations,
            {"organizations": ["ACME"]},
        )
        self.assertEqual([item["name"] for item in filtered], ["ACME"])

    def test_filter_export_organizations_name_glob(self):
        organizations = [
            {"name": "ACME-prod", "id": 1},
            {"name": "Other", "id": 2},
        ]
        filtered = EXPORT_FILTERS.filter_export_organizations(
            organizations,
            {"name_include": ["ACME-*"]},
        )
        self.assertEqual([item["name"] for item in filtered], ["ACME-prod"])

    def test_filter_export_items_organization_scope(self):
        items = [
            {"name": "repo-a", "organization": {"name": "ACME"}},
            {"name": "repo-b", "organization": {"name": "Other"}},
        ]
        filtered = EXPORT_FILTERS.filter_export_items(
            items,
            {"organizations": ["ACME"]},
        )
        self.assertEqual([item["name"] for item in filtered], ["repo-a"])

    def test_filter_export_items_name_exclude(self):
        items = [
            {"name": "prod-hostgroup"},
            {"name": "test-hostgroup"},
        ]
        filtered = EXPORT_FILTERS.filter_export_items(
            items,
            {"name_exclude": ["test-*"]},
        )
        self.assertEqual([item["name"] for item in filtered], ["prod-hostgroup"])

    def test_filter_export_items_login_key(self):
        items = [
            {"login": "admin"},
            {"login": "service"},
        ]
        filtered = EXPORT_FILTERS.filter_export_items(
            items,
            {"name_include": ["service"]},
            name_key="login",
        )
        self.assertEqual([item["login"] for item in filtered], ["service"])

    def test_build_export_search_query_name_glob(self):
        query = EXPORT_FILTERS.build_export_search_query({"name_include": ["ACME-*"]})
        self.assertEqual(query, 'name ~ "ACME-%"')

    def test_build_export_search_query_organization_and_name(self):
        query = EXPORT_FILTERS.build_export_search_query(
            {
                "organizations": ["ACME"],
                "name_exclude": ["test-*"],
            }
        )
        self.assertEqual(
            query,
            'organization = "ACME" AND NOT (name ~ "test-%")',
        )

    def test_build_export_search_query_merges_extra_search(self):
        query = EXPORT_FILTERS.build_export_search_query(
            {"name_include": ["prod-*"]},
            extra_search="redhat=false",
            supports_organization=False,
        )
        self.assertEqual(query, 'name ~ "prod-%" AND redhat=false')

    def test_build_export_search_query_returns_none_for_empty_filters(self):
        self.assertIsNone(EXPORT_FILTERS.build_export_search_query({}))

    def test_build_export_search_query_skips_name_when_regex_enabled(self):
        query = EXPORT_FILTERS.build_export_search_query(
            {
                "name_use_regex": True,
                "name_include": ["^ACME"],
                "organizations": ["ACME"],
            }
        )
        self.assertEqual(query, 'organization = "ACME"')

    def test_append_export_search_to_api_link(self):
        link = EXPORT_FILTERS.append_export_search_to_api_link(
            "/katello/api/repositories?full_result=true",
            {"organizations": ["ACME"]},
        )
        self.assertEqual(
            link,
            "/katello/api/repositories?full_result=true&search=organization%20%3D%20%22ACME%22",
        )

    def test_filter_export_items_location_allowlist(self):
        items = [
            {"name": "hg-a", "location_name": "DC1"},
            {"name": "hg-b", "location_name": "DC2"},
        ]
        filtered = EXPORT_FILTERS.filter_export_items(items, {"locations": ["DC1"]})
        self.assertEqual([item["name"] for item in filtered], ["hg-a"])

    def test_filter_export_items_domain_exclude(self):
        items = [
            {"name": "subnet-a", "domains": [{"name": "example.com"}]},
            {"name": "subnet-b", "domains": [{"name": "lab.example.com"}]},
        ]
        filtered = EXPORT_FILTERS.filter_export_items(items, {"domains_exclude": ["lab.example.com"]})
        self.assertEqual([item["name"] for item in filtered], ["subnet-a"])

    def test_filters_for_post_api_export_subnets_strips_domains(self):
        filters = {"domains": ["example.com"], "name_include": ["net-a"]}
        stripped = EXPORT_FILTERS.filters_for_post_api_export(filters, "subnets")
        self.assertNotIn("domains", stripped)
        self.assertEqual(stripped.get("name_include"), ["net-a"])

    def test_append_locked_export_search_to_api_link(self):
        link = EXPORT_FILTERS.append_locked_export_search_to_api_link(
            "/api/ptables?per_page=all",
            skip_locked=True,
        )
        self.assertEqual(
            link,
            "/api/ptables?per_page=all&search=locked%3Dfalse",
        )
        locked_only = EXPORT_FILTERS.append_locked_export_search_to_api_link(
            "/api/provisioning_templates?per_page=all",
            skip_locked=False,
            locked_only=True,
        )
        self.assertEqual(
            locked_only,
            "/api/provisioning_templates?per_page=all&search=locked%3Dtrue",
        )

    def test_reject_orphaned_katello_products_skips_string_product(self):
        items = [
            {
                "name": "custom",
                "product": "My Product",
                "url": "https://example.com/repo",
            },
            {
                "name": "orphan",
                "product": {"orphaned": True},
                "url": "https://example.com/orphan",
            },
        ]
        filtered = EXPORT_FILTERS.reject_orphaned_katello_products(items)
        self.assertEqual([item["name"] for item in filtered], ["custom"])

    def test_filter_export_items_subnet_domain_scope_after_api_search(self):
        items = [
            {"name": "net-a", "id": 1},
            {"name": "net-b", "id": 2},
        ]
        filters = {"domains": ["example.com"]}
        self.assertEqual(EXPORT_FILTERS.filter_export_items(items, filters), [])
        stripped = EXPORT_FILTERS.filters_for_post_api_export(filters, "subnets")
        self.assertEqual(
            [item["name"] for item in EXPORT_FILTERS.filter_export_items(items, stripped)],
            ["net-a", "net-b"],
        )

    def test_filter_export_items_hostgroup_parent_branch(self):
        items = [
            {"name": "web", "title": "Production/web"},
            {"name": "db", "title": "Production/db"},
            {"name": "other", "title": "Staging/app"},
        ]
        filtered = EXPORT_FILTERS.filter_export_items(
            items,
            {"hostgroup_parents": ["Production"]},
            apply_hostgroup_parents=True,
        )
        self.assertEqual([item["name"] for item in filtered], ["web", "db"])

    def test_build_export_search_query_location_and_domain(self):
        query = EXPORT_FILTERS.build_export_search_query(
            {"locations": ["DC1"], "domains": ["example.com"]},
            supports_organization=False,
            supports_location=True,
            supports_domain=True,
        )
        self.assertEqual(
            query,
            'location = "DC1" AND domain = "example.com"',
        )

    def test_build_export_search_query_hostgroup_parents(self):
        query = EXPORT_FILTERS.build_export_search_query(
            {"hostgroup_parents": ["Production"]},
            supports_organization=False,
            supports_hostgroup_parents=True,
        )
        self.assertEqual(
            query,
            '(title = "Production" OR title ~ "Production/%")',
        )

    def test_filter_export_items_product_scope(self):
        items = [
            {"name": "repo-a", "product": {"name": "ACME"}},
            {"name": "repo-b", "product": {"name": "Other"}},
        ]
        filtered = EXPORT_FILTERS.filter_export_items(items, {"products": ["ACME"]})
        self.assertEqual([item["name"] for item in filtered], ["repo-a"])

    def test_filter_export_items_lifecycle_environment(self):
        items = [
            {"name": "key-a", "environment": {"name": "Dev"}},
            {"name": "key-b", "environment": {"name": "Prod"}},
        ]
        filtered = EXPORT_FILTERS.filter_export_items(items, {"lifecycle_environments_exclude": ["Prod"]})
        self.assertEqual([item["name"] for item in filtered], ["key-a"])

    def test_filter_export_items_auth_source_and_admin(self):
        items = [
            {"login": "admin", "auth_source_name": "Internal", "admin": True},
            {"login": "ldap-user", "auth_source_name": "LDAP", "admin": False},
        ]
        filtered = EXPORT_FILTERS.filter_export_items(
            items,
            {"auth_sources": ["LDAP"], "users_admin": False},
            name_key="login",
        )
        self.assertEqual([item["login"] for item in filtered], ["ldap-user"])

    def test_build_export_search_query_product_and_search_passthrough(self):
        query = EXPORT_FILTERS.build_export_search_query(
            {
                "products": ["ACME"],
                "search": "custom = true",
                "search_by_type": {"repositories": "download_policy = immediate"},
            },
            supports_product=True,
            resource_type="repositories",
        )
        self.assertEqual(
            query,
            'product = "ACME" AND custom = true AND download_policy = immediate',
        )

    def test_append_export_search_for_resource_repositories(self):
        link = EXPORT_FILTERS.append_export_search_for_resource(
            "/katello/api/repositories?full_result=true",
            {"products": ["ACME"]},
            "repositories",
        )
        self.assertIn("product", link)
        self.assertIn("search=", link)

    def test_filter_export_items_settings_include(self):
        items = [
            {"name": "foreman_url", "value": "https://sat.example.com"},
            {"name": "ignored_setting", "value": "x"},
        ]
        filtered = EXPORT_FILTERS.filter_export_items(items, {"settings_include": ["foreman_url"]})
        self.assertEqual([item["name"] for item in filtered], ["foreman_url"])

    def test_filter_reconcile_scope_objects_organizations(self):
        items = [
            {"name": "keep_org", "label": "keep_org"},
            {"name": "skip_org", "label": "skip_org"},
        ]
        filtered = EXPORT_FILTERS.filter_reconcile_scope_objects(
            items,
            {"organizations": ["keep_org"]},
            "satellite_organizations",
        )
        self.assertEqual([item["name"] for item in filtered], ["keep_org"])

    def test_filter_reconcile_scope_objects_hostgroup_parents(self):
        items = [
            {"name": "dc1/web", "title": "dc1/web"},
            {"name": "dc2/web", "title": "dc2/web"},
        ]
        filtered = EXPORT_FILTERS.filter_reconcile_scope_objects(
            items,
            {"hostgroup_parents": ["dc1"]},
            "satellite_hostgroups",
        )
        self.assertEqual([item["name"] for item in filtered], ["dc1/web"])

    def test_filter_reconcile_scope_objects_repository_sets_enabled(self):
        items = [
            {"name": "enabled-set", "enabled": True},
            {"name": "disabled-set", "enabled": False},
        ]
        filtered = EXPORT_FILTERS.filter_reconcile_scope_objects(
            items,
            {"repository_sets_only_enabled": True},
            "satellite_repository_sets",
        )
        self.assertEqual([item["name"] for item in filtered], ["enabled-set"])


if __name__ == "__main__":
    unittest.main()
