# Testing the collection

Following there's an example of how this collection can be used to export and import Satellite Configuration.

## Integration test: skip locked factory objects at export

Against a live Satellite (default install recommended), verify that locked factory
provisioning templates, partition tables, and job templates are **not** written to
the export tree when using default `filetree_create` skip settings:

```console
export SATELLITE_SERVER_URL="https://satellite.example.com"
export SATELLITE_USERNAME="admin"
export SATELLITE_PASSWORD="secret"
export SATELLITE_VALIDATE_CERTS="true"

tests/integration/run_integration_tests.sh skip_locked
# or:
ansible-playbook tests/integration/filetree_create_skip_locked_export.yaml \
  --tags always,skip_locked,provisioning_templates,partition_tables,job_templates,yaml_format
```

The playbook queries `/api/provisioning_templates`, `/api/ptables`, and
`/api/job_templates` for locked objects, runs the full **filetree_create** role with CLI
`--tags` for the three object types plus `yaml_format`, and asserts that no locked name
appears in the generated CaC files (including `Kickstart default` and `Preseed default LVM`
when present on the server).

## Integration test: export scope filters and reconcile symmetry

Against a live Satellite, verify every `satellite_configuration_filetree_create_filters`
dimension through the full **filetree_create** role and scoped compare through the full
**filetree_reconcile** role. Each test case must pass CLI `--tags` for the test selector,
object-type block, and `yaml_format` or `compare` — the same as production playbooks.
`ansible_run_tags` cannot be set from playbook vars; use `tests/integration/run_integration_tests.sh`
for the full suite. Do not use `tasks_from: get_*.yaml` or `apply: tags` on `include_role`.

Fixture values are discovered from the API unless overridden with environment variables.

See `skills/live-satellite-integration-tests.mdc` before adding new integration tests.

```console
export SATELLITE_SERVER_URL="https://satellite.example.com"
export SATELLITE_USERNAME="admin"
export SATELLITE_PASSWORD="secret"
export SATELLITE_VALIDATE_CERTS="true"

# Full suite (one ansible-playbook invocation per test with correct --tags)
tests/integration/run_integration_tests.sh all

# Export filter suites only
tests/integration/run_integration_tests.sh filters

# One export filter manually
ansible-playbook tests/integration/filetree_create_export_filters.yaml \
  --tags always,filter_organizations,organizations,yaml_format

# One reconcile case manually
ansible-playbook tests/integration/filetree_create_export_filters.yaml \
  --tags always,reconcile,reconcile_cac_out_of_scope,organizations,yaml_format,compare
```

Optional environment variables:

- `SATELLITE_CONFIGURATION_FILETREE_PATH` — export output directory (default under `/tmp`)
- `SATELLITE_EXPORT_FILTER_ORGANIZATION` — primary organization fixture
- `SATELLITE_EXPORT_FILTER_DOMAIN_NAME` — primary domain fixture
- `SATELLITE_EXPORT_FILTER_LOCATION` — primary location fixture

Export filter tags (`filter_<name>`):

| Tag | Filter key | Export object type |
| --- | --- | --- |
| `filter_organizations` | `organizations` | `satellite_organizations` |
| `filter_organizations_repositories` | `organizations` | `satellite_repositories` |
| `filter_organizations_exclude` | `organizations_exclude` | `satellite_organizations` |
| `filter_name_include` | `name_include` | `satellite_domains` |
| `filter_name_exclude` | `name_exclude` | `satellite_domains` |
| `filter_name_use_regex` | `name_use_regex` + `name_include` | `satellite_domains` |
| `filter_locations` | `locations` | `satellite_hostgroups` |
| `filter_locations_exclude` | `locations_exclude` | `satellite_hostgroups` |
| `filter_domains` | `domains` | `satellite_subnets` |
| `filter_domains_exclude` | `domains_exclude` | `satellite_subnets` |
| `filter_hostgroup_parents` | `hostgroup_parents` | `satellite_hostgroups` |
| `filter_products` | `products` | `satellite_repositories` |
| `filter_products_exclude` | `products_exclude` | `satellite_repositories` |
| `filter_lifecycle_environments` | `lifecycle_environments` | `satellite_lifecycle_environments` |
| `filter_lifecycle_environments_exclude` | `lifecycle_environments_exclude` | `satellite_lifecycle_environments` |
| `filter_content_views` | `content_views` | `satellite_content_views` |
| `filter_content_views_exclude` | `content_views_exclude` | `satellite_content_views` |
| `filter_labels` | `labels` | `satellite_repositories` |
| `filter_labels_exclude` | `labels_exclude` | `satellite_repositories` |
| `filter_repository_sets_only_enabled` | `repository_sets_only_enabled` | `satellite_repository_sets` |
| `filter_auth_sources` | `auth_sources` | `satellite_users` |
| `filter_auth_sources_exclude` | `auth_sources_exclude` | `satellite_users` |
| `filter_users_admin` | `users_admin` | `satellite_users` |
| `filter_settings_include` | `settings_include` | `satellite_settings` |
| `filter_settings_exclude` | `settings_exclude` | `satellite_settings` |
| `filter_roles_include_builtin` | `roles_include_builtin` | `satellite_roles` |
| `filter_roles_include_locked` | `roles_include_locked` | `satellite_roles` |
| `filter_search` | `search` | `satellite_domains` |
| `filter_search_by_type` | `search_by_type` | `satellite_domains` |

Reconcile scope tags (`reconcile_<case>`):

| Tag | Scenario |
| --- | --- |
| `reconcile_cac_out_of_scope` | Out-of-scope CaC organization does not produce `state: present` |
| `reconcile_live_out_of_scope` | Out-of-scope live organization does not produce `state: absent` |
| `reconcile_unscoped_legacy` | Without `scope_filters`, out-of-scope CaC produces `present_new` |
| `reconcile_domains_scope` | Domain `name_include` scope ignores out-of-scope CaC domain |

Tests that need optional Satellite content (nested host groups, repository labels, a second
organization, and so on) are skipped automatically when fixtures cannot be discovered.

## Export your configuration using the following commands

Define `satellite` or `satellite_source` in your vars file. For round-trip workflows, prefer `satellite_source` (export) and `satellite_target` (import) in the same file — see the collection README.

- Using `ansible-playbook`

  ```console
  ansible-playbook infra.satellite_configuration.run_filetree_create.yaml -e@vars/satellite.yaml -e '{satellite_configuration_filetree_path: /tmp/satellite_output}'
  ```

- Using `ansible-navigator`

  ```console
  ansible-navigator run infra.satellite_configuration.run_filetree_create.yaml \
    --tags settings \
    --eei registry.redhat.io/ansible-automation-platform-26/ee-supported-rhel9 \
    --pp never \
    -m stdout \
    --eev ~/satellite-configuration:~/satellite-configuration/tests/collections/ansible_collections/infra/satellite_configuration \
    --eev ~/satellite-configuration:~/satellite-configuration \
    -- \
    -e@~/satellite-configuration/tests/vars/satellite.yaml \
    -e '{satellite_configuration_filetree_path: ~/satellite-configuration/tests/satellite_output}'
  ```

## Import your configuration as code using the following commands

- Using `ansible-playbook`

  ```console
  ansible-playbook -i localhost, infra.satellite_configuration.run_filetree_read.yaml -e@vars/satellite.yaml -e '{satellite_configuration_filetree_path: configs}'
  ```

## Role Input Variables

### Role: `dispatch`

| Variable Name | Default Value | Description |
| --- | --- | --- |
| `satellite_username` | `{{ lookup("env", "SATELLITE_USERNAME") }}` | The username to connect to the Satellite instance |
| `satellite_password` | `{{ lookup("env", "SATELLITE_PASSWORD") }}` | The password to connect to the Satellite instance |
| `satellite_server_url` | `{{ lookup("env", "SATELLITE_SERVER_URL") }}` | The Satellite instance's URL/IP |
| `satellite_configuration_dispatch_content_views_purge_count` | `6` | Keep this many newest content view versions after publish (tag `cv_publish_promote`). Alias: `content_views_purge_count`. |
| `satellite_configuration_dispatch_content_view_publish_promote` | `true` | When `true`, publishes and promotes content views after creation. Set `false` to skip or on re-runs. |
| `satellite_configuration_dispatch_secure_logging` | `true` | When `true`, sets `no_log` on dispatch tasks for sensitive object types (users, settings, content credentials, LDAP). Set `false` when debugging to surface API errors in the log. |

### Role: `filetree_create`

| Variable Name | Default Value | Description |
| --- | --- | --- |
| `satellite_configuration_filetree_path` | `/tmp/satellite_filetree_config` | Base directory for `satellite_<type>.d/` fragments (export and import). `output_path` in `filetree_create` is an alias. |

### Role: `filetree_read`

<table>
  <thead>
    <tr>
      <th>Variable Name</th>
      <th>Default Value</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>satellite_configuration_filetree_read_secure_logging</code></td>
      <td><code>true</code></td>
      <td>When <code>true</code>, sets <code>no_log</code> only while loading variables listed in <code>satellite_configuration_sensitive_vars</code> (role <code>global_vars</code>). Set <code>false</code> when debugging.</td>
    </tr>
    <tr>
      <td><code>satellite_activation_keys</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Activation Keys.</td>
    </tr>
    <tr>
      <td><code>satellite_auth_sources_ldap</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Authenticator Sources (LDAP)</td>
    </tr>
    <tr>
      <td><code>satellite_content_credentials</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Content Credentials</td>
    </tr>
    <tr>
      <td><code>satellite_content_view_filters</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Content View Filters</td>
    </tr>
    <tr>
      <td><code>satellite_content_views</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Content Views</td>
    </tr>
    <tr>
      <td><code>satellite_domains</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Domains</td>
    </tr>
    <tr>
      <td><code>satellite_host_collections</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Host Collections</td>
    </tr>
    <tr>
      <td><code>satellite_hostgroups</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Host Groups</td>
    </tr>
    <tr>
      <td><code>satellite_lifecycle_environments</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Lifecycle Environments</td>
    </tr>
    <tr>
      <td><code>satellite_locations</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Locations</td>
    </tr>
    <tr>
      <td><code>satellite_operatingsystems</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Operating Systems</td>
    </tr>
    <tr>
      <td><code>satellite_organizations</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Organizations</td>
    </tr>
    <tr>
      <td><code>satellite_partition_tables</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Partition Tables</td>
    </tr>
    <tr>
      <td><code>satellite_products</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Products</td>
    </tr>
    <tr>
      <td><code>satellite_provisioning_templates</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Provisioning Templates</td>
    </tr>
    <tr>
      <td><code>satellite_repositories</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Repositories</td>
    </tr>
    <tr>
      <td><code>satellite_repository_sets</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Repository Sets</td>
    </tr>
    <tr>
      <td><code>satellite_roles</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Roles</td>
    </tr>
    <tr>
      <td><code>satellite_settings</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Settings</td>
    </tr>
    <tr>
      <td><code>satellite_subnets</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Subnets</td>
    </tr>
    <tr>
      <td><code>satellite_sync_plans</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Synchronization Plans</td>
    </tr>
    <tr>
      <td><code>satellite_usergroups</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite User Groups</td>
    </tr>
    <tr>
      <td><code>satellite_users</code></td>
      <td><code>[]</code></td>
      <td>List with the Satellite Users</td>
    </tr>
    <tr>
      <td><code>satellite_configuration_filetree_read_tasks</code></td>
      <td><a href="https://github.com/redhat-cop/infra.satellite_configuration/blob/devel/roles/filetree_read/defaults/main.yml#L29-L53">See defaults file</a></td>
      <td>List to define how to read each object type. Each list item needs the following information:
        <ul>
          <li> <strong>name</strong>: Name of the Object Type,
          <li> <strong>var</strong>: Variable that contains the Objects for that object type,
          <li> <strong>tags</strong>: Tags to filter the tasks to be executed/skipped,
          <li> <strong>path</strong>: Path where the CaC files are found for the current object type
        </ul>
      </td>
    </tr>
  </tbody>
</table>
