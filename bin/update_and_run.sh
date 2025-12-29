#! /bin/bash
set -e

declare -r override_env='override.env'
declare -r env_file='.env'
bin_dir="$(dirname "$(realpath --relative-to "$(pwd)" "$0")")"
declare -r bin_dir
declare -r compose_cmd="${bin_dir}/sb-compose.sh"
declare -r admin_password_file='secrets/saltbox_admin_password'
declare -ir msg_sleep=2
declare -ir image_pull_retries=3
declare -r usage_str="
Update images and run a Salt.Box Docker Compose based instance.

Usage: ./bin/update_and_run.sh [-d|--detach] [-h|--help] [SERVICE]...

  -d|--detach\t\tDetach Docker Compose after start
  --drop-data\t\tDelete all volumes before start!
  -f|--force\t\tRewrite with no confirmation
  -h|--help\t\tPrint this message
  -l|--login\t\tTry to login to registry
  -n|--no-pull\t\tAvoid to update current repository and images from Internet
  --no-git-pull\t\tDo not pull current repository even if possible
  --no-image-pull\tDo not pull newer images from registry
  --no-root\t\tDo not use sudo, run by current user
  --only-env\t\tOnly merge example.env and override.env and exit
  --only-update\t\tOnly merge .env file and update images
  -w|--watch\t\tEnable Docker Compose watch for developement

Last --only-* flag overrides preceding.
"
declare -r success_pre_msg_tpl='
 ####################################################
######################################################
##                                                  ##
## Salt.Box Compose will be started now.            ##
##                                                  ##
## Basic administrator: %-27s ##
## Password: %-38s ##
##                                                  ##
######################################################
 ####################################################
  #####
  ###
 #
'
declare -r success_post_msg_tpl='
 #
  ###
  #####
 ####################################################
######################################################
##                                                  ##
## Salt.Box Compose has been started.               ##
##                                                  ##
## Basic administrator: %-27s ##
## Password: %-38s ##
##                                                  ##
######################################################
 ####################################################
'

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
    sudo "$@"
  else
    "$@"
  fi
}

function git_pull_required() {
  local branch

  if [ $git_pull_flag = 0 ]; then
    echo 0
    return
  fi

  if ! branch=$(git branch --show-current 2> /dev/null); then
    warn Error on running git branch subcommand, skipping git pull
    echo 0
    return
  fi

  if [ -z "$branch" ]; then
    warn No current Git branch, skipping git pull
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
make_secrets_arg=('secrets.json')
down_args=()
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
    --no-git-pull) git_pull_flag=0 ;;
    --no-image-pull) image_pull_flag=0 ;;
    --no-root) no_root_flag=1 ;;
    --only-env) last_stage='dotenv';;
    --only-update) last_stage='build' ;;
    -w|--watch) up_args+=('--watch') ;;
    -*) err "Unknown option $i" ;;
    *) up_args+=("$i") ;;
  esac
done

if sudo_predic; then
  msg="Failed to execute by root. Run by root or configure sudo for the user."
  sudo --validate || err "$msg"
fi

if [ $detach_flag = 1 ]; then up_args+=('--detach'); fi

if [ "$(git_pull_required)" = 1 ]; then
  echo_run ./bin/git_pull_dev_repos.py --only-compose
fi

if [ -f "$env_file" ]; then
  if [ $force_flag = 0 ]; then
    read -p "File '$env_file' already exists, overwrite? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      rm "$env_file"
    else
      warn "Using existing '$env_file'"
    fi
  else
    rm "$env_file"
  fi
fi

if [ ! -f "$env_file" ]; then
  cat example.env > "$env_file"

  if [ -f "$override_env" ]; then
    cat "$override_env" >> "$env_file"
  else
    warn "No $override_env file, using defaults"
  fi

  chown "$(stat -c %u:%g .)" "$env_file"
  echo "New $env_file has been created"
fi


function on_env_validation_fail() {
  if [ $force_flag = 1 ]; then
    warn 'Adviced to correct override.env or .env'
    sleep $msg_sleep
  else
    read -p "Warning on the .env file. Continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 0; fi
  fi
}

echo_run ./bin/validate_dotenv.py || on_env_validation_fail

if [ $last_stage = 'dotenv' ]; then exit 0; fi

if [ "$(git_pull_required)" = 1 ]; then
  echo_run ./bin/git_pull_dev_repos.py --no-compose
fi

# shellcheck source=/dev/null
IFS=',' read -ra make_secrets_confs <<< "$(source "$env_file" && echo "$_UPDATE_AND_RUN_EXTRA_SECRETS_CONFS")"
make_secrets_arg+=("${make_secrets_confs[@]}")
echo_run ./bin/make_secrets.py "${make_secrets_arg[@]}"

if [ $login_flag = 1 ]; then
  # shellcheck source=/dev/null
  registry=$(
    source "$env_file"
    echo "$IMAGE_REGISTRY" | cut --delimiter '/' --fields 1
  )

  if [ -z "$registry" ]; then
    err "Failed to get registry from $env_file"
  fi
  echo_run as_root docker login "$registry"
fi


if [ $image_pull_flag = 1 ]; then
  retry $image_pull_retries echo_run as_root "$compose_cmd" pull --ignore-buildable
fi

echo_run as_root "$compose_cmd" build

if [ $last_stage = 'build' ]; then exit 0; fi

if [ $drop_data_flag = 1 ]; then
  if [ $force_flag = 1 ]; then
    down_args+=('--volumes')
  else
    read -p "Delete volumes? IT MEANS SYSTEM DATA LOSS (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      down_args+=('--volumes')
    else
      warn "Skipping data deletion"
    fi
  fi
fi

echo_run as_root "$compose_cmd" down "${down_args[@]}"


# shellcheck source=/dev/null
admin_username=$(source "$env_file" && echo "$SALTBOX_ADMIN_USERNAME")
admin_password="$(cat "$admin_password_file")"
if [ $detach_flag = 0 ]; then
  # shellcheck disable=SC2059
  printf "$success_pre_msg_tpl" "${admin_username}" "$admin_password"
  sleep $msg_sleep
fi

echo_run as_root "$compose_cmd" up "${up_args[@]}"

if [ $detach_flag = 1 ]; then
  # shellcheck disable=SC2059
  printf "$success_post_msg_tpl" "${admin_username}" "$admin_password"
fi
