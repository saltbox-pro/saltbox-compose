#! /bin/sh

set -e

CONFIG_TMPL_PATH="/docker/config.yaml.tmpl"
CONFIG_OUT_PATH="/home/filebrowser/data/config.yaml"
PING_IP_PATTERN="[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"
KEYCLOAK_SALTBOX_CORE_SECRET_FILE="/run/secrets/keycloak_client_saltbox_core_password"

OIDC_CLIENT_SECRET="$(cat ${KEYCLOAK_SALTBOX_CORE_SECRET_FILE})"
export OIDC_CLIENT_SECRET

log_info() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO ] ${*}"
}

# TODO (a.karmanov): Delete the workaround when auth on proxy will be implemented
resolve_proxy() {
  proxy_ip=$(ping -c1 proxy | head -n1 | grep -oE "${PING_IP_PATTERN}")
  if [ -n "${proxy_ip}" ] && [ -n "${WEB_SERVER_OUTER_SOCKET}" ]; then
    echo "${proxy_ip}" "${WEB_SERVER_OUTER_SOCKET}" >> /etc/hosts
  fi
}

# TODO (a.karmanov): Delete the workaround when auth on proxy will be implemented
if [ -n "${BASIC_AUTH_USERNAME}" ] && [ -n "${BASIC_AUTH_PASSWORD}" ]; then
  log_info "Basic auth is enabled. Setting up split-horizon DNS for ${WEB_SERVER_OUTER_SOCKET} to route OIDC requests through proxy"
  resolve_proxy
fi

if [ -n "${MIGRATION_SOURCE_ENABLED}" ]; then
  log_info "Module migration is enabled. Configuring the '/srv/migrator' source"
  MIGRATOR_SOURCE_BLOCK="$(cat "${MIGRATOR_SOURCE_BLOCK_FILE}")"
else
  log_info "Module migration is disabled. Skipping '/srv/migrator' source configuration"
  MIGRATOR_SOURCE_BLOCK=""
fi
export MIGRATOR_SOURCE_BLOCK

envsubst < "${CONFIG_TMPL_PATH}" > "${CONFIG_OUT_PATH}"
exec filebrowser -c "${CONFIG_OUT_PATH}"
