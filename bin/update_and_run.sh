#! /bin/bash
set -e

override_env='override.env'
env_file='.env'
usage_str="
Update images and run a Salt.Box Docker Compose based instance.

Usage: sudo ./bin/update_and_run.sh [-d|--detach] [-h|--help] [SERVICE]...

  -d|--detach\tDetach Docker Compose after start
  -f|--force\tRewrite with no confirmation
  -h|--help\tPrint this message
  -l|--login\tTry to login to registry
  -n|--no-pull\tDo not pull newer images from registry
  --only-env\tOnly merge example.env and override.env and exit
  --only-update\tOnly merge .env file and update images
  -w|--watch\tEnable Docker Compose watch for developement

Last --only-* flag overrides preceding.
"
declare -r admin_password_file='secrets/saltbox_admin_password'
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

warn() {
  1>&2 echo "$@"
}

err() {
  warn "$@"
  exit 1
}

up_args=('--remove-orphans')
detach_flag=0
force_flag=0
pull_flag=1
login_flag=0
last_stage='up'

for i in "$@"; do
  # shellcheck disable=SC2059
  case $i in
    -d|--detach) detach_flag=1 ;;
    -f|--force) force_flag=1 ;;
    -h|--help) printf "$usage_str" && exit 0 ;;
    -l|--login) login_flag=1 ;;
    -n|--no-pull) pull_flag=0 ;;
    --only-env) last_stage='dotenv';;
    --only-update) last_stage='build' ;;
    -w|--watch) up_args+=('--watch') ;;
    -*) err "Unknown option $i" ;;
    *) up_args+=("$i") ;;
  esac
done

if [ $detach_flag = 1 ]; then up_args+=('--detach'); fi

if [ "$(id -u)" -ne 0 ]; then
  err "Root access required, try sudo $0"
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

if [ $last_stage = 'dotenv' ]; then exit 0; fi

(set -x; ./bin/make_secrets.py)

if [ $login_flag = 1 ]; then
  # shellcheck source=/dev/null
  registry=$(
    source "$env_file"
    echo "$IMAGE_REGISTRY" | cut --delimiter '/' --fields 1
  )

  if [ -z "$registry" ]; then
    err "Failed to get registry from $env_file"
  fi
  (set -x; docker login "$registry")
fi

if [ $pull_flag = 1 ]; then
  (set -x; docker compose pull --ignore-buildable)
fi

(set -x; docker compose build)

if [ $last_stage = 'build' ]; then exit 0; fi

(set -x; docker compose down)

# shellcheck source=/dev/null
admin_username=$(source "$env_file" && echo "$SALTBOX_ADMIN_USERNAME")
admin_password="$(cat "$admin_password_file")"
if [ $detach_flag = 0 ]; then
  # shellcheck disable=SC2059
  printf "$success_pre_msg_tpl" "${admin_username}" "$admin_password"
  sleep 2
fi

(set -x; docker compose up "${up_args[@]}")

if [ $detach_flag = 1 ]; then
  # shellcheck disable=SC2059
  printf "$success_post_msg_tpl" "${admin_username}" "$admin_password"
fi
