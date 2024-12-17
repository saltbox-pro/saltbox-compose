#! /bin/sh

set -e

fastms_core_password=$(cat /run/secrets/keycloak_client_fastms_core_password)
user_password=$(cat /run/secrets/keycloak_user_password)

if [ -z "$KEYCLOAK_REALM" ]; then
  >&2 echo 'Missing KEYCLOAK_REALM value'
  exit 1
fi

kcadm-init.sh

if kcadm.sh get realms/"${KEYCLOAK_REALM}" --fields id > /dev/null; then
  echo REALM Already exists
  exit 0
fi

kcadm.sh create realms -s "realm=${KEYCLOAK_REALM}" -s enabled=true
kcadm.sh create clients \
  --target-realm "${KEYCLOAK_REALM}" \
  --file ./client.json \
  --set "clientId=${KEYCLOAK_CLIENT}" \
  --set "directAccessGrantsEnabled=${KEYCLOAK_CLIENT_DIRECT_ACCESS:-false}" \
  --set "secret=${fastms_core_password}"

echo "Realm ${KEYCLOAK_REALM} has been created"

if [ -z "$KEYCLOAK_USER_NAME" ]; then
  echo No user to create
  exit 0
fi

user_id=$(
  kcadm.sh create users \
    --target-realm "$KEYCLOAK_REALM" \
    --set "username=${KEYCLOAK_USER_NAME}" \
    --set "firstName=${KEYCLOAK_USER_FIRSTNAME}" \
    --set "lastName=${KEYCLOAK_USER_LASTNAME}" \
    --set "email=${KEYCLOAK_USER_EMAIL}" \
    --set enabled=true \
    --id
)
kcadm.sh set-password \
  --target-realm "$KEYCLOAK_REALM" \
  --userid "$user_id" \
  --new-password "$user_password"

echo "User ${KEYCLOAK_USER_NAME} for realm ${KEYCLOAK_REALM} has been created"
