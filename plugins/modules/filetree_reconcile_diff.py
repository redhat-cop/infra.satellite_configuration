#!/usr/bin/python
# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: filetree_reconcile_diff
short_description: Compare live export YAML with CaC and write reconcile diff files
description:
  - Compares one object type at a time between a live export directory and a Configuration as Code directory.
  - Pairs YAML files by relative path and compares them at file level (whitespace-normalized text diff) before object reconciliation.
  - Loads only one file pair at a time to avoid loading both full environments into memory at once.
  - Writes diff fragments with C(state) set to V(absent) or V(present) for use with M(infra.satellite_configuration.filetree_read) and dispatch.
options:
  live_dir:
    description: Directory containing live export fragments (for example C(satellite_domains.d/)).
    required: true
    type: path
  cac_dir:
    description: Directory containing desired-state CaC fragments for the same object type.
    required: true
    type: path
  output_dir:
    description: Directory where the diff YAML fragment is written when differences exist.
    required: true
    type: path
  var_name:
    description: Top-level list variable name (for example C(satellite_domains)).
    required: true
    type: str
  merge_key:
    description: Object key used to match live and CaC entries.
    default: name
    type: str
  output_filename:
    description:
      - Filename for the generated diff fragment inside I(output_dir).
      - When omitted, C(var_name).yaml is used.
    type: str
  ignore_keys:
    description: Object keys removed before comparing live and CaC entries and from C(state=absent) copies of live objects.
    default: [created_at, updated_at, id, state]
    type: list
    elements: str
  scope_filters:
    description:
      - Export scope filters applied to both live and CaC objects before reconciliation.
      - When omitted or V(null), no scope filtering is applied (legacy compare behavior).
      - Use the same structure as C(satellite_configuration_filetree_create_filters).
    type: dict
    default: null
  roles_name_excludes:
    description:
      - Exact role names excluded before scope filtering when comparing C(satellite_roles).
      - Aligns with C(filetree_create_roles_name_excludes) on export.
    type: list
    elements: str
    default: []
author:
  - Ivan Aragonés (@ivarmu)
"""

EXAMPLES = r"""
- name: Generate reconcile diff for domains
  infra.satellite_configuration.filetree_reconcile_diff:
    live_dir: /tmp/reconcile_live/satellite_domains.d
    cac_dir: configs/satellite_domains.d
    output_dir: /tmp/reconcile_diff/satellite_domains.d
    var_name: satellite_domains
...
"""

RETURN = r"""
changed:
  description: Whether a diff file was written or updated.
  type: bool
  returned: always
diff_count:
  description: Number of reconcile entries written.
  type: int
  returned: always
present_new:
  description: Objects present in CaC but missing from the live export.
  type: int
  returned: always
present_changed:
  description: Objects present in both sides but with different definitions.
  type: int
  returned: always
absent:
  description: Objects present in the live export but missing from CaC.
  type: int
  returned: always
output_file:
  description: Path to the generated diff file, or empty when no differences were found.
  type: str
  returned: always
...
"""

import os
import traceback

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.infra.satellite_configuration.plugins.module_utils.reconcile_utils import (
        ReconcileCompareError,
        dump_diff_document,
        reconcile_directories,
    )
except ModuleNotFoundError:
    import importlib.util
    from pathlib import Path

    _UTILS_PATH = Path(__file__).resolve().parent.parent / "module_utils" / "reconcile_utils.py"
    _UTILS_SPEC = importlib.util.spec_from_file_location("reconcile_utils", _UTILS_PATH)
    _UTILS_MODULE = importlib.util.module_from_spec(_UTILS_SPEC)
    _UTILS_SPEC.loader.exec_module(_UTILS_MODULE)
    ReconcileCompareError = _UTILS_MODULE.ReconcileCompareError
    dump_diff_document = _UTILS_MODULE.dump_diff_document
    reconcile_directories = _UTILS_MODULE.reconcile_directories

try:
    import yaml
except ImportError:
    yaml = None


def write_reconcile_diff_file(output_dir, output_filename, var_name, diff_items):
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, output_filename)
    rendered = dump_diff_document(var_name, diff_items)
    existing = ""
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as file_handle:
            existing = file_handle.read()
    changed = rendered != existing
    if changed:
        with open(output_file, "w", encoding="utf-8") as file_handle:
            file_handle.write(rendered)
    return output_file, changed


def run_module():
    module = AnsibleModule(
        argument_spec={
            "live_dir": {"type": "path", "required": True},
            "cac_dir": {"type": "path", "required": True},
            "output_dir": {"type": "path", "required": True},
            "var_name": {"type": "str", "required": True},
            # no_log=False: names contain "key" but values are not secrets.
            "merge_key": {"type": "str", "default": "name", "no_log": False},
            "output_filename": {"type": "str", "required": False},
            "ignore_keys": {
                "type": "list",
                "elements": "str",
                # Explicit order must match DOCUMENTATION (not list(frozenset)).
                "default": ["created_at", "updated_at", "id", "state"],
                "no_log": False,
            },
            "scope_filters": {"type": "dict", "default": None},
            "roles_name_excludes": {
                "type": "list",
                "elements": "str",
                "default": [],
                "no_log": False,
            },
        },
        supports_check_mode=True,
    )

    if yaml is None:
        module.fail_json(msg="PyYAML (python3-yaml) is required on the target.")

    params = module.params
    output_filename = params["output_filename"] or f"{params['var_name']}.yaml"

    try:
        diff_items, stats = reconcile_directories(
            params["cac_dir"],
            params["live_dir"],
            params["var_name"],
            params["merge_key"],
            frozenset(params["ignore_keys"]),
            params["scope_filters"],
            params["roles_name_excludes"],
        )

        if not diff_items:
            module.exit_json(
                changed=False,
                diff_count=0,
                present_new=0,
                present_changed=0,
                absent=0,
                output_file="",
                msg="No differences found.",
            )

        if module.check_mode:
            output_file = os.path.join(params["output_dir"], output_filename)
            changed = True
        else:
            output_file, changed = write_reconcile_diff_file(
                params["output_dir"],
                output_filename,
                params["var_name"],
                diff_items,
            )

        module.exit_json(
            changed=changed,
            diff_count=len(diff_items),
            present_new=stats["present_new"],
            present_changed=stats["present_changed"],
            absent=stats["absent"],
            output_file=output_file,
            msg=f"Wrote {len(diff_items)} reconcile entries.",
        )
    except ReconcileCompareError as exc:
        module.fail_json(msg=str(exc))
    except Exception as exc:
        module.fail_json(msg=f"Error: {exc}", exception=traceback.format_exc())


if __name__ == "__main__":
    run_module()
