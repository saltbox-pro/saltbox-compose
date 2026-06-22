#! /bin/bash
set -eu -o pipefail

declare -r base_env_file='base.env'
declare -r local_env_file='override.env'

declare -a compose_args=("--env-file=${base_env_file}")

function set_extra_env_files {
  # shellcheck source=/dev/null
  IFS=',' read -ra extra_env_files <<< "$(
    source "$base_env_file"
    if [[ -f "$local_env_file" ]]
    then source "$local_env_file"
    else echo "No '$local_env_file' file" >&2
    fi
    echo "$_UPDATE_AND_RUN_EXTRA_ENV_FILES"
  )"
  for env_path in "${extra_env_files[@]}"; do
    compose_args+=("--env-file=${env_path}")
  done
  if [ -f "$local_env_file" ]; then
    compose_args+=("--env-file=${local_env_file}")
  fi
}

set_extra_env_files

cmd=('docker' 'compose' "${compose_args[@]}" "$@")

echo "$ ${cmd[*]}" >&2
echo >&2

exec docker compose "${compose_args[@]}" "$@"

# vi: shiftwidth=2
