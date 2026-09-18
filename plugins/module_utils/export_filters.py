# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

import fnmatch
import re

try:
    from urllib.parse import quote
except ImportError:  # Python 2 (ansible-test import sanity)
    from urllib import quote  # pylint: disable=no-name-in-module,import-error

__metaclass__ = type


def is_locked(item):
    """Return True when a Foreman API object is locked (factory/built-in)."""
    if not isinstance(item, dict):
        return False
    locked = item.get("locked", False)
    if isinstance(locked, str):
        return locked.lower() in ("true", "1", "yes")
    return bool(locked)


def reject_locked_items(items, skip_locked=True):
    """Drop locked items from an API index or detail list when skip_locked is true."""
    if not skip_locked:
        return list(items or [])
    return [item for item in (items or []) if not is_locked(item)]


def reject_orphaned_katello_products(items):
    """Drop Katello repositories whose nested product dict is marked orphaned."""
    filtered = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        product = item.get("product")
        if isinstance(product, dict) and bool(product.get("orphaned")):
            continue
        filtered.append(item)
    return filtered


def append_locked_export_search_to_api_link(api_link, skip_locked=True, locked_only=False):
    """Append Foreman search= for locked scope when index responses omit the locked attribute."""
    if locked_only:
        search_fragment = "locked=true"
    elif skip_locked:
        search_fragment = "locked=false"
    else:
        return str(api_link)
    separator = "&" if "?" in str(api_link) else "?"
    return str(api_link) + separator + "search=" + quote(search_fragment)


def locked_item_names(items):
    """Return display names for locked items when the API object exposes a locked field."""
    names = []
    for item in items or []:
        if not is_locked(item):
            continue
        if isinstance(item, dict):
            names.append(item.get("name", str(item.get("id", "unknown"))))
        else:
            names.append(str(item))
    return names


def _normalize_export_filters(filters):
    if not isinstance(filters, dict):
        return {}
    return filters


def _export_item_name(item, name_key="name"):
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return str(item)
    if name_key in item and item[name_key] is not None:
        return str(item[name_key])
    if "name" in item and item["name"] is not None:
        return str(item["name"])
    return ""


def _export_item_organization_name(item):
    if not isinstance(item, dict):
        return ""
    organization = item.get("organization")
    if isinstance(organization, dict):
        return str(organization.get("name") or "")
    if organization is not None:
        return str(organization)
    organization_name = item.get("organization_name")
    if organization_name is not None:
        return str(organization_name)
    return ""


def _export_pattern_matches(value, patterns, use_regex=False):
    if not patterns:
        return False
    for pattern in patterns:
        if pattern is None:
            continue
        pattern_text = str(pattern)
        if not pattern_text:
            continue
        if use_regex:
            if re.search(pattern_text, value):
                return True
        elif fnmatch.fnmatchcase(value, pattern_text):
            return True
    return False


def _export_passes_name_filters(name, filters):
    filters = _normalize_export_filters(filters)
    include_patterns = filters.get("name_include") or []
    exclude_patterns = filters.get("name_exclude") or []
    use_regex = bool(filters.get("name_use_regex"))

    if include_patterns and not _export_pattern_matches(name, include_patterns, use_regex):
        return False
    if exclude_patterns and _export_pattern_matches(name, exclude_patterns, use_regex):
        return False
    return True


def filter_export_organizations(organizations, filters=None):
    """Filter organization objects or names for filetree_create export scope."""
    filters = _normalize_export_filters(filters)
    include_orgs = filters.get("organizations") or []
    exclude_orgs = filters.get("organizations_exclude") or []

    filtered = []
    for organization in organizations or []:
        name = _export_item_name(organization, "name")
        if include_orgs and name not in include_orgs:
            continue
        if exclude_orgs and name in exclude_orgs:
            continue
        if not _export_passes_name_filters(name, filters):
            continue
        filtered.append(organization)
    return filtered


def _collect_related_names(item, scalar_keys, list_keys=()):
    if not isinstance(item, dict):
        return []
    names = []
    for key in scalar_keys:
        value = item.get(key)
        if value is None:
            continue
        if isinstance(value, dict):
            if value.get("name"):
                names.append(str(value["name"]))
            elif value.get("title"):
                names.append(str(value["title"]))
        else:
            names.append(str(value))
    for key in list_keys:
        values = item.get(key)
        if not isinstance(values, list):
            continue
        for entry in values:
            if isinstance(entry, dict):
                if entry.get("name"):
                    names.append(str(entry["name"]))
                elif entry.get("title"):
                    names.append(str(entry["title"]))
            elif entry is not None:
                names.append(str(entry))
    return names


def _export_item_location_names(item):
    return _collect_related_names(
        item,
        ("location", "location_name", "default_location", "default_location_name"),
        ("locations",),
    )


def _export_item_domain_names(item):
    return _collect_related_names(
        item,
        ("domain", "domain_name"),
        ("domains",),
    )


def _export_item_product_names(item):
    return _collect_related_names(item, ("product", "product_name"), ())


def _export_item_lifecycle_environment_names(item):
    return _collect_related_names(
        item,
        (
            "lifecycle_environment",
            "lifecycle_environment_name",
            "environment",
            "environment_name",
        ),
        (),
    )


def _export_item_content_view_names(item):
    return _collect_related_names(item, ("content_view", "content_view_name"), ())


def _export_item_label_names(item):
    return _collect_related_names(item, ("label", "content_label"), ())


def _export_item_auth_source_names(item):
    names = _collect_related_names(item, ("auth_source", "auth_source_name"), ())
    if isinstance(item, dict):
        internal = item.get("auth_source_internal")
        if isinstance(internal, dict) and internal.get("name"):
            names.append(str(internal["name"]))
    return names


def _passes_exact_name_list_filters(values, include_values, exclude_values):
    if include_values and not any(value in include_values for value in values):
        return False
    if exclude_values and any(value in exclude_values for value in values):
        return False
    return True


def _passes_optional_dimension(values, include_values, exclude_values):
    if not include_values and not exclude_values:
        return True
    if include_values and not values:
        return False
    return _passes_exact_name_list_filters(values, include_values, exclude_values)


def _passes_settings_name_filters(name, filters):
    filters = _normalize_export_filters(filters)
    include_settings = filters.get("settings_include") or []
    exclude_settings = filters.get("settings_exclude") or []
    if not include_settings and not exclude_settings:
        return True
    if include_settings and name not in include_settings:
        return False
    if exclude_settings and name in exclude_settings:
        return False
    return True


def _passes_users_admin_filter(item, filters):
    filters = _normalize_export_filters(filters)
    users_admin = filters.get("users_admin")
    if users_admin is None or users_admin == "":
        return True
    if isinstance(users_admin, str):
        want_admin = users_admin.lower() in ("true", "1", "yes")
    else:
        want_admin = bool(users_admin)
    is_admin = False
    if isinstance(item, dict):
        admin_value = item.get("admin")
        if isinstance(admin_value, str):
            is_admin = admin_value.lower() in ("true", "1", "yes")
        else:
            is_admin = bool(admin_value)
    return is_admin == want_admin


def _hostgroup_in_parent_branch(item, parent_roots):
    if not parent_roots:
        return True
    title = ""
    if isinstance(item, dict):
        title = str(item.get("title") or item.get("name") or "")
    if not title:
        return False
    for root in parent_roots:
        root_text = str(root)
        if title == root_text or title.startswith(root_text + "/"):
            return True
    return False


def filter_export_items(items, filters=None, name_key="name", apply_hostgroup_parents=False):
    """Filter export objects by organization, location, domain, name, and optional hostgroup branch scope."""
    filters = _normalize_export_filters(filters)
    include_orgs = filters.get("organizations") or []
    exclude_orgs = filters.get("organizations_exclude") or []
    include_locations = filters.get("locations") or []
    exclude_locations = filters.get("locations_exclude") or []
    include_domains = filters.get("domains") or []
    exclude_domains = filters.get("domains_exclude") or []
    hostgroup_parents = filters.get("hostgroup_parents") or []
    include_products = filters.get("products") or []
    exclude_products = filters.get("products_exclude") or []
    include_lifecycle_environments = filters.get("lifecycle_environments") or []
    exclude_lifecycle_environments = filters.get("lifecycle_environments_exclude") or []
    include_content_views = filters.get("content_views") or []
    exclude_content_views = filters.get("content_views_exclude") or []
    include_labels = filters.get("labels") or []
    exclude_labels = filters.get("labels_exclude") or []
    include_auth_sources = filters.get("auth_sources") or []
    exclude_auth_sources = filters.get("auth_sources_exclude") or []

    filtered = []
    for item in items or []:
        name = _export_item_name(item, name_key)
        if not _export_passes_name_filters(name, filters):
            continue
        if not _passes_settings_name_filters(name, filters):
            continue

        organization_name = _export_item_organization_name(item)
        if include_orgs or exclude_orgs:
            if include_orgs:
                if not organization_name or organization_name not in include_orgs:
                    continue
            if exclude_orgs and organization_name in exclude_orgs:
                continue

        location_names = _export_item_location_names(item)
        if include_locations or exclude_locations:
            if include_locations and not location_names:
                continue
            if not _passes_exact_name_list_filters(location_names, include_locations, exclude_locations):
                continue

        domain_names = _export_item_domain_names(item)
        if include_domains or exclude_domains:
            if include_domains and not domain_names:
                continue
            if not _passes_exact_name_list_filters(domain_names, include_domains, exclude_domains):
                continue

        if apply_hostgroup_parents and not _hostgroup_in_parent_branch(item, hostgroup_parents):
            continue

        if not _passes_optional_dimension(_export_item_product_names(item), include_products, exclude_products):
            continue
        if not _passes_optional_dimension(
            _export_item_lifecycle_environment_names(item),
            include_lifecycle_environments,
            exclude_lifecycle_environments,
        ):
            continue
        if not _passes_optional_dimension(
            _export_item_content_view_names(item),
            include_content_views,
            exclude_content_views,
        ):
            continue
        if not _passes_optional_dimension(_export_item_label_names(item), include_labels, exclude_labels):
            continue

        if include_auth_sources or exclude_auth_sources or filters.get("users_admin") not in (None, ""):
            auth_source_names = _export_item_auth_source_names(item)
            if include_auth_sources or exclude_auth_sources:
                if include_auth_sources and not auth_source_names:
                    continue
                if not _passes_exact_name_list_filters(auth_source_names, include_auth_sources, exclude_auth_sources):
                    continue
            if not _passes_users_admin_filter(item, filters):
                continue

        filtered.append(item)
    return filtered


RECONCILE_LOCKED_VAR_NAMES = frozenset(
    {
        "satellite_provisioning_templates",
        "satellite_partition_tables",
        "satellite_job_templates",
        "satellite_installation_mediums",
    }
)


def _role_item_is_builtin(item):
    if not isinstance(item, dict):
        return False
    builtin = item.get("builtin")
    if builtin is None:
        return False
    if isinstance(builtin, str):
        return builtin.lower() not in ("0", "false", "")
    return int(builtin) != 0


def _passes_role_reconcile_filters(item, filters, roles_name_excludes=None):
    if not isinstance(item, dict):
        return False
    name = item.get("name")
    if roles_name_excludes and name in roles_name_excludes:
        return False
    filters = _normalize_export_filters(filters)
    if _role_item_is_builtin(item) and not bool(filters.get("roles_include_builtin")):
        return False
    if is_locked(item) and not bool(filters.get("roles_include_locked")):
        return False
    return True


def _repository_set_is_enabled(item):
    if not isinstance(item, dict):
        return True
    enabled = item.get("enabled")
    if enabled is None:
        return True
    if isinstance(enabled, str):
        return enabled.lower() in ("true", "1", "yes")
    return bool(enabled)


def filter_reconcile_scope_objects(items, filters=None, var_name="", roles_name_excludes=None):
    """Filter reconcile YAML objects using the same scope rules as filetree_create export."""
    filters = _normalize_export_filters(filters)
    scoped_items = list(items or [])

    if var_name == "satellite_organizations":
        return filter_export_organizations(scoped_items, filters)

    if var_name in RECONCILE_LOCKED_VAR_NAMES:
        scoped_items = reject_locked_items(scoped_items, skip_locked=True)

    if var_name == "satellite_repository_sets":
        if filters.get("repository_sets_only_enabled", True):
            scoped_items = [item for item in scoped_items if _repository_set_is_enabled(item)]

    if var_name == "satellite_roles":
        scoped_items = [item for item in scoped_items if _passes_role_reconcile_filters(item, filters, roles_name_excludes)]

    apply_hostgroup_parents = var_name == "satellite_hostgroups"
    return filter_export_items(scoped_items, filters, "name", apply_hostgroup_parents)


def _quote_search_value(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _glob_pattern_to_name_predicate(pattern):
    pattern_text = str(pattern)
    if not pattern_text:
        return None
    if "*" not in pattern_text and "?" not in pattern_text:
        return "name = " + _quote_search_value(pattern_text)
    like_chars = []
    for char in pattern_text:
        if char == "*":
            like_chars.append("%")
        elif char == "?":
            like_chars.append("_")
        elif char == "%":
            like_chars.append("\\%")
        elif char == "_":
            like_chars.append("\\_")
        else:
            like_chars.append(char)
    return "name ~ " + _quote_search_value("".join(like_chars))


def _name_search_parts(filters):
    filters = _normalize_export_filters(filters)
    if filters.get("name_use_regex"):
        return []
    include_patterns = filters.get("name_include") or []
    exclude_patterns = filters.get("name_exclude") or []
    parts = []
    include_predicates = []
    for pattern in include_patterns:
        predicate = _glob_pattern_to_name_predicate(pattern)
        if predicate:
            include_predicates.append(predicate)
    if include_predicates:
        if len(include_predicates) == 1:
            parts.append(include_predicates[0])
        else:
            parts.append("(" + " OR ".join(include_predicates) + ")")
    for pattern in exclude_patterns:
        predicate = _glob_pattern_to_name_predicate(pattern)
        if predicate:
            parts.append("NOT (" + predicate + ")")
    return parts


def _exact_field_search_parts(field_name, include_values, exclude_values):
    parts = []
    if include_values:
        predicates = [field_name + " = " + _quote_search_value(value) for value in include_values]
        if len(predicates) == 1:
            parts.append(predicates[0])
        else:
            parts.append("(" + " OR ".join(predicates) + ")")
    for value in exclude_values:
        parts.append(field_name + " != " + _quote_search_value(value))
    return parts


def _organization_search_parts(filters, supports_organization=True):
    if not supports_organization:
        return []
    filters = _normalize_export_filters(filters)
    return _exact_field_search_parts(
        "organization",
        filters.get("organizations") or [],
        filters.get("organizations_exclude") or [],
    )


def _location_search_parts(filters, supports_location=True):
    if not supports_location:
        return []
    filters = _normalize_export_filters(filters)
    return _exact_field_search_parts(
        "location",
        filters.get("locations") or [],
        filters.get("locations_exclude") or [],
    )


def _domain_search_parts(filters, supports_domain=True):
    if not supports_domain:
        return []
    filters = _normalize_export_filters(filters)
    return _exact_field_search_parts(
        "domain",
        filters.get("domains") or [],
        filters.get("domains_exclude") or [],
    )


def _optional_search_fragment(extra_search):
    if extra_search is None:
        return None
    if extra_search.__class__.__name__ == "Omit":
        return None
    text = str(extra_search).strip()
    return text or None


def _resolved_extra_search(extra_search, filters, resource_type=None):
    fragments = []
    base_fragment = _optional_search_fragment(extra_search)
    if base_fragment:
        fragments.append(base_fragment)
    filters = _normalize_export_filters(filters)
    global_fragment = _optional_search_fragment(filters.get("search"))
    if global_fragment:
        fragments.append(global_fragment)
    by_type = filters.get("search_by_type") or {}
    if resource_type and isinstance(by_type, dict):
        type_fragment = _optional_search_fragment(by_type.get(resource_type))
        if type_fragment:
            fragments.append(type_fragment)
    if not fragments:
        return None
    return " AND ".join(fragments)


def _hostgroup_parent_search_parts(filters, supports_hostgroup_parents=False):
    if not supports_hostgroup_parents:
        return []
    filters = _normalize_export_filters(filters)
    parents = filters.get("hostgroup_parents") or []
    if not parents:
        return []
    predicates = []
    for root in parents:
        root_text = str(root)
        predicates.append("title = " + _quote_search_value(root_text))
        predicates.append("title ~ " + _quote_search_value(root_text + "/%"))
    if len(predicates) == 1:
        return [predicates[0]]
    return ["(" + " OR ".join(predicates) + ")"]


def _product_search_parts(filters, supports_product=True):
    if not supports_product:
        return []
    filters = _normalize_export_filters(filters)
    return _exact_field_search_parts(
        "product",
        filters.get("products") or [],
        filters.get("products_exclude") or [],
    )


def _lifecycle_environment_search_parts(filters, supports_lifecycle_environment=True):
    if not supports_lifecycle_environment:
        return []
    filters = _normalize_export_filters(filters)
    return _exact_field_search_parts(
        "environment",
        filters.get("lifecycle_environments") or [],
        filters.get("lifecycle_environments_exclude") or [],
    )


def _content_view_search_parts(filters, supports_content_view=True):
    if not supports_content_view:
        return []
    filters = _normalize_export_filters(filters)
    return _exact_field_search_parts(
        "content_view",
        filters.get("content_views") or [],
        filters.get("content_views_exclude") or [],
    )


def _label_search_parts(filters, supports_label=True):
    if not supports_label:
        return []
    filters = _normalize_export_filters(filters)
    return _exact_field_search_parts(
        "label",
        filters.get("labels") or [],
        filters.get("labels_exclude") or [],
    )


def _settings_search_parts(filters, supports_settings=False):
    if not supports_settings:
        return []
    filters = _normalize_export_filters(filters)
    return _exact_field_search_parts(
        "name",
        filters.get("settings_include") or [],
        filters.get("settings_exclude") or [],
    )


def _auth_source_search_parts(filters, supports_auth_source=False):
    if not supports_auth_source:
        return []
    filters = _normalize_export_filters(filters)
    return _exact_field_search_parts(
        "auth_source",
        filters.get("auth_sources") or [],
        filters.get("auth_sources_exclude") or [],
    )


def build_export_search_query(
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
    """Build a Foreman/Katello scoped_search string from export scope filters."""
    parts = []
    parts.extend(_organization_search_parts(filters, supports_organization))
    parts.extend(_location_search_parts(filters, supports_location))
    parts.extend(_domain_search_parts(filters, supports_domain))
    parts.extend(_hostgroup_parent_search_parts(filters, supports_hostgroup_parents))
    parts.extend(_product_search_parts(filters, supports_product))
    parts.extend(_lifecycle_environment_search_parts(filters, supports_lifecycle_environment))
    parts.extend(_content_view_search_parts(filters, supports_content_view))
    parts.extend(_label_search_parts(filters, supports_label))
    parts.extend(_settings_search_parts(filters, supports_settings))
    parts.extend(_auth_source_search_parts(filters, supports_auth_source))
    parts.extend(_name_search_parts(filters))
    extra_fragment = _resolved_extra_search(extra_search, filters, resource_type)
    if extra_fragment:
        parts.append(extra_fragment)
    if filters and _normalize_export_filters(filters).get("users_admin") not in (
        None,
        "",
    ):
        users_admin = _normalize_export_filters(filters).get("users_admin")
        if isinstance(users_admin, str):
            want_admin = users_admin.lower() in ("true", "1", "yes")
        else:
            want_admin = bool(users_admin)
        parts.append("admin = " + ("true" if want_admin else "false"))
    if not parts:
        return None
    return " AND ".join(parts)


def append_export_search_to_api_link(
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
    """Append a search= query parameter to an API path when export filters apply."""
    search_query = build_export_search_query(
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
    if not search_query:
        return str(api_link)
    separator = "&" if "?" in str(api_link) else "?"
    return str(api_link) + separator + "search=" + quote(search_query)


_EXPORT_API_FILTER_KEYS_BY_SUPPORT_FLAG = {
    "supports_organization": ("organizations", "organizations_exclude"),
    "supports_location": ("locations", "locations_exclude"),
    "supports_domain": ("domains", "domains_exclude"),
    "supports_hostgroup_parents": ("hostgroup_parents",),
    "supports_product": ("products", "products_exclude"),
    "supports_lifecycle_environment": (
        "lifecycle_environments",
        "lifecycle_environments_exclude",
    ),
    "supports_content_view": ("content_views", "content_views_exclude"),
    "supports_label": ("labels", "labels_exclude"),
    "supports_settings": ("settings_include", "settings_exclude"),
    "supports_auth_source": ("auth_sources", "auth_sources_exclude"),
}

_EXTRA_POST_API_EXPORT_FILTER_KEYS_BY_RESOURCE = {
    "users": ("users_admin",),
}


def filters_for_post_api_export(filters=None, resource_type=None):
    """Return export filters with dimensions removed that API search already applies."""
    normalized = _normalize_export_filters(filters)
    if not resource_type:
        return normalized
    stripped = dict(normalized)
    supports = EXPORT_RESOURCE_API_SEARCH_SUPPORTS.get(str(resource_type), {})
    keys_to_remove = []
    for support_flag, filter_keys in _EXPORT_API_FILTER_KEYS_BY_SUPPORT_FLAG.items():
        if supports.get(support_flag):
            keys_to_remove.extend(filter_keys)
    keys_to_remove.extend(_EXTRA_POST_API_EXPORT_FILTER_KEYS_BY_RESOURCE.get(str(resource_type), ()))
    for key in keys_to_remove:
        stripped.pop(key, None)
    return stripped


EXPORT_RESOURCE_API_SEARCH_SUPPORTS = {
    "activation_keys": {"supports_lifecycle_environment": True},
    "content_views": {
        "supports_organization": True,
        "supports_product": True,
        "supports_content_view": True,
    },
    "domains": {"supports_location": True},
    "hostgroups": {
        "supports_location": True,
        "supports_domain": True,
        "supports_hostgroup_parents": True,
    },
    "lifecycle_environments": {
        "supports_organization": True,
        "supports_lifecycle_environment": True,
    },
    "products": {"supports_product": True, "supports_label": True},
    "repositories": {
        "supports_organization": True,
        "supports_product": True,
        "supports_label": True,
    },
    "repository_sets": {"supports_product": True, "supports_label": True},
    "settings": {"supports_settings": True},
    "subnets": {"supports_domain": True},
    "users": {"supports_location": True, "supports_auth_source": True},
}


def append_export_search_for_resource(api_link, filters=None, resource_type=None, extra_search=None):
    """Append export scope search= using per-resource API field support defaults."""
    flags = {
        "supports_organization": False,
        "supports_location": False,
        "supports_domain": False,
        "supports_hostgroup_parents": False,
        "supports_product": False,
        "supports_lifecycle_environment": False,
        "supports_content_view": False,
        "supports_label": False,
        "supports_settings": False,
        "supports_auth_source": False,
    }
    if resource_type:
        flags.update(EXPORT_RESOURCE_API_SEARCH_SUPPORTS.get(resource_type, {}))
    return append_export_search_to_api_link(api_link, filters, extra_search, resource_type=resource_type, **flags)
