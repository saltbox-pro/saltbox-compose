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

pam_user='mongod'
admin_password="$(cat "$MONGO_ADMIN_PASSWORD_FILE")"

key_file='/etc/mongo/key'
install -m 400 -o "${pam_user}" -g "${pam_user}" "$MONGOD_KEY_FILE" "$key_file"

chown --recursive "${pam_user}:${pam_user}" /var/lib/mongo/

mongod_base() {
  gosu "${pam_user}" mongod \
    --config "$MONGOD_CONF_FILE" \
    --replSet "$MONGOD_REPLICA_SET" \
    --keyFile "$key_file"
}

init_pidfile='/tmp/docker-entrypoint-mongod.pid'
rm -f "$init_pidfile"

mongod_base --pidfilepath="$init_pidfile" --fork --syslog run

try="$WAIT_FOR_INIT"
while true; do
  if mongosh 'admin' --eval 'quit(0)' > /dev/null 2>&1; then
    break
  fi
  try=$(( try - 1 ))
  if [ "$try" -le 0 ]; then
    err "MongoDB did not response in ${WAIT_FOR_INIT} seconds for init"
  fi
  sleep 1
done

mongosh <<EOF
use admin

try {
  rs.status()
} catch (err) {
  rs.initiate({_id:'${MONGOD_REPLICA_SET}',members:[{_id:0,host:'mongo:27017'}]})
}

db.createUser(
  {
    user: "${MONGO_ADMIN_USERNAME}",
    pwd: "${admin_password}",
    roles: [ { role: "userAdminAnyDatabase", db: "admin" }, "readWriteAnyDatabase" ]
  }
)
EOF

mongod_base --pidfilepath="$init_pidfile" --shutdown
rm -f "$init_pidfile"

exec mongod_base run "$@"
