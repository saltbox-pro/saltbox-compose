#! /bin/sh
set -e

conf_file='/etc/redis/redis_custom.conf'
password="$(cat /run/secrets/redis_salt_password)"

mkdir --parents "$(dirname "$conf_file")"
cat <<EOF > "$conf_file"
# Allow all for all users by password
user ${USERNAME} +@all on >${password}
EOF

redis-server "$conf_file" "$@"
