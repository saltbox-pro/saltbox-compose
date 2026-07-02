#! /bin/bash
set -eu -o pipefail

declare -r base_env_file='base.env'
declare -r local_env_file='override.env'
declare -r separators=',:'
declare -r extra_env_var='_UPDATE_AND_RUN_EXTRA_ENV_FILES'

function warn() {
  1>&2 echo "$@"
}

function err() {
  warn "$@"
  exit 1
}

function print_help() {
  printf '%b' "
Update images and run a Salt.Box Docker Compose based instance.

Usage: $0 [-h|--help] COMMAND

  get VARIABLE\t\tGet value of VARIABLE
  env-files\t\tPrint ordered paths of all configured Salt.Box Compose \
dotenv-files, one per line
  extra-env-files\tGet splitted ${extra_env_var}, one value per line
  -h|--help\t\tPrint this message

Script ignores any extra args after command.
"
}

function get_extra_env_files() {
  # shellcheck source=/dev/null
  IFS="$separators" read -ra extra_env_files <<< "$(
    source "$base_env_file"
    if [[ -f "$local_env_file" ]]
    then source "$local_env_file"
    else warn "No '$local_env_file' file"
    fi
    echo "${!extra_env_var}"
  )"
  for env_path in "${extra_env_files[@]}"; do
    echo "$env_path"
  done
}

function get_all_env_files() {
  echo "$base_env_file"
  get_extra_env_files
  if [ -f "$local_env_file" ]; then
    echo "$local_env_file"
  else
    warn "File $local_env_file excluded"
  fi
}

function get_var() {
  var=$1
  envs=$(set -e && get_all_env_files)
  (
    for line in $envs; do
      # shellcheck source=/dev/null
      source "$line"
    done
    if [[ ! -v "$var" ]]; then
      err "Variable '$var' not found in dotfiles"
    fi
    echo "${!var}"
  ) || exit $?
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help) print_help && exit 0 ;;
    get) shift && get_var "$1" && exit 0 ;;
    extra-env-files) get_extra_env_files && exit 0 ;;
    env-files) get_all_env_files && exit 0 ;;
    *) err "Unexpected arg $1" ;;
  esac
done

print_help

# vi: sw=2
