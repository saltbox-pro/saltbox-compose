#! /bin/sh

set -e

CONFIG_TMPL_PATH="/docker/config.yaml.tmpl"
CONFIG_OUT_PATH="/home/filebrowser/data/config.yaml"
KEYCLOAK_SALTBOX_CORE_SECRET_FILE="/run/secrets/keycloak_client_saltbox_core_password"

OIDC_CLIENT_SECRET="$(cat ${KEYCLOAK_SALTBOX_CORE_SECRET_FILE})"
export OIDC_CLIENT_SECRET

log_info() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO ] ${*}"
}

## TODO (a.karmanov): Delete the workaround when auth on proxy will be implemented
## FIXME Not works for IP addr, not works for localhost, not works for host:443
kc_ip=$(nslookup proxy 127.0.0.11 | awk '/^Address: /{print $2; exit}')
sb_host=${ISSUER_URL#*://}
sb_host=${sb_host%%[:/]*}
rslv="${kc_ip} ${sb_host}"
log_info "Setting hosts line: ${rslv}"
log_info 'Attention! Be sure to use to use WEB_SERVER_OUTER_SOCKET in form of HOSTNAME where HOSTNAME is not a "localhost"'
echo "${kc_ip} ${sb_host}" >> /etc/hosts

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
