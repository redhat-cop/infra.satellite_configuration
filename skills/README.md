# Satellite Configuration Skills

Repository workflow skills in **`.mdc`** format (YAML frontmatter + Markdown). Portable location: `skills/` at the repo root (not under `.cursor/`).

## How to Use

- Ask the agent to **use a skill by name** (for example `Use extend-dispatch-object-type for …`).
- Be specific about the object type and scope.
- For new object types, use **`add-object-type-end-to-end`** so all three roles stay in sync.
- **Always apply FQCN** — read `fqcn-standards.mdc` before editing tasks, templates, or playbooks.

## FQCN (mandatory)

See **`fqcn-standards.mdc`** for full rules. Summary:

- `ansible.builtin.*` for builtins
- `redhat.satellite.*` for Satellite modules/roles
- `infra.satellite_configuration.*` for this collection (roles, modules, **filters in `.j2` templates**)
- Role `meta/main.yml` dependencies and `include_role` names must use collection FQCN

## YAML document end (mandatory)

Every Ansible task/playbook YAML file under `roles/` and `playbooks/` must end with `...` (ansible-lint `yaml[document-end]`). This includes helper includes (`*_batch.yaml`, `wait_for_*.yaml`, etc.), not only `satellite_<domain>.yaml`. See **`fqcn-standards.mdc`**.

## End-to-End and Role Extension

| Skill | Purpose |
| --- | --- |
| `add-object-type-end-to-end` | New `satellite_*` type across create, read, dispatch |
| `extend-filetree-create-object-type` | Export pipeline (`get_*`, templates) |
| `extend-filetree-read-object-type` | Ingest from `.d/` fragments (+ overrides) |
| `extend-dispatch-object-type` | Apply/reconcile dispatch tasks |
| `export-satellite-config` | General `filetree_create` export patterns |
| `read-filetree-variables` | `filetree_read` ingest behavior |
| `filetree-variable-layout` | CaC directory layout conventions |
| `format-generated-yaml` | `format_yaml` module usage |
| `fqcn-standards` | FQCN rules for all code |
| `changelog-fragments` | Required `changelogs/fragments/` entries for PRs |
| `live-satellite-integration-tests` | Live-Satellite tests under `tests/integration/` (full roles, yaml_format) |

## Domain Workflows (dispatch / export)

| Skill | Object / area |
| --- | --- |
| `manage-activation-key` | Activation keys |
| `manage-auth-sources-ldap` | LDAP auth sources |
| `manage-content-credentials` | Content credentials |
| `manage-content-view` | Content views |
| `manage-content-view-filters` | CV filters |
| `manage-domains` | Domains |
| `manage-host-collections` | Host collections |
| `manage-hostgroups` | Host groups |
| `manage-lifecycle-environment` | Lifecycle environments |
| `manage-locations` | Locations |
| `manage-operatingsystems` | Operating systems |
| `manage-organizations` | Organizations |
| `manage-partition-tables` | Partition tables |
| `manage-products` | Products |
| `manage-provisioning-templates` | Provisioning templates |
| `manage-repository-sets` | Repository sets |
| `manage-settings` | Settings |
| `manage-subnets` | Subnets |
| `manage-sync-plan` | Sync plans |
| `manage-usergroups` | User groups |
| `add-repository` | Custom repositories |
| `async-repository-sync-and-wait` | Repository sync/wait |
| `promote-content` | CV publish/promote |
| `export-network-and-host-topology` | Domains, subnets, hostgroups export |
| `satellite-connection-defaults` | `satellite` / `satellite_source` / `satellite_target` |

## Consistency

When adding a new object type, update in one change set:

- `roles/filetree_create`
- `roles/filetree_read`
- `roles/dispatch`

Naming: `satellite_<resource_plural>`, `get_<domain>.yaml`, `satellite_<domain>.yaml`, `satellite_<resource_plural>.yaml.j2`, `satellite_<resource_plural>.d/`.

## Cursor Integration

- **Rules:** `.cursor/rules/satellite-general.mdc` (always apply), `.cursor/rules/skills-discovery.mdc` (points here).
- **Skills path:** `skills/*.mdc` — use `globs` in frontmatter to auto-attach skills to matching files when supported.
