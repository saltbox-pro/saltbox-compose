#! /bin/sh
set -e

## Set client directAccessGrantsEnabled property on start based on
## KEYCLOAK_CLIENT_DIRECT_ACCESS variable.

KEYCLOAK_CLIENT_DIRECT_ACCESS="${KEYCLOAK_CLIENT_DIRECT_ACCESS:-false}"

echo "Setting ${KEYCLOAK_CLIENT}.directAccessGrantsEnabled='${KEYCLOAK_CLIENT_DIRECT_ACCESS}'"

KEYCLOAK_CLIENT_ID=$(
  kcadm.sh get -r salt.box clients --fields id,clientId \
    | jq -c ".[] | select(.clientId == \"${KEYCLOAK_CLIENT}\")" \
    | jq -r .id)

kcadm.sh update -r salt.box "clients/${KEYCLOAK_CLIENT_ID}" \
  -s "directAccessGrantsEnabled='${KEYCLOAK_CLIENT_DIRECT_ACCESS}'"
