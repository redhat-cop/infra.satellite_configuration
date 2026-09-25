# infra.satellite_configuration.filetree_reconcile

Reconcile the live Satellite configuration against Configuration as Code (CaC).

## Workflow

1. **Export** — `filetree_create` writes the current API state to `satellite_configuration_filetree_reconcile_live_path`.
2. **Compare** — `filetree_reconcile_diff` pairs YAML files by relative path between the live and CaC `.d/` directories. Each pair is compared at file level (whitespace-normalized text, like `diff`); only when a pair differs semantically are reconcile entries generated. One file pair is processed at a time.
3. **Generate** — diff fragments are written to `satellite_configuration_filetree_reconcile_diff_path` with:
   - `state: absent` when an object exists in the live export but not in CaC
   - `state: present` when an object exists in CaC but not in the live export, or when definitions differ (CaC wins)
   - For `state: present`, fields that exist on the live object but are omitted from CaC are emitted with an empty value (`""`, `{}`, or `[]`) so manual API drift is cleared on dispatch
4. **Apply** — `filetree_read` loads only object types that have fragments under `.reconcile_diff/` (not the full CaC tree), then `dispatch` applies them to `satellite_target`.

## Requirements

- `satellite_source` for export (step 1)
- `satellite_target` for apply (step 4)
- CaC fragments under `satellite_configuration_filetree_reconcile_cac_path`

## Role Variables

| Variable | Default | Description |
| --- | --- | --- |
| `satellite_configuration_filetree_reconcile_cac_path` | `satellite_configuration_filetree_path` | Optional override when CaC lives outside the filetree path |
| `satellite_configuration_filetree_reconcile_live_path` | `{{ satellite_configuration_filetree_path }}/.reconcile_live` | Live export output |
| `satellite_configuration_filetree_reconcile_diff_path` | `{{ satellite_configuration_filetree_path }}/.reconcile_diff` | Generated diff fragments |
| `satellite_configuration_filetree_reconcile_export` | `true` | Run export step |
| `satellite_configuration_filetree_reconcile_compare` | `true` | Run compare/generate step |
| `satellite_configuration_filetree_reconcile_apply` | `true` | Run apply step |
| `satellite_configuration_filetree_reconcile_tasks` | `{{ satellite_configuration_filetree_read_tasks }}` | Object types to compare |
| `satellite_configuration_filetree_reconcile_secure_logging` | `true` | Scope `no_log` on sensitive compare tasks |
| `satellite_configuration_filetree_reconcile_filters` | `{{ satellite_configuration_filetree_create_filters }}` | Scope filters applied to **both** live and CaC objects during compare |
| `satellite_configuration_filetree_reconcile_apply_scope_filters` | `true` | When `false`, compare ignores scope filters (legacy unscoped behavior) |
| `satellite_configuration_filetree_reconcile_roles_name_excludes` | `{{ satellite_builtin_role_name_skips }}` | Built-in role names excluded before scope filtering |
| `satellite_configuration_filetree_reconcile_roles_name_excludes_extra` | `[]` | Additional role names excluded before scope filtering |

## Export scope filters (symmetry with filetree_create)

The live export step uses `filetree_create` and therefore honors `satellite_configuration_filetree_create_filters`. By default, compare applies the same scope to **both** sides via `satellite_configuration_filetree_reconcile_filters` (aliased to the create filters). Objects outside the export scope are omitted from the diff instead of producing false `state: present` (CaC-only, out of scope) or `state: absent` (live-only, out of scope) entries.

Set `satellite_configuration_filetree_reconcile_apply_scope_filters: false` to compare full CaC trees without scope filtering. Override `satellite_configuration_filetree_reconcile_filters` when compare scope must differ from export scope.

## Example Playbook

See [`playbooks/run_filetree_reconcile.yaml`](../../playbooks/run_filetree_reconcile.yaml).

```yaml
---
- name: Reconcile Satellite configuration against CaC
  hosts: localhost
  connection: local
  gather_facts: false
  collections:
    - infra.satellite_configuration
    - redhat.satellite
  vars:
    satellite_configuration_filetree_path: configs
  module_defaults:
    group/redhat.satellite.satellite:
      username: "{{ satellite.admin.username }}"
      password: "{{ satellite.admin.password }}"
      server_url: "{{ satellite.server_url }}"
      validate_certs: "{{ satellite.validate_certs }}"
  roles:
    - role: infra.satellite_configuration.filetree_reconcile
```

## Tags

| Tag | Phase |
| --- | --- |
| `export` | Live export (`filetree_create` → `.reconcile_live/`) |
| `compare` | Reset diff directory and compare/generate (directory setup tasks) |
| `apply` | Load diff fragments (`filetree_read`) and apply (`dispatch`) |
| `<object_type>` | Per-type compare only (for example `organizations`, `domains`) — forwarded from `satellite_configuration_filetree_read_tasks` |

Per-type tags filter **compare** and **apply** (object types only; workflow tags `export`, `compare`, and `apply` are excluded from object-type filtering). When object-type tags are present on the CLI, only those types are compared or applied. When only workflow tags are used (for example `compare` or `apply`), all object types run for that phase.

Examples:

```bash
# Full reconcile (export + compare + apply)
ansible-playbook playbooks/run_filetree_reconcile.yaml -e@vars/satellite.yaml

# Re-compare all types using an existing live export (no re-export, no apply)
ansible-playbook playbooks/run_filetree_reconcile.yaml -e@vars/satellite.yaml \
  --tags compare \
  -e '{satellite_configuration_filetree_reconcile_export: false, satellite_configuration_filetree_reconcile_apply: false}'

# Re-compare one type only (no full diff directory reset)
ansible-playbook playbooks/run_filetree_reconcile.yaml -e@vars/satellite.yaml \
  --tags provisioning_templates \
  -e '{satellite_configuration_filetree_reconcile_export: false, satellite_configuration_filetree_reconcile_apply: false}'

# Compare and apply organizations only (no live re-export)
ansible-playbook playbooks/run_filetree_reconcile.yaml -e@vars/satellite.yaml \
  --tags organizations,apply \
  -e '{satellite_configuration_filetree_reconcile_export: false}'

# Apply an existing diff without re-export or re-compare
ansible-playbook playbooks/run_filetree_reconcile.yaml -e@vars/satellite.yaml \
  --tags apply \
  -e '{satellite_configuration_filetree_reconcile_export: false, satellite_configuration_filetree_reconcile_compare: false}'
```

Generate diff only (no apply): set `satellite_configuration_filetree_reconcile_apply: false` or omit the `apply` tag.
