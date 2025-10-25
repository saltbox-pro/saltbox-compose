#! /bin/bash

set -e

info() {
  echo "> $*"
}

warn() {
  1>&2 info "$@"
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

mongod_noauth=(
  gosu "${pam_user}" mongod
  --config "$MONGOD_CONF_FILE"
)

mongod_auth=(
  gosu "${pam_user}" mongod
  --config "$MONGOD_CONF_FILE"
  --replSet "$MONGOD_REPLICA_SET"
  --keyFile "$key_file"
)

await_mongod() {
  info 'Waiting for mongod responce'
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
}

init() {
  init_pidfile='/tmp/docker-entrypoint-mongod.pid'
  rm -f "$init_pidfile"

  mongosh_cmd=(gosu "$pam_user" mongosh)

  info 'Run MongoDB local init instance'
  "${mongod_noauth[@]}" --noauth --pidfilepath="$init_pidfile" --fork --syslog run
  await_mongod
  "${mongosh_cmd[@]}" --file '/etc/mongo/init/drop_stale_replset.js'
  info 'Shutting down the local init instance'
  "${mongod_noauth[@]}" --pidfilepath="$init_pidfile" --shutdown
  rm -f "$init_pidfile"

  info 'Run MongoDB init instance'
  "${mongod_auth[@]}" --transitionToAuth --pidfilepath="$init_pidfile" --fork --syslog run
  await_mongod
  info 'Init replica set'
  "${mongosh_cmd[@]}" --file '/etc/mongo/init/replica_set.js'
  info 'Recreate users'
  env \
    MONGO_ROOT_PASSWORD="$(cat "$MONGO_ROOT_PASSWORD_FILE")" \
    MONGO_USER_PASSWORD="$(cat "$MONGO_USER_PASSWORD_FILE")" \
    "${mongosh_cmd[@]}" --file '/etc/mongo/init/users.js'
  info 'Shutting down the init instance'
  "${mongod_auth[@]}" --pidfilepath="$init_pidfile" --shutdown
  rm -f "$init_pidfile"

  touch "$init_mark_file"
  info 'MongoDB init finished'
}

init

cmd=("${mongod_auth[@]}" run "$@")
info "$ ${cmd[*]}"
exec "${cmd[@]}"
