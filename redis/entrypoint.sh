#! /bin/sh
set -e

conf_subdir='/etc/redis/redis.conf.d'
acl_conf_file="${conf_subdir}/10-acl.conf"
tls_conf_file="${conf_subdir}/10-tls.conf"
password="$(cat /run/secrets/redis_salt_password)"
key_password="$(cat /run/secrets/redis_salt_private_key_password)"

mkdir --parents "$conf_subdir"

cat <<EOF > "$acl_conf_file"
# Allow all exclusively for user ${REDIS_USERNAME} by password

user default reset nopass on -@all ~* &*
user ${REDIS_USERNAME} reset nopass on +@all ~* &* >${password}
EOF

cat <<EOF > "$tls_conf_file"
## Encryption settings

port 0
tls-port 6379
tls-cert-file /etc/redis/certs/redis.crt
tls-key-file /etc/redis/certs/redis.key
tls-ca-cert-file /etc/redis/certs/ca.crt
tls-key-file-pass "${key_password}"
tls-auth-clients "${TLS_AUTH_CLIENT}"
EOF


redis-server /etc/redis/redis.conf "$@"
