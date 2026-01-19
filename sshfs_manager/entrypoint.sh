#! /bin/sh

set -e

CONFIG_TMPL_PATH='/docker/config.yaml.tmpl'
CONFIG_OUT_PATH='/home/filebrowser/data/config.yaml'

export OIDC_CLIENT_SECRET="$(cat /run/secrets/keycloak_client_saltbox_core_password)"

# Check if proxy host is resolvable
if ! getent hosts "${KEYCLOAK_INTERNAL_PROXY}" >/dev/null 2>&1; then
    echo "Warning: ${KEYCLOAK_INTERNAL_PROXY} not resolvable, waiting..."
    sleep 2
    if ! getent hosts "${KEYCLOAK_INTERNAL_PROXY}" >/dev/null 2>&1; then
        echo "ERROR: Cannot resolve ${KEYCLOAK_INTERNAL_PROXY}"
        exit 1
    fi
fi

# Add localhost alias to proxy container IP for OIDC issuer validation
PROXY_IP=$(getent hosts "${KEYCLOAK_INTERNAL_PROXY}" | awk '{ print $1 }')
if [ -n "$PROXY_IP" ]; then
    echo "Adding localhost alias: ${PROXY_IP} ${WEB_SERVER_OUTER_SOCKET}"
    echo "${PROXY_IP} ${WEB_SERVER_OUTER_SOCKET}" >> /etc/hosts
else
    echo "ERROR: Cannot get IP for ${KEYCLOAK_INTERNAL_PROXY}"
    exit 1
fi

envsubst < "${CONFIG_TMPL_PATH}" > "${CONFIG_OUT_PATH}"
exec filebrowser -c "${CONFIG_OUT_PATH}"
