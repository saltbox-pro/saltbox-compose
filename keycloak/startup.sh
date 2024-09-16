#!/bin/sh

export KEYCLOAK_ADMIN_PASSWORD=$(cat /run/secrets/keycloak_admin_password)
/opt/keycloak/bin/kc.sh "$@"
