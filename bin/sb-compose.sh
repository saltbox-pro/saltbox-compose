#! /bin/bash

declare -r env_file='.env'
declare -a compose_args

function set_extra_env_files {
  # shellcheck source=/dev/null
  IFS=',' read -ra env_files <<< "$(source "$env_file" && echo "$_UPDATE_AND_RUN_EXTRA_ENV_FILES")"
  for env_path in "${env_files[@]}"; do
    compose_args+=("--env-file=$env_path")
  done
}

set_extra_env_files
compose_args+=('--env-file=.env')

exec docker compose "${compose_args[@]}" "$@"
