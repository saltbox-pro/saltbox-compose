#! /bin/sh
set -e

init_pidfile='/tmp/docker-entrypoint-mongod.pid'

warn() {
  1>&2 echo "$@"
}

err() {
  warn "$@"
  exit 1
}

if [ -e "$init_pidfile" ]; then
    err 'Initialization seems in progress'
fi

mongosh 'admin' --eval 'db.hello()'
