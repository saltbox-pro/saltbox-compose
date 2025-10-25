#! /bin/bash

set -e

warn() {
  1>&2 echo "$@"
}

err() {
  warn "$@"
  exit 1
}

pam_user='mongod'
data_dir='/var/lib/mongo/'
init_mark_file="${data_dir}/.inited"

key_file='/etc/mongo/key'
install -m 400 -o "${pam_user}" -g "${pam_user}" "$MONGOD_KEY_FILE" "$key_file"

chown --recursive "${pam_user}:${pam_user}" "$data_dir"

mongod_base=(
  gosu "${pam_user}" mongod
  --config "$MONGOD_CONF_FILE"
  --replSet "$MONGOD_REPLICA_SET"
)

init() {
  init_pidfile='/tmp/docker-entrypoint-mongod.pid'
  rm -f "$init_pidfile"

  mongosh_cmd=(gosu "$pam_user" mongosh)

  echo 'Run MongoDB init instance'
  "${mongod_base[@]}" --noauth --pidfilepath="$init_pidfile" --fork --syslog run

  try="$WAIT_FOR_INIT"
  while true; do
    if "${mongosh_cmd[@]}" 'admin' --eval 'quit(0)'; then
      break
    fi
    (( try-- ))
    if [ "$try" -le 0 ]; then
      err "MongoDB did not response in ${WAIT_FOR_INIT} seconds for init"
    fi
    sleep 1
  done

  echo 'Run init.js script'
  env \
    MONGO_ROOT_PASSWORD="$(cat "$MONGO_ROOT_PASSWORD_FILE")" \
    MONGO_USER_PASSWORD="$(cat "$MONGO_USER_PASSWORD_FILE")" \
    "${mongosh_cmd[@]}" --file /etc/mongo/init.js

  echo 'Shutting down the init instance'
  "${mongod_base[@]}" --keyFile "$key_file" --pidfilepath="$init_pidfile" --shutdown
  rm -f "$init_pidfile"
  touch "$init_mark_file"
  echo 'MongoDB init finished'
}

if [ ! -f "$init_mark_file" ]; then
  init;
else
  echo 'MongoDB instance is already initialized'
fi

cmd=("${mongod_base[@]}" --keyFile "$key_file" run "$@")
echo "$ ${cmd[*]}"
exec "${cmd[@]}"
