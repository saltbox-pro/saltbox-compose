#!/bin/sh

export KEYCLOAK_ADMIN_PASSWORD=$(cat /run/secrets/keycloak_admin_password)
export KC_DB_PASSWORD=$(cat /run/secrets/keycloak_database_password)
export CLIENT_FASTMS_CORE_PASSWORD=$(cat /run/secrets/keycloak_client_fastms_core_password)
/opt/keycloak/bin/kc.sh "$@"
