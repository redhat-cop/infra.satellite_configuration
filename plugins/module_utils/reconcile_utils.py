# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import io
import os

try:
    import yaml
except ImportError:
    yaml = None

try:
    from ansible_collections.infra.satellite_configuration.plugins.module_utils.export_filters import (
        filter_reconcile_scope_objects,
    )
except ModuleNotFoundError:
    import importlib.util
    from pathlib import Path

    _EXPORT_FILTERS_PATH = Path(__file__).resolve().parent / "export_filters.py"
    _EXPORT_FILTERS_SPEC = importlib.util.spec_from_file_location(
        "export_filters",
        _EXPORT_FILTERS_PATH,
    )
    _EXPORT_FILTERS_MODULE = importlib.util.module_from_spec(_EXPORT_FILTERS_SPEC)
    _EXPORT_FILTERS_SPEC.loader.exec_module(_EXPORT_FILTERS_MODULE)
    filter_reconcile_scope_objects = _EXPORT_FILTERS_MODULE.filter_reconcile_scope_objects

DEFAULT_IGNORE_KEYS = frozenset(
    {
        "created_at",
        "updated_at",
        "id",
        "state",
    }
)

YAML_EXTENSIONS = (".yaml", ".yml")


class ReconcileCompareError(Exception):
    """Raised when a file-pair comparison cannot be performed safely."""


def iter_yaml_files(directory):
    """Yield YAML file paths under directory, one path at a time."""
    if not directory or not os.path.isdir(directory):
        return
    for root, _dirs, files in os.walk(directory):
        for filename in sorted(files):
            if filename.endswith(YAML_EXTENSIONS):
                yield os.path.join(root, filename)


def directory_has_yaml_files(directory):
    for _path in iter_yaml_files(directory):
        return True
    return False


def iter_relative_yaml_files(directory):
    """Yield (relative_path, absolute_path) for YAML files under directory."""
    if not directory or not os.path.isdir(directory):
        return
    base = os.path.abspath(directory)
    for path in iter_yaml_files(directory):
        yield os.path.relpath(path, base), path


def iter_file_pairs(cac_dir, live_dir):
    """Yield paired YAML files by relative path between CaC and live directories."""
    cac_files = dict(iter_relative_yaml_files(cac_dir))
    live_files = dict(iter_relative_yaml_files(live_dir))
    for relative_path in sorted(set(cac_files) | set(live_files)):
        yield relative_path, cac_files.get(relative_path), live_files.get(relative_path)


def read_file_text(path):
    with open(path, "r", encoding="utf-8") as file_handle:
        return file_handle.read()


def normalize_text_for_compare(text):
    """Normalize YAML text for file-level comparison (ignore blank lines and trailing spaces)."""
    normalized_lines = []
    for line in text.splitlines():
        stripped = line.rstrip()
        if stripped == "":
            continue
        normalized_lines.append(stripped)
    if not normalized_lines:
        return ""
    return "\n".join(normalized_lines) + "\n"


def files_equal_at_text_level(cac_path, live_path):
    """Return True when two YAML files differ only in whitespace layout."""
    return normalize_text_for_compare(read_file_text(cac_path)) == normalize_text_for_compare(read_file_text(live_path))


def load_objects_from_file(path, var_name, scope_filters=None, roles_name_excludes=None):
    """Load objects for var_name from a single YAML file."""
    if yaml is None:
        raise ImportError("PyYAML is required")
    with open(path, "r", encoding="utf-8") as file_handle:
        document = yaml.safe_load(file_handle)
    if not isinstance(document, dict):
        return []
    items = document.get(var_name, [])
    if not isinstance(items, list):
        return []
    objects = [item for item in items if isinstance(item, dict)]
    if scope_filters is not None:
        objects = filter_reconcile_scope_objects(
            objects,
            scope_filters,
            var_name,
            roles_name_excludes,
        )
    return objects


def build_object_index_from_file(path, var_name, merge_key, scope_filters=None, roles_name_excludes=None):
    """Build an object index from a single YAML file."""
    index = {}
    for item in load_objects_from_file(path, var_name, scope_filters, roles_name_excludes):
        key = item.get(merge_key)
        if key is None:
            continue
        index[key] = item
    return index


def normalize_value(value, ignore_keys):
    if isinstance(value, dict):
        return normalize_dict(value, ignore_keys)
    if isinstance(value, list):
        return [normalize_value(entry, ignore_keys) for entry in value]
    return value


def normalize_dict(data, ignore_keys):
    normalized = {}
    for key, value in data.items():
        if key in ignore_keys:
            continue
        normalized[key] = normalize_value(value, ignore_keys)
    return normalized


def objects_equal(left, right, ignore_keys):
    return normalize_dict(left, ignore_keys) == normalize_dict(right, ignore_keys)


def build_absent_entry(live_object, ignore_keys=None):
    """Copy the full live object into a state=absent entry for dispatch."""
    if ignore_keys is None:
        ignore_keys = DEFAULT_IGNORE_KEYS
    entry = {key: value for key, value in live_object.items() if key not in ignore_keys}
    entry["state"] = "absent"
    return entry


def reset_value_for_type(value):
    """Return an empty value suitable for clearing a live-only field on dispatch."""
    if isinstance(value, dict):
        return {}
    if isinstance(value, list):
        return []
    if value is None:
        return None
    return ""


def merge_present_with_live_resets(cac_object, live_object, ignore_keys):
    """Build a present entry from CaC and clear live-only fields explicitly."""
    entry = dict(cac_object)
    for key, live_value in live_object.items():
        if key in ignore_keys:
            continue
        if key not in entry:
            entry[key] = reset_value_for_type(live_value)
        elif isinstance(live_value, dict) and isinstance(entry.get(key), dict):
            entry[key] = merge_present_with_live_resets(entry[key], live_value, ignore_keys)
    return entry


def build_present_entry(cac_object, live_object=None, ignore_keys=None):
    if ignore_keys is None:
        ignore_keys = DEFAULT_IGNORE_KEYS
    if live_object is not None:
        entry = merge_present_with_live_resets(cac_object, live_object, ignore_keys)
    else:
        entry = dict(cac_object)
    entry["state"] = "present"
    return entry


def compute_diff_items(live_index, cac_index, ignore_keys):
    diff_items = []
    stats = {"present_new": 0, "present_changed": 0, "absent": 0}

    for key, live_object in live_index.items():
        cac_object = cac_index.get(key)
        if cac_object is None:
            diff_items.append(build_absent_entry(live_object, ignore_keys))
            stats["absent"] += 1
        elif not objects_equal(live_object, cac_object, ignore_keys):
            diff_items.append(build_present_entry(cac_object, live_object, ignore_keys))
            stats["present_changed"] += 1

    for key, cac_object in cac_index.items():
        if key not in live_index:
            diff_items.append(build_present_entry(cac_object))
            stats["present_new"] += 1

    return diff_items, stats


def merge_stats(left, right):
    return {
        "present_new": left["present_new"] + right["present_new"],
        "present_changed": left["present_changed"] + right["present_changed"],
        "absent": left["absent"] + right["absent"],
    }


def reconcile_file_pair(
    cac_path,
    live_path,
    var_name,
    merge_key,
    ignore_keys,
    scope_filters=None,
    roles_name_excludes=None,
):
    """Compare one CaC/live file pair and return reconcile entries for that file only."""
    if cac_path and live_path:
        if files_equal_at_text_level(cac_path, live_path):
            return [], {"present_new": 0, "present_changed": 0, "absent": 0}
        live_index = build_object_index_from_file(
            live_path,
            var_name,
            merge_key,
            scope_filters,
            roles_name_excludes,
        )
        cac_index = build_object_index_from_file(
            cac_path,
            var_name,
            merge_key,
            scope_filters,
            roles_name_excludes,
        )
        return compute_diff_items(live_index, cac_index, ignore_keys)

    if live_path and not cac_path:
        live_index = build_object_index_from_file(
            live_path,
            var_name,
            merge_key,
            scope_filters,
            roles_name_excludes,
        )
        diff_items = [build_absent_entry(live_object, ignore_keys) for live_object in live_index.values()]
        return diff_items, {"present_new": 0, "present_changed": 0, "absent": len(diff_items)}

    if cac_path and not live_path:
        cac_index = build_object_index_from_file(
            cac_path,
            var_name,
            merge_key,
            scope_filters,
            roles_name_excludes,
        )
        diff_items = [build_present_entry(cac_object) for cac_object in cac_index.values()]
        return diff_items, {"present_new": len(diff_items), "present_changed": 0, "absent": 0}

    return [], {"present_new": 0, "present_changed": 0, "absent": 0}


def reconcile_directories(
    cac_dir,
    live_dir,
    var_name,
    merge_key,
    ignore_keys,
    scope_filters=None,
    roles_name_excludes=None,
):
    """Compare paired YAML files one at a time without loading both trees in memory."""
    diff_items = []
    stats = {"present_new": 0, "present_changed": 0, "absent": 0}
    file_pairs = list(iter_file_pairs(cac_dir, live_dir))

    live_has_yaml = directory_has_yaml_files(live_dir)
    cac_has_yaml = directory_has_yaml_files(cac_dir)

    if live_has_yaml and not cac_has_yaml:
        raise ReconcileCompareError(
            f"CaC directory {cac_dir} has no YAML files while live directory {live_dir} does; "
            "refusing to mark live objects absent. Check satellite_configuration_filetree_reconcile_cac_path."
        )

    if not file_pairs:
        return diff_items, stats

    for _relative_path, cac_path, live_path in file_pairs:
        pair_items, pair_stats = reconcile_file_pair(
            cac_path,
            live_path,
            var_name,
            merge_key,
            ignore_keys,
            scope_filters,
            roles_name_excludes,
        )
        diff_items.extend(pair_items)
        stats = merge_stats(stats, pair_stats)

    return diff_items, stats


def dump_diff_document(var_name, diff_items):
    if yaml is None:
        raise ImportError("PyYAML is required")
    output_buffer = io.StringIO()
    yaml.dump(
        {var_name: diff_items},
        output_buffer,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        explicit_start=True,
        explicit_end=True,
    )
    return output_buffer.getvalue()
