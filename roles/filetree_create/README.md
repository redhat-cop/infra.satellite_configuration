# infra.satellite.filetree_create

The role `infra.satellite.filetree_create` is intended to be used as the first step to begin using the Configuration as Code on Red Hat Satellite, when you already have a running instance of any of them. Obviously, you also could start to write your objects as code from scratch, but the idea behind the creation of that role is to simplify your lives and make that task a little bit easier.

## Requirements

* Collections:
  * [redhat.satellite][link_redhat.satellite]: Can be installed with the command `ansible-galaxy collection install redhat.satellite` (Requires [configuration][link_galaxy_configuration]).

* Python libraries:
  * [`PyYAML`][link_pyyaml]: Can be installed with one of the following methods:

    **RHEL 8**

    ```console
    sudo dnf install -y epel-release
    sudo dnf install -y python3-yaml
    ```

    **RHEL 9**

    ```console
    sudo dnf config-manager --set-enabled crb
    sudo dnf install -y python3-yaml
    ```

    **RHEL 10**

    ```console
    sudo dnf install -y python3-yaml
    ```

    **Pip**

    ```console
    pip install pyyaml
    ```

## Role Variables

The following variables are required for that role to work properly:

| Variable Name | Default Value | Required | Type | Description |
| :------------ | :-----------: | :------: | :------: | :---------- |
| `satellite` | N/A | yes* | dict | Connection to the Red Hat Satellite instance. *Optional when `satellite_source` is set (export uses `satellite_source` and falls back to `satellite`). Fields are described below. |
| `satellite_source` | — | no | dict | Source Satellite for export; same shape as `satellite`. Preferred for round-trip workflows together with `satellite_target`. |
| `satellite.server_url` | N/A | yes | str | Red Hat Satellite Server URL (must include the protocol  to be used 'https://'). |
| `satellite.validate_certs` | N/A | yes | str | Specifies whether to validate certificates or not when connecting to Red Hat Satellite server. |
| `satellite.admin` | N/A | yes | dict | Contains all the information related to the user to use to connect to the Red Hat Satellite server. Fields are described below. |
| `satellite.admin.username` | N/A | yes | str | Specifies the username to be used. |
| `satellite.admin.password` | N/A | yes | str | Specifies the password to be used. |
| `satellite.template` | N/A | yes | dict | Contains the information needed for the generated files' permissions. Fields are described below. |
| `satellite.template.set_ownership` | `false` | no | bool | When `true`, `owner` and `group` are applied to generated files. When `false` (default), files are owned by the Ansible user (avoids `chown` failures without root). The export directory is always created with `mode` only. |
| `satellite.template.owner` | N/A | if `set_ownership` | str | User name or UID for generated files when `set_ownership` is `true`. |
| `satellite.template.group` | N/A | if `set_ownership` | str | Group name or GID for generated files when `set_ownership` is `true`. |
| `satellite.template.mode` | N/A | yes | str | Specifies the permissions the generated files will have. |
| `filetree_create_roles_name_excludes` | see role `global_vars` | no | list | Exact role names skipped as built-in defaults before `GET /api/roles/:id`. |
| `filetree_create_roles_name_excludes_extra` | `[]` | no | list | Additional role names to skip (e.g. site-specific clones of built-ins you do not want exported). |
| `filetree_create_include_locked_templates` | `false` | no | bool | When `true`, export locked factory provisioning templates, partition tables, job templates, and installation media (full-site backup mode). Overrides the per-type `filetree_create_skip_locked_*` vars below. |
| `filetree_create_skip_locked_provisioning_templates` | `true` | no | bool | Omit locked factory provisioning templates (for example `Kickstart default`) from export. |
| `filetree_create_skip_locked_partition_tables` | `true` | no | bool | Omit locked factory partition tables (for example `Preseed default LVM`) from export. |
| `filetree_create_skip_locked_job_templates` | `true` | no | bool | Omit locked factory job templates from export. |
| `filetree_create_skip_locked_installation_mediums` | `true` | no | bool | Omit locked factory installation media from export when the API exposes `locked`. |
| `filetree_create_skip_satellite_host_operatingsystem` | `false` | no | bool | When `true`, omit the operating system assigned to the Satellite host (matched via `satellite.server_url` hostname on `/api/hosts`). Opt-in because some migrations need every OS exported. |
| `output_path` | see `satellite_configuration_filetree_path` in role `global_vars` | no | str | Alias for `satellite_configuration_filetree_path`. Export writes `satellite_<type>.d/<type>.yaml` under this directory. |
| `satellite_configuration_export_source_aliases` | `[]` | no | list | Extra IPs, short names, or alternate FQDNs of the source Satellite to replace in installation-medium paths with `vault_satellite_installation_mediums_target_fqdn`. |

## Output files format

By default, the `filetree_create` role formats generated YAML files with `infra.satellite_configuration.format_yaml` (tag `yaml_format`, backed by `PyYAML`). Skip it with `--skip-tags yaml_format` when debugging raw template output.

Export templates wrap problematic values (PEM/GPG keys, descriptions with `:`, product names with `,`, SSH keys) in literal blocks protected by `{% raw %}` / `{% endraw %}` markers; `format_yaml` unwraps those markers and emits canonical block-style YAML.

## Example Playbook

```yaml
---
- name: Export Satellite Configuration
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
    - name: Ensure that the output_path exists
      ansible.builtin.file:
        path: "{{ output_path }}"
        mode: "0777"
        state: directory
      tags: always

    - name: Export Satellite configuration
      ansible.builtin.import_role:
        name: infra.satellite_configuration.filetree_create
...
```

The output files are written under `satellite_<object_type>.d/` directories beneath `satellite_configuration_filetree_path`. Each directory contains a YAML file with the list for that object type. This layout matches `filetree_read` import paths, so export output can be applied without manual restructuring.

The exportation can be triggered with the following command:

```console
ansible-playbook infra.satellite_configuration.run_filetree_create.yaml -e@vars/satellite.yaml -e '{satellite_configuration_filetree_path: /tmp/satellite_output}'
```

Where the `vars/satellite.yaml` file is defined as follows:

```yaml
---
satellite:
  server_url: "https://satellite.server.domain.com"
  validate_certs: true
  admin:
    username: username
    password: password
  template:
    mode: '0666'
    # Optional: set set_ownership: true and owner/group when your environment can chown (e.g. root).
    # owner: '1000'
    # group: '1000'
...
```

One example of the generated files follows:

```console
/tmp/satellite_filetree_config
├── satellite_activation_keys.yaml
├── satellite_auth_sources_ldap.yaml
├── satellite_content_credentials.yaml
├── satellite_content_views.yaml
├── satellite_domains.yaml
├── satellite_host_collections.yaml
├── satellite_hostgroups.yaml
├── satellite_lifecycle_environments.yaml
├── satellite_locations.yaml
├── satellite_operatingsystems.yaml
├── satellite_organizations.yaml
├── satellite_products.yaml
├── satellite_repositories.yaml
├── satellite_repository_sets.yaml
├── satellite_roles.yaml
├── satellite_settings.yaml
├── satellite_subnets.yaml
├── satellite_sync_plans.yaml
├── satellite_usergroups.yaml
└── satellite_users.yaml
```

`satellite_roles.yaml` includes **custom roles only**: the `/api/roles` index is often missing `builtin`, so known **built-in role names** are removed first (`satellite_builtin_role_name_skips` from role **`global_vars`**, exposed as `filetree_create_roles_name_excludes` plus optional `filetree_create_roles_name_excludes_extra`), then each **`GET /api/roles/:id`** payload is dropped unless **`builtin` is `0`** and **`locked`** is false (Foreman marks plugin and built-in roles such as `ForemanRhCloud Read Only` as locked). The same skip list is used by **`dispatch`** when importing legacy exports. **Filter rows** are filled by calling **`GET /api/filters/:id`** for each stub (Foreman embeds only `id` / `resource_type` on the role), so **permissions** and **search** export correctly.

**Locked factory templates** (`provisioning_templates`, `partition_tables`, `job_templates`, and locked `installation_mediums`) are omitted from export by default (`filetree_create_skip_locked_*`, symmetric with **`dispatch`** import guards). Ansible logs how many locked objects were skipped and prints up to five sample names. Set **`filetree_create_include_locked_templates: true`** (or each `filetree_create_skip_locked_*` to `false`) for a full-site backup that retains factory defaults such as `Kickstart default` and `Preseed default LVM`. Optionally set **`filetree_create_skip_satellite_host_operatingsystem: true`** to omit the OS used by the Satellite host itself.

`satellite_users.yaml` emits fields compatible with `redhat.satellite.user`: **`auth_source`**, **`default_organization`**, and **`default_location`** as plain strings (not nested API objects), **`auth_source`** from **`auth_source_internal.name`** when the API omits `auth_source`, and **no `usergroups`** (assign users to groups via `satellite_usergroups` / `redhat.satellite.usergroup`). Internal-auth users reference **`user_password`** via `{{ vault_satellite_users_passwords['login'] }}` (filled from `vault_template.yaml` on import).

`satellite_auth_sources_ldap.yaml` is built from **`GET /api/auth_source_ldaps/:id`**. **`account_password`** is write-only in the API; exports always emit `{{ vault_satellite_auth_sources_ldap_account_passwords['name'] }}` for each LDAP source.

**`vault_template.yaml`** is written at the export root with predictable `vault_*` variables (`satellite_configuration_vault_template_vars` in role **`global_vars`**). CaC fragments reference those variables directly; replace placeholder values, optionally encrypt the file, and pass it on import with `-e@…/vault_template.yaml`. `vault_satellite_installation_mediums_target_fqdn` is included only when exported installation medium `path` values reference a source Satellite hostname.

## License

GPLv3+

## Author Information

* [Silvio Pérez][link_silvinux]
* [Ivan Aragonés][link_ivarmu]

[link_pyyaml]: https://pypi.org/project/PyYAML/
[link_redhat.satellite]: https://console.redhat.com/ansible/automation-hub/repo/published/redhat/satellite/
[link_galaxy_configuration]: https://console.redhat.com/ansible/automation-hub/repo/published/redhat/satellite/distributions/
[link_silvinux]: https://github.com/silvinux
[link_ivarmu]: https://github.com/ivarmu
