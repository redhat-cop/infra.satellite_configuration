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

ansible-playbook tests/integration/filetree_create_skip_locked_export.yaml \
  --skip-tags yaml_format
```

The playbook queries `/api/provisioning_templates`, `/api/ptables`, and
`/api/job_templates` for locked objects, exports the three object types, and asserts
that no locked name appears in the generated CaC files (including `Kickstart default`
and `Preseed default LVM` when present on the server).

## Export your configuration using the following commands

Define `satellite` or `satellite_source` in your vars file. For round-trip workflows, prefer `satellite_source` (export) and `satellite_target` (import) in the same file — see the collection README.

* Using `ansible-playbook`

  ```console
  ansible-playbook infra.satellite_configuration.run_filetree_create.yaml -e@vars/satellite.yaml -e '{satellite_configuration_filetree_path: /tmp/satellite_output}'
  ```

* Using `ansible-navigator`

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

* Using `ansible-playbook`

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
