#!/bin/sh

set -e

KEYCLOAK_ADMIN_PASSWORD="$(cat /run/secrets/keycloak_admin_password)"
KC_DB_PASSWORD="$(cat /run/secrets/keycloak_database_password)"
export KEYCLOAK_ADMIN_PASSWORD KC_DB_PASSWORD

/opt/keycloak/bin/kc.sh "$@"
