#! /bin/sh

## The sub-script creates very basic realm and may be used as example to extend
## the realm.
##
## DO NOT EXTEND THE SCRIPT BETWEEN SALT.BOX VERSIONS!
## Create further sub-scripts to extend the realm.

# shellcheck source=../create-realm-common.sh
. '/usr/local/lib/saltbox/create-realm-common.sh'
: "${SSHFS_MANAGER_ENABLED:=false}"

if ! kcadm.sh get realms/"${KEYCLOAK_REALM}" --fields id >/dev/null 2>&1; then
  echo -e "\nRealm '${KEYCLOAK_REALM}' does not exist. Creating."
  kcadm.sh create realms -s "realm=${KEYCLOAK_REALM}" -s enabled=false
else
echo -e "\nSetting realm '${KEYCLOAK_REALM}' disabled."
  kcadm.sh update "realms/${KEYCLOAK_REALM}" -s enabled=false
fi
echo

saltbox_client_uuid=$(kc_create_client \
  "${KEYCLOAK_CLIENT}" \
  "${_saltbox_core_password}" \
  "${_collections_admin_role}" \
  "./client.json" \
  "Collections admin role")

kc_create_role \
  "${saltbox_client_uuid}" \
  "${_admin_role}" \
  "Salt.Box admin role"

kc_create_role \
  "${saltbox_client_uuid}" \
  "${_tasks_admin_role}" \
  "Tasks admin role"

kc_create_role \
  "${saltbox_client_uuid}" \
  "${_jobs_admin_role}" \
  "Jobs admin role"

kc_create_role \
  "${saltbox_client_uuid}" \
  "${_test_common_role}" \
  "Test common role"

kc_create_role \
  "${saltbox_client_uuid}" \
  "${_masters_admin_role}" \
  "Masters admin role"

kc_create_role \
  "${saltbox_client_uuid}" \
  "${_scheduler_admin_role}" \
  "Scheduler admin role"

if [ -z "$KEYCLOAK_USER_NAME" ]; then
  echo No user to create
else
  kc_create_user \
    "${KEYCLOAK_USER_NAME}" \
    "${KEYCLOAK_USER_EMAIL}" \
    "${KEYCLOAK_USER_FIRSTNAME}" \
    "${KEYCLOAK_USER_LASTNAME}" \
    "${_sb_user_password}"
fi

if [ -z "$KEYCLOAK_ADMIN_NAME" ]; then
  echo No admin to create
else
  kc_create_user \
    "${KEYCLOAK_ADMIN_NAME}" \
    "${KEYCLOAK_ADMIN_EMAIL}" \
    "${KEYCLOAK_ADMIN_FIRSTNAME}" \
    "${KEYCLOAK_ADMIN_LASTNAME}" \
    "${_sb_admin_password}"

  kc_assign_client_role_to_user \
    "${KEYCLOAK_REALM}" \
    "${KEYCLOAK_ADMIN_NAME}" \
    "${KEYCLOAK_CLIENT}" \
    "${_admin_role}"
  
  kc_assign_client_role_to_user \
    "${KEYCLOAK_REALM}" \
    "${KEYCLOAK_ADMIN_NAME}" \
    "${KEYCLOAK_CLIENT}" \
    "${_collections_admin_role}"
  
  kc_assign_client_role_to_user \
    "${KEYCLOAK_REALM}" \
    "${KEYCLOAK_ADMIN_NAME}" \
    "${KEYCLOAK_CLIENT}" \
    "${_tasks_admin_role}"
  
  kc_assign_client_role_to_user \
    "${KEYCLOAK_REALM}" \
    "${KEYCLOAK_ADMIN_NAME}" \
    "${KEYCLOAK_CLIENT}" \
    "${_jobs_admin_role}"
  
  kc_assign_client_role_to_user \
    "${KEYCLOAK_REALM}" \
    "${KEYCLOAK_ADMIN_NAME}" \
    "${KEYCLOAK_CLIENT}" \
    "${_test_common_role}"
  
  kc_assign_client_role_to_user \
    "${KEYCLOAK_REALM}" \
    "${KEYCLOAK_ADMIN_NAME}" \
    "${KEYCLOAK_CLIENT}" \
    "${_masters_admin_role}"
  
  kc_assign_client_role_to_user \
    "${KEYCLOAK_REALM}" \
    "${KEYCLOAK_ADMIN_NAME}" \
    "${KEYCLOAK_CLIENT}" \
    "${_scheduler_admin_role}"

  if [ "${SSHFS_MANAGER_ENABLED}" = "true" ]; then
    kc_assign_client_to_scope \
      "${saltbox_client_uuid}" \
      "groups" \
      "./membership_mapper.json"

    kc_assign_user_to_group \
      "${KEYCLOAK_ADMIN_NAME}" \
      "filebrowser-admins"

    kc_assign_user_to_group \
      "${KEYCLOAK_USER_NAME}" \
      "filebrowser-users"
  fi

  if [ -n "${_grafana_password}" ]; then

    grafana_client_uuid=$(kc_create_client \
      "${KEYCLOAK_CLIENT_GRAFANA}" \
      "${_grafana_password}" \
      "${_grafana_admin_role}" \
      "./grafana_client.json" \
      "Grafana admin role")

    kc_assign_client_role_to_user \
      "${KEYCLOAK_REALM}" \
      "${KEYCLOAK_ADMIN_NAME}" \
      "${KEYCLOAK_CLIENT_GRAFANA}" \
      "${_grafana_admin_role}"

     user_client_expected_roles["${KEYCLOAK_ADMIN_NAME}:${KEYCLOAK_CLIENT_GRAFANA}"]="${_grafana_admin_role}"
  fi
fi

if "${KEYCLOAK_STRICT_ROLE_CHECK}"; then
  if kc_all_expected_roles_assigned; then
    echo -e "Realm '${KEYCLOAK_REALM}' exists and all expected roles are assigned\n"
    exit 0
  else
    echo -e "Realm '${KEYCLOAK_REALM}' exists but some expected roles are missing\n"
  fi
fi
