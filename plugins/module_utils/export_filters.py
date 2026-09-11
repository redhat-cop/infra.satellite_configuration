# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

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


def locked_item_names(items):
    """Return display names for locked items in an API index or detail list."""
    names = []
    for item in items or []:
        if not is_locked(item):
            continue
        if isinstance(item, dict):
            names.append(item.get("name", str(item.get("id", "unknown"))))
        else:
            names.append(str(item))
    return names
