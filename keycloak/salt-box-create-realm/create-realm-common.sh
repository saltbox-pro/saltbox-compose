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

_salt_box_core_password=$(cat /run/secrets/keycloak_client_salt_box_core_password)
_user_password=$(cat /run/secrets/keycloak_user_password)
# TODO _admin_password=$(cat /run/secrets/keycloak_???admin_password)
_collections_admin_role="collections_admin"
