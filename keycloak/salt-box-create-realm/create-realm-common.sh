#! /bin/sh
# shellcheck disable=SC3043
set -e

trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

kc_create_user() {
  local _username="$1"
  local _email="$2"
  local _firstName="$3"
  local _lastName="$4"
  local _password="$5"

  local user_id
  user_id="$(kcadm.sh create users \
    --target-realm "$KEYCLOAK_REALM" \
    --set "username=${_username}" \
    --set "firstName=${_firstName}" \
    --set "lastName=${_lastName}" \
    --set "email=${_email}" \
    --set enabled=true \
    --id)"
  kcadm.sh set-password \
    --target-realm "$KEYCLOAK_REALM" \
    --userid "$user_id" \
    --new-password "$_password"

  echo "User '${_username}' in realm '${KEYCLOAK_REALM}' has been created"
}

if [ -z "$KEYCLOAK_REALM" ]; then
  >&2 echo 'Missing KEYCLOAK_REALM value'
  exit 1
fi

_saltbox_core_password=$(cat /run/secrets/keycloak_client_saltbox_core_password)
_sb_user_password=$(cat /run/secrets/saltbox_user_password)
_sb_admin_password=$(cat /run/secrets/saltbox_admin_password)
_admin_role="saltbox_admin"
_collections_admin_role="collections_admin"
_tasks_admin_role="tasks_admin"
_jobs_admin_role="jobs_admin"
_masters_admin_role="masters_admin"
_scheduler_admin_role="scheduler_admin"
_test_common_role="test_common"
