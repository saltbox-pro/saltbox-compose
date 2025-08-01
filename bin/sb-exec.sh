#! /bin/bash
# shellcheck disable=SC2016

# Salt.Box Compose helper script to run some common commands in containers.
#
# Running `salt` on the default Master example:
#
#   sudo ./bin/sb-exec.sh salt '*' test.ping

set -e

cmd=(docker compose exec)

function warn() {
  # shellcheck disable=SC2059
  1>&2 printf "$@"
}

function err() {
  warn "$@"
  exit 1
}

function check_docker_access() {
  docker compose logs --tail 0 > /dev/null 2>&1 \
    || err '\nFailed to connect to Docker. `sudo` required?\n'
}

err_msg='
Unknown command, valid commands are:

  salt\tRuns `salt` on salt-master
'

case $1 in
  salt) cmd+=(salt-master salt) ;;
  *) err "$err_msg" ;;
esac

shift
cmd+=("$@")

check_docker_access

echo "$ ${cmd[*]}"
exec "${cmd[@]}"
