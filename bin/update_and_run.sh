#! /bin/bash
set -eu -o pipefail

declare -r override_env='override.env'
declare -r deprecated_env='.env'
bin_dir="$(dirname "$(realpath --relative-to "$(pwd)" "$0")")"
declare -r bin_dir
declare -r compose_cmd="${bin_dir}/sb-compose.sh"
declare -r admin_password_file='secrets/saltbox_admin_password'
declare -ir msg_sleep=4
declare -ir image_pull_retries=3
declare -r usage_str="
Update images and run a Salt.Box Docker Compose based instance.

Usage: ./bin/update_and_run.sh [-d|--detach] [-h|--help] [SERVICE]...

  -d|--detach\t\tDetach Docker Compose after start
  --drop-data\t\tDelete all volumes before start!
  -f|--force\t\tNo confirmations
  -h|--help\t\tPrint this message
  -l|--login\t\tTry to login to registry
  -n|--no-pull\t\tAvoid to update current repository and images from Internet
  --no-git-pull\t\tDo not pull current repository even if possible
  --no-image-pull\tDo not pull newer images from registry
  --no-progress\t\tHide progress bars, good for CI
  --no-root\t\tDo not use sudo, run by current user
  --only-update\t\tOnly update images and exit
  -w|--watch\t\tEnable Docker Compose watch for developement

Last --only-* flag overrides preceding.
"
declare -r success_msg_tpl='
   ####################################################
 ########################################################
##                                                      ##
## Salt.Box Compose will start soon                     ##
##                                                      ##
## URL: %-47s ##
## Basic administrator: %-31s ##
## Password: %-42s ##
##                                                      ##
 ########################################################
   ####################################################
'

function success_msg() {
  post=${1:-0}
  admin_username=$(get_env_var 'SALTBOX_ADMIN_USERNAME')
  admin_password="$(cat "$admin_password_file")"
  sb_url="https://$(get_env_var 'WEB_SERVER_OUTER_SOCKET')"
  if [ "$post" == 1 ]; then
    printf '    #\n    ###\n    ####'
  fi
  # shellcheck disable=SC2059
  printf "$success_msg_tpl" "$sb_url" "$admin_username" "$admin_password"
  if [ "$post" != 1 ]; then
    printf '    #####\n    ###\n    #\n'
    sleep $msg_sleep
  else
    printf '\n'
  fi
}

function warn() {
  1>&2 echo "$@"
}

function err() {
  warn "$@"
  exit 1
}

function echo_run() {
  echo ">>> $*"
  "$@"
}

function sudo_predic() {
  [ $no_root_flag = 0 ] && [ "$(id -u)" -ne 0 ]
}

function as_root() {
  if sudo_predic; then
    SHELL="$BASH" sudo --shell "$@"; return $?
  else
    "$@"
  fi
}

function get_env_var() {
  "${bin_dir}/dotenv_tool.sh" get "${1}"
}

function git_pull_required() {
  local branch

  if [ $git_pull_flag = 0 ]; then
    echo 0
    return
  fi

  if ! branch=$(git branch --show-current 2> /dev/null); then
    warn "Error on running git branch subcommand, skipping 'git pull'"
    echo 0
    return
  fi

  if [ -z "$branch" ]; then
    warn 'No current Git branch, skipping git pull'
    echo 0
    return
  fi

  echo 1
}

function retry() {
  local -i retries=$1
  shift

  local -i counter=0

  until "$@"; do
    (( counter += 1 ))
    if [ $counter -ge $retries ]; then
      echo "Command failed after $retries attempts"
      return 1
    fi
    echo "Attempt $counter/$retries"
    sleep 1
  done
}

up_args=('--remove-orphans')
pull_args=('--ignore-buildable')
make_secrets_arg=('secrets.json')
down_args=()
down_drop_args=('--volumes' '--remove-orphans')
detach_flag=0
drop_data_flag=0
force_flag=0
git_pull_flag=1
image_pull_flag=1
login_flag=0
no_root_flag=0
last_stage='up'

for i in "$@"; do
  # shellcheck disable=SC2059
  case $i in
    -d|--detach) detach_flag=1 ;;
    --drop-data) drop_data_flag=1 ;;
    -f|--force) force_flag=1 ;;
    -h|--help) printf "$usage_str" && exit 0 ;;
    -l|--login) login_flag=1 ;;
    -n|--no-pull) git_pull_flag=0; image_pull_flag=0 ;;
    --no-progress) pull_args+=('--quiet') ;;
    --no-git-pull) git_pull_flag=0 ;;
    --no-image-pull) image_pull_flag=0 ;;
    --no-root) no_root_flag=1 ;;
    --only-update) last_stage='build' ;;
    -w|--watch) up_args+=('--watch') ;;
    -*) err "Unknown option $i" ;;
    *) up_args+=("$i") ;;
  esac
done

# Update sudo cached credentials
if sudo_predic; then
  msg="Failed to execute by root. Run by root or configure sudo for the user."
  sudo --validate || err "$msg"
fi

# Docker smoke-test
as_root docker version > /dev/null && err=0 || err=$?
if [ "$err" -eq 1 ]; then
  warn ''
  warn "Failed to connecto to \`dockerd\`"
  err "Run again with \`--no-root\` flag if docker command not requires to be run as root."
elif [ "$err" -eq 127 ]; then
  warn ''
  err "Failed to run \`docker\`. Check required Docker version is installed."
elif [ "$err" -ne 0 ]; then
  warn ''
  err "Unexpected error on \`docker version\` command, retcode was ${err}"
fi

if [ $detach_flag = 1 ]; then up_args+=('--detach'); fi


# Update dev stuff, if can
if [ "$(git_pull_required)" = 1 ]; then
  echo_run ./bin/git_pull_dev_repos.py --only-compose
fi

if [[ ! -f "$override_env" ]]; then
  warn "No '${override_env}' file, using defaults"
  sleep $msg_sleep
fi

if [[ -f "$deprecated_env" ]]; then
  warn "FOUND DEPRECATED '${deprecated_env}' FILE"
  warn "Deprecated '${deprecated_env}' will not be used"
  sleep $msg_sleep
fi

function on_env_validation_fail() {
  if [ $force_flag = 1 ]; then
    warn "Adviced to correct '${override_env}'"
    sleep $msg_sleep
  else
    read -p "Warning on the '${override_env}' file. Continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 0; fi
  fi
}

echo_run ./bin/validate_dotenv.py || on_env_validation_fail

if [ "$(git_pull_required)" = 1 ]; then
  echo_run ./bin/git_pull_dev_repos.py --no-compose
fi

secr_confs=$(bin/dotenv_tool.sh extra-secrets-confs)
make_secrets_confs=()
if [[ ! -z "$secr_confs" ]]; then
    mapfile -t make_secrets_confs <<< "$secr_confs"
fi
make_secrets_arg+=("${make_secrets_confs[@]}")
echo_run ./bin/make_secrets.py "${make_secrets_arg[@]}"

if [ $login_flag = 1 ]; then
  registry=$(get_env_var 'IMAGE_REGISTRY' | cut --delimiter '/' --fields 1)

  if [ -z "$registry" ]; then
    err "Failed to get registry from dotenv files IMAGE_REGISTRY variable"
  fi
  echo_run as_root docker login "$registry"
fi


if [ $image_pull_flag = 1 ]; then
  retry $image_pull_retries echo_run as_root "$compose_cmd" pull "${pull_args[@]}"
fi

echo_run as_root "$compose_cmd" build

if [ $last_stage = 'build' ]; then exit 0; fi

if [ $drop_data_flag = 1 ]; then
  if [ $force_flag = 1 ]; then
      REPLY='y'
  else
    read -p "Delete volumes? IT MEANS SYSTEM DATA LOSS (y/n): " -n 1 -r
    echo
  fi
  if [[ $REPLY =~ ^[Yy]$ ]]; then
      down_args+=("${down_drop_args[@]}")
  else
      warn "Skipping data deletion"
  fi
fi

echo_run as_root "$compose_cmd" down "${down_args[@]}"

if [ $detach_flag = 0 ]; then success_msg; fi

echo_run as_root "$compose_cmd" up "${up_args[@]}"

if [ $detach_flag = 1 ]; then success_msg 1; fi

# vi: shiftwidth=2
