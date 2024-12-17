#! /bin/sh

set -e

admin_password=$(cat /run/secrets/keycloak_admin_password)

kcadm.sh config credentials \
  --server "${KEYCLOAK_URL}" \
  --realm master \
  --user admin \
  --password "$admin_password"
