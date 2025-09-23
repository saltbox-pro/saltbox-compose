#! /bin/sh
# shellcheck disable=SC2016

set -e
trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

proxy_cert_state_file='/mnt/proxy_certs/.proxy_alt_names'

warn() {
  2>&1 echo "$@"
}

proxy_state() {
cat << EOF
$SSL_ALT_NAMES_IP
$SSL_ALT_NAMES_DNS
EOF
}

CA_KEY_PASSWORD="$(cat /run/secrets/redis_salt_ca_private_key_password)"
REDIS_KEY_PASSWORD="$(cat /run/secrets/redis_salt_private_key_password)"
export CA_KEY_PASSWORD REDIS_KEY_PASSWORD

./render-template.py --output-dir /root/ hier.yaml.jinja2

# Recreate cert for Nginx if SSL_ALT_NAMES_* altered in system config
touch "$proxy_cert_state_file"
proxy_cert_last_state="$(cat "$proxy_cert_state_file")"
if [ "$(proxy_state)" != "$proxy_cert_last_state" ]; then
  warn Proxy certificate Alternative Names has been changed, certificate will be reissued
  rm "$PROXY_CERT"
fi

make-certs /root/hier.yaml

proxy_state > "$proxy_cert_state_file"
