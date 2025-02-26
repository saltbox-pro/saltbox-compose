#! /bin/sh

set -e
trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

admin_password=$(cat /run/secrets/keycloak_admin_password)

kcadm.sh config credentials \
  --server "${KEYCLOAK_URL}" \
  --realm master \
  --user admin \
  --password "$admin_password"
