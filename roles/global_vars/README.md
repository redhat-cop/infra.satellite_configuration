# infra.satellite_configuration.global_vars

## Description

Role that defines static variables shared across other roles in this collection. Consumer roles declare a dependency in `meta/main.yml`:

```yaml
dependencies:
  - role: global_vars
```

## Provided variables

| Variable Name | Default | Description |
| :--- | :---: | :--- |
| `satellite_builtin_role_name_skips` | see `defaults/main.yml` | Built-in / locked Foreman role names skipped on export and import |
| `satellite_builtin_role_name_skips_extra` | `[]` | Additional role names to skip on export and import |
| `satellite_configuration_sensitive_vars` | see `defaults/main.yml` | CaC list names that may contain secrets; used by `read_contents.yml` to scope `no_log` per object type in the ingest loop |
| `satellite_redhat_repository_url_substring` | `cdn.redhat.com` | URL substring used to exclude Red Hat CDN repositories from custom repository export/dispatch |
| `satellite_configuration_filetree_read_raw_template_vars` | see `defaults/main.yml` | CaC list names loaded via `slurp` + `from_yaml` in `filetree_read` (no Jinja templating on fragment contents) |
| `satellite_configuration_filetree_path` | `/tmp/satellite_filetree_config` | Base directory for export and import `.d/` fragments |
| `satellite_configuration_vault_placeholder` | `CHANGEME` | Scalar placeholder written into generated `vault_template.yaml` |
| `satellite_configuration_vault_template_vars` | see `defaults/main.yml` | Vault variable names generated in `vault_template.yaml` and referenced from CaC fragments |
| `satellite_settings_host_specific_names` | see `defaults/main.yml` | Host-specific setting names exported with `vault_satellite_settings_host_specific` refs |
| `satellite_source` | — | Optional dict with the same shape as `satellite`; used by `filetree_create` for export (falls back to `satellite` when omitted) |
| `satellite_target` | — | Optional dict with the same shape as `satellite`; used by `filetree_read` and `dispatch` for import (falls back to `satellite` when omitted) |
| `satellite_configuration_overrides_path` | — | Optional base directory for per-type `.d/` override fragments merged during `filetree_read` |
| `satellite_configuration_filetree_read_merge_key` | `name` | Default object key for merging override fragments in `filetree_read` |
| `satellite_configuration_filetree_create_filters` | see `defaults/main.yml` | Optional `filetree_create` export scope (organizations, names, locations, domains, hostgroup branch roots) |

### Source and target Satellite connections

Round-trip workflows can define **two** connections in one vars file so export and import never share the same endpoint by mistake:

```yaml
satellite_source:
  server_url: "https://sat-01.corp.example.com"
  validate_certs: true
  admin:
    username: admin
    password: "{{ vault_source_admin_password }}"
  template:
    mode: "0666"

satellite_target:
  server_url: "https://sat.rh.corp.example.com"
  validate_certs: true
  admin:
    username: admin
    password: "{{ vault_target_admin_password }}"
```

`filetree_create` resolves `satellite` from `satellite_source` when set. `filetree_read` and `dispatch` resolve `satellite` from `satellite_target` when set. The legacy single `satellite` variable remains supported for export-only or import-only playbooks.

## License

GPLv3+
