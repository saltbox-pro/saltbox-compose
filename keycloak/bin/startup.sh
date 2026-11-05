#!/bin/sh

set -e
trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

KC_BOOTSTRAP_ADMIN_PASSWORD="$(cat /run/secrets/keycloak_admin_password)"
KC_DB_PASSWORD="$(cat /run/secrets/keycloak_database_password)"
export KC_BOOTSTRAP_ADMIN_PASSWORD KC_DB_PASSWORD

kc.sh "$@"
