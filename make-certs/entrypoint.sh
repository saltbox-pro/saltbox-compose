#! /bin/sh
# shellcheck disable=SC2016

set -e
trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

proxy_last_alt_name_file='/mnt/proxy_certs/.proxy_alt_name'

warn() {
  2>&1 echo "$@"
}

CA_KEY_PASSWORD="$(cat /run/secrets/redis_salt_ca_private_key_password)"
REDIS_KEY_PASSWORD="$(cat /run/secrets/redis_salt_private_key_password)"
PROXY_CERT='/mnt/proxy_certs/proxy.crt'
export CA_KEY_PASSWORD REDIS_KEY_PASSWORD

envsubst '$CA_KEY_PASSWORD $PROXY_ALT_NAME $PROXY_CERT $REDIS_KEY_PASSWORD' \
  < /root/hier.yaml.tpl \
  > /root/hier.yaml

# Recreate cert for Nginx if WEB_SERVER_ALT_NAME altered in system config
touch "$proxy_last_alt_name_file"
proxy_last_alt_name="$(cat "$proxy_last_alt_name_file")"
cat "$proxy_last_alt_name_file"
if [ "$PROXY_ALT_NAME" != "$proxy_last_alt_name" ]; then
  warn "PROXY_ALT_NAME has been changed: ${proxy_last_alt_name} -> ${PROXY_ALT_NAME}"
  warn will reissue the proxy certificate
  rm "$PROXY_CERT"
fi

make-certs /root/hier.yaml

echo "$PROXY_ALT_NAME" > "$proxy_last_alt_name_file"
cat "$proxy_last_alt_name_file"
