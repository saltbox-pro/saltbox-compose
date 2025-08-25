#! /bin/sh
set -e

## The sub-script creates very basic realm and may be used as example to extend
## the realm.
##
## DO NOT EXTEND THE SCRIPT BETWEEN SALT.BOX VERSIONS!
## Create further sub-scripts to extend the realm.

# shellcheck source=../create-realm-common.sh
. '/usr/local/lib/salt-box/create-realm-common.sh'

if kcadm.sh get realms/"${KEYCLOAK_REALM}" --fields id > /dev/null; then
  echo "Realm '${KEYCLOAK_REALM}' already exists"
  exit 0
fi

kcadm.sh create realms -s "realm=${KEYCLOAK_REALM}" -s enabled=true
KEYCLOAK_CLIENT_ID=$(kcadm.sh create clients \
  --target-realm "${KEYCLOAK_REALM}" \
  --file ./client.json \
  --set "clientId=${KEYCLOAK_CLIENT}" \
  --set "secret=${_saltbox_core_password}" -i)
echo "Client with id '${KEYCLOAK_CLIENT_ID}' created"

kcadm.sh create "clients/${KEYCLOAK_CLIENT_ID}/roles" \
  -r "${KEYCLOAK_REALM}" \
  -s name="${_admin_role}" \
  -s "description=Saltbox admin role"
echo "Saltbox admin role created"

kcadm.sh create "clients/${KEYCLOAK_CLIENT_ID}/roles" \
  -r "${KEYCLOAK_REALM}" \
  -s name="${_collections_admin_role}" \
  -s "description=Collections admin role"
echo "Collections admin role created"

kcadm.sh create "clients/${KEYCLOAK_CLIENT_ID}/roles" \
  -r "${KEYCLOAK_REALM}" \
  -s name="${_tasks_admin_role}" \
  -s "description=Tasks admin role"
echo "Tasks admin role created"

kcadm.sh create "clients/${KEYCLOAK_CLIENT_ID}/roles" \
  -r "${KEYCLOAK_REALM}" \
  -s name="${_jobs_admin_role}" \
  -s "description=Jobs admin role"
echo "Jobs admin role created"

kcadm.sh create "clients/${KEYCLOAK_CLIENT_ID}/roles" \
  -r "${KEYCLOAK_REALM}" \
  -s name="${_masters_admin_role}" \
  -s "description=Masters admin role"
echo "Masters admin role created"

kcadm.sh create "clients/${KEYCLOAK_CLIENT_ID}/roles" \
  -r "${KEYCLOAK_REALM}" \
  -s name="${_test_common_role}" \
  -s "description=Test common role"
echo "Test common role created"

echo "Realm ${KEYCLOAK_REALM} has been created"

if [ -z "$KEYCLOAK_USER_NAME" ]; then
  echo No user to create
else
  kc_create_user \
    "${KEYCLOAK_USER_NAME}" \
    "${KEYCLOAK_USER_EMAIL}" \
    "${KEYCLOAK_USER_FIRSTNAME}" \
    "${KEYCLOAK_USER_LASTNAME}" \
    "${_sb_user_password}"

  kcadm.sh add-roles -r "${KEYCLOAK_REALM}" \
    --uusername "${KEYCLOAK_USER_NAME}" \
    --cclientid "${KEYCLOAK_CLIENT}" \
    --rolename "${_test_common_role}"
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

  kcadm.sh add-roles -r "${KEYCLOAK_REALM}" \
    --uusername "${KEYCLOAK_ADMIN_NAME}" \
    --cclientid "${KEYCLOAK_CLIENT}" \
    --rolename "${_admin_role}"
fi
