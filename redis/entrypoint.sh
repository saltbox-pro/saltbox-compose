#! /bin/sh

set -e
trap '[ $? -eq 0 ] && exit 0 || echo "ERROR on $0 line ${LINENO}"' EXIT

warn() {
  1>&2 echo "$@"
}

err() {
  warn "$@"
  exit 1
}

conf_subdir='/etc/redis/redis.conf.d'
acl_conf_file="${conf_subdir}/10-acl.conf"
tls_conf_file="${conf_subdir}/10-tls.conf"
password="$(cat "$REDIS_PASSWORD_SECRET_FILE")"
plain_port="${REDIS_PLAIN_PORT:-0}"  # By defaul no-TLS port is disabled

if [ -z "$REDIS_USERNAME" ]; then err 'Empty or missing REDIS_USERNAME'; fi

if [ "$plain_port" != '0' ]; then
  warn ''
  warn "ATTENTION! Unencrypted Redis port ${plain_port} is enabled";
  warn ''
fi

mkdir --parents "$conf_subdir"

cat <<EOF > "$acl_conf_file"
# Allow all exclusively for user ${REDIS_USERNAME} by password

user default reset nopass on -@all ~* &*
user ${REDIS_USERNAME} reset nopass on +@all ~* &* >${password}
EOF

write_tls_conf() {
  key_password="$(cat "$REDIS_PRIVATE_KEY_PASSWORD_SECRET")"
  cat <<EOF > "$tls_conf_file"
## Encryption settings

port ${plain_port}
tls-port 6379
tls-cert-file /etc/redis/certs/redis.crt
tls-key-file /etc/redis/certs/redis.key
tls-ca-cert-file /etc/redis/certs/ca.crt
tls-key-file-pass "${key_password}"
tls-auth-clients "${TLS_AUTH_CLIENT}"
EOF
}

case "$REDIS_ENCRYPTION" in
  'on') write_tls_conf ;;
  'off') warn 'ENCRYPTION DISABLED' ;;
  *) err "Unexpected REDIS_ENCRYPTION value \"$REDIS_ENCRYPTION\"" ;;
esac


redis-server /etc/redis/redis.conf "$@"
