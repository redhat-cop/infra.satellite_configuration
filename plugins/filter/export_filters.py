# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

try:
    from ansible_collections.infra.satellite_configuration.plugins.module_utils.export_filters import (
        is_locked,
        locked_item_names,
        reject_locked_items,
    )
except ModuleNotFoundError:
    import importlib.util
    from pathlib import Path

    _EXPORT_FILTERS_PATH = Path(__file__).resolve().parent.parent / "module_utils" / "export_filters.py"
    _EXPORT_SPEC = importlib.util.spec_from_file_location("export_filters", _EXPORT_FILTERS_PATH)
    _EXPORT_MODULE = importlib.util.module_from_spec(_EXPORT_SPEC)
    _EXPORT_SPEC.loader.exec_module(_EXPORT_MODULE)
    is_locked = _EXPORT_MODULE.is_locked
    locked_item_names = _EXPORT_MODULE.locked_item_names
    reject_locked_items = _EXPORT_MODULE.reject_locked_items


class FilterModule:
    """Filters for filetree_create export exclusions."""

    def filters(self):
        return {
            "satellite_configuration_export_item_is_locked": self.satellite_configuration_export_item_is_locked,
            "satellite_configuration_locked_item_names": self.satellite_configuration_locked_item_names,
            "satellite_configuration_reject_locked_items": self.satellite_configuration_reject_locked_items,
        }

    def satellite_configuration_export_item_is_locked(self, item):
        return is_locked(item)

    def satellite_configuration_locked_item_names(self, items):
        return locked_item_names(items)

    def satellite_configuration_reject_locked_items(self, items, skip_locked=True):
        return reject_locked_items(items, skip_locked)
