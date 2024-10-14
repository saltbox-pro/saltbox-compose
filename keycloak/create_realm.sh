#! /bin/sh

set -e

alias kcadm=./bin/kcadm.sh

admin_password=$(cat /run/secrets/keycloak_admin_password)
fastms_core_password=$(cat /run/secrets/keycloak_client_fastms_core_password)

kcadm config credentials \
  --server "${KEYCLOAK_URL}" \
  --realm master \
  --user admin \
  --password "$admin_password"

if kcadm get realms/"${KEYCLOAK_REALM}" --fields id > /dev/null; then
  echo REALM Already exists
  exit 0
fi

kcadm create realms -s "realm=${KEYCLOAK_REALM}" -s enabled=true
kcadm create clients \
  -r "${KEYCLOAK_REALM}" \
  -f ./client.json \
  -s "clientId=${KEYCLOAK_CLIENT}" \
  -s "secret=${fastms_core_password}"

echo "Realm ${KEYCLOAK_REALM} has been created"
