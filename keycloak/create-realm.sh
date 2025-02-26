#! /bin/sh
# shellcheck disable=SC3043

# The script creates and populates the realm for Salt.Box.

# TODO Implement "migrations"
# Script should check if every object exists to be extandable between versions.

set -e
trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT


salt_box_create_user() {
  local _username="$1"
  local _email="$2"
  local _firstName="$3"
  local _lastName="$4"

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
    --new-password "$user_password"

  echo "User '${_username}' in realm '${KEYCLOAK_REALM}' has been created"
}


salt_box_core_password=$(cat /run/secrets/keycloak_client_salt_box_core_password)
user_password=$(cat /run/secrets/keycloak_user_password)
collections_admin_role="collections_admin"

is_keycloak_admin_debug=0

if [ -z "$KEYCLOAK_REALM" ]; then
  >&2 echo 'Missing KEYCLOAK_REALM value'
  exit 1
fi

kcadm-init.sh

if kcadm.sh get realms/"${KEYCLOAK_REALM}" --fields id > /dev/null; then
  echo REALM Already exists

  if [ $is_keycloak_admin_debug -eq 1 ]; then
    echo Debuging! Deliting REALM...
    kcadm.sh delete realms/"${KEYCLOAK_REALM}"
  else
    exit 0
  fi
fi


kcadm.sh create realms -s "realm=${KEYCLOAK_REALM}" -s enabled=true
KEYCLOAK_CLIENT_ID=$(kcadm.sh create clients \
  --target-realm "${KEYCLOAK_REALM}" \
  --file ./client.json \
  --set "clientId=${KEYCLOAK_CLIENT}" \
  --set "directAccessGrantsEnabled=${KEYCLOAK_CLIENT_DIRECT_ACCESS:-false}" \
  --set "secret=${salt_box_core_password}" -i)
echo "Client with id '${KEYCLOAK_CLIENT_ID}' created"

kcadm.sh create "clients/${KEYCLOAK_CLIENT_ID}/roles" \
  -r "${KEYCLOAK_REALM}" \
  -s name="${collections_admin_role}" \
  -s "description=Collections admin role"
echo "Admin role created"

echo "Realm ${KEYCLOAK_REALM} has been created"

if [ -z "$KEYCLOAK_USER_NAME" ]; then
  echo No user to create
else
  salt_box_create_user \
    "${KEYCLOAK_USER_NAME}" \
    "${KEYCLOAK_USER_EMAIL}" \
    "${KEYCLOAK_USER_FIRSTNAME}" \
    "${KEYCLOAK_USER_LASTNAME}"
fi

if [ -z "$KEYCLOAK_ADMIN_NAME" ]; then
  echo No admin to create
else
  salt_box_create_user \
    "${KEYCLOAK_ADMIN_NAME}" \
    "${KEYCLOAK_ADMIN_EMAIL}" \
    "${KEYCLOAK_ADMIN_FIRSTNAME}" \
    "${KEYCLOAK_ADMIN_LASTNAME}"

  kcadm.sh add-roles -r "${KEYCLOAK_REALM}" \
    --uusername "${KEYCLOAK_ADMIN_NAME}" \
    --cclientid "${KEYCLOAK_CLIENT}" \
    --rolename "${collections_admin_role}"
fi
