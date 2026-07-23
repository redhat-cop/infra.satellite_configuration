============================================
infra.satellite\_configuration Release Notes
============================================

.. contents:: Topics

v1.3.1
======

Bugfixes
--------

- release automation - create and merge the changelog PR with GITHUB_TOKEN so merge_release no longer fails when GH_WORKFLOW_KEY lacks createPullRequest.

v1.3.0
======

Minor Changes
-------------

- Add partner certification checks (galaxy-importer, ansible-lint production profile, and ansible-test sanity) to CI so CRC Automation Hub import failures are caught before release.
- Rename content_views_purge_count default to satellite_configuration_dispatch_content_views_purge_count (compat alias kept).
- Run galaxy-importer in pre-commit (and extend local ansible-doc checks to filters) so CRC/Galaxy import findings fail before a release is published.
- Ship .ansible-lint in the collection artifact so Galaxy Importer respects collection skip_list (for example internal-error without redhat.satellite).

Bugfixes
--------

- dispatch - avoid recursive Jinja self-reference when passing satellite_operatingsystems into redhat.satellite.operatingsystems (Galaxy Importer ansible-lint jinja[invalid]).
- filetree_reconcile_diff - align DOCUMENTATION defaults with argument_spec for ignore_keys and output_filename (ansible-test validate-modules).
- release automation - treat Verify Releases as successful when either Galaxy or Automation Hub publish succeeds so a single publish failure does not abort merge and EE build.

v1.2.1
======

Bugfixes
--------

- CI - prepare Automation Hub collections in the trusted approval workflow and restore them in pre-commit tests so fork pull requests no longer fail when ``CRC_PUBLISH_KEY`` is unavailable.
- Fix pre-commit approval-gate hanging when the pull_request_target approval workflow never starts (for example GITHUB_TOKEN-created update-pre-commit PRs) by falling back to the in-workflow requires-approval environment gate.
- dispatch - avoid recursive Jinja self-reference when passing satellite_manifest_download and RHSM credentials into redhat.satellite.manifest (ansible-lint jinja[invalid]).
- filters - add ansible-doc sidecar documentation for satellite_configuration_contains_template_markers, satellite_configuration_unwrap_raw_markers, satellite_configuration_sanitize_partition_table_layout, and satellite_configuration_merge_by_key (Galaxy Importer ansible-doc).

v1.2.0
======

Minor Changes
-------------

- Add dispatch support for domains, subnets, and host groups via redhat.satellite.domains, subnets, and hostgroups.
- Add filetree_reconcile role to detect and remediate drift between live Satellite state and Configuration as Code (export, compare, generate diff, apply).
- Add filetree_reconcile_diff module and reconcile_utils for file-pair YAML comparison with state present and state absent entries.
- Add job template export, ingest, and dispatch (redhat.satellite.job_template) with vault-backed hidden template input defaults.
- Add optional subscription manifest upload (redhat.satellite.manifest) and pre-flight manifest validation before content tasks.
- Add role global_vars for shared static variables (built-in role skips, sensitive var lists, filetree path, Red Hat CDN filter).
- Add run_filetree_reconcile playbook with export, compare, and apply workflow tags plus per-object-type filtering.
- Add satellite_configuration_merge_by_key filter for override merge by object name (or per-type merge_key).
- Add satellite_configuration_overrides_path for environment-specific CaC override fragments merged during filetree_read.
- Add satellite_configuration_unwrap_raw_markers filter and raw_markers module utils for CaC round-trip.
- Add satellite_source and satellite_target for round-trip export/import with separate endpoints in one vars file.
- Document supported object types and known gaps (compute resources, global parameters, SCAP, webhooks, HTTP proxies, remote execution).
- Move satellite_configuration_filetree_read_tasks to global_vars so filetree_read and filetree_reconcile share the same object-type list and paths.
- Re-enable content view publish/promote dispatch with satellite_configuration_dispatch_content_view_publish_promote and satellite_content_view_versions.
- Restructure configs to the same .d layout for greenfield CaC authoring.
- Unify export and import under satellite_configuration_filetree_path with satellite type .d fragments (no org/env path nesting).
- dispatch - support satellite_manifests list for per-organization manifest upload and validation.
- filetree_create generates vault_template.yaml with vault_* variables referenced directly from CaC fragments (LDAP, users, settings, installation mediums).

Bugfixes
--------

- dispatch - apply RBAC in dependency order (organizations, locations, roles, users, usergroups); skip Red Hat CDN repos; opt-in host collection membership.
- dispatch - order host_collections before activation_keys; provisioning templates before operatingsystems with phased OS default assignment.
- dispatch - remove unsupported provisioning_template description; fix content_view_version_cleanup include_role usage.
- dispatch - reorder content and provisioning tasks per round-trip dependencies; enable content_view_filters dispatch.
- dispatch - scope no_log to sensitive object types only; filter locked provisioning templates before loop evaluation.
- dispatch content view publish/promote - promote latest_version when needs_publish is false (same-host re-import); poll foreman_tasks between batches and wait only while content view tasks are running.
- dispatch partition tables - sanitize invalid <%# %> metadata blocks before import; load via slurp in filetree_read.
- dispatch products - omit sync_plan on initial pass so sync plans can be created first.
- dispatch products - skip Red Hat subscription products on initial pass; batch custom products with configurable pause to reduce Satellite RAM spikes.
- dispatch products - two-pass create (without sync_plan, then associate after sync_plans) to break products/sync_plans circular dependency.
- dispatch provisioning templates - create snippets first with kind snippet; skip OS default assignment for snippets.
- dispatch repositories - flatten nested gpg_key/SSL credential dicts from legacy exports; fix repository sync handler notify casing.
- dispatch sync_plans - associate only custom (non-subscription) products on the products pass.
- dispatch sync_plans - two-pass create (without products, then associate after products) to break products/sync_plans circular dependency.
- filetree_create - enrich kickstart releasever from enabled repositories; strip use_netgroups for Active Directory LDAP sources on export.
- filetree_create - skip readonly settings, locked/built-in roles, Red Hat CDN repositories, enabled-only repository sets, host collection membership, and host-specific settings by default.
- filetree_create activation keys export - emit host_collections as name strings for dispatch module compatibility.
- filetree_create export - emit operating system references as name/major/minor; resolve target titles on dispatch.
- filetree_create export - escape installation-medium hostname regex patterns; support source aliases for IP-based paths.
- filetree_create export - fix repository CDN filtering, enabled repository set selection, and repository set organization lookup without re-exporting organizations.
- filetree_create export - use dir_mode for .d fragment directories; replace invalid Jinja list comprehensions in LDAP and roles tasks.
- filetree_create export - vault-ref hidden entity parameters (hostgroups, operatingsystems, domains, subnets, organizations, locations).
- filetree_create export - vault-ref hidden job template input defaults via /api/templates/:id/template_inputs.
- filetree_create export templates - fix users, products, content credentials, settings, and repository sets YAML formatting (colons, commas, SSH keys, raw fields).
- filetree_create installation mediums export - replace source Satellite FQDN in path with vault_satellite_installation_mediums_target_fqdn reference.
- filetree_create products export - export custom Anonymous-provider products, resolve sync_plan names, and omit internal provider/sync_plan IDs.
- filetree_create products export - omit subscription products via Katello search redhat=false when skip flag is enabled (index API omits redhat/provider_name).
- filetree_create products export - resolve sync_plan names without Katello per_page=all on sync_plans API.
- filetree_create provisioning templates export - emit kind snippet instead of a bare snippet boolean flag.
- filetree_create repositories export - emit gpg_key and SSL credential references as flat name strings.
- filetree_create repositories export - omit gpg_key_id numeric field from export.
- filetree_create settings export - quote encrypted and YAML-alias masked values so format_yaml can parse satellite_settings output.
- filetree_create users export - emit default mail for Internal users without email (required on create).
- filetree_create vault_template.yaml - document required vault variables with placeholder comments for two-host import.
- filetree_read - fail clearly when vault variables are undefined during include_vars (avoid ansible-core TypeError on failed_when).
- filetree_read - load settings, LDAP, and users with include_vars (no_log disabled on load) so vault refs resolve; keep slurp for ERB-heavy templates.
- filetree_read - tolerate empty or missing .d/ directories when setting loaded CaC variables.
- format_yaml - preserve PEM/GPG multiline content, quote YAML-significant scalars, unwrap raw/endraw export wrappers, and normalize legacy unsafe tags.
- galaxy.yml - require redhat.satellite >=5.8.0 instead of an exact pin.
- handle bootstrap PRs where pre-commit-approve.yml is not yet on devel by applying inline approval rules and a manual-approval environment gate for .github changes
- run changelog validation in the pull_request workflow so actions/checkout no longer refuses fork PR code from a pull_request_target context
- split pre-commit CI into a trusted pull_request_target approval workflow and a pull_request test workflow that waits for approval before checking out fork PR code

v1.1.3
======

Bugfixes
--------

- README - use absolute URLs for Automation Hub rendering and add a Support section per certified collection template.
- The file .ansible-lint is now ignored when building the release of the collection
- ansible-lint - remove evaluate-only rule suppressions for fqcn[action] and role-name[path].
- fixed the LICENSE field in the galaxy.yml file so it is showing GPL >= 3 right now
- playbooks - refactor example playbooks for ansible-lint syntax-check compatibility (remove YAML anchors, use collection FQCN roles).

v1.1.2
======

Bugfixes
--------

- README - use absolute URLs for Automation Hub rendering and add a Support section per certified collection template.
- ansible-lint - remove evaluate-only rule suppressions for fqcn[action] and role-name[path].
- playbooks - refactor example playbooks for ansible-lint syntax-check compatibility (remove YAML anchors, use collection FQCN roles).

v1.1.1
======

Bugfixes
--------

- Re-publish collection as 1.1.1 after withdrawing the failed 1.1.0 GitHub release and CRC import review.

v1.1.0
======

Minor Changes
-------------

- Add a local collection Python sanity check in pre-commit to mirror galaxy-importer and ansible-test feedback before publishing.
- Add pylint to pre-commit with a repository ``.pylintrc``; scope black and pylint to ``plugins/`` and ``tests/unit``, and exclude paths such as ``.ansible/`` that are not part of the source tree.
- Lower the minimum supported ``ansible-core`` version to 2.16 (``meta/runtime.yml``), aligned with ``redhat.satellite`` and Satellite 6.18 shipped stacks.
- Updated the README.md files of each role
- filetree_create - export custom roles and users to ``satellite_roles.yaml`` and ``satellite_users.yaml`` using tags ``roles`` and ``users``. Default roles are excluded by configurable name blocklist (thin index lacks ``builtin``) plus filters on full role JSON after ``GET /api/roles/:id``.
- filetree_create - optional ``satellite.template.set_ownership`` (default ``false``) to apply ``owner``/``group`` on templated export files; the playbook only sets ``mode`` on the output directory to avoid ``chown`` errors for local runs.
- format_yaml - apply pylint-driven code quality updates (no change to module behaviour).
- format_yaml - fix PEM repair f-string for Python 3.7–3.11 compatibility (required by ansible-test sanity and galaxy-importer).
- galaxy.yml - expand ``build_ignore`` so development, CI, and test paths are omitted from the collection artifact.

Bugfixes
--------

- Add installation_mediums. This has been added using the cursor skills provided by the PR
- Fix the clean_fields.j2 template to remove spaces at the end of lines as they were preventing the 'yq -P' to process raw data correctly.
- Fix the filetree_create role as the provisioning template's output needs to have the operatingsystem's title instead of it's name to let the dispatch to work properly.
- Fix the output of the format_yaml.py module to correctly format the output (Certificates mainly)
- Read files when there are files to read
- Remove extra new lines that was introduced when templating
- Remove yq from the collection and add a new module to process the yaml files using PyYAML.
- Replace the format_yaml.py module with the one available from infra.aap_configuration_extended collection.
- ansible.cfg - use the correct INI key ``collections_path`` (singular) so vendored collections under ``./collections`` are actually loaded; ``collections_paths`` was ignored by Ansible.
- filetree_create - ``satellite_roles.yaml.j2`` emits readable multi-line YAML under Ansible default ``trim_blocks`` (explicit newlines after each permission and after ``search``, ``{%- endfor %}`` / ``{%- endif %}`` to avoid doubled blanks, and a blank line between filter entries).
- filetree_create - export role filters with permissions and search by following ``GET /api/filters/:id`` for each stub returned on ``GET /api/roles/:id`` (Foreman embed is thin).
- filetree_create - keep canonical YAML formatting by passing ``preserve_comments: false`` to ``format_yaml`` (restores full round-trip dump behavior).
- filetree_create - move ``format_yaml`` steps into ``include_tasks`` so tag-filtered runs (e.g. ``--tags roles,users``) do not require the collection action to be resolvable at parse time.
- filetree_create - restore ``preserve_comments: false`` for ``format_yaml`` so generated YAML is fully canonicalized (block-style lists/dicts) rather than only having indentation adjusted (module default preserves comments).
- fixes some bugs and lintering issues.
- format_yaml - fix module documentation YAML parsing by avoiding a colon+space sequence inside an inline example.
- release_auto workflow - create GitHub releases as draft on the release branch; publish only after tarball upload to avoid immutable-tag errors on re-run.
- remove the prefix "satellite_*" from the tags
- run_filetree_create playbook - drop ``module_defaults`` for ``redhat.satellite.organization_info`` so the play can be parsed without the Satellite collection installed; role tasks already pass connection parameters explicitly.
- run_filetree_create playbook - resolve ``filetree_create`` by path next to ``playbooks/`` so the export works from a git checkout without installing the collection into ``collections_paths``.
- tests/unit - add Ansible module boilerplate to unit test modules so ansible-test sanity passes on published artifacts.
- tests/unit - remove module shebang from unit test file (ansible-test shebang sanity on CRC import).
