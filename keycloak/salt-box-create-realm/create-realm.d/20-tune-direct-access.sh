#! /bin/sh
set -e

## Set client directAccessGrantsEnabled property on start based on
## KEYCLOAK_CLIENT_DIRECT_ACCESS variable.

KEYCLOAK_CLIENT_DIRECT_ACCESS="${KEYCLOAK_CLIENT_DIRECT_ACCESS:-false}"

echo "Setting ${KEYCLOAK_CLIENT}.directAccessGrantsEnabled='${KEYCLOAK_CLIENT_DIRECT_ACCESS}'"

KEYCLOAK_CLIENT_ID=$(
  kcadm.sh get clients \
    -r "${KEYCLOAK_REALM}" \
    -q clientId="${KEYCLOAK_CLIENT}" \
    --format csv \
    --fields id \
    --noquotes)

kcadm.sh update -r salt.box "clients/${KEYCLOAK_CLIENT_ID}" \
  -s "directAccessGrantsEnabled='${KEYCLOAK_CLIENT_DIRECT_ACCESS}'"
