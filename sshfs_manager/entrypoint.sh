#! /bin/sh

set -e

CONFIG_TMPL_PATH='/docker/config.yaml.tmpl'
CONFIG_OUT_PATH='/home/filebrowser/data/config.yaml'

export OIDC_CLIENT_SECRET="$(cat /run/secrets/keycloak_client_saltbox_core_password)"

envsubst < "${CONFIG_TMPL_PATH}" > "${CONFIG_OUT_PATH}"
exec filebrowser -c "${CONFIG_OUT_PATH}"
