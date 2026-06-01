# infra.satellite.filetree_create

THIS IS A TEST COMMENT TO CHECK THE CI

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
| `satellite` | N/A | yes | dict | Contains all the information needed to connect to the Red Hat Satellite instance. Fields are described below. |
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
| `filetree_create_roles_name_excludes` | see `defaults/main.yml` | no | list | Exact role names skipped as built-in defaults before `GET /api/roles/:id`. |
| `filetree_create_roles_name_excludes_extra` | `[]` | no | list | Additional role names to skip (e.g. site-specific clones of built-ins you do not want exported). |
| `output_path` | `/tmp/satellite_filetree_config` | no | str | The path to the output directory where all the generated `yaml` files with the corresponding objects as code will be written to. |

## Output files format

By default, `infra.aap_configuration_extended.filetree` role formats generated YAML files with `infra.satellite_configuration.format_yaml` (backed by `PyYAML`) to enhance readability. This can be skipped thanks to the tag `yaml_format`, that can be used in the `--skip-tags yaml_format` ansible-playbook parameter.

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

    - name: Get Organizations
      ansible.builtin.import_role:
        name: infra.satellite_configuration.filetree_create

    - name: "Block to fix the output files' format"
      tags: always
      block:
        - name: "Search for all the generated files"
          ansible.builtin.find:
            paths: "{{ output_path }}"
            recurse: true
            patterns:
              - '*.yaml'
              - '*.yml'
          register: _generated_files

        - name: "Re-write all the generated files to make them more readable (Content Credentials special case)"
          ansible.builtin.shell: |
            yq -i '(.satellite_content_credentials[].content) |= (trim + "\n") | (.satellite_content_credentials[].content) style="literal"' '{{ _current_file.path }}'; yq -i -P '{{ _current_file.path }}'
          when: "'content_credentials' in _current_file.path"
          changed_when: true
          loop: "{{ _generated_files.files }}"
          loop_control:
            loop_var: _current_file
            label: "{{ _current_file.path }}"
          # noqa: risky-shell-pipe
          # ^ The shell command above does't use any pipe (only in the yq search)

        - name: "Re-write all the generated files to make them more readable"
          ansible.builtin.shell: "/usr/bin/env yq -i -P '{{ _current_file.path }}' && echo '...' >> '{{ _current_file.path }}'"
          changed_when: true
          loop: "{{ _generated_files.files }}"
          loop_control:
            loop_var: _current_file
            label: "{{ _current_file.path }}"
...
```

The output files are all located in the same directory. Each file contains a YAML list with all the objects belonging to the same object type. This output format allows to load all the objects both from the standard Ansible `group_vars` and from the `infra.satellite_configuration.filetree_read` role.

The exportation can be triggered with the following command:

```console
ansible-playbook infra.satellite_configuration.run_filetree_create.yaml -e@vars/satellite.yaml -e '{output_path: /tmp/satellite_output}'
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

`satellite_roles.yaml` includes **custom roles only**: the `/api/roles` index is often missing `builtin`, so known **built-in role names** are removed first (`filetree_create_roles_name_excludes` plus optional `filetree_create_roles_name_excludes_extra`), then each **`GET /api/roles/:id`** payload is dropped when `builtin` or `locked` still indicates a system role. **Filter rows** are filled by calling **`GET /api/filters/:id`** for each stub (Foreman embeds only `id` / `resource_type` on the role), so **permissions** and **search** export correctly.

`satellite_users.yaml` emits fields compatible with `redhat.satellite.user`: **`auth_source`**, **`default_organization`**, and **`default_location`** as plain strings (not nested API objects), **`auth_source`** from **`auth_source_internal.name`** when the API omits `auth_source`, and **no `usergroups`** (assign users to groups via `satellite_usergroups` / `redhat.satellite.usergroup`). **Passwords are never exported**; when applying with `dispatch`, set **`user_password`** per user (Vault) or **`satellite_users_default_password`** for new Internal-auth users.

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
