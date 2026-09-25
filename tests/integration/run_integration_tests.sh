#!/usr/bin/env bash
# Live-Satellite integration tests: each case runs the full filetree_create or
# filetree_reconcile role with CLI --tags (ansible_run_tags cannot be set from playbooks).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTION_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${COLLECTION_ROOT}"

SETUP_TAGS="always"
EXTRA_ARGS=("$@")

run_playbook() {
  local playbook="$1"
  local tags="$2"
  echo "==> ansible-playbook ${playbook} --tags ${tags}" "${EXTRA_ARGS[@]}"
  ansible-playbook "${playbook}" --tags "${tags}" "${EXTRA_ARGS[@]}"
}

EXPORT_FILTERS_PLAYBOOK="tests/integration/filetree_create_export_filters.yaml"
SKIP_LOCKED_PLAYBOOK="tests/integration/filetree_create_skip_locked_export.yaml"

# test_tag:role_block_tag
FILTER_TESTS=(
  "filter_organizations:organizations"
  "filter_organizations_repositories:repositories"
  "filter_organizations_exclude:organizations"
  "filter_name_include:domains"
  "filter_name_exclude:domains"
  "filter_name_use_regex:domains"
  "filter_locations:hostgroups"
  "filter_locations_exclude:hostgroups"
  "filter_domains:subnets"
  "filter_domains_exclude:subnets"
  "filter_hostgroup_parents:hostgroups"
  "filter_products:repositories"
  "filter_products_exclude:repositories"
  "filter_lifecycle_environments:lifecycle_environments"
  "filter_lifecycle_environments_exclude:lifecycle_environments"
  "filter_content_views:content_views"
  "filter_content_views_exclude:content_views"
  "filter_labels:repositories"
  "filter_labels_exclude:repositories"
  "filter_repository_sets_only_enabled:repository_sets"
  "filter_auth_sources:users"
  "filter_auth_sources_exclude:users"
  "filter_users_admin:users"
  "filter_settings_include:settings"
  "filter_settings_exclude:settings"
  "filter_roles_include_builtin:roles"
  "filter_roles_include_locked:roles"
  "filter_search:domains"
  "filter_search_by_type:domains"
)

# test_tag:comma-separated role/compare tags
RECONCILE_TESTS=(
  "reconcile_cac_out_of_scope:organizations,yaml_format,compare"
  "reconcile_live_out_of_scope:compare,organizations"
  "reconcile_unscoped_legacy:compare,organizations"
  "reconcile_domains_scope:domains,yaml_format,compare"
)

run_export_filter_tests() {
  local entry test_tag role_tag
  for entry in "${FILTER_TESTS[@]}"; do
    IFS=':' read -r test_tag role_tag <<< "${entry}"
    run_playbook "${EXPORT_FILTERS_PLAYBOOK}" \
      "${SETUP_TAGS},${test_tag},${role_tag},yaml_format"
  done
}

run_reconcile_scope_tests() {
  local entry test_tag role_tags
  for entry in "${RECONCILE_TESTS[@]}"; do
    IFS=':' read -r test_tag role_tags <<< "${entry}"
    run_playbook "${EXPORT_FILTERS_PLAYBOOK}" \
      "${SETUP_TAGS},reconcile,${test_tag},${role_tags}"
  done
}

run_skip_locked_export_test() {
  run_playbook "${SKIP_LOCKED_PLAYBOOK}" \
    "${SETUP_TAGS},skip_locked,provisioning_templates,partition_tables,job_templates,yaml_format"
}

usage() {
  cat <<'EOF'
Usage: tests/integration/run_integration_tests.sh [suite] [ansible-playbook extra args...]

Suites (default: all):
  filters    Export scope filter tests (filetree_create)
  reconcile  Reconcile scope symmetry tests (filetree_reconcile)
  skip_locked  Locked factory object export test
  all        Run every suite above

Each suite invokes ansible-playbook with --tags so the full role entrypoint behaves
like production (for example organizations,yaml_format or compare,organizations).

Examples:
  tests/integration/run_integration_tests.sh filters
  tests/integration/run_integration_tests.sh all -e satellite@vars/satellite.yaml
  ansible-playbook tests/integration/filetree_create_export_filters.yaml \
    --tags always,filter_organizations,organizations,yaml_format
EOF
}

main() {
  local suite="${1:-all}"
  if [[ "${suite}" != "filters" && "${suite}" != "reconcile" && "${suite}" != "skip_locked" && "${suite}" != "all" ]]; then
    if [[ "${suite}" == "-h" || "${suite}" == "--help" ]]; then
      usage
      exit 0
    fi
    EXTRA_ARGS=("$@")
    suite="all"
  else
    shift || true
    EXTRA_ARGS=("$@")
  fi

  case "${suite}" in
    filters)
      run_export_filter_tests
      ;;
    reconcile)
      run_reconcile_scope_tests
      ;;
    skip_locked)
      run_skip_locked_export_test
      ;;
    all)
      run_export_filter_tests
      run_reconcile_scope_tests
      run_skip_locked_export_test
      ;;
  esac
}

main "$@"
