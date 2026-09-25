# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from ansible_collections.infra.satellite_configuration.plugins.module_utils.export_filters import (
        append_export_search_for_resource,
        append_export_search_to_api_link,
        append_locked_export_search_to_api_link,
        build_export_search_query,
        filter_export_items,
        filter_export_organizations,
        filters_for_post_api_export,
        is_locked,
        locked_item_names,
        reject_locked_items,
        reject_orphaned_katello_products,
    )
except ModuleNotFoundError:
    import importlib.util
    from pathlib import Path

    _EXPORT_FILTERS_PATH = Path(__file__).resolve().parent.parent / "module_utils" / "export_filters.py"
    _EXPORT_SPEC = importlib.util.spec_from_file_location("export_filters", _EXPORT_FILTERS_PATH)
    _EXPORT_MODULE = importlib.util.module_from_spec(_EXPORT_SPEC)
    _EXPORT_SPEC.loader.exec_module(_EXPORT_MODULE)
    append_export_search_for_resource = _EXPORT_MODULE.append_export_search_for_resource
    append_export_search_to_api_link = _EXPORT_MODULE.append_export_search_to_api_link
    append_locked_export_search_to_api_link = _EXPORT_MODULE.append_locked_export_search_to_api_link
    build_export_search_query = _EXPORT_MODULE.build_export_search_query
    filter_export_items = _EXPORT_MODULE.filter_export_items
    filter_export_organizations = _EXPORT_MODULE.filter_export_organizations
    filters_for_post_api_export = _EXPORT_MODULE.filters_for_post_api_export
    is_locked = _EXPORT_MODULE.is_locked
    locked_item_names = _EXPORT_MODULE.locked_item_names
    reject_locked_items = _EXPORT_MODULE.reject_locked_items
    reject_orphaned_katello_products = _EXPORT_MODULE.reject_orphaned_katello_products


class FilterModule:
    """Filters for filetree_create export exclusions."""

    def filters(self):
        return {
            "satellite_configuration_export_item_is_locked": self.satellite_configuration_export_item_is_locked,
            "satellite_configuration_append_export_search_for_resource": self.satellite_configuration_append_export_search_for_resource,
            "satellite_configuration_append_export_search_to_api_link": self.satellite_configuration_append_export_search_to_api_link,
            "satellite_configuration_append_locked_export_search_to_api_link": self.satellite_configuration_append_locked_export_search_to_api_link,
            "satellite_configuration_build_export_search_query": self.satellite_configuration_build_export_search_query,
            "satellite_configuration_filter_export_items": self.satellite_configuration_filter_export_items,
            "satellite_configuration_filters_for_post_api_export": self.satellite_configuration_filters_for_post_api_export,
            "satellite_configuration_filter_export_organizations": self.satellite_configuration_filter_export_organizations,
            "satellite_configuration_locked_item_names": self.satellite_configuration_locked_item_names,
            "satellite_configuration_reject_locked_items": self.satellite_configuration_reject_locked_items,
            "satellite_configuration_reject_orphaned_katello_products": self.satellite_configuration_reject_orphaned_katello_products,
        }

    def satellite_configuration_export_item_is_locked(self, item):
        return is_locked(item)

    def satellite_configuration_locked_item_names(self, items):
        return locked_item_names(items)

    def satellite_configuration_reject_locked_items(self, items, skip_locked=True):
        return reject_locked_items(items, skip_locked)

    def satellite_configuration_reject_orphaned_katello_products(self, items):
        return reject_orphaned_katello_products(items)

    def satellite_configuration_filter_export_organizations(self, organizations, filters=None):
        return filter_export_organizations(organizations, filters)

    def satellite_configuration_filter_export_items(self, items, filters=None, name_key="name", apply_hostgroup_parents=False):
        return filter_export_items(items, filters, name_key, apply_hostgroup_parents)

    def satellite_configuration_filters_for_post_api_export(self, filters, resource_type):
        return filters_for_post_api_export(filters, resource_type)

    def satellite_configuration_build_export_search_query(
        self,
        filters=None,
        extra_search=None,
        supports_organization=True,
        supports_location=False,
        supports_domain=False,
        supports_hostgroup_parents=False,
        supports_product=False,
        supports_lifecycle_environment=False,
        supports_content_view=False,
        supports_label=False,
        supports_settings=False,
        supports_auth_source=False,
        resource_type=None,
    ):
        return build_export_search_query(
            filters,
            extra_search,
            supports_organization,
            supports_location,
            supports_domain,
            supports_hostgroup_parents,
            supports_product,
            supports_lifecycle_environment,
            supports_content_view,
            supports_label,
            supports_settings,
            supports_auth_source,
            resource_type,
        )

    def satellite_configuration_append_export_search_to_api_link(
        self,
        api_link,
        filters=None,
        extra_search=None,
        supports_organization=True,
        supports_location=False,
        supports_domain=False,
        supports_hostgroup_parents=False,
        supports_product=False,
        supports_lifecycle_environment=False,
        supports_content_view=False,
        supports_label=False,
        supports_settings=False,
        supports_auth_source=False,
        resource_type=None,
    ):
        return append_export_search_to_api_link(
            api_link,
            filters,
            extra_search,
            supports_organization,
            supports_location,
            supports_domain,
            supports_hostgroup_parents,
            supports_product,
            supports_lifecycle_environment,
            supports_content_view,
            supports_label,
            supports_settings,
            supports_auth_source,
            resource_type,
        )

    def satellite_configuration_append_export_search_for_resource(self, api_link, filters=None, resource_type=None, extra_search=None):
        return append_export_search_for_resource(api_link, filters, resource_type, extra_search)

    def satellite_configuration_append_locked_export_search_to_api_link(self, api_link, skip_locked=True, locked_only=False):
        return append_locked_export_search_to_api_link(api_link, skip_locked, locked_only)
