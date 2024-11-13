#! /bin/sh
set -e

conf_file='/etc/redis/redis.conf.d/10-acl.conf'
password="$(cat /run/secrets/redis_salt_password)"

mkdir --parents "$(dirname "$conf_file")"
cat <<EOF > "$conf_file"
# Allow all exclusively for user ${REDIS_USERNAME} by password

user default off
user ${REDIS_USERNAME} reset nopass on +@all ~* >${password}
EOF

redis-server /etc/redis/redis.conf "$@"
